"""Validate harness visual reviews and attach them to immutable extraction evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path

from dd_engine.artifacts import atomic_write_json, file_sha256, load_json
from dd_engine.errors import ExtractionError
from dd_engine.extraction.models import JsonObject, make_unit
from dd_engine.extraction.pipeline import (
    EXTRACTION_OUTPUTS,
    _aggregate_summary,
    _validate_units,
    _write_jsonl,
)
from dd_engine.runs import load_manifest
from dd_engine.state import complete_stage, reopen_completed_stage
from dd_engine.time import utc_now

VISION_REVIEW_SCHEMA_VERSION = 1


def _load_review_input(path: Path, run_id: str) -> JsonObject:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExtractionError(f"cannot read visual-review input {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExtractionError("visual-review input must be a JSON object")
    if value.get("run_id") not in {None, run_id}:
        raise ExtractionError("visual-review input belongs to another run")
    if not isinstance(value.get("reviewer"), str) or not str(value["reviewer"]).strip():
        raise ExtractionError("visual-review input requires a non-empty reviewer")
    if not isinstance(value.get("results"), list) or not value["results"]:
        raise ExtractionError("visual-review input requires a non-empty results list")
    return value


def _load_units(path: Path, run_id: str) -> list[JsonObject]:
    result: list[JsonObject] = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict) or value.get("run_id") != run_id:
                raise ExtractionError(f"invalid extracted unit at line {line_number}")
            result.append(value)
    except ExtractionError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExtractionError(f"cannot load extracted units for visual review: {exc}") from exc
    return result


def _next_ordinal(units: list[JsonObject], source_id: str) -> int:
    ordinals = []
    for unit in units:
        if unit.get("source_id") != source_id:
            continue
        match = re.search(r"-UNIT-(\d+)$", str(unit.get("unit_id", "")))
        if match:
            ordinals.append(int(match.group(1)))
    return max(ordinals, default=0) + 1


def ingest_vision_review(run: str | Path, review_file: str | Path) -> JsonObject:
    """Attach explicit harness transcriptions without letting Python invoke a model."""

    run_path, manifest = load_manifest(run)
    if manifest["stages"]["extract"]["state"] != "completed":
        raise ExtractionError("visual review requires a completed extraction stage")
    run_id = str(manifest["run_id"])
    input_path = Path(review_file).expanduser().resolve(strict=False)
    if not input_path.is_file():
        raise ExtractionError(f"visual-review input not found: {input_path}")
    supplied = _load_review_input(input_path, run_id)

    queue_path = run_path / "extracts" / "needs_vision.json"
    queue = load_json(queue_path)
    raw_tasks = queue.get("tasks")
    if not isinstance(raw_tasks, list):
        raise ExtractionError("vision queue has no task list")
    tasks = [item for item in raw_tasks if isinstance(item, dict)]
    tasks_by_id = {str(item.get("task_id")): item for item in tasks}
    if len(tasks_by_id) != len(tasks):
        raise ExtractionError("vision queue task IDs are missing or duplicated")

    register = load_json(run_path / "source_register" / "source_register.json")
    raw_sources = register.get("sources")
    if not isinstance(raw_sources, list):
        raise ExtractionError("source register has no source list")
    sources = {
        str(item["source_id"]): item
        for item in raw_sources
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }
    units = _load_units(run_path / "extracts" / "extracted_units.jsonl", run_id)
    reviewed_at = str(supplied.get("reviewed_at") or utc_now())
    reviewer = str(supplied["reviewer"]).strip()
    prepared: list[tuple[JsonObject, JsonObject, JsonObject]] = []
    seen: set[str] = set()
    for index, raw_result in enumerate(supplied["results"], start=1):
        if not isinstance(raw_result, dict):
            raise ExtractionError(f"visual-review result {index} is not an object")
        task_id = raw_result.get("task_id")
        if not isinstance(task_id, str) or task_id not in tasks_by_id:
            raise ExtractionError(f"visual-review result {index} references an unknown task")
        if task_id in seen:
            raise ExtractionError(f"duplicate visual-review result for {task_id}")
        seen.add(task_id)
        task = tasks_by_id[task_id]
        if task.get("status") != "pending" or task.get("model_result") is not None:
            raise ExtractionError(f"visual-review task is not pending: {task_id}")
        transcription = raw_result.get("transcription")
        if not isinstance(transcription, str) or not transcription.strip():
            raise ExtractionError(f"visual-review result {task_id} has no transcription")
        confidence = raw_result.get("confidence")
        if (
            not isinstance(confidence, int | float)
            or isinstance(confidence, bool)
            or not 0 <= float(confidence) <= 1
        ):
            raise ExtractionError(f"visual-review result {task_id} has invalid confidence")
        source_id = str(task.get("source_id"))
        source = sources.get(source_id)
        if source is None or task.get("source_checksum") != source.get("sha256"):
            raise ExtractionError(f"visual-review task {task_id} fails source identity checks")
        asset = task.get("asset")
        if not isinstance(asset, dict) or not isinstance(asset.get("path"), str):
            raise ExtractionError(f"visual-review task {task_id} has no review asset")
        asset_path = (run_path / str(asset["path"])).resolve(strict=False)
        if not asset_path.is_relative_to(run_path) or not asset_path.is_file():
            raise ExtractionError(f"visual-review asset is missing or outside the run: {task_id}")
        if file_sha256(asset_path) != asset.get("sha256"):
            raise ExtractionError(f"visual-review asset checksum changed: {task_id}")
        locator = task.get("locator")
        if not isinstance(locator, dict):
            raise ExtractionError(f"visual-review task {task_id} has no locator")
        result = {
            "confidence": round(float(confidence), 6),
            "method": "harness_visual_review",
            "model_id": None,
            "model_id_reason": "the active harness did not expose a model identifier",
            "reviewed_at": reviewed_at,
            "reviewer": reviewer,
            "token_counts": None,
            "token_counts_reason": "the active harness did not expose per-review token usage",
            "transcription": transcription.strip(),
        }
        unit = make_unit(
            run_id=run_id,
            source=source,
            ordinal=_next_ordinal([*units, *(item[2] for item in prepared)], source_id),
            unit_type="pdf_page" if locator.get("type") == "pdf_page" else "image",
            locator=dict(locator),
            extraction_method="harness_visual_review",
            confidence=float(confidence),
            content={"text": transcription.strip(), "visual_review_task_id": task_id},
            limitation=(
                "Harness transcription is review evidence, not deterministic OCR; consult the "
                "hashed rendered asset for visual confirmation."
            ),
        )
        prepared.append((task, result, unit))

    extraction = load_json(run_path / "extracts" / "extraction_manifest.json")
    source_records = extraction.get("sources")
    if not isinstance(source_records, list):
        raise ExtractionError("extraction manifest has no source records")
    reopen_completed_stage(run_path, "extract", "explicit harness visual-review evidence ingested")
    for task, result, unit in prepared:
        task["model_result"] = result
        task["status"] = "reviewed"
        units.append(unit)
    for source_record in source_records:
        if not isinstance(source_record, dict):
            continue
        source_id = str(source_record.get("source_id"))
        source_tasks = [task for task in tasks if task.get("source_id") == source_id]
        reviewed_tasks = [task for task in source_tasks if task.get("status") == "reviewed"]
        source_record["unit_count"] = sum(unit.get("source_id") == source_id for unit in units)
        source_record["vision_review_count"] = len(reviewed_tasks)
        if source_tasks and len(reviewed_tasks) == len(source_tasks):
            if source_record.get("status") in {"queued_for_vision", "partially_extracted"}:
                source_record["status"] = "successfully_extracted"
            source_record["limitation"] = (
                "All queued visual assets were reviewed by the harness; transcriptions remain "
                "subject to the recorded confidence and hashed-asset check."
            )
    _validate_units(units)
    pending = [task for task in tasks if task.get("status") == "pending"]
    summary = _aggregate_summary(source_records, units, pending)
    summary["vision_review_count"] = sum(task.get("status") == "reviewed" for task in tasks)
    extraction["completed_at"] = utc_now()
    extraction["summary"] = summary
    extraction["vision_review"] = {
        "harness_review_performed": True,
        "python_model_execution_performed": False,
        "reviewed_at": reviewed_at,
        "reviewer": reviewer,
    }
    queue.update(
        {
            "count": len(pending),
            "harness_review_performed": True,
            "model_execution_performed": True,
            "python_model_execution_performed": False,
            "queue_status": "complete" if not pending else "partially_reviewed",
            "reviewed_count": len(tasks) - len(pending),
            "tasks": tasks,
        }
    )
    review_path = run_path / "extracts" / "vision_review.json"
    previous_reviews: list[JsonObject] = []
    if review_path.is_file():
        previous = load_json(review_path).get("reviews")
        if isinstance(previous, list):
            previous_reviews = [item for item in previous if isinstance(item, dict)]
    review_payload: JsonObject = {
        "harness_review_performed": True,
        "python_model_execution_performed": False,
        "reviews": [
            *previous_reviews,
            *[
                {
                    "asset_sha256": task["asset"]["sha256"],
                    "locator": task["locator"],
                    "result": result,
                    "source_checksum": task["source_checksum"],
                    "source_id": task["source_id"],
                    "task_id": task["task_id"],
                }
                for task, result, _ in prepared
            ],
        ],
        "run_id": run_id,
        "schema_version": VISION_REVIEW_SCHEMA_VERSION,
    }
    atomic_write_json(run_path / "extracts" / "extraction_manifest.json", extraction)
    _write_jsonl(run_path / "extracts" / "extracted_units.jsonl", units)
    atomic_write_json(queue_path, queue)
    atomic_write_json(review_path, review_payload)
    completed = complete_stage(
        run_path,
        "extract",
        required_artifacts=[*EXTRACTION_OUTPUTS, "extracts/vision_review.json"],
    )
    return {
        "pending_count": len(pending),
        "reviewed_count": len(prepared),
        "run_id": run_id,
        "stage_state": completed["stages"]["extract"]["state"],
        "total_reviewed_count": len(tasks) - len(pending),
    }
