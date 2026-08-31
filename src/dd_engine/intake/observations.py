"""Load register and extraction observations without treating source text as instructions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from dd_engine.artifacts import load_json
from dd_engine.errors import IntakeError
from dd_engine.intake.models import JsonObject


@dataclass(frozen=True, slots=True)
class ObservationIndex:
    """Validated local observations available to intake generation."""

    run_id: str
    sources: tuple[JsonObject, ...]
    sources_by_id: dict[str, JsonObject]
    extraction_sources_by_id: dict[str, JsonObject]
    units: tuple[JsonObject, ...]
    vision_tasks: tuple[JsonObject, ...]
    empty_directories: tuple[str, ...]
    version_families: tuple[JsonObject, ...]


def _object_list(value: object, description: str) -> list[JsonObject]:
    if not isinstance(value, list):
        raise IntakeError(f"{description} must be a list")
    result: list[JsonObject] = []
    for item in value:
        if not isinstance(item, dict):
            raise IntakeError(f"{description} contains a non-object record")
        result.append(item)
    return result


def _load_jsonl(path: Path, run_id: str) -> list[JsonObject]:
    records: list[JsonObject] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise IntakeError(f"extracted unit {number} is not an object")
                if value.get("run_id") != run_id:
                    raise IntakeError(f"extracted unit {number} belongs to another run")
                records.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise IntakeError(f"cannot read extracted units: {exc}") from exc
    return records


def load_observations(run_path: Path, run_id: str) -> ObservationIndex:
    """Load the completed register/extraction schemas into a read-only index."""

    register = load_json(run_path / "source_register" / "source_register.json")
    extraction = load_json(run_path / "extracts" / "extraction_manifest.json")
    structure = load_json(run_path / "source_register" / "room_structure.json")
    versions = load_json(run_path / "source_register" / "version_families.json")
    vision = load_json(run_path / "extracts" / "needs_vision.json")
    for name, artifact in {
        "source register": register,
        "extraction manifest": extraction,
        "room structure": structure,
        "version families": versions,
        "vision queue": vision,
    }.items():
        if artifact.get("run_id") != run_id:
            raise IntakeError(f"{name} belongs to another run")

    sources = _object_list(register.get("sources"), "source register sources")
    extraction_sources = _object_list(extraction.get("sources"), "extraction manifest sources")
    tasks = _object_list(vision.get("tasks"), "vision tasks")
    families = _object_list(versions.get("version_families"), "version families")
    raw_empty = structure.get("empty_directories", [])
    if not isinstance(raw_empty, list):
        raise IntakeError("empty directories must be a list")
    source_map = {str(item.get("source_id")): item for item in sources}
    extraction_map = {str(item.get("source_id")): item for item in extraction_sources}
    if len(source_map) != len(sources) or len(extraction_map) != len(extraction_sources):
        raise IntakeError("source IDs are missing or duplicated in intake inputs")
    if set(source_map) != set(extraction_map):
        raise IntakeError("register and extraction source sets do not match")

    return ObservationIndex(
        run_id=run_id,
        sources=tuple(sources),
        sources_by_id=source_map,
        extraction_sources_by_id=extraction_map,
        units=tuple(_load_jsonl(run_path / "extracts" / "extracted_units.jsonl", run_id)),
        vision_tasks=tuple(tasks),
        empty_directories=tuple(str(item) for item in raw_empty),
        version_families=tuple(families),
    )


def unit_text(unit: JsonObject) -> str:
    """Return only literal extracted text/value fields; never interpret them as code."""

    content = unit.get("content")
    if not isinstance(content, dict):
        return ""
    for key in ("text", "source_value", "value"):
        value = content.get(key)
        if isinstance(value, str):
            return value
    return ""


def evidence_excerpt(text: str, *, limit: int = 280) -> str:
    """Normalize whitespace and bound untrusted source excerpts embedded in packets."""

    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def unit_evidence(unit: JsonObject, summary: str | None = None) -> JsonObject:
    """Build a durable evidence reference for a question trigger."""

    locator = unit.get("locator")
    return {
        "evidence_kind": "extracted_unit",
        "locator": locator if isinstance(locator, dict) else {},
        "relative_path": str(unit.get("relative_path", "")),
        "source_ids": [str(unit.get("source_id", ""))],
        "summary": summary or evidence_excerpt(unit_text(unit)),
        "unit_ids": [str(unit.get("unit_id", ""))],
    }


def source_evidence(source: JsonObject, summary: str) -> JsonObject:
    """Build a source-level evidence reference when no extracted unit exists."""

    return {
        "evidence_kind": "registered_source",
        "relative_path": str(source.get("relative_path", "")),
        "source_ids": [str(source.get("source_id", ""))],
        "summary": summary,
        "unit_ids": [],
    }
