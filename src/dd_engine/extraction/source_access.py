"""Read registered physical and ZIP-member sources without mutating the room."""

from __future__ import annotations

import hashlib
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from dd_engine.artifacts import file_sha256
from dd_engine.errors import SourceIntegrityError


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _physical_path(room_root: Path, relative_path: str) -> Path:
    posix = PurePosixPath(relative_path)
    if posix.is_absolute() or any(part in {"", ".", ".."} for part in posix.parts):
        raise SourceIntegrityError(f"registered source path is unsafe: {relative_path}")
    candidate = room_root.joinpath(*posix.parts)
    if _is_link_like(candidate):
        raise SourceIntegrityError(f"registered source became link-like: {relative_path}")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise SourceIntegrityError(
            f"registered source is unavailable: {relative_path}: {exc}"
        ) from exc
    if not resolved.is_relative_to(room_root) or not resolved.is_file():
        raise SourceIntegrityError(f"registered source escaped the room: {relative_path}")
    return resolved


def _verify_hash(path: Path, expected: str, label: str) -> None:
    try:
        observed = file_sha256(path)
    except OSError as exc:
        raise SourceIntegrityError(f"cannot hash {label}: {exc}") from exc
    if observed != expected:
        raise SourceIntegrityError(
            f"source checksum mismatch for {label}: registered={expected}, observed={observed}"
        )


def _read_bounded_member(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    *,
    maximum_member_bytes: int,
) -> bytes:
    if info.file_size > maximum_member_bytes:
        raise SourceIntegrityError(
            "archive member exceeds the registered extraction limit: "
            f"{info.file_size} > {maximum_member_bytes}"
        )
    chunks: list[bytes] = []
    observed = 0
    try:
        with archive.open(info, "r") as handle:
            while True:
                chunk = handle.read(min(1024 * 1024, maximum_member_bytes + 1 - observed))
                if not chunk:
                    break
                observed += len(chunk)
                if observed > maximum_member_bytes:
                    raise SourceIntegrityError("archive member exceeded its extraction read limit")
                chunks.append(chunk)
    except SourceIntegrityError:
        raise
    except Exception as exc:
        raise SourceIntegrityError(f"archive member could not be read safely: {exc}") from exc
    if observed != info.file_size:
        raise SourceIntegrityError(
            f"archive member size mismatch: registered={info.file_size}, observed={observed}"
        )
    return b"".join(chunks)


def read_registered_source(
    room_root: Path,
    source: dict[str, Any],
    sources_by_id: dict[str, dict[str, Any]],
    register_limits: dict[str, Any],
) -> bytes:
    """Resolve one registered source and prove its bytes still match the register."""

    expected = source.get("sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise SourceIntegrityError("registered source has no usable SHA-256 checksum")

    container_id = source.get("container_source_id")
    if container_id is None:
        relative_path = str(source["relative_path"])
        if relative_path.startswith("zip://"):
            raise SourceIntegrityError("virtual source has no registered container")
        path = _physical_path(room_root, relative_path)
        _verify_hash(path, expected, relative_path)
        try:
            return path.read_bytes()
        except OSError as exc:
            raise SourceIntegrityError(
                f"cannot read registered source {relative_path}: {exc}"
            ) from exc

    container = sources_by_id.get(str(container_id))
    if container is None:
        raise SourceIntegrityError(f"archive container source is missing: {container_id}")
    container_hash = container.get("sha256")
    if not isinstance(container_hash, str):
        raise SourceIntegrityError(f"archive container has no checksum: {container_id}")
    container_path = _physical_path(room_root, str(container["relative_path"]))
    _verify_hash(container_path, container_hash, str(container["relative_path"]))

    index = source.get("archive_member_index")
    member_name = source.get("archive_member_name")
    if not isinstance(index, int) or index < 1 or not isinstance(member_name, str):
        raise SourceIntegrityError("archive member has an invalid registered locator")
    maximum = register_limits.get("max_archive_member_uncompressed_bytes")
    if not isinstance(maximum, int) or maximum <= 0:
        raise SourceIntegrityError("source register contains invalid archive limits")
    try:
        with zipfile.ZipFile(container_path) as archive:
            infos = [item for item in archive.infolist() if not item.is_dir()]
            if index > len(infos):
                raise SourceIntegrityError("registered archive member index no longer exists")
            info = infos[index - 1]
            if info.filename != member_name:
                raise SourceIntegrityError(
                    "archive member name changed at registered index: "
                    f"expected={member_name!r}, observed={info.filename!r}"
                )
            payload = _read_bounded_member(
                archive,
                info,
                maximum_member_bytes=maximum,
            )
    except SourceIntegrityError:
        raise
    except (OSError, zipfile.BadZipFile, NotImplementedError) as exc:
        raise SourceIntegrityError(f"cannot reopen registered archive safely: {exc}") from exc

    observed = hashlib.sha256(payload).hexdigest()
    if observed != expected:
        raise SourceIntegrityError(
            "archive-member checksum mismatch: "
            f"registered={expected}, observed={observed}"
        )
    return payload
