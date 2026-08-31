"""Complete deterministic source register and safe-ingestion stage."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import defaultdict
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from dd_engine.artifacts import atomic_write_json, atomic_write_text, file_sha256, load_json
from dd_engine.errors import DDEngineError, InventoryError
from dd_engine.inventory.archives import inspect_zip
from dd_engine.inventory.content import (
    classify_document,
    classify_workstream,
    extension_type_mismatch,
    inspect_bytes,
    inspect_file,
)
from dd_engine.inventory.models import (
    ContentInspection,
    InventoryResult,
    RegisterLimits,
    RegistrationOutcome,
    SourceRecord,
)
from dd_engine.runs import load_manifest
from dd_engine.source_paths import validate_data_room_path, walk_data_room
from dd_engine.state import complete_stage, fail_stage, start_stage

REGISTER_SCHEMA_VERSION = 1
REGISTER_OUTPUTS = (
    "source_register/source_register.json",
    "source_register/source_register.csv",
    "source_register/source_register.md",
    "source_register/room_structure.json",
    "source_register/duplicate_groups.json",
    "source_register/version_families.json",
    "source_register/unreadable_sources.json",
)
_TERMINAL_INVENTORY_STATUSES = frozenset(
    {
        "blocked_unsafe",
        "registered",
        "registered_container",
        "registered_unreadable",
        "registered_unsupported",
    }
)
_VERSION_MARKER = re.compile(
    r"^(?:amend(?:ed|ment)?|draft|final|original|redacted|unredacted|rev(?:ision|ised|ised|\d+)?|revised|v\d+)$"
)
_VERSION_NOISE = frozenset(
    {
        "agreement",
        "and",
        "completed",
        "customer",
        "document",
        "framework",
        "legal",
        "register",
        "response",
        "responses",
        "statutory",
        "updated",
    }
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _stable_json_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _modified_time(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def _folder_area(relative_path: str, container_path: str | None = None) -> str:
    if container_path is not None:
        member_name = relative_path.split("!/", 1)[-1].split("#entry-", 1)[0]
        member_parent = PurePosixPath(member_name).parent.as_posix()
        container = PurePosixPath(container_path)
        area = f"{container.parent.as_posix()}/{container.name}"
        if member_parent != ".":
            area = f"{area}/{member_parent}"
        return area.strip("/")
    parent_parts = PurePosixPath(relative_path).parent.parts
    if not parent_parts or parent_parts == (".",):
        return "."
    return "/".join(parent_parts[:2])


def _status_fields(
    inspection: ContentInspection, *, archive_container: bool, blocked: bool
) -> tuple[str, str, bool, bool]:
    if archive_container:
        return "registered_container", "not_applicable_container", False, False
    if blocked:
        return "blocked_unsafe", "blocked", True, False
    if inspection.readability_status in {"unreadable", "encrypted"}:
        return "registered_unreadable", "blocked_unreadable", True, False
    if inspection.readability_status == "unsupported":
        return "registered_unsupported", "unsupported", True, False
    return "registered", "not_started", False, True


def _new_record(
    *,
    relative_path: str,
    filename: str,
    size_bytes: int | None,
    sha256: str | None,
    modified_time: str | None,
    inspection: ContentInspection,
    archive_container: bool = False,
    archive_member_index: int | None = None,
    archive_member_name: str | None = None,
    compressed_size_bytes: int | None = None,
    container_path: str | None = None,
    crc32: str | None = None,
    blocked: bool = False,
    extra_error: str | None = None,
    extra_warnings: tuple[str, ...] = (),
) -> SourceRecord:
    extension = PurePosixPath(filename.replace("\\", "/")).suffix.casefold()
    document_class, document_confidence, document_basis = classify_document(relative_path)
    workstream, workstream_confidence, workstream_basis = classify_workstream(relative_path)
    inventory_status, extraction_status, forced_review, include_in_analysis = _status_fields(
        inspection,
        archive_container=archive_container,
        blocked=blocked,
    )
    warnings = list(dict.fromkeys((*inspection.warnings, *extra_warnings)))
    error = extra_error or inspection.error
    mismatch = extension_type_mismatch(extension, inspection.detected_type)
    if mismatch:
        warnings.append("extension_content_type_mismatch")
    if inspection.detected_type == "zip" and not archive_container:
        warnings.append("nested_archive_registered_but_not_expanded")
    warnings = list(dict.fromkeys(warnings))
    analysis_eligible = not archive_container
    review_required = bool(
        forced_review
        or error
        or warnings
        or mismatch
        or document_class == "unknown"
        or workstream == "unknown"
    )
    return {
        "analysis_eligible": analysis_eligible,
        "analysis_representative": analysis_eligible,
        "archive_member_index": archive_member_index,
        "archive_member_name": archive_member_name,
        "compressed_size_bytes": compressed_size_bytes,
        "container_path": container_path,
        "container_source_id": None,
        "crc32": crc32,
        "detected_mime_type": inspection.detected_mime_type,
        "detected_type": inspection.detected_type,
        "document_class_confidence": document_confidence,
        "duplicate_group": None,
        "error": error,
        "extension": extension,
        "extension_type_mismatch": mismatch,
        "extraction_status": extraction_status,
        "filename": filename,
        "folder_area": _folder_area(relative_path, container_path),
        "identity_key": None,
        "include_in_analysis": include_in_analysis,
        "inventory_status": inventory_status,
        "is_archive_container": archive_container,
        "likely_document_class": document_class,
        "likely_workstream": workstream,
        "modified_time": modified_time,
        "near_duplicate_group": None,
        "probable_version_confidence": 0.0,
        "probable_version_status": "undetermined",
        "readability_status": "blocked" if blocked else inspection.readability_status,
        "relative_path": relative_path,
        "review_required": review_required,
        "same_basename_group": None,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "source_id": None,
        "version_evidence": [],
        "version_family": None,
        "warnings": warnings,
        "classification_evidence": [document_basis, workstream_basis],
        "workstream_confidence": workstream_confidence,
    }


def _physical_record(path: Path, room_root: Path) -> SourceRecord:
    relative_path = path.relative_to(room_root).as_posix()
    size_bytes: int | None = None
    sha256: str | None = None
    stat_error: str | None = None
    try:
        size_bytes = path.stat().st_size
        sha256 = file_sha256(path)
    except OSError as exc:
        stat_error = f"file metadata/hash unavailable: {exc}"
    inspection = inspect_file(path)
    is_container = inspection.detected_type == "zip"
    return _new_record(
        relative_path=relative_path,
        filename=path.name,
        size_bytes=size_bytes,
        sha256=sha256,
        modified_time=_modified_time(path),
        inspection=inspection,
        archive_container=is_container,
        extra_error=stat_error,
    )


def _archive_member_record(member: Any, container_path: str) -> SourceRecord:
    if member.data is None:
        inspection = ContentInspection(None, "not_inspected", "unreadable")
        blocked = True
        sha256 = None
    else:
        inspection = inspect_bytes(member.data, member.archive_member_name)
        blocked = member.error is not None
        sha256 = _sha256_bytes(member.data)
    return _new_record(
        relative_path=member.virtual_path,
        filename=PurePosixPath(member.archive_member_name.replace("\\", "/")).name,
        size_bytes=member.size_bytes,
        sha256=sha256,
        modified_time=member.modified_time,
        inspection=inspection,
        archive_member_index=member.archive_member_index,
        archive_member_name=member.archive_member_name,
        compressed_size_bytes=member.compressed_size_bytes,
        container_path=container_path,
        crc32=member.crc32,
        blocked=blocked,
        extra_error=member.error,
        extra_warnings=member.warnings,
    )


def _identity(record: SourceRecord) -> str:
    value = {
        "archive_member_index": record["archive_member_index"],
        "container_path": record["container_path"],
        "crc32": record["crc32"],
        "relative_path": record["relative_path"],
        "sha256": record["sha256"],
        "size_bytes": record["size_bytes"],
    }
    return _stable_json_hash(value)


def _add_warning(record: SourceRecord, warning: str) -> None:
    warnings = list(record["warnings"])
    if warning not in warnings:
        warnings.append(warning)
    record["warnings"] = warnings
    record["review_required"] = True


def _assign_exact_duplicates(records: list[SourceRecord]) -> list[dict[str, Any]]:
    by_hash: defaultdict[str, list[SourceRecord]] = defaultdict(list)
    for record in records:
        if record["sha256"] is not None and not record["is_archive_container"]:
            by_hash[str(record["sha256"])].append(record)
    groups: list[dict[str, Any]] = []
    candidates = [items for items in by_hash.values() if len(items) > 1]
    candidates.sort(key=lambda items: str(items[0]["relative_path"]).casefold())
    for number, items in enumerate(candidates, start=1):
        group_id = f"DUP-{number:04d}"
        representative = next(
            (item for item in items if item["inventory_status"] == "registered"),
            items[0],
        )
        for item in items:
            item["duplicate_group"] = group_id
            item["analysis_representative"] = item is representative
            if item is not representative:
                item["include_in_analysis"] = False
            _add_warning(item, "exact_checksum_duplicate")
        groups.append(
            {
                "duplicate_group": group_id,
                "kind": "exact_checksum",
                "representative_source_id": representative["source_id"],
                "sha256": representative["sha256"],
                "source_ids": [item["source_id"] for item in items],
                "paths": [item["relative_path"] for item in items],
            }
        )
    return groups


def _assign_same_basename(records: list[SourceRecord]) -> list[dict[str, Any]]:
    by_name: defaultdict[str, list[SourceRecord]] = defaultdict(list)
    for record in records:
        if not record["is_archive_container"]:
            by_name[str(record["filename"]).casefold()].append(record)
    groups = [items for items in by_name.values() if len(items) > 1]
    groups.sort(key=lambda items: str(items[0]["filename"]).casefold())
    result: list[dict[str, Any]] = []
    for number, items in enumerate(groups, start=1):
        group_id = f"NAME-{number:04d}"
        distinct_hashes = {item["sha256"] for item in items}
        for item in items:
            item["same_basename_group"] = group_id
            _add_warning(item, "same_basename_multiple_locations")
        result.append(
            {
                "group_id": group_id,
                "filename": items[0]["filename"],
                "hashes_differ": len(distinct_hashes) > 1,
                "paths": [item["relative_path"] for item in items],
                "source_ids": [item["source_id"] for item in items],
            }
        )
    return result


def _version_features(record: SourceRecord) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    stem = PurePosixPath(str(record["filename"])).stem.casefold()
    tokens = tuple(re.findall(r"[a-z]+\d*|\d{4}", stem))
    markers = tuple(token for token in tokens if _VERSION_MARKER.match(token))
    dates = tuple(token for token in tokens if re.fullmatch(r"(?:19|20)\d{2}", token))
    core = [
        token
        for token in tokens
        if token not in _VERSION_NOISE
        and token not in markers
        and token not in dates
        and not re.fullmatch(r"v?\d+", token)
    ]
    return " ".join(core), markers, dates


def _version_rank(
    record: SourceRecord, markers: tuple[str, ...], dates: tuple[str, ...]
) -> tuple[int, int, str]:
    marker_rank = 1
    if any(marker == "draft" for marker in markers):
        marker_rank = 0
    if any(marker == "original" for marker in markers):
        marker_rank = 1
    if any(marker.startswith(("amend", "rev", "v")) for marker in markers):
        marker_rank = 3
    if any(marker == "final" for marker in markers):
        marker_rank = 4
    numeric = [int(value) for marker in markers for value in re.findall(r"\d+", marker)]
    numeric.extend(int(value) for value in dates)
    return marker_rank, max(numeric, default=0), str(record["relative_path"])


def _assign_versions(
    records: list[SourceRecord],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: defaultdict[
        tuple[str, str, str], list[tuple[SourceRecord, tuple[str, ...], tuple[str, ...]]]
    ] = defaultdict(list)
    for record in records:
        if record["is_archive_container"] or record["sha256"] is None:
            continue
        core, markers, dates = _version_features(record)
        if core:
            key = (str(record["likely_workstream"]), str(record["detected_type"]), core)
            candidates[key].append((record, markers, dates))
    families = [
        (key, items)
        for key, items in candidates.items()
        if len(items) > 1 and any(markers for _, markers, _ in items)
    ]
    families.sort(key=lambda item: item[0])
    version_families: list[dict[str, Any]] = []
    near_candidates: list[dict[str, Any]] = []
    for number, (key, items) in enumerate(families, start=1):
        family_id = f"VER-{number:04d}"
        ranked = sorted(items, key=lambda item: _version_rank(*item))
        probable_current = ranked[-1][0]
        explicit_current = bool(ranked[-1][1])
        confidence = 0.85 if explicit_current else 0.6
        evidence: list[dict[str, Any]] = []
        for record, markers, dates in ranked:
            is_current = record is probable_current
            record["version_family"] = family_id
            record["probable_version_status"] = (
                "potentially_current" if is_current else "potentially_superseded"
            )
            record["probable_version_confidence"] = confidence if is_current else 0.75
            record["version_evidence"] = [
                f"normalized filename family: {key[2]}",
                f"version markers: {', '.join(markers) if markers else 'none'}",
                f"filename date tokens: {', '.join(dates) if dates else 'none'}",
                "file modified time: "
                f"{record['modified_time'] if record['modified_time'] else 'unavailable'}",
                "content hashes differ"
                if len({item[0]["sha256"] for item in items}) > 1
                else "content hashes match",
                "candidate relationship only; authority not established",
            ]
            _add_warning(record, "version_candidate_not_authoritative")
            evidence.append(
                {
                    "date_tokens": list(dates),
                    "markers": list(markers),
                    "modified_time": record["modified_time"],
                    "sha256": record["sha256"],
                    "size_bytes": record["size_bytes"],
                    "source_id": record["source_id"],
                }
            )
        version_families.append(
            {
                "confidence": confidence,
                "evidence": evidence,
                "family_key": key[2],
                "probable_current_source_id": probable_current["source_id"],
                "source_ids": [record["source_id"] for record, _, _ in ranked],
                "status": "candidate_only_not_authoritative",
                "version_family": family_id,
            }
        )
        unique_hashes = {record["sha256"] for record, _, _ in items}
        sizes = [int(record["size_bytes"]) for record, _, _ in items if record["size_bytes"]]
        size_ratio = min(sizes) / max(sizes) if sizes else 0.0
        if len(unique_hashes) > 1 and size_ratio >= 0.5:
            near_id = f"NEAR-{len(near_candidates) + 1:04d}"
            for record, _, _ in items:
                record["near_duplicate_group"] = near_id
                _add_warning(record, "near_duplicate_candidate")
            near_candidates.append(
                {
                    "basis": "shared normalized version family with different hashes",
                    "near_duplicate_group": near_id,
                    "size_ratio": round(size_ratio, 6),
                    "source_ids": [record["source_id"] for record, _, _ in items],
                    "version_family": family_id,
                }
            )
    return version_families, near_candidates


def _validate_complete_register(records: list[SourceRecord]) -> None:
    source_ids = [record["source_id"] for record in records]
    paths = [record["relative_path"] for record in records]
    errors: list[str] = []
    if len(source_ids) != len(set(source_ids)):
        errors.append("source IDs are not unique")
    if len(paths) != len(set(paths)):
        errors.append("relative/virtual paths are not unique")
    for record in records:
        if record["inventory_status"] not in _TERMINAL_INVENTORY_STATUSES:
            errors.append(f"{record['source_id']} has no terminal inventory status")
        if (
            record["inventory_status"] in {"registered", "registered_container"}
            and not record["sha256"]
        ):
            errors.append(f"{record['source_id']} is registered without a content hash")
        if Path(str(record["relative_path"])).is_absolute():
            errors.append(f"{record['source_id']} contains an absolute local path")
    if errors:
        raise InventoryError("; ".join(errors))


def inventory_room(room_path: str | Path, limits: RegisterLimits) -> InventoryResult:
    """Build a complete in-memory inventory without writing or extracting files."""

    walk = walk_data_room(room_path)
    records: list[SourceRecord] = []
    archive_directories: list[dict[str, Any]] = []
    for path in walk.files:
        record = _physical_record(path, walk.root)
        records.append(record)
        if record["is_archive_container"]:
            container_path = str(record["relative_path"])
            archive = inspect_zip(path, container_path, limits)
            record["warnings"] = list(dict.fromkeys((*record["warnings"], *archive.warnings)))
            if archive.error:
                record["inventory_status"] = "registered_unreadable"
                record["extraction_status"] = "blocked_unreadable"
                record["readability_status"] = "unreadable"
                record["error"] = archive.error
                record["review_required"] = True
            record["archive_member_count"] = len(archive.members)
            archive_directories.extend(archive.directories)
            records.extend(
                _archive_member_record(member, container_path) for member in archive.members
            )
        else:
            record["archive_member_count"] = 0

    records.sort(
        key=lambda record: (
            str(record["relative_path"]).casefold(),
            str(record["relative_path"]),
            int(record["archive_member_index"] or 0),
        )
    )
    for number, record in enumerate(records, start=1):
        record["source_id"] = f"SRC-{number:04d}"
        record["identity_key"] = _identity(record)
    container_ids = {
        str(record["relative_path"]): record["source_id"]
        for record in records
        if record["is_archive_container"]
    }
    for record in records:
        if record["container_path"] is not None:
            record["container_source_id"] = container_ids.get(str(record["container_path"]))

    duplicate_groups = _assign_exact_duplicates(records)
    same_basename = _assign_same_basename(records)
    version_families, near_candidates = _assign_versions(records)
    _validate_complete_register(records)

    empty_directories = tuple(
        path.relative_to(walk.root).as_posix() for path in walk.empty_directories
    )
    physical_directories = tuple(
        {
            "empty": path in walk.empty_directories,
            "path": path.relative_to(walk.root).as_posix(),
        }
        for path in walk.directories
    )
    input_checksum = _stable_json_hash(
        {
            "empty_directories": empty_directories,
            "limits": limits.as_dict(),
            "register_schema_version": REGISTER_SCHEMA_VERSION,
            "sources": [
                {
                    "identity_key": record["identity_key"],
                    "inventory_status": record["inventory_status"],
                    "relative_path": record["relative_path"],
                }
                for record in records
            ],
        }
    )
    summary = {
        "analysis_eligible_documents": sum(bool(item["analysis_eligible"]) for item in records),
        "analysis_included_after_exact_dedup": sum(
            bool(item["include_in_analysis"]) for item in records
        ),
        "archive_containers": sum(bool(item["is_archive_container"]) for item in records),
        "archive_members": sum(item["container_path"] is not None for item in records),
        "blocked_sources": sum(item["inventory_status"] == "blocked_unsafe" for item in records),
        "empty_directories": len(empty_directories),
        "exact_duplicate_groups": len(duplicate_groups),
        "logical_source_items": len(records),
        "near_duplicate_candidates": len(near_candidates),
        "physical_files": len(walk.files),
        "same_basename_conflicts": len(same_basename),
        "source_register_entries": len(records),
        "terminal_inventory_entries": sum(
            item["inventory_status"] in _TERMINAL_INVENTORY_STATUSES for item in records
        ),
        "unreadable_sources": sum(
            item["inventory_status"] == "registered_unreadable" for item in records
        ),
        "unsupported_sources": sum(
            item["inventory_status"] == "registered_unsupported" for item in records
        ),
        "version_families": len(version_families),
    }
    return InventoryResult(
        archive_directories=tuple(archive_directories),
        duplicate_groups=tuple(duplicate_groups),
        empty_directories=empty_directories,
        input_checksum=input_checksum,
        near_duplicate_candidates=tuple(near_candidates),
        physical_directories=physical_directories,
        same_basename_conflicts=tuple(same_basename),
        sources=tuple(records),
        summary=summary,
        version_families=tuple(version_families),
    )


def _csv_text(run_id: str, records: tuple[SourceRecord, ...]) -> str:
    fields = (
        "run_id",
        "source_id",
        "relative_path",
        "filename",
        "extension",
        "detected_mime_type",
        "detected_type",
        "extension_type_mismatch",
        "size_bytes",
        "sha256",
        "container_source_id",
        "container_path",
        "archive_member_name",
        "folder_area",
        "likely_document_class",
        "likely_workstream",
        "inventory_status",
        "extraction_status",
        "readability_status",
        "error",
        "warnings",
        "duplicate_group",
        "near_duplicate_group",
        "same_basename_group",
        "version_family",
        "probable_version_status",
        "probable_version_confidence",
        "analysis_eligible",
        "include_in_analysis",
        "review_required",
    )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for record in records:
        row = dict(record)
        row["run_id"] = run_id
        row["warnings"] = json.dumps(record["warnings"], ensure_ascii=False, separators=(",", ":"))
        writer.writerow(row)
    return output.getvalue()


def _markdown_text(run_id: str, result: InventoryResult) -> str:
    def clean(value: object) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")

    lines = [
        "# Source register",
        "",
        f"Run ID: `{run_id}`",
        "",
        f"Room fingerprint: `{result.input_checksum}`",
        "",
        "## Summary",
        "",
    ]
    lines.extend(f"- {key.replace('_', ' ')}: {value}" for key, value in result.summary.items())
    lines.extend(
        [
            "",
            "## Sources",
            "",
            "| Source ID | Path | Type | Workstream | Inventory | Readability | "
            "Duplicate | Version | Review |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for record in result.sources:
        lines.append(
            "| "
            + " | ".join(
                clean(record[key])
                for key in (
                    "source_id",
                    "relative_path",
                    "detected_type",
                    "likely_workstream",
                    "inventory_status",
                    "readability_status",
                    "duplicate_group",
                    "version_family",
                    "review_required",
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _write_outputs(
    run_path: Path, run_id: str, room_name: str, limits: RegisterLimits, result: InventoryResult
) -> None:
    output = run_path / "source_register"
    atomic_write_json(
        output / "source_register.json",
        {
            "input_checksum": result.input_checksum,
            "register_limits": limits.as_dict(),
            "room_label": room_name,
            "run_id": run_id,
            "schema_version": REGISTER_SCHEMA_VERSION,
            "sources": list(result.sources),
            "summary": result.summary,
        },
    )
    atomic_write_text(output / "source_register.csv", _csv_text(run_id, result.sources))
    atomic_write_text(output / "source_register.md", _markdown_text(run_id, result))
    atomic_write_json(
        output / "room_structure.json",
        {
            "archive_directories": list(result.archive_directories),
            "empty_directories": list(result.empty_directories),
            "physical_directories": list(result.physical_directories),
            "run_id": run_id,
            "schema_version": REGISTER_SCHEMA_VERSION,
        },
    )
    atomic_write_json(
        output / "duplicate_groups.json",
        {
            "exact_duplicate_groups": list(result.duplicate_groups),
            "near_duplicate_candidates": list(result.near_duplicate_candidates),
            "run_id": run_id,
            "same_basename_conflicts": list(result.same_basename_conflicts),
            "schema_version": REGISTER_SCHEMA_VERSION,
        },
    )
    atomic_write_json(
        output / "version_families.json",
        {
            "run_id": run_id,
            "schema_version": REGISTER_SCHEMA_VERSION,
            "version_families": list(result.version_families),
        },
    )
    adverse = [
        record
        for record in result.sources
        if record["inventory_status"]
        in {"blocked_unsafe", "registered_unreadable", "registered_unsupported"}
    ]
    atomic_write_json(
        output / "unreadable_sources.json",
        {
            "count": len(adverse),
            "run_id": run_id,
            "schema_version": REGISTER_SCHEMA_VERSION,
            "sources": adverse,
        },
    )


def _existing_outcome(run_path: Path, input_checksum: str) -> RegistrationOutcome:
    payload = load_json(run_path / "source_register" / "source_register.json")
    if payload.get("input_checksum") != input_checksum or not isinstance(
        payload.get("summary"), dict
    ):
        raise InventoryError(
            "completed register artifacts do not match the current room fingerprint"
        )
    return RegistrationOutcome(
        input_checksum=input_checksum,
        reused=True,
        run_path=run_path,
        summary={str(key): int(value) for key, value in payload["summary"].items()},
    )


def register_room(run: str | Path, room: str | Path, limits: RegisterLimits) -> RegistrationOutcome:
    """Run or idempotently reuse the complete source-register stage."""

    run_path, manifest = load_manifest(run)
    room_root = validate_data_room_path(room)
    if run_path.is_relative_to(room_root) or room_root.is_relative_to(run_path):
        raise InventoryError("run directory and source room must not overlap")
    result = inventory_room(room_root, limits)
    started = start_stage(run_path, "register", input_checksum=result.input_checksum)
    if started["stages"]["register"]["state"] == "completed":
        return _existing_outcome(run_path, result.input_checksum)
    try:
        _write_outputs(run_path, manifest["run_id"], room_root.name, limits, result)
        complete_stage(run_path, "register", required_artifacts=REGISTER_OUTPUTS)
    except (OSError, ValueError, DDEngineError) as exc:
        with suppress(DDEngineError):
            fail_stage(run_path, "register", str(exc))
        if isinstance(exc, DDEngineError):
            raise
        raise InventoryError(f"source-register stage failed: {exc}") from exc
    return RegistrationOutcome(
        input_checksum=result.input_checksum,
        reused=False,
        run_path=run_path,
        summary=result.summary,
    )
