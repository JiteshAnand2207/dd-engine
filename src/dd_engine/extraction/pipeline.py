"""Run-level orchestration for tiered, local-first extraction."""

from __future__ import annotations

import importlib.metadata
import json
from collections import Counter
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path

from dd_engine.artifacts import (
    append_json_line,
    atomic_write_json,
    atomic_write_text,
    file_sha256,
    load_json,
)
from dd_engine.config import EngineConfig
from dd_engine.errors import DDEngineError, ExtractionError
from dd_engine.extraction.cache import ExtractionCache
from dd_engine.extraction.documents import extract_csv, extract_docx, extract_image
from dd_engine.extraction.models import (
    TERMINAL_EXTRACTION_STATUSES,
    ExtractionOutcome,
    JsonObject,
    SourceExtraction,
    stable_json_checksum,
)
from dd_engine.extraction.pdfs import OCRCapability, detect_ocr_capability, extract_pdf
from dd_engine.extraction.source_access import read_registered_source
from dd_engine.extraction.spreadsheets import extract_xlsx
from dd_engine.runs import load_manifest
from dd_engine.source_paths import validate_data_room_path, walk_data_room
from dd_engine.state import complete_stage, fail_stage, start_stage
from dd_engine.time import utc_now

EXTRACTOR_VERSION = "phase5-local-v1"
EXTRACTION_SCHEMA_VERSION = 1
EXTRACTION_OUTPUTS = (
    "extracts/extraction_manifest.json",
    "extracts/extracted_units.jsonl",
    "extracts/extraction_failures.json",
    "extracts/needs_vision.json",
)


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unavailable"


def extraction_config_record(config: EngineConfig, ocr: OCRCapability) -> JsonObject:
    """Return all behavior-affecting extraction settings and local capabilities."""

    return {
        "dependencies": {
            "openpyxl": _package_version("openpyxl"),
            "Pillow": _package_version("Pillow"),
            "pypdf": _package_version("pypdf"),
            "pypdfium2": _package_version("pypdfium2"),
            "python-docx": _package_version("python-docx"),
        },
        "extractor_version": EXTRACTOR_VERSION,
        "ocr": ocr.as_dict(),
        "settings": asdict(config.extraction),
    }


def _registered_adverse_result(source: JsonObject) -> SourceExtraction | None:
    inventory_status = str(source["inventory_status"])
    if bool(source.get("is_archive_container")):
        return SourceExtraction(
            status="unsupported",
            primary_method="archive_container_inventory_only",
            limitation=(
                "ZIP container is retained as a source; its direct members are "
                "extracted separately"
            ),
            failure_reason="archive container is not itself an analytical document",
            metrics={"archive_containers": 1},
        )
    if inventory_status in {"blocked_unsafe", "registered_unreadable"}:
        return SourceExtraction(
            status="failed",
            primary_method="not_extracted_registered_failure",
            limitation="source could not safely reach a document parser",
            failure_reason=str(source.get("error") or inventory_status),
            metrics={"registered_failures": 1},
        )
    if inventory_status == "registered_unsupported":
        return SourceExtraction(
            status="unsupported",
            primary_method="unsupported_content_type",
            limitation="detected content type is outside the Phase 5 deterministic extractors",
            failure_reason=str(source.get("error") or source.get("detected_type")),
            metrics={"unsupported_sources": 1},
        )
    return None


def _dispatch(
    *,
    payload: bytes,
    source: JsonObject,
    run_id: str,
    run_path: Path,
    config: EngineConfig,
    config_namespace: str,
    ocr: OCRCapability,
) -> SourceExtraction:
    detected_type = str(source["detected_type"])
    if detected_type == "pdf":
        return extract_pdf(
            payload=payload,
            source=source,
            run_id=run_id,
            run_path=run_path,
            config_namespace=config_namespace,
            min_native_characters=config.extraction.pdf_min_native_characters,
            render_scale=config.extraction.render_scale,
            ocr=ocr,
        )
    if detected_type == "docx":
        return extract_docx(
            payload=payload,
            source=source,
            run_id=run_id,
            run_path=run_path,
            config_namespace=config_namespace,
        )
    if detected_type == "xlsx":
        return extract_xlsx(payload=payload, source=source, run_id=run_id)
    if detected_type == "csv":
        return extract_csv(payload=payload, source=source, run_id=run_id)
    if detected_type in {"jpeg", "png"}:
        return extract_image(
            payload=payload,
            source=source,
            run_id=run_id,
            run_path=run_path,
            config_namespace=config_namespace,
        )
    return SourceExtraction(
        status="unsupported",
        primary_method="unsupported_content_type",
        limitation="no deterministic Phase 5 extractor is registered for this content type",
        failure_reason=detected_type,
        metrics={"unsupported_sources": 1},
    )


