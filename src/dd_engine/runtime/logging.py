"""Honest, local-only runtime task, usage, cost and research ledgers."""

from __future__ import annotations

import json
import re
import secrets
import time
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dd_engine.artifacts import (
    append_json_line,
    atomic_write_json,
    atomic_write_text,
    file_sha256,
    load_json,
)
from dd_engine.errors import DDEngineError
from dd_engine.evidence.models import JsonObject
from dd_engine.runs import load_manifest
from dd_engine.time import utc_now

RUN_LOG_SCHEMA_VERSION = 1
RUN_LOG_PATH = Path("logs/run-log.jsonl")
RUN_LOG_MARKDOWN_PATH = Path("logs/run-log.md")
RUN_LOG_VALIDATION_PATH = Path("logs/run-log-validation.json")
PUBLIC_RESEARCH_LOG_PATH = Path("logs/public-research-log.jsonl")

ROUTING_CLASSES = frozenset(
    {"local_deterministic", "economical_reasoning", "frontier_judgment"}
)
TOKEN_BASES = frozenset({"actual", "estimated", "unavailable"})
COST_BASES = frozenset({"estimated_from_versioned_rate_card", "unavailable"})
BILLING_MODES = frozenset({"local_no_model", "subscription", "api", "other", "unknown"})
TASK_STATUSES = frozenset({"succeeded", "failed"})
RESEARCH_ACTIONS = frozenset({"attempted", "rejected", "completed", "not_performed"})
_SOURCE_ID = re.compile(r"^SRC-\d{4}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")


