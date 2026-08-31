"""Typed values and stable record helpers for local extraction."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

TERMINAL_EXTRACTION_STATUSES = frozenset(
    {
        "successfully_extracted",
        "partially_extracted",
        "queued_for_vision",
        "unsupported",
        "failed",
    }
)


def stable_json_checksum(value: object) -> str:
    """Hash a JSON-compatible value using one canonical encoding."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def make_unit(
    *,
    run_id: str,
    source: JsonObject,
    ordinal: int,
    unit_type: str,
    locator: JsonObject,
    extraction_method: str,
    confidence: float,
    content: JsonObject,
    warnings: list[str] | None = None,
    limitation: str | None = None,
) -> JsonObject:
    """Create a stable unit carrying immutable source and content addresses."""

    return {
        "confidence": round(confidence, 6),
        "content": content,
        "extracted_content_checksum": stable_json_checksum(content),
        "extraction_method": extraction_method,
        "limitation": limitation,
        "locator": locator,
        "relative_path": source["relative_path"],
        "run_id": run_id,
        "source_checksum": source["sha256"],
        "source_id": source["source_id"],
        "unit_id": f"{source['source_id']}-UNIT-{ordinal:06d}",
        "unit_type": unit_type,
        "untrusted_source_data": True,
        "warnings": warnings or [],
    }


@dataclass(slots=True)
class SourceExtraction:
    """Complete extraction result for exactly one registered source."""

    status: str
    primary_method: str
    units: list[JsonObject] = field(default_factory=list)
    vision_tasks: list[JsonObject] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    limitation: str | None = None
    failure_reason: str | None = None
    metrics: JsonObject = field(default_factory=dict)

    def as_cache_payload(self) -> JsonObject:
        """Return the parser result without transient cache-hit metadata."""

        return {
            "failure_reason": self.failure_reason,
            "limitation": self.limitation,
            "metrics": self.metrics,
            "primary_method": self.primary_method,
            "status": self.status,
            "units": self.units,
            "vision_tasks": self.vision_tasks,
            "warnings": self.warnings,
        }

    @classmethod
    def from_cache_payload(cls, payload: JsonObject) -> SourceExtraction:
        """Rehydrate a validated cache result."""

        status = payload.get("status")
        if status not in TERMINAL_EXTRACTION_STATUSES:
            raise ValueError("cache result has an invalid terminal status")
        return cls(
            status=str(status),
            primary_method=str(payload["primary_method"]),
            units=list(payload.get("units", [])),
            vision_tasks=list(payload.get("vision_tasks", [])),
            warnings=[str(item) for item in payload.get("warnings", [])],
            limitation=(
                str(payload["limitation"]) if payload.get("limitation") is not None else None
            ),
            failure_reason=(
                str(payload["failure_reason"])
                if payload.get("failure_reason") is not None
                else None
            ),
            metrics=dict(payload.get("metrics", {})),
        )


@dataclass(frozen=True, slots=True)
class ExtractionOutcome:
    """Public outcome of one run-level extraction invocation."""

    input_checksum: str
    reused: bool
    run_path: Path
    summary: JsonObject