def _source_manifest_record(
    source: JsonObject, result: SourceExtraction, *, cache_status: str
) -> JsonObject:
    return {
        "cache_status": cache_status,
        "detected_type": source["detected_type"],
        "failure_reason": result.failure_reason,
        "limitation": result.limitation,
        "metrics": result.metrics,
        "primary_extraction_method": result.primary_method,
        "relative_path": source["relative_path"],
        "source_checksum": source["sha256"],
        "source_id": source["source_id"],
        "status": result.status,
        "unit_count": len(result.units),
        "vision_task_count": len(result.vision_tasks),
        "warnings": result.warnings,
    }


def _validate_units(units: list[JsonObject]) -> None:
    unit_ids: set[str] = set()
    for unit in units:
        unit_id = unit.get("unit_id")
        if not isinstance(unit_id, str) or unit_id in unit_ids:
            raise ExtractionError("extracted unit IDs are missing or not unique")
        unit_ids.add(unit_id)
        content = unit.get("content")
        if not isinstance(content, dict):
            raise ExtractionError(f"{unit_id} has no object-shaped content")
        if unit.get("extracted_content_checksum") != stable_json_checksum(content):
            raise ExtractionError(f"{unit_id} has an invalid extracted-content checksum")
        if not isinstance(unit.get("locator"), dict):
            raise ExtractionError(f"{unit_id} has no structured source locator")
        if not isinstance(unit.get("source_checksum"), str):
            raise ExtractionError(f"{unit_id} has no source checksum")
        confidence = unit.get("confidence")
        if not isinstance(confidence, int | float) or not 0 <= confidence <= 1:
            raise ExtractionError(f"{unit_id} has invalid extraction confidence")


def _validate_complete_sources(
    registered: list[JsonObject], source_records: list[JsonObject], tasks: list[JsonObject]
) -> None:
    registered_ids = [str(item["source_id"]) for item in registered]
    extracted_ids = [str(item["source_id"]) for item in source_records]
    if extracted_ids != registered_ids:
        raise ExtractionError(
            "extraction manifest does not preserve every registered source in order"
        )
    for record in source_records:
        if record["status"] not in TERMINAL_EXTRACTION_STATUSES:
            raise ExtractionError(f"{record['source_id']} has no terminal extraction status")
    for task in tasks:
        if task.get("status") != "pending" or task.get("model_result") is not None:
            raise ExtractionError("vision queue contains a fabricated or non-pending result")


def _aggregate_summary(
    source_records: list[JsonObject], units: list[JsonObject], tasks: list[JsonObject]
) -> JsonObject:
    status_counts = Counter(str(item["status"]) for item in source_records)
    method_counts = Counter(str(item["extraction_method"]) for item in units)
    primary_counts = Counter(str(item["primary_extraction_method"]) for item in source_records)
    summary: JsonObject = {
        "cache_hits": sum(item["cache_status"] == "hit" for item in source_records),
        "cache_misses": sum(item["cache_status"] == "miss" for item in source_records),
        "cache_not_applicable": sum(
            item["cache_status"] == "not_applicable" for item in source_records
        ),
        "extracted_units": len(units),
        "extraction_method_counts": dict(sorted(method_counts.items())),
        "source_primary_method_counts": dict(sorted(primary_counts.items())),
        "source_status_counts": dict(sorted(status_counts.items())),
        "sources_terminal": sum(
            item["status"] in TERMINAL_EXTRACTION_STATUSES for item in source_records
        ),
        "sources_total": len(source_records),
        "vision_queue_count": len(tasks),
    }
    aggregate_keys = {
        "archive_containers",
        "csv_cells",
        "csv_rows",
        "docx_embedded_images",
        "docx_headings",
        "docx_paragraph_units",
        "docx_table_cells",
        "docx_tables",
        "image_metadata_units",
        "pdf_embedded_images",
        "pdf_embedded_image_failures",
        "pdf_pages_failed",
        "pdf_pages_image_only",
        "pdf_pages_low_text",
        "pdf_pages_native_text",
        "pdf_pages_ocr",
        "pdf_pages_total",
        "pdf_pages_vision_queued",
        "spreadsheet_cached_formula_values",
        "spreadsheet_cell_units",
        "spreadsheet_currency_formatted_cells",
        "spreadsheet_date_formatted_cells",
        "spreadsheet_formula_errors",
        "spreadsheet_formulas",
        "spreadsheet_hidden_columns",
        "spreadsheet_hidden_rows",
        "spreadsheet_hidden_sheets",
        "spreadsheet_merged_ranges",
        "spreadsheet_named_ranges",
        "spreadsheet_sheets",
        "spreadsheet_subtotal_cells",
        "spreadsheet_total_cells",
        "spreadsheet_visible_sheets",
    }
    for key in sorted(aggregate_keys):
        summary[key] = sum(
            int(record["metrics"].get(key, 0))
            for record in source_records
            if isinstance(record.get("metrics"), dict)
        )
    sheet_coverage: list[JsonObject] = []
    for record in source_records:
        metrics = record.get("metrics", {})
        if not isinstance(metrics, dict):
            continue
        for sheet in metrics.get("spreadsheet_sheet_coverage", []):
            value = dict(sheet)
            value.update(
                {
                    "relative_path": record["relative_path"],
                    "source_id": record["source_id"],
                }
            )
            sheet_coverage.append(value)
    summary["spreadsheet_sheet_coverage"] = sheet_coverage
    return summary


