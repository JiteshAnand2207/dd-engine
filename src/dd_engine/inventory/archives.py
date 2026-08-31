"""Bounded ZIP central-directory inspection with no filesystem extraction."""

from __future__ import annotations

import re
import stat
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from dd_engine.inventory.models import ArchiveInspection, ArchiveMember, RegisterLimits

_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


def canonical_relative_path(value: str) -> str:
    """Normalize Windows/POSIX separators and reject non-relative traversal."""

    if not value or "\x00" in value:
        raise ValueError("path is empty or contains a null byte")
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or _DRIVE_PREFIX.match(normalized):
        raise ValueError("absolute paths and drive prefixes are forbidden")
    path = PurePosixPath(normalized)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("relative traversal or ambiguous path components are forbidden")
    return path.as_posix()


def _member_safety_error(info: zipfile.ZipInfo) -> str | None:
    name = info.filename
    if "\\" in name:
        return "backslash archive path is unsafe on cross-platform extraction"
    try:
        canonical_relative_path(name)
    except ValueError as exc:
        return str(exc)
    unix_mode = (info.external_attr >> 16) & 0xFFFF
    if unix_mode and stat.S_ISLNK(unix_mode):
        return "symbolic-link archive member is forbidden"
    if info.flag_bits & 0x1:
        return "encrypted archive member is not read during registration"
    return None


def _zip_modified_time(info: zipfile.ZipInfo) -> str | None:
    try:
        year, month, day, hour, minute, second = info.date_time
        return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
    except (TypeError, ValueError):
        return None


def _read_member(
    archive: zipfile.ZipFile, info: zipfile.ZipInfo, maximum_bytes: int
) -> tuple[bytes | None, str | None]:
    chunks: list[bytes] = []
    observed = 0
    try:
        with archive.open(info, "r") as handle:
            while True:
                chunk = handle.read(min(1024 * 1024, maximum_bytes + 1 - observed))
                if not chunk:
                    break
                observed += len(chunk)
                if observed > maximum_bytes:
                    return None, "archive member exceeded the configured read limit"
                chunks.append(chunk)
    except Exception as exc:
        return None, f"archive member could not be read safely: {exc}"
    if observed != info.file_size:
        return None, (
            f"archive member size mismatch: central directory={info.file_size}, observed={observed}"
        )
    return b"".join(chunks), None


def inspect_zip(
    archive_path: Path, container_relative_path: str, limits: RegisterLimits
) -> ArchiveInspection:
    """Inspect every direct ZIP member in memory without extracting any path."""

    try:
        archive = zipfile.ZipFile(archive_path)
    except (OSError, ValueError, zipfile.BadZipFile, NotImplementedError) as exc:
        return ArchiveInspection((), f"invalid ZIP container: {exc}", (), ())

    with archive:
        infos = archive.infolist()
        file_infos = [info for info in infos if not info.is_dir()]
        directory_infos = [info for info in infos if info.is_dir()]
        duplicate_counts = Counter(info.filename for info in file_infos)
        occurrences: defaultdict[str, int] = defaultdict(int)
        warnings: list[str] = []
        global_errors: list[str] = []
        total_uncompressed = sum(max(info.file_size, 0) for info in file_infos)
        if len(file_infos) > limits.max_archive_members:
            global_errors.append(
                "archive member-count limit exceeded: "
                f"{len(file_infos)} > {limits.max_archive_members}"
            )
        if total_uncompressed > limits.max_archive_total_uncompressed_bytes:
            global_errors.append(
                "archive total-uncompressed-size limit exceeded: "
                f"{total_uncompressed} > {limits.max_archive_total_uncompressed_bytes}"
            )
        if global_errors:
            warnings.extend(global_errors)

        archive_directories: list[dict[str, object]] = []
        for index, info in enumerate(directory_infos, start=1):
            safety_error = _member_safety_error(info)
            if safety_error is None:
                normalized = canonical_relative_path(info.filename.rstrip("/"))
                virtual_path = f"zip://{container_relative_path}!/{normalized}/"
                prefix = f"{normalized}/"
                empty: bool | None = not any(
                    candidate.filename != info.filename
                    and candidate.filename.replace("\\", "/").startswith(prefix)
                    for candidate in infos
                )
            else:
                virtual_path = f"zip://{container_relative_path}!/__unsafe_directory_{index:04d}__/"
                empty = None
            archive_directories.append(
                {
                    "archive_member_name": info.filename,
                    "empty": empty,
                    "error": safety_error,
                    "path": virtual_path,
                    "safe": safety_error is None,
                }
            )

        members: list[ArchiveMember] = []
        observed_total_uncompressed = 0
        for index, info in enumerate(file_infos, start=1):
            occurrences[info.filename] += 1
            occurrence = occurrences[info.filename]
            member_warnings: list[str] = []
            safety_error = _member_safety_error(info)
            if duplicate_counts[info.filename] > 1:
                member_warnings.append("duplicate_archive_member_name")
            if safety_error is None:
                normalized = canonical_relative_path(info.filename)
                virtual_path = f"zip://{container_relative_path}!/{normalized}"
                if occurrence > 1:
                    virtual_path += f"#entry-{occurrence:04d}"
            else:
                virtual_path = f"zip://{container_relative_path}!/__unsafe_member_{index:04d}__"

            error = safety_error
            if error is None and global_errors:
                error = "; ".join(global_errors)
            if error is None and info.file_size > limits.max_archive_member_uncompressed_bytes:
                error = (
                    "archive member-uncompressed-size limit exceeded: "
                    f"{info.file_size} > {limits.max_archive_member_uncompressed_bytes}"
                )

            data: bytes | None = None
            if error is None:
                remaining_total = (
                    limits.max_archive_total_uncompressed_bytes - observed_total_uncompressed
                )
                if remaining_total <= 0:
                    error = "archive total-uncompressed-size read budget exhausted"
            if error is None:
                data, error = _read_member(
                    archive,
                    info,
                    min(
                        limits.max_archive_member_uncompressed_bytes,
                        remaining_total,
                    ),
                )
                if data is not None:
                    observed_total_uncompressed += len(data)
            members.append(
                ArchiveMember(
                    archive_member_index=index,
                    archive_member_name=info.filename,
                    compressed_size_bytes=info.compress_size,
                    crc32=f"{info.CRC:08x}",
                    data=data,
                    error=error,
                    modified_time=_zip_modified_time(info),
                    size_bytes=info.file_size,
                    virtual_path=virtual_path,
                    warnings=tuple(member_warnings),
                )
            )
        return ArchiveInspection(
            directories=tuple(archive_directories),
            error=None,
            members=tuple(members),
            warnings=tuple(dict.fromkeys(warnings)),
        )