class RuntimeLogError(DDEngineError):
    """Raised when a runtime/task/research log would be incomplete or misleading."""


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RuntimeLogError(f"{field} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RuntimeLogError(f"{field} is not a valid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise RuntimeLogError(f"{field} must be UTC")
    return parsed


def _text(value: object, field: str, *, nullable: bool = False, maximum: int = 800) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip():
        raise RuntimeLogError(f"{field} must be a non-empty string")
    normalized = " ".join(value.split())
    if len(normalized) > maximum:
        raise RuntimeLogError(f"{field} exceeds the {maximum}-character logging limit")
    return normalized


def _nullable_number(value: object, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
        raise RuntimeLogError(f"{field} must be null or a non-negative number")
    return float(value)


def _nullable_tokens(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeLogError(f"{field} must be null or a non-negative integer")
    return value


def _source_ids(run_path: Path, value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise RuntimeLogError("source_ids_supplied must be a list of source IDs")
    result = list(dict.fromkeys(str(item) for item in value))
    invalid = [item for item in result if not _SOURCE_ID.fullmatch(item)]
    if invalid:
        raise RuntimeLogError("invalid source ID(s) in task log: " + ", ".join(invalid))
    register_path = run_path / "source_register" / "source_register.json"
    if result and register_path.is_file():
        register = load_json(register_path)
        raw_sources = register.get("sources")
        known = (
            {
                str(item.get("source_id"))
                for item in raw_sources
                if isinstance(item, dict)
            }
            if isinstance(raw_sources, list)
            else set()
        )
        missing = [item for item in result if item not in known]
        if missing:
            raise RuntimeLogError("task log references unknown source ID(s): " + ", ".join(missing))
    return result


def _artifact_checksums(run_path: Path, value: object) -> list[JsonObject]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise RuntimeLogError("output_artifact_paths must be a list of run-local paths")
    root = run_path.resolve(strict=True)
    results: list[JsonObject] = []
    for raw_path in dict.fromkeys(str(item) for item in value):
        candidate = Path(raw_path)
        path = candidate if candidate.is_absolute() else run_path / candidate
        resolved = path.resolve(strict=False)
        if not resolved.is_relative_to(root) or resolved == root:
            raise RuntimeLogError(f"output artifact is outside the run: {raw_path}")
        if not resolved.is_file():
            raise RuntimeLogError(f"output artifact does not exist: {raw_path}")
        results.append(
            {
                "path": resolved.relative_to(root).as_posix(),
                "sha256": file_sha256(resolved),
                "size_bytes": resolved.stat().st_size,
            }
        )
    return results


def _read_records(path: Path) -> list[JsonObject]:
    if not path.is_file():
        return []
    records: list[JsonObject] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise RuntimeLogError(f"{path.name} line {number} is not an object")
                records.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeLogError(f"cannot read {path}: {exc}") from exc
    return records


def _render_summary(run_id: str, records: list[JsonObject]) -> str:
    status = Counter(str(item.get("status")) for item in records)
    routes = Counter(str(item.get("routing_class")) for item in records)
    stages = Counter(str(item.get("stage")) for item in records)
    unavailable_usage = sum(item.get("token_count_basis") == "unavailable" for item in records)
    estimated_cost = sum(
        float(item["estimated_api_equivalent_cost_usd"])
        for item in records
        if isinstance(item.get("estimated_api_equivalent_cost_usd"), int | float)
    )
    lines = [
        "# Run log summary",
        "",
        f"Run ID: `{run_id}`",
        "",
        f"Task records: {len(records)}",
        f"Succeeded: {status['succeeded']}",
        f"Failed: {status['failed']}",
        f"Usage unavailable: {unavailable_usage}",
        f"API-equivalent estimated cost recorded: USD {estimated_cost:.6f}",
        "",
        "## Routing",
        "",
    ]
    lines.extend(f"- {name}: {count}" for name, count in sorted(routes.items()))
    lines.extend(["", "## Stages", ""])
    lines.extend(f"- {name}: {count}" for name, count in sorted(stages.items()))
    lines.extend(
        [
            "",
            "## Tasks",
            "",
            "| Task ID | Stage | Routing | Harness | Model | Status | Duration ms |",
            "|---|---|---|---|---|---|---:|",
        ]
    )
    for item in records:
        lines.append(
            "| "
            + " | ".join(
                str(value if value is not None else "not visible").replace("|", "\\|")
                for value in (
                    item.get("task_id"),
                    item.get("stage"),
                    item.get("routing_class"),
                    item.get("provider_harness"),
                    item.get("actual_model"),
                    item.get("status"),
                    item.get("duration_ms"),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _append_task(run_path: Path, record: JsonObject) -> JsonObject:
    append_json_line(run_path / RUN_LOG_PATH, record)
    records = _read_records(run_path / RUN_LOG_PATH)
    atomic_write_text(
        run_path / RUN_LOG_MARKDOWN_PATH,
        _render_summary(str(record["run_id"]), records),
    )
    return record


def _task_record(
    *,
    run_path: Path,
    stage: str,
    task_id: str,
    task_name: str,
    purpose: str,
    provider_harness: str,
    actual_model: str | None,
    actual_model_unavailable_reason: str | None,
    routing_class: str,
    started_at: str,
    ended_at: str,
    source_ids_supplied: object,
    input_tokens: object,
    output_tokens: object,
    token_count_basis: str,
    token_count_unavailable_reason: str | None,
    estimated_api_equivalent_cost_usd: object,
    cost_estimate_basis: str,
    rate_card_reference: str | None,
    cost_unavailable_reason: str | None,
    billing_mode: str,
    actual_billed_cost_usd: object,
    retry_count: int,
    fallback_used: bool,
    fallback_from: str | None,
    fallback_reason: str | None,
    error: JsonObject | None,
    output_artifact_paths: object,
    raw_sensitive_content_logged: bool,
) -> JsonObject:
    run_path, manifest = load_manifest(run_path)
    if routing_class not in ROUTING_CLASSES:
        raise RuntimeLogError(f"unknown routing_class: {routing_class}")
    if token_count_basis not in TOKEN_BASES:
        raise RuntimeLogError(f"unknown token_count_basis: {token_count_basis}")
    if cost_estimate_basis not in COST_BASES:
        raise RuntimeLogError(f"unknown cost_estimate_basis: {cost_estimate_basis}")
    if billing_mode not in BILLING_MODES:
        raise RuntimeLogError(f"unknown billing_mode: {billing_mode}")
    if raw_sensitive_content_logged:
        raise RuntimeLogError("raw sensitive content must not be written to the run log")
    start = _parse_utc(started_at, "started_at")
    end = _parse_utc(ended_at, "ended_at")
    if end < start:
        raise RuntimeLogError("ended_at must not precede started_at")
    normalized_input = _nullable_tokens(input_tokens, "input_tokens")
    normalized_output = _nullable_tokens(output_tokens, "output_tokens")
    token_reason = _text(
        token_count_unavailable_reason,
        "token_count_unavailable_reason",
        nullable=True,
    )
    if token_count_basis == "unavailable":
        if normalized_input is not None or normalized_output is not None or token_reason is None:
            raise RuntimeLogError("unavailable token counts require null values and a reason")
    elif normalized_input is None or normalized_output is None:
        raise RuntimeLogError("actual/estimated token counts require input and output values")
    estimated_cost = _nullable_number(
        estimated_api_equivalent_cost_usd,
        "estimated_api_equivalent_cost_usd",
    )
    cost_reason = _text(cost_unavailable_reason, "cost_unavailable_reason", nullable=True)
    normalized_rate_card = _text(rate_card_reference, "rate_card_reference", nullable=True)
    if estimated_cost is None and cost_reason is None:
        raise RuntimeLogError("an unavailable API-equivalent cost requires a reason")
    if estimated_cost is None and cost_estimate_basis != "unavailable":
        raise RuntimeLogError("a null API-equivalent cost requires an unavailable basis")
    if estimated_cost is not None and (
        cost_estimate_basis != "estimated_from_versioned_rate_card"
        or normalized_rate_card is None
    ):
        raise RuntimeLogError("estimated cost requires a versioned rate-card reference")
    if actual_model is None and actual_model_unavailable_reason is None:
        raise RuntimeLogError("a null actual_model requires an explicit visibility reason")
    if actual_model is not None and actual_model_unavailable_reason is not None:
        raise RuntimeLogError(
            "actual_model_unavailable_reason must be null when actual_model is visible"
        )
    if routing_class == "local_deterministic" and actual_model is not None:
        raise RuntimeLogError("local_deterministic tasks cannot claim a model call")
    if type(retry_count) is not int or retry_count < 0:
        raise RuntimeLogError("retry_count must be a non-negative integer")
    if type(fallback_used) is not bool:
        raise RuntimeLogError("fallback_used must be true or false")
    if fallback_used and fallback_reason is None:
        raise RuntimeLogError("fallback use requires a fallback_reason")
    status = "failed" if error is not None else "succeeded"
    actual_cost = _nullable_number(actual_billed_cost_usd, "actual_billed_cost_usd")
    if routing_class == "local_deterministic" and (
        billing_mode != "local_no_model" or actual_cost != 0.0
    ):
        raise RuntimeLogError(
            "local_deterministic tasks require local_no_model billing and zero actual cost"
        )
    return {
        "actual_billed_cost_usd": actual_cost,
        "actual_model": actual_model,
        "actual_model_unavailable_reason": actual_model_unavailable_reason,
        "billing_mode": billing_mode,
        "cost_estimate_basis": cost_estimate_basis,
        "cost_unavailable_reason": cost_reason,
        "duration_ms": round((end - start).total_seconds() * 1000, 3),
        "ended_at": ended_at,
        "error": error,
        "estimated_api_equivalent_cost_usd": estimated_cost,
        "fallback_from": fallback_from,
        "fallback_reason": fallback_reason,
        "fallback_used": fallback_used,
        "input_tokens": normalized_input,
        "output_artifact_checksums": _artifact_checksums(run_path, output_artifact_paths),
        "output_tokens": normalized_output,
        "provider_harness": provider_harness,
        "purpose": purpose,
        "rate_card_reference": normalized_rate_card,
        "raw_sensitive_content_logged": False,
        "retry_count": retry_count,
        "routing_class": routing_class,
        "run_id": manifest["run_id"],
        "schema_version": RUN_LOG_SCHEMA_VERSION,
        "source_ids_supplied": _source_ids(run_path, source_ids_supplied),
        "stage": stage,
        "started_at": started_at,
        "status": status,
        "task_id": task_id,
        "task_name": task_name,
        "token_count_basis": token_count_basis,
        "token_count_unavailable_reason": token_reason,
    }


@dataclass(slots=True)
class LocalTaskSession:
    """One zero-model CLI task whose terminal record is always appended."""

    run_path: Path
    stage: str
    task_id: str
    task_name: str
    purpose: str
    started_at: str
    source_ids_supplied: list[str]
    _started_monotonic: float
    _finished: bool = False

    def finish(
        self,
        *,
        output_artifact_paths: list[str] | None = None,
        error: BaseException | str | None = None,
    ) -> JsonObject:
        if self._finished:
            raise RuntimeLogError(f"task {self.task_id} has already been finished")
        self._finished = True
        ended_at = utc_now()
        duration_ms = (time.perf_counter() - self._started_monotonic) * 1000
        calculated_start = datetime.fromisoformat(ended_at[:-1] + "+00:00").timestamp()
        calculated_start -= duration_ms / 1000
        started_at = datetime.fromtimestamp(calculated_start, UTC).isoformat(
            timespec="microseconds"
        ).replace("+00:00", "Z")
        error_value: JsonObject | None = None
        if error is not None:
            error_value = {
                "message": " ".join(str(error).split())[:800],
                "type": type(error).__name__ if isinstance(error, BaseException) else "TaskError",
            }
        record = _task_record(
            run_path=self.run_path,
            stage=self.stage,
            task_id=self.task_id,
            task_name=self.task_name,
            purpose=self.purpose,
            provider_harness="local_python",
            actual_model=None,
            actual_model_unavailable_reason="not applicable: zero-model route",
            routing_class="local_deterministic",
            started_at=started_at,
            ended_at=ended_at,
            source_ids_supplied=self.source_ids_supplied,
            input_tokens=None,
            output_tokens=None,
            token_count_basis="unavailable",
            token_count_unavailable_reason="not applicable: zero-model route",
            estimated_api_equivalent_cost_usd=None,
            cost_estimate_basis="unavailable",
            rate_card_reference=None,
            cost_unavailable_reason="not applicable: zero-model route",
            billing_mode="local_no_model",
            actual_billed_cost_usd=0.0,
            retry_count=0,
            fallback_used=False,
            fallback_from=None,
            fallback_reason=None,
            error=error_value,
            output_artifact_paths=output_artifact_paths or [],
            raw_sensitive_content_logged=False,
        )
        return _append_task(self.run_path, record)


def start_local_task(
    run: str | Path,
    *,
    stage: str,
    task_name: str,
    purpose: str,
    source_ids_supplied: list[str] | None = None,
) -> LocalTaskSession:
    """Start a real local deterministic task without claiming a model call."""

    run_path, _ = load_manifest(run)
    now = utc_now()
    compact = now.replace("-", "").replace(":", "").replace(".", "")
    task_id = f"TASK-{stage.upper()}-{compact}-{secrets.token_hex(3)}"
    return LocalTaskSession(
        run_path=run_path,
        stage=stage,
        task_id=task_id,
        task_name=task_name,
        purpose=purpose,
        started_at=now,
        source_ids_supplied=source_ids_supplied or [],
        _started_monotonic=time.perf_counter(),
    )


def record_task_from_file(run: str | Path, input_path: str | Path) -> JsonObject:
    """Validate and append one harness/model task supplied by Codex or Claude Code."""

    run_path, _ = load_manifest(run)
    payload = load_json(Path(input_path).expanduser().resolve(strict=True))
    allowed = {
        "actual_billed_cost_usd",
        "actual_model",
        "actual_model_unavailable_reason",
        "billing_mode",
        "cost_estimate_basis",
        "cost_unavailable_reason",
        "ended_at",
        "error",
        "estimated_api_equivalent_cost_usd",
        "fallback_from",
        "fallback_reason",
        "fallback_used",
        "input_tokens",
        "output_artifact_paths",
        "output_tokens",
        "provider_harness",
        "purpose",
        "rate_card_reference",
        "raw_sensitive_content_logged",
        "retry_count",
        "routing_class",
        "source_ids_supplied",
        "stage",
        "started_at",
        "task_id",
        "task_name",
        "token_count_basis",
        "token_count_unavailable_reason",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise RuntimeLogError("unknown task-log field(s): " + ", ".join(unknown))
    raw_error = payload.get("error")
    if raw_error is not None and not isinstance(raw_error, dict):
        raise RuntimeLogError("error must be null or an object")
    error_value: JsonObject | None = None
    if isinstance(raw_error, dict):
        error_value = {
            "message": _text(raw_error.get("message"), "error.message"),
            "type": _text(raw_error.get("type"), "error.type", maximum=120),
        }
    raw_retry_count = payload.get("retry_count", 0)
    if type(raw_retry_count) is not int:
        raise RuntimeLogError("retry_count must be a non-negative integer")
    raw_fallback_used = payload.get("fallback_used", False)
    if type(raw_fallback_used) is not bool:
        raise RuntimeLogError("fallback_used must be true or false")
    task_id = payload.get("task_id")
    if task_id is None:
        task_id = f"TASK-MODEL-{secrets.token_hex(8)}"
    record = _task_record(
        run_path=run_path,
        stage=str(_text(payload.get("stage"), "stage", maximum=80)),
        task_id=str(_text(task_id, "task_id", maximum=160)),
        task_name=str(_text(payload.get("task_name"), "task_name", maximum=160)),
        purpose=str(_text(payload.get("purpose"), "purpose")),
        provider_harness=str(
            _text(payload.get("provider_harness"), "provider_harness", maximum=120)
        ),
        actual_model=_text(payload.get("actual_model"), "actual_model", nullable=True),
        actual_model_unavailable_reason=_text(
            payload.get("actual_model_unavailable_reason"),
            "actual_model_unavailable_reason",
            nullable=True,
        ),
        routing_class=str(payload.get("routing_class")),
        started_at=str(payload.get("started_at")),
        ended_at=str(payload.get("ended_at")),
        source_ids_supplied=payload.get("source_ids_supplied", []),
        input_tokens=payload.get("input_tokens"),
        output_tokens=payload.get("output_tokens"),
        token_count_basis=str(payload.get("token_count_basis", "unavailable")),
        token_count_unavailable_reason=_text(
            payload.get("token_count_unavailable_reason"),
            "token_count_unavailable_reason",
            nullable=True,
        ),
        estimated_api_equivalent_cost_usd=payload.get(
            "estimated_api_equivalent_cost_usd"
        ),
        cost_estimate_basis=str(payload.get("cost_estimate_basis", "unavailable")),
        rate_card_reference=_text(
            payload.get("rate_card_reference"), "rate_card_reference", nullable=True
        ),
        cost_unavailable_reason=_text(
            payload.get("cost_unavailable_reason"),
            "cost_unavailable_reason",
            nullable=True,
        ),
        billing_mode=str(payload.get("billing_mode", "unknown")),
        actual_billed_cost_usd=payload.get("actual_billed_cost_usd"),
        retry_count=raw_retry_count,
        fallback_used=raw_fallback_used,
        fallback_from=_text(
            payload.get("fallback_from"), "fallback_from", nullable=True
        ),
        fallback_reason=_text(
            payload.get("fallback_reason"), "fallback_reason", nullable=True
        ),
        error=error_value,
        output_artifact_paths=payload.get("output_artifact_paths", []),
        raw_sensitive_content_logged=payload.get("raw_sensitive_content_logged") is True,
    )
    return _append_task(run_path, record)


def _research_record(run_path: Path, payload: JsonObject) -> JsonObject:
    _, manifest = load_manifest(run_path)
    action = str(payload.get("action"))
    if action not in RESEARCH_ACTIONS:
        raise RuntimeLogError(f"unknown public-research action: {action}")
    if (
        action in {"attempted", "completed"}
        and manifest["config"]["public_research_enabled"] is not True
    ):
        raise RuntimeLogError("public research is disabled for this run")
    if payload.get("confidential_room_content_included") is not False:
        raise RuntimeLogError(
            "public queries must confirm no confidential room content was included"
        )
    result_used = payload.get("result_used")
    if type(result_used) is not bool:
        raise RuntimeLogError("result_used must be true or false")
    query = _text(payload.get("query"), "query", nullable=True, maximum=500)
    url = _text(payload.get("url"), "url", nullable=True, maximum=1000)
    source_type = _text(payload.get("source_type"), "source_type", nullable=True)
    if action == "not_performed" and any(value is not None for value in (query, url, source_type)):
        raise RuntimeLogError("not_performed research must have null query, URL and source type")
    if action in {"attempted", "rejected", "completed"} and query is None:
        raise RuntimeLogError(f"{action} research requires a query")
    if action == "completed" and (query is None or url is None or source_type is None):
        raise RuntimeLogError("completed research requires query, URL and source type")
    if action in {"not_performed", "rejected"} and result_used:
        raise RuntimeLogError(f"{action} research cannot mark a result as used")
    claims = payload.get("claim_ids_supported", [])
    citations = payload.get("citations_supported", [])
    if not isinstance(claims, list) or any(not isinstance(item, str) for item in claims):
        raise RuntimeLogError("claim_ids_supported must be a string list")
    if not isinstance(citations, list) or any(not isinstance(item, str) for item in citations):
        raise RuntimeLogError("citations_supported must be a string list")
    retrieved_hash = payload.get("retrieved_page_sha256")
    if retrieved_hash is not None and (
        not isinstance(retrieved_hash, str) or not _SHA256.fullmatch(retrieved_hash)
    ):
        raise RuntimeLogError("retrieved_page_sha256 must be null or a SHA-256 digest")
    return {
        "action": action,
        "citations_supported": citations,
        "claim_ids_supported": claims,
        "conclusion": _text(payload.get("conclusion"), "conclusion", nullable=True),
        "confidential_room_content_included": False,
        "confidentiality_confirmation": (
            "The query contained no source-room text, personal data, confidential figures or "
            "document-derived allegations."
        ),
        "purpose": _text(payload.get("purpose"), "purpose"),
        "query": query,
        "result_used": result_used,
        "retrieved_page_sha256": retrieved_hash,
        "run_id": manifest["run_id"],
        "schema_version": RUN_LOG_SCHEMA_VERSION,
        "source_type": source_type,
        "timestamp": _parse_utc(
            str(payload.get("timestamp") or utc_now()), "timestamp"
        ).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "url": url,
    }


def record_public_research(run: str | Path, input_value: str | Path | JsonObject) -> JsonObject:
    """Append a complete privacy-safe public research action."""

    run_path, _ = load_manifest(run)
    payload = (
        load_json(Path(input_value).expanduser().resolve(strict=True))
        if isinstance(input_value, str | Path)
        else dict(input_value)
    )
    record = _research_record(run_path, payload)
    append_json_line(run_path / PUBLIC_RESEARCH_LOG_PATH, record)
    return record


def audit_run_logs(run: str | Path) -> JsonObject:
    """Validate completed-stage coverage and honest usage/privacy fields."""

    run_path, manifest = load_manifest(run)
    records = _read_records(run_path / RUN_LOG_PATH)
    errors: list[str] = []
    required_fields = {
        "actual_billed_cost_usd",
        "actual_model",
        "actual_model_unavailable_reason",
        "billing_mode",
        "cost_estimate_basis",
        "cost_unavailable_reason",
        "duration_ms",
        "ended_at",
        "error",
        "estimated_api_equivalent_cost_usd",
        "fallback_from",
        "fallback_reason",
        "fallback_used",
        "input_tokens",
        "output_artifact_checksums",
        "output_tokens",
        "provider_harness",
        "purpose",
        "rate_card_reference",
        "raw_sensitive_content_logged",
        "retry_count",
        "routing_class",
        "run_id",
        "schema_version",
        "source_ids_supplied",
        "stage",
        "started_at",
        "status",
        "task_id",
        "task_name",
        "token_count_basis",
        "token_count_unavailable_reason",
    }
    task_ids: set[str] = set()
    for number, record in enumerate(records, start=1):
        missing = sorted(required_fields - set(record))
        if missing:
            errors.append(f"run-log line {number} missing: {', '.join(missing)}")
        if record.get("run_id") != manifest["run_id"]:
            errors.append(f"run-log line {number} has a mismatched run ID")
        if record.get("routing_class") not in ROUTING_CLASSES:
            errors.append(f"run-log line {number} has an invalid routing class")
        if record.get("status") not in TASK_STATUSES:
            errors.append(f"run-log line {number} has an invalid status")
        if record.get("billing_mode") not in BILLING_MODES:
            errors.append(f"run-log line {number} has an invalid billing mode")
        if record.get("raw_sensitive_content_logged") is not False:
            errors.append(f"run-log line {number} may contain raw sensitive content")
        try:
            start = _parse_utc(record.get("started_at"), "started_at")
            end = _parse_utc(record.get("ended_at"), "ended_at")
            if end < start:
                errors.append(f"run-log line {number} has reversed timestamps")
        except RuntimeLogError as exc:
            errors.append(f"run-log line {number} has invalid timing: {exc}")
        duration = record.get("duration_ms")
        if isinstance(duration, bool) or not isinstance(duration, int | float) or duration < 0:
            errors.append(f"run-log line {number} has an invalid duration")
        source_ids = record.get("source_ids_supplied")
        if not isinstance(source_ids, list) or any(
            not isinstance(item, str) or not _SOURCE_ID.fullmatch(item)
            for item in source_ids
        ):
            errors.append(f"run-log line {number} has invalid supplied source IDs")
        actual_model = record.get("actual_model")
        model_reason = record.get("actual_model_unavailable_reason")
        if actual_model is None and not model_reason:
            errors.append(f"run-log line {number} lacks the model-unavailable reason")
        if actual_model is not None and (
            not isinstance(actual_model, str) or not actual_model.strip()
        ):
            errors.append(f"run-log line {number} has an invalid actual model")
        if actual_model is not None and model_reason is not None:
            errors.append(f"run-log line {number} has ambiguous actual-model visibility")
        token_basis = record.get("token_count_basis")
        if token_basis not in TOKEN_BASES:
            errors.append(f"run-log line {number} has an invalid token basis")
        if record.get("token_count_basis") == "unavailable" and not record.get(
            "token_count_unavailable_reason"
        ):
            errors.append(f"run-log line {number} lacks the token-unavailable reason")
        if token_basis == "unavailable" and (
            record.get("input_tokens") is not None or record.get("output_tokens") is not None
        ):
            errors.append(f"run-log line {number} invents unavailable token values")
        if token_basis in {"actual", "estimated"} and (
            type(record.get("input_tokens")) is not int
            or type(record.get("output_tokens")) is not int
        ):
            errors.append(f"run-log line {number} lacks numeric token values")
        cost_basis = record.get("cost_estimate_basis")
        estimated_cost = record.get("estimated_api_equivalent_cost_usd")
        if cost_basis not in COST_BASES:
            errors.append(f"run-log line {number} has an invalid cost basis")
        if estimated_cost is None and (
            cost_basis != "unavailable" or not record.get("cost_unavailable_reason")
        ):
            errors.append(f"run-log line {number} lacks the cost-unavailable basis/reason")
        if estimated_cost is not None and (
            isinstance(estimated_cost, bool)
            or not isinstance(estimated_cost, int | float)
            or estimated_cost < 0
            or cost_basis != "estimated_from_versioned_rate_card"
            or not record.get("rate_card_reference")
        ):
            errors.append(f"run-log line {number} has an untraceable cost estimate")
        if record.get("routing_class") == "local_deterministic" and (
            actual_model is not None
            or record.get("billing_mode") != "local_no_model"
            or record.get("actual_billed_cost_usd") != 0.0
        ):
            errors.append(f"run-log line {number} makes a false local model/billing claim")
        checksums = record.get("output_artifact_checksums")
        if not isinstance(checksums, list):
            errors.append(f"run-log line {number} has an invalid output-checksum list")
        else:
            for checksum in checksums:
                if (
                    not isinstance(checksum, dict)
                    or not isinstance(checksum.get("path"), str)
                    or not _SHA256.fullmatch(str(checksum.get("sha256")))
                    or not isinstance(checksum.get("size_bytes"), int)
                    or checksum.get("size_bytes", -1) < 0
                ):
                    errors.append(f"run-log line {number} has a malformed output checksum")
                    break
        task_id = str(record.get("task_id"))
        if task_id in task_ids:
            errors.append(f"run-log line {number} repeats task ID {task_id}")
        task_ids.add(task_id)
    completed_stages = [
        stage
        for stage, value in manifest["stages"].items()
        if isinstance(value, dict) and value.get("state") == "completed"
    ]
    succeeded_stages = {
        str(item.get("stage")) for item in records if item.get("status") == "succeeded"
    }
    missing_stage_logs = [stage for stage in completed_stages if stage not in succeeded_stages]
    if missing_stage_logs:
        errors.append(
            "completed stages lack successful task logs: " + ", ".join(missing_stage_logs)
        )
    research_records = _read_records(run_path / PUBLIC_RESEARCH_LOG_PATH)
    if not research_records:
        errors.append("public research log has no performed/not_performed record")
    for number, record in enumerate(research_records, start=1):
        for field in (
            "query",
            "timestamp",
            "purpose",
            "url",
            "source_type",
            "result_used",
            "claim_ids_supported",
            "citations_supported",
            "confidential_room_content_included",
        ):
            if field not in record:
                errors.append(f"public-research line {number} missing {field}")
        if record.get("confidential_room_content_included") is not False:
            errors.append(f"public-research line {number} failed confidentiality confirmation")
    route_counts = Counter(str(item.get("routing_class")) for item in records)
    status_counts = Counter(str(item.get("status")) for item in records)
    result: JsonObject = {
        "checked_at": utc_now(),
        "completed_stages": completed_stages,
        "errors": errors,
        "missing_completed_stage_logs": missing_stage_logs,
        "privacy_checks_passed": not any(
            "sensitive" in error or "confidential" in error for error in errors
        ),
        "public_research_record_count": len(research_records),
        "route_counts": dict(sorted(route_counts.items())),
        "run_id": manifest["run_id"],
        "schema_version": RUN_LOG_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "status_counts": dict(sorted(status_counts.items())),
        "task_record_count": len(records),
    }
    atomic_write_json(run_path / RUN_LOG_VALIDATION_PATH, result)
    return result
