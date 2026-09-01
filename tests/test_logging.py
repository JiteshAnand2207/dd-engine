from __future__ import annotations

import json
from pathlib import Path

import pytest

from dd_engine.artifacts import append_json_line
from dd_engine.config import load_config
from dd_engine.runs import create_run
from dd_engine.runtime.logging import (
    RuntimeLogError,
    audit_run_logs,
    record_public_research,
    record_task_from_file,
    start_local_task,
)


def test_jsonl_events_are_valid_and_appended_without_rewriting(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "events.jsonl"
    first_event = {"event": "run_created", "run_id": "run-1", "sequence": 1}
    second_event = {"event": "stage_started", "run_id": "run-1", "sequence": 2}

    append_json_line(log_path, first_event)
    original_bytes = log_path.read_bytes()
    append_json_line(log_path, second_event)

    final_bytes = log_path.read_bytes()
    records = [json.loads(line) for line in final_bytes.decode().splitlines()]
    assert final_bytes.startswith(original_bytes)
    assert records == [first_event, second_event]


def test_local_task_log_is_honest_zero_model_route(tmp_path: Path) -> None:
    run_path = create_run(load_config(cwd=tmp_path), runs_root=tmp_path / "runs")
    session = start_local_task(
        run_path,
        stage="register",
        task_name="test_register",
        purpose="Exercise local deterministic logging.",
    )
    record = session.finish(output_artifact_paths=["manifest.json"])

    assert record["routing_class"] == "local_deterministic"
    assert record["provider_harness"] == "local_python"
    assert record["actual_model"] is None
    assert record["token_count_basis"] == "unavailable"
    assert record["input_tokens"] is None
    assert record["output_tokens"] is None
    assert record["estimated_api_equivalent_cost_usd"] is None
    assert record["billing_mode"] == "local_no_model"
    assert record["actual_billed_cost_usd"] == 0.0
    assert record["raw_sensitive_content_logged"] is False
    assert record["output_artifact_checksums"][0]["path"] == "manifest.json"
    assert (run_path / "logs" / "run-log.md").is_file()


def _model_task_payload() -> dict[str, object]:
    return {
        "actual_billed_cost_usd": None,
        "actual_model": None,
        "actual_model_unavailable_reason": "The harness did not expose an exact model ID.",
        "billing_mode": "subscription",
        "cost_estimate_basis": "unavailable",
        "cost_unavailable_reason": "No exact model or token counts were exposed.",
        "ended_at": "2026-09-01T12:01:00.000000Z",
        "error": None,
        "estimated_api_equivalent_cost_usd": None,
        "fallback_from": None,
        "fallback_reason": None,
        "fallback_used": False,
        "input_tokens": None,
        "output_artifact_paths": ["manifest.json"],
        "output_tokens": None,
        "provider_harness": "codex",
        "purpose": "Review a structured finding without logging source text.",
        "rate_card_reference": None,
        "raw_sensitive_content_logged": False,
        "retry_count": 0,
        "routing_class": "frontier_judgment",
        "source_ids_supplied": [],
        "stage": "analyse",
        "started_at": "2026-09-01T12:00:00.000000Z",
        "task_name": "financial_review",
        "token_count_basis": "unavailable",
        "token_count_unavailable_reason": "Subscription task usage was not exposed.",
    }


def test_model_task_null_usage_and_subscription_are_explicit(tmp_path: Path) -> None:
    run_path = create_run(load_config(cwd=tmp_path), runs_root=tmp_path / "runs")
    input_path = tmp_path / "model-task.json"
    input_path.write_text(json.dumps(_model_task_payload()), encoding="utf-8")

    record = record_task_from_file(run_path, input_path)

    assert record["routing_class"] == "frontier_judgment"
    assert record["actual_model"] is None
    assert record["billing_mode"] == "subscription"
    assert record["duration_ms"] == 60_000
    assert record["estimated_api_equivalent_cost_usd"] is None


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("raw_sensitive_content_logged", True, "raw sensitive content"),
        ("token_count_unavailable_reason", None, "unavailable token counts"),
        ("routing_class", "imaginary_route", "unknown routing_class"),
        ("cost_estimate_basis", "guess", "unknown cost_estimate_basis"),
    ),
)
def test_task_log_rejects_false_or_unsafe_records(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    run_path = create_run(load_config(cwd=tmp_path), runs_root=tmp_path / "runs")
    payload = _model_task_payload()
    payload[field] = value
    input_path = tmp_path / "invalid-task.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuntimeLogError, match=message):
        record_task_from_file(run_path, input_path)


def test_public_research_not_performed_and_log_audit(tmp_path: Path) -> None:
    run_path = create_run(load_config(cwd=tmp_path), runs_root=tmp_path / "runs")
    task = start_local_task(
        run_path,
        stage="status",
        task_name="status",
        purpose="Read run state.",
    )
    task.finish()
    research = record_public_research(
        run_path,
        {
            "action": "not_performed",
            "citations_supported": [],
            "claim_ids_supported": [],
            "conclusion": "Research remained disabled.",
            "confidential_room_content_included": False,
            "purpose": "Test the disabled research record.",
            "query": None,
            "result_used": False,
            "retrieved_page_sha256": None,
            "source_type": None,
            "timestamp": "2026-09-01T12:00:00.000000Z",
            "url": None,
        },
    )

    assert research["confidential_room_content_included"] is False
    assert research["result_used"] is False
    result = audit_run_logs(run_path)
    assert result["status"] == "passed"
    assert result["privacy_checks_passed"] is True


def test_log_audit_rejects_duplicate_task_ids(tmp_path: Path) -> None:
    run_path = create_run(load_config(cwd=tmp_path), runs_root=tmp_path / "runs")
    task = start_local_task(
        run_path,
        stage="status",
        task_name="status",
        purpose="Read run state.",
    )
    record = task.finish()
    append_json_line(run_path / "logs" / "run-log.jsonl", record)
    record_public_research(
        run_path,
        {
            "action": "not_performed",
            "citations_supported": [],
            "claim_ids_supported": [],
            "conclusion": "Research remained disabled.",
            "confidential_room_content_included": False,
            "purpose": "Test the disabled research record.",
            "query": None,
            "result_used": False,
            "retrieved_page_sha256": None,
            "source_type": None,
            "timestamp": "2026-09-01T12:00:00.000000Z",
            "url": None,
        },
    )

    result = audit_run_logs(run_path)

    assert result["status"] == "failed"
    assert any("repeats task ID" in error for error in result["errors"])


def test_disabled_research_can_record_a_policy_rejection(tmp_path: Path) -> None:
    run_path = create_run(load_config(cwd=tmp_path), runs_root=tmp_path / "runs")

    record = record_public_research(
        run_path,
        {
            "action": "rejected",
            "citations_supported": [],
            "claim_ids_supported": [],
            "conclusion": "Rejected because public research is disabled.",
            "confidential_room_content_included": False,
            "purpose": "Record the denied request without performing it.",
            "query": "Public target market overview",
            "result_used": False,
            "retrieved_page_sha256": None,
            "source_type": None,
            "timestamp": "2026-09-01T12:00:00.000000Z",
            "url": None,
        },
    )

    assert record["action"] == "rejected"
    assert record["result_used"] is False


def test_runtime_contract_files_define_required_routes_and_pauses() -> None:
    root = Path(__file__).resolve().parents[1]
    routing = (root / "config" / "model-routing.yaml").read_text(encoding="utf-8")
    prompt = (root / "prompts" / "runtime" / "run_engine.md").read_text(encoding="utf-8")
    red_team = (root / "prompts" / "runtime" / "red_team.md").read_text(encoding="utf-8")
    runtime_flow = (root / "docs" / "runtime-flow.md").read_text(encoding="utf-8")

    assert routing.count("  local_deterministic:") == 1
    assert routing.count("  economical_reasoning:") == 1
    assert routing.count("  frontier_judgment:") == 1
    assert "Use a cheaper model only if this harness explicitly exposes one" in prompt
    assert prompt.count("**Pause") == 2
    assert "Never bypass `awaiting_input`" in prompt
    assert "brand-new Codex task/chat" in red_team
    assert "Claude Code can run the same Python CLI" in runtime_flow