def _write_jsonl(path: Path, units: list[JsonObject]) -> None:
    text = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
        for item in units
    )
    atomic_write_text(path, text)


def _existing_outcome(run_path: Path, input_checksum: str) -> ExtractionOutcome:
    payload = load_json(run_path / "extracts" / "extraction_manifest.json")
    if payload.get("input_checksum") != input_checksum or not isinstance(
        payload.get("summary"), dict
    ):
        raise ExtractionError("completed extraction artifacts do not match current inputs")
    return ExtractionOutcome(
        input_checksum=input_checksum,
        reused=True,
        run_path=run_path,
        summary=dict(payload["summary"]),
    )


def _room_snapshot(
    room_root: Path, sources: list[JsonObject]
) -> tuple[str, list[str]]:
    """Hash the current physical room so stage/cache reuse cannot hide changes."""

    walk = walk_data_room(room_root)
    current = {
        path.relative_to(room_root).as_posix(): file_sha256(path) for path in walk.files
    }
    registered = {
        str(source["relative_path"]): source.get("sha256")
        for source in sources
        if source.get("container_source_id") is None
    }
    errors: list[str] = []
    missing = sorted(set(registered) - set(current))
    added = sorted(set(current) - set(registered))
    mismatched = sorted(
        path
        for path in set(current) & set(registered)
        if current[path] != registered[path]
    )
    if missing:
        errors.append(f"registered physical source(s) missing: {', '.join(missing)}")
    if added:
        errors.append(f"unregistered physical source(s) added: {', '.join(added)}")
    if mismatched:
        errors.append(f"registered source checksum(s) changed: {', '.join(mismatched)}")
    return stable_json_checksum(current), errors


