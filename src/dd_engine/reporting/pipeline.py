"""Phase 10 report assembly, deterministic brief rendering and final validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dd_engine.artifacts import (
    append_json_line,
    atomic_write_json,
    atomic_write_text,
    file_sha256,
    load_json,
)
from dd_engine.constants import StageState
from dd_engine.errors import ReportError
from dd_engine.evidence.models import JsonObject
from dd_engine.evidence.store import load_record_sets
from dd_engine.extraction.models import stable_json_checksum
from dd_engine.reporting.pdf import PageLayout, render_ic_brief_pdf
from dd_engine.reporting.rendering import (
    build_ic_brief_content,
    render_due_diligence_report,
    render_ic_brief_markdown,
    render_outstanding_information,
)
from dd_engine.reporting.validation import validate_report_bundle
from dd_engine.runs import load_manifest
from dd_engine.state import (
    complete_stage,
    fail_stage,
    reopen_completed_stage,
    start_stage,
)
from dd_engine.time import utc_now

REPORT_VERSION = "phase14-report-v7"

REPORT_OUTPUTS = (
    "outputs/due_diligence_report.md",
    "outputs/ic_brief.md",
    "outputs/ic_brief.pdf",
    "outputs/outstanding_information.md",
    "outputs/report_validation.json",
)

_PAYLOAD_PATHS = {
    "financial": "workstreams/financial.json",
    "commercial": "workstreams/commercial.json",
    "legal_contractual": "workstreams/legal_contractual.json",
    "operational_management": "workstreams/operational_management.json",
    "it": "workstreams/it.json",
    "tax": "tax/tax-findings.json",
}

_UPSTREAM_PATHS = (
    "source_register/source_register.json",
    "extracts/extraction_manifest.json",
    "extracts/needs_vision.json",
    "intake/round_1_questions.json",
    "intake/round_1_answers.json",
    "intake/round_2_questions.json",
    "intake/round_2_answers.json",
    "evidence/claims.jsonl",
    "evidence/evidence.jsonl",
    "evidence/calculations.jsonl",
    "evidence/contradictions.jsonl",
    "evidence/gaps.jsonl",
    "evidence/issues.jsonl",
    "workstreams/analysis_validation.json",
    *_PAYLOAD_PATHS.values(),
)

_BUNDLE_PATHS = REPORT_OUTPUTS[:4]


def _upstream_paths(run_path: Path) -> tuple[str, ...]:
    paths = list(_UPSTREAM_PATHS)
    resolution = "red_team/red_team_resolution.json"
    if (run_path / resolution).is_file():
        paths.append(resolution)
    return tuple(paths)


def _validation_paths(run_path: Path) -> tuple[str, ...]:
    return (*_upstream_paths(run_path), *_BUNDLE_PATHS)


@dataclass(frozen=True, slots=True)
class ReportOutcome:
    """Public result of report generation."""

    input_fingerprint: str
    reused: bool
    run_path: Path
    stage_state: str
    summary: dict[str, object]
    validation_passed: bool


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    """Public result of final report validation."""

    input_fingerprint: str
    reused: bool
    run_path: Path
    stage_state: str
    summary: dict[str, object]
    validation_passed: bool


def _require_analysis_complete(run_path: Path, manifest: JsonObject) -> JsonObject:
    stages = manifest.get("stages")
    if not isinstance(stages, dict):
        raise ReportError("run manifest has no stage collection")
    analyse = stages.get("analyse")
    if not isinstance(analyse, dict) or analyse.get("state") != StageState.COMPLETED.value:
        raise ReportError("Phase 10 requires current completed Phase 8 and Phase 9 analysis")
    validation_path = run_path / "workstreams" / "analysis_validation.json"
    if not validation_path.is_file():
        raise ReportError("Phase 10 requires analysis_validation.json")
    validation = load_json(validation_path)
    if validation.get("status") != "passed":
        raise ReportError("Phase 10 requires passing analysis validation")
    return validation


def _fingerprint(run_path: Path, paths: tuple[str, ...], *, version: str) -> str:
    artifacts: list[JsonObject] = []
    for relative_path in paths:
        path = run_path / relative_path
        if not path.is_file():
            raise ReportError(f"required Phase 10 input is missing: {relative_path}")
        artifacts.append({"path": relative_path, "sha256": file_sha256(path)})
    return stable_json_checksum({"artifacts": artifacts, "version": version})


def _load_payloads(run_path: Path) -> dict[str, JsonObject]:
    return {
        name: load_json(run_path / relative_path) for name, relative_path in _PAYLOAD_PATHS.items()
    }


def _load_questions_answers(
    run_path: Path,
) -> tuple[list[JsonObject], dict[str, JsonObject]]:
    questions: list[JsonObject] = []
    answers: dict[str, JsonObject] = {}
    for round_number in (1, 2):
        question_payload = load_json(run_path / "intake" / f"round_{round_number}_questions.json")
        raw_questions = question_payload.get("questions")
        if not isinstance(raw_questions, list):
            raise ReportError(f"round {round_number} question packet has no question list")
        questions.extend(item for item in raw_questions if isinstance(item, dict))
        answer_payload = load_json(run_path / "intake" / f"round_{round_number}_answers.json")
        raw_answers = answer_payload.get("answers")
        if not isinstance(raw_answers, list):
            raise ReportError(f"round {round_number} answer packet has no answer list")
        for item in raw_answers:
            if isinstance(item, dict) and isinstance(item.get("question_id"), str):
                answers[str(item["question_id"])] = item
    return questions, answers


def _summaries(run_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    register = load_json(run_path / "source_register" / "source_register.json")
    extraction = load_json(run_path / "extracts" / "extraction_manifest.json")
    register_summary = register.get("summary")
    extraction_summary = extraction.get("summary")
    extraction_values = dict(extraction_summary) if isinstance(extraction_summary, dict) else {}
    vision = load_json(run_path / "extracts" / "needs_vision.json")
    tasks = vision.get("tasks")
    vision_tasks = (
        [item for item in tasks if isinstance(item, dict)] if isinstance(tasks, list) else []
    )
    extraction_values["vision_queue_count"] = sum(
        item.get("status") != "reviewed" or not isinstance(item.get("model_result"), dict)
        for item in vision_tasks
    )
    extraction_values["vision_reviewed_count"] = sum(
        item.get("status") == "reviewed" and isinstance(item.get("model_result"), dict)
        for item in vision_tasks
    )
    return (
        dict(register_summary) if isinstance(register_summary, dict) else {},
        extraction_values,
    )


def _existing_generated_at(run_path: Path, bundle_fingerprint: str) -> str | None:
    path = run_path / "outputs" / "report_validation.json"
    if not path.is_file():
        return None
    value = load_json(path)
    if value.get("input_fingerprint") != bundle_fingerprint:
        return None
    generated_at = value.get("generated_at")
    return str(generated_at) if isinstance(generated_at, str) else None


def _validation_payload(
    *,
    run_path: Path,
    run_id: str,
    report_input_fingerprint: str,
    payloads: dict[str, JsonObject],
    records: dict[str, list[JsonObject]],
    bundle_fingerprint: str,
    layouts: tuple[PageLayout, PageLayout] | None,
) -> JsonObject:
    existing: JsonObject | None = None
    existing_path = run_path / "outputs" / "report_validation.json"
    if existing_path.is_file():
        candidate = load_json(existing_path)
        if candidate.get("input_fingerprint") == bundle_fingerprint:
            existing = candidate
    report_text = (run_path / "outputs" / "due_diligence_report.md").read_text(encoding="utf-8")
    brief_text = (run_path / "outputs" / "ic_brief.md").read_text(encoding="utf-8")
    outstanding_text = (run_path / "outputs" / "outstanding_information.md").read_text(
        encoding="utf-8"
    )
    result = validate_report_bundle(
        run_path=run_path,
        run_id=run_id,
        payloads=payloads,
        records=records,
        report_text=report_text,
        brief_text=brief_text,
        outstanding_text=outstanding_text,
        input_fingerprint=bundle_fingerprint,
        layouts=layouts,
        generated_at=_existing_generated_at(run_path, bundle_fingerprint),
    )
    if layouts is None and existing is not None:
        existing_checks = existing.get("checks")
        result_checks = result.get("checks")
        if isinstance(existing_checks, dict) and isinstance(result_checks, dict):
            existing_pdf = existing_checks.get("pdf")
            result_pdf = result_checks.get("pdf")
            if isinstance(existing_pdf, dict) and isinstance(result_pdf, dict):
                existing_layout = existing_pdf.get("layout")
                if isinstance(existing_layout, list):
                    result_pdf["layout"] = existing_layout
    result["report_input_fingerprint"] = report_input_fingerprint
    result["report_version"] = REPORT_VERSION
    result["untrusted_source_data_was_executed"] = False
    resolution_path = run_path / "red_team" / "red_team_resolution.json"
    resolution: JsonObject | None = (
        load_json(resolution_path) if resolution_path.is_file() else None
    )
    reconciled = bool(
        resolution
        and resolution.get("run_id") == run_id
        and isinstance(resolution.get("summary"), dict)
        and resolution["summary"].get("total") == len(resolution.get("dispositions", []))
    )
    isolation_names = (
        "packet-allowlist.json",
        "sealed-packet-manifest.json",
        "isolation-manifest.json",
    )
    isolation_present = all((run_path / "red_team" / name).is_file() for name in isolation_names)
    result["red_team_reconciled"] = reconciled
    result["independent_red_team_performed"] = reconciled and isolation_present
    unresolved = (
        int(resolution["summary"].get("unresolved", 0))
        if reconciled and resolution is not None
        else 0
    )
    result["release_ready"] = bool(
        result["status"] == "passed"
        and result["independent_red_team_performed"]
        and unresolved == 0
    )
    result["validation_scope"] = (
        "phase_13_reconciled_candidate_bundle" if reconciled else "phase_10_candidate_report_bundle"
    )
    return result


def _stage_artifacts_match(run_path: Path, stage: JsonObject) -> bool:
    artifacts = stage.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return False
    for item in artifacts:
        if not isinstance(item, dict):
            return False
        relative_path = item.get("path")
        expected = item.get("sha256")
        if not isinstance(relative_path, str) or not isinstance(expected, str):
            return False
        path = run_path / relative_path
        if not path.is_file() or file_sha256(path) != expected:
            return False
    return True


def _report_outcome_from_validation(
    run_path: Path,
    input_fingerprint: str,
    *,
    reused: bool,
) -> ReportOutcome:
    validation = load_json(run_path / "outputs" / "report_validation.json")
    _, manifest = load_manifest(run_path)
    return ReportOutcome(
        input_fingerprint=input_fingerprint,
        reused=reused,
        run_path=run_path,
        stage_state=str(manifest["stages"]["report"]["state"]),
        summary=dict(validation.get("summary", {})),
        validation_passed=validation.get("status") == "passed",
    )


def generate_report(run: str | Path) -> ReportOutcome:
    """Generate all Phase 10 outputs and complete report only after fail-closed checks pass."""

    run_path, manifest = load_manifest(run)
    analysis_validation = _require_analysis_complete(run_path, manifest)
    input_fingerprint = _fingerprint(run_path, _upstream_paths(run_path), version=REPORT_VERSION)
    report_stage = manifest["stages"]["report"]
    if not isinstance(report_stage, dict):
        raise ReportError("manifest report stage is invalid")
    if report_stage.get("state") == StageState.COMPLETED.value:
        validation_path = run_path / "outputs" / "report_validation.json"
        if validation_path.is_file():
            existing = load_json(validation_path)
            try:
                current_bundle = _fingerprint(
                    run_path, _validation_paths(run_path), version=f"{REPORT_VERSION}-validation"
                )
            except ReportError:
                current_bundle = ""
            if (
                report_stage.get("input_checksum") == input_fingerprint
                and existing.get("status") == "passed"
                and existing.get("input_fingerprint") == current_bundle
                and _stage_artifacts_match(run_path, report_stage)
            ):
                return _report_outcome_from_validation(run_path, input_fingerprint, reused=True)
        if report_stage.get("input_checksum") != input_fingerprint:
            start_stage(run_path, "report", input_checksum=input_fingerprint)
        else:
            reopen_completed_stage(run_path, "report", "Phase 10 output integrity changed")
    else:
        start_stage(run_path, "report", input_checksum=input_fingerprint)

    run_id = str(manifest["run_id"])
    try:
        payloads = _load_payloads(run_path)
        records = load_record_sets(run_path)
        questions, answers = _load_questions_answers(run_path)
        register_summary, extraction_summary = _summaries(run_path)
        citation_validation = analysis_validation.get("citation_validation")
        citation_obj = citation_validation if isinstance(citation_validation, dict) else {}
        citation_summary = citation_obj.get("summary")
        citation_summary_obj = citation_summary if isinstance(citation_summary, dict) else {}
        red_team_resolution_path = run_path / "red_team" / "red_team_resolution.json"
        red_team_resolution = (
            load_json(red_team_resolution_path) if red_team_resolution_path.is_file() else None
        )

        report_text = render_due_diligence_report(
            run_id=run_id,
            payloads=payloads,
            records=records,
            questions=questions,
            answers=answers,
            register_summary=register_summary,
            extraction_summary=extraction_summary,
            citation_summary=citation_summary_obj,
            red_team_resolution=red_team_resolution,
        )
        outstanding_text = render_outstanding_information(
            run_id=run_id,
            payloads=payloads,
            gaps=records["gaps"],
            questions=questions,
            answers=answers,
        )
        brief_content = build_ic_brief_content(
            run_id=run_id,
            payloads=payloads,
            records=records,
            answers=answers,
            questions=questions,
        )
        brief_text = render_ic_brief_markdown(brief_content)
        outputs = run_path / "outputs"
        atomic_write_text(outputs / "due_diligence_report.md", report_text)
        atomic_write_text(outputs / "ic_brief.md", brief_text)
        atomic_write_text(outputs / "outstanding_information.md", outstanding_text)
        layouts = render_ic_brief_pdf(outputs / "ic_brief.pdf", brief_content)
        bundle_fingerprint = _fingerprint(
            run_path, _validation_paths(run_path), version=f"{REPORT_VERSION}-validation"
        )
        validation = _validation_payload(
            run_path=run_path,
            run_id=run_id,
            report_input_fingerprint=input_fingerprint,
            payloads=payloads,
            records=records,
            bundle_fingerprint=bundle_fingerprint,
            layouts=layouts,
        )
        atomic_write_json(outputs / "report_validation.json", validation)
        if validation.get("status") != "passed":
            fail_stage(run_path, "report", "Phase 10 report validation failed")
            raise ReportError("Phase 10 report validation failed")
        complete_stage(run_path, "report", required_artifacts=REPORT_OUTPUTS)
        append_json_line(
            run_path / "logs" / "events.jsonl",
            {
                "event": "phase_10_report_validated",
                "input_fingerprint": input_fingerprint,
                "run_id": run_id,
                "status": "passed",
                "timestamp": utc_now(),
            },
        )
        return _report_outcome_from_validation(run_path, input_fingerprint, reused=False)
    except ReportError:
        _, latest = load_manifest(run_path)
        if latest["stages"]["report"]["state"] == StageState.RUNNING.value:
            fail_stage(run_path, "report", "Phase 10 report generation failed")
        raise
    except (OSError, KeyError, TypeError, ValueError) as exc:
        _, latest = load_manifest(run_path)
        if latest["stages"]["report"]["state"] == StageState.RUNNING.value:
            fail_stage(run_path, "report", f"Phase 10 report generation failed: {exc}")
        raise ReportError(f"Phase 10 report generation failed: {exc}") from exc


def _validation_outcome(
    run_path: Path, input_fingerprint: str, *, reused: bool
) -> ValidationOutcome:
    validation = load_json(run_path / "outputs" / "report_validation.json")
    _, manifest = load_manifest(run_path)
    return ValidationOutcome(
        input_fingerprint=input_fingerprint,
        reused=reused,
        run_path=run_path,
        stage_state=str(manifest["stages"]["validate"]["state"]),
        summary=dict(validation.get("summary", {})),
        validation_passed=validation.get("status") == "passed",
    )


def validate_report_outputs(run: str | Path) -> ValidationOutcome:
    """Independently revalidate the Phase 10 bundle and complete the validate stage."""

    run_path, manifest = load_manifest(run)
    _require_analysis_complete(run_path, manifest)
    if manifest["stages"]["report"]["state"] != StageState.COMPLETED.value:
        raise ReportError("final validation requires a completed Phase 10 report stage")
    report_input_fingerprint = _fingerprint(
        run_path, _upstream_paths(run_path), version=REPORT_VERSION
    )
    input_fingerprint = _fingerprint(
        run_path, _validation_paths(run_path), version=f"{REPORT_VERSION}-validation"
    )
    validate_stage = manifest["stages"]["validate"]
    if not isinstance(validate_stage, dict):
        raise ReportError("manifest validate stage is invalid")
    validation_path = run_path / "outputs" / "report_validation.json"
    if validate_stage.get("state") == StageState.COMPLETED.value and validation_path.is_file():
        existing = load_json(validation_path)
        if (
            validate_stage.get("input_checksum") == input_fingerprint
            and existing.get("input_fingerprint") == input_fingerprint
            and existing.get("status") == "passed"
        ):
            return _validation_outcome(run_path, input_fingerprint, reused=True)
    start_stage(run_path, "validate", input_checksum=input_fingerprint)
    run_id = str(manifest["run_id"])
    try:
        payloads = _load_payloads(run_path)
        records = load_record_sets(run_path)
        validation = _validation_payload(
            run_path=run_path,
            run_id=run_id,
            report_input_fingerprint=report_input_fingerprint,
            payloads=payloads,
            records=records,
            bundle_fingerprint=input_fingerprint,
            layouts=None,
        )
        atomic_write_json(validation_path, validation)
        if validation.get("status") != "passed":
            fail_stage(run_path, "validate", "Phase 10 final validation failed")
            raise ReportError("Phase 10 final validation failed")
        complete_stage(
            run_path,
            "validate",
            required_artifacts=("outputs/report_validation.json",),
            invalidate_downstream_on_change=False,
        )
        append_json_line(
            run_path / "logs" / "events.jsonl",
            {
                "event": "phase_10_final_validation_passed",
                "input_fingerprint": input_fingerprint,
                "run_id": run_id,
                "status": "passed",
                "timestamp": utc_now(),
            },
        )
        return _validation_outcome(run_path, input_fingerprint, reused=False)
    except ReportError:
        _, latest = load_manifest(run_path)
        if latest["stages"]["validate"]["state"] == StageState.RUNNING.value:
            fail_stage(run_path, "validate", "Phase 10 final validation failed")
        raise
    except (OSError, KeyError, TypeError, ValueError) as exc:
        _, latest = load_manifest(run_path)
        if latest["stages"]["validate"]["state"] == StageState.RUNNING.value:
            fail_stage(run_path, "validate", f"Phase 10 final validation failed: {exc}")
        raise ReportError(f"Phase 10 final validation failed: {exc}") from exc