def extract_run(
    run: str | Path,
    room: str | Path,
    config: EngineConfig,
) -> ExtractionOutcome:
    """Extract every source-register row and write the complete Phase 5 contract."""

    run_path, manifest = load_manifest(run)
    if manifest["stages"]["register"]["state"] != "completed":
        raise ExtractionError("extract requires a completed source-register stage")
    room_root = validate_data_room_path(room)
    if run_path.is_relative_to(room_root) or room_root.is_relative_to(run_path):
        raise ExtractionError("run directory and source room must not overlap")

    register_path = run_path / "source_register" / "source_register.json"
    register = load_json(register_path)
    if register.get("run_id") != manifest["run_id"]:
        raise ExtractionError("source register belongs to a different run")
    raw_sources = register.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ExtractionError("source register contains no source rows")
    sources: list[JsonObject] = []
    for item in raw_sources:
        if not isinstance(item, dict):
            raise ExtractionError("source register contains a non-object row")
        sources.append(item)
    sources_by_id = {str(item["source_id"]): item for item in sources}
    if len(sources_by_id) != len(sources):
        raise ExtractionError("source register source IDs are not unique")
    register_limits = register.get("register_limits")
    if not isinstance(register_limits, dict):
        raise ExtractionError("source register has no archive limit record")

    ocr = detect_ocr_capability(config.extraction.optional_ocr)
    config_record = extraction_config_record(config, ocr)
    config_fingerprint = stable_json_checksum(config_record)
    room_snapshot_fingerprint, room_snapshot_errors = _room_snapshot(room_root, sources)
    input_checksum = stable_json_checksum(
        {
            "config_fingerprint": config_fingerprint,
            "extractor_version": EXTRACTOR_VERSION,
            "register_output_checksum": manifest["stages"]["register"]["output_checksum"],
            "room_snapshot_fingerprint": room_snapshot_fingerprint,
            "source_register_sha256": file_sha256(register_path),
        }
    )
    started = start_stage(run_path, "extract", input_checksum=input_checksum)
    if started["stages"]["extract"]["state"] == "completed":
        return _existing_outcome(run_path, input_checksum)
    if room_snapshot_errors:
        diagnostic = (
            "source room no longer matches the completed register; rerun register before "
            "extraction: " + "; ".join(room_snapshot_errors)
        )
        fail_stage(run_path, "extract", diagnostic)
        raise ExtractionError(diagnostic)

    started_at = utc_now()
    extracts_dir = run_path / "extracts"
    (extracts_dir / "rendered_pages").mkdir(parents=True, exist_ok=True)
    (extracts_dir / "cache").mkdir(parents=True, exist_ok=True)
    config_namespace = config_fingerprint[:16]
    cache = ExtractionCache(
        run_path=run_path,
        extractor_version=EXTRACTOR_VERSION,
        config_fingerprint=config_fingerprint,
    )
    source_records: list[JsonObject] = []
    units: list[JsonObject] = []
    tasks: list[JsonObject] = []
    try:
        for source in sources:
            adverse = _registered_adverse_result(source)
            cache_status = "not_applicable"
            if adverse is not None:
                result = adverse
            else:
                try:
                    payload = read_registered_source(
                        room_root, source, sources_by_id, register_limits
                    )
                    cached = cache.load(source)
                    if cached is not None:
                        result = cached
                        cache_status = "hit"
                    else:
                        result = _dispatch(
                            payload=payload,
                            source=source,
                            run_id=manifest["run_id"],
                            run_path=run_path,
                            config=config,
                            config_namespace=config_namespace,
                            ocr=ocr,
                        )
                        cache_status = "miss"
                        if result.status not in {"failed", "unsupported"}:
                            cache.store(source, result)
                except (OSError, ValueError, DDEngineError) as exc:
                    result = SourceExtraction(
                        status="failed",
                        primary_method="source_or_parser_failure",
                        limitation="source extraction failed; other registered sources continued",
                        failure_reason=str(exc),
                        metrics={"source_parser_failures": 1},
                    )
            source_records.append(
                _source_manifest_record(source, result, cache_status=cache_status)
            )
            units.extend(result.units)
            tasks.extend(result.vision_tasks)

        _validate_units(units)
        _validate_complete_sources(sources, source_records, tasks)
        summary = _aggregate_summary(source_records, units, tasks)
        completed_at = utc_now()
        adverse_sources = [
            record
            for record in source_records
            if record["status"] in {"failed", "partially_extracted", "unsupported"}
        ]
        atomic_write_json(
            extracts_dir / "extraction_manifest.json",
            {
                "completed_at": completed_at,
                "configuration": config_record,
                "configuration_fingerprint": config_fingerprint,
                "extractor_version": EXTRACTOR_VERSION,
                "input_checksum": input_checksum,
                "run_id": manifest["run_id"],
                "schema_version": EXTRACTION_SCHEMA_VERSION,
                "source_register_checksum": file_sha256(register_path),
                "sources": source_records,
                "started_at": started_at,
                "summary": summary,
                "terminal_statuses": sorted(TERMINAL_EXTRACTION_STATUSES),
            },
        )
        _write_jsonl(extracts_dir / "extracted_units.jsonl", units)
        atomic_write_json(
            extracts_dir / "extraction_failures.json",
            {
                "count": len(adverse_sources),
                "failed_sources": [
                    item for item in source_records if item["status"] == "failed"
                ],
                "partial_sources": [
                    item for item in source_records if item["status"] == "partially_extracted"
                ],
                "run_id": manifest["run_id"],
                "schema_version": EXTRACTION_SCHEMA_VERSION,
                "unsupported_sources": [
                    item for item in source_records if item["status"] == "unsupported"
                ],
            },
        )
        atomic_write_json(
            extracts_dir / "needs_vision.json",
            {
                "count": len(tasks),
                "model_execution_performed": False,
                "queue_status": "pending" if tasks else "empty",
                "run_id": manifest["run_id"],
                "schema_version": EXTRACTION_SCHEMA_VERSION,
                "tasks": tasks,
            },
        )
        complete_stage(run_path, "extract", required_artifacts=EXTRACTION_OUTPUTS)
        append_json_line(
            run_path / "logs" / "events.jsonl",
            {
                "event": "extraction_completed",
                "input_checksum": input_checksum,
                "run_id": manifest["run_id"],
                "summary": summary,
                "timestamp": utc_now(),
            },
        )
    except (OSError, ValueError, DDEngineError) as exc:
        with suppress(DDEngineError):
            fail_stage(run_path, "extract", str(exc))
        if isinstance(exc, DDEngineError):
            raise
        raise ExtractionError(f"extraction stage failed: {exc}") from exc
    return ExtractionOutcome(
        input_checksum=input_checksum,
        reused=False,
        run_path=run_path,
        summary=summary,
    )
