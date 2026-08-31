"""Build the extraction-dependent evidence foundation without starting workstream analysis."""

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
from dd_engine.errors import EvidenceError
from dd_engine.evidence.citations import validate_citations
from dd_engine.evidence.models import Gap, JsonObject
from dd_engine.evidence.store import RECORD_PATHS, load_record_sets, write_record_set
from dd_engine.extraction.models import stable_json_checksum
from dd_engine.runs import load_manifest
from dd_engine.time import utc_now

FOUNDATION_VERSION = "phase7-evidence-v1"


@dataclass(frozen=True, slots=True)
class EvidenceFoundationOutcome:
    """Public result of one evidence-foundation build and validation."""

    input_fingerprint: str
    reused: bool
    run_path: Path
    summary: JsonObject
    validation_passed: bool


def _optional_json(path: Path, run_id: str) -> JsonObject | None:
    if not path.is_file():
        return None
    value = load_json(path)
    if value.get("run_id") != run_id:
        raise EvidenceError(f"artifact belongs to another run: {path}")
    return value


def _active_questions(run_path: Path, run_id: str) -> list[tuple[JsonObject, JsonObject | None]]:
    result: list[tuple[JsonObject, JsonObject | None]] = []
    for round_number in (1, 2):
        questions = _optional_json(
            run_path / "intake" / f"round_{round_number}_questions.json", run_id
        )
        if questions is None or questions.get("status") == "invalidated":
            continue
        answers = _optional_json(run_path / "intake" / f"round_{round_number}_answers.json", run_id)
        if answers is not None and answers.get("status") == "invalidated":
            answers = None
        result.append((questions, answers))
    return result


def _priority_materiality(priority: object) -> str:
    return {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }.get(str(priority), "medium")


def _intake_gaps(run_path: Path, run_id: str) -> list[JsonObject]:
    gaps: list[JsonObject] = []
    seen: set[str] = set()
    for question_payload, answer_payload in _active_questions(run_path, run_id):
        raw_answers = answer_payload.get("answers", []) if answer_payload is not None else []
        answer_by_id = {
            str(item.get("question_id")): item
            for item in raw_answers
            if isinstance(item, dict) and isinstance(item.get("question_id"), str)
        }
        raw_questions = question_payload.get("questions", [])
        for index, question in enumerate(raw_questions, start=1):
            if not isinstance(question, dict):
                continue
            question_id = str(question.get("question_id", f"question-{index}"))
            structured_gap = question.get("structured_gap")
            requested_gap_id = (
                structured_gap.get("gap_id") if isinstance(structured_gap, dict) else None
            )
            gap_id = str(requested_gap_id or f"GAP-{question_id}")
            if gap_id in seen:
                gap_id = f"{gap_id}-{question_id}"
            seen.add(gap_id)
            answer = answer_by_id.get(question_id)
            resolution = answer.get("resolution_status") if answer is not None else "open"
            status = {
                "closed": "resolved",
                "narrowed": "narrowed",
                "open": "open",
            }.get(str(resolution), "open")
            missing_evidence: list[str] = []
            description = (
                structured_gap.get("description") if isinstance(structured_gap, dict) else None
            )
            if isinstance(description, str) and description:
                missing_evidence.append(description)
            if answer is None:
                missing_evidence.append(
                    "No explicit answer artifact/record is available; silence was not treated "
                    "as an answer."
                )
                answer_provenance = None
            else:
                ambiguity = answer.get("ambiguity", [])
                if isinstance(ambiguity, list):
                    missing_evidence.extend(str(item) for item in ambiguity)
                answer_provenance = {
                    "normalised_interpretation": answer.get("normalised_interpretation"),
                    "provenance": answer.get("provenance"),
                    "resolution_status": answer.get("resolution_status"),
                    "verbatim_answer": answer.get("verbatim_answer"),
                    "verbatim_answer_sha256": answer.get("verbatim_answer_sha256"),
                }
            if not missing_evidence:
                missing_evidence.append(
                    "The intake record is retained as resolved evidence rather than deleted."
                )
            source_ids = question.get("supporting_source_ids", [])
            decisions = question.get("decision_potentially_affected", [])
            gaps.append(
                Gap(
                    run_id=run_id,
                    gap_id=gap_id,
                    expected_information=str(
                        question.get("exact_question", "Missing intake information")
                    ),
                    evidence_that_it_is_missing=tuple(missing_evidence),
                    importance=_priority_materiality(question.get("priority")),
                    affected_decision=tuple(str(item) for item in decisions),
                    requested_follow_up=str(
                        question.get(
                            "exact_question", "Provide the requested source-backed information."
                        )
                    ),
                    status=status,
                    intake_question_id=question_id,
                    source_ids=tuple(str(item) for item in source_ids),
                    answer_provenance=answer_provenance,
                    origin="foundation_intake",
                ).as_record()
            )
    return gaps


def _extraction_gaps(run_path: Path, run_id: str) -> list[JsonObject]:
    failures = load_json(run_path / "extracts" / "extraction_failures.json")
    vision = load_json(run_path / "extracts" / "needs_vision.json")
    gaps: list[JsonObject] = []
    for key in ("failed_sources", "partial_sources"):
        raw_sources = failures.get(key, [])
        for source in raw_sources:
            if not isinstance(source, dict):
                continue
            source_id = str(source.get("source_id"))
            status = str(source.get("status"))
            details = [f"Extraction status is {status}."]
            if source.get("failure_reason"):
                details.append(f"Failure: {source['failure_reason']}")
            if source.get("limitation"):
                details.append(f"Limitation: {source['limitation']}")
            gaps.append(
                Gap(
                    run_id=run_id,
                    gap_id=f"GAP-EXTRACTION-{source_id}",
                    expected_information=(
                        f"Readable, source-verifiable content from {source.get('relative_path')}"
                    ),
                    evidence_that_it_is_missing=tuple(details),
                    importance="high" if status == "failed" else "medium",
                    affected_decision=("scope", "diligence_priority", "go_no_go"),
                    requested_follow_up=(
                        "Provide a readable replacement or document explicitly that the source "
                        "cannot be obtained."
                    ),
                    status="open",
                    source_ids=(source_id,),
                    origin="foundation_extraction",
                ).as_record()
            )

    grouped_tasks: dict[str, list[JsonObject]] = {}
    for task in vision.get("tasks", []):
        if isinstance(task, dict) and isinstance(task.get("source_id"), str):
            grouped_tasks.setdefault(str(task["source_id"]), []).append(task)
    for source_id, tasks in sorted(grouped_tasks.items()):
        first = tasks[0]
        gaps.append(
            Gap(
                run_id=run_id,
                gap_id=f"GAP-VISION-{source_id}",
                expected_information=f"Visual meaning of {first.get('relative_path')}",
                evidence_that_it_is_missing=(
                    f"{len(tasks)} local vision task(s) remain pending with null model_result.",
                    "Deterministic extraction captured metadata/rendering but did not interpret "
                    "visual content.",
                ),
                importance="high",
                affected_decision=("scope", "diligence_priority"),
                requested_follow_up=(
                    "Complete an authenticated local vision review and retain its result with the "
                    "source checksum and locator."
                ),
                status="open",
                source_ids=(source_id,),
                origin="foundation_vision",
            ).as_record()
        )
    return gaps


def _input_artifacts(run_path: Path) -> list[JsonObject]:
    required = (
        "source_register/source_register.json",
        "source_register/version_families.json",
        "extracts/extraction_manifest.json",
        "extracts/extracted_units.jsonl",
        "extracts/extraction_failures.json",
        "extracts/needs_vision.json",
    )
    optional = tuple(
        f"intake/round_{round_number}_{kind}.json"
        for round_number in (1, 2)
        for kind in ("questions", "answers")
    )
    records: list[JsonObject] = []
    for relative_path in (*required, *optional):
        path = run_path / relative_path
        if relative_path in required and not path.is_file():
            raise EvidenceError(f"evidence foundation input is missing: {relative_path}")
        if path.is_file():
            records.append({"path": relative_path, "sha256": file_sha256(path)})
    return records


def _record_artifacts(run_path: Path) -> list[JsonObject]:
    return [
        {"path": relative_path, "sha256": file_sha256(run_path / relative_path)}
        for relative_path in RECORD_PATHS.values()
    ]


def _coverage_markdown(report: JsonObject, record_sets: dict[str, list[JsonObject]]) -> str:
    summary = report["summary"]
    coverage = summary["material_claim_coverage"]
    coverage_text = "not applicable (no material claims)" if coverage is None else f"{coverage:.1%}"
    open_gaps = sum(item.get("status") in {"open", "narrowed"} for item in record_sets["gaps"])
    lines = [
        "# Evidence coverage",
        "",
        f"Run ID: `{report['run_id']}`",
        "",
        "This is a deterministic validation ledger, not workstream analysis or report prose.",
        "",
        f"Validation status: **{str(report['status']).upper()}**",
        "",
        "## Coverage",
        "",
        "| Measure | Result |",
        "|---|---:|",
        f"| Claims | {summary['claim_count']} |",
        f"| Material claims | {summary['material_claim_count']} |",
        f"| Material claim citation coverage | {coverage_text} |",
        f"| Evidence citations | {summary['evidence_count']} |",
        f"| Calculations | {summary['calculation_count']} |",
        f"| Contradictions | {summary['contradiction_count']} |",
        f"| Gaps | {summary['gap_count']} ({open_gaps} open/narrowed) |",
        f"| Issues | {summary['issue_count']} |",
        f"| Failed citations | {summary['failed_citation_count']} |",
        "| Structural/reference errors | "
        f"{summary['record_error_count'] + summary['reference_error_count']} |",
        "",
        "## Failed citations",
        "",
    ]
    if report["failed_citations"]:
        for citation in report["failed_citations"]:
            codes = ", ".join(str(item["code"]) for item in citation["errors"])
            lines.append(f"- `{citation['citation_id']}`: {codes}")
    else:
        lines.append("None.")
    lines.extend(["", "## Duplicate-corroboration protection", ""])
    exclusions = report["duplicate_corroboration_exclusions"]
    if exclusions:
        for exclusion in exclusions:
            excluded = ", ".join(exclusion["excluded_evidence_ids"])
            lines.append(
                f"- Claim `{exclusion['claim_id']}`: `{excluded}` excluded from independent "
                f"corroboration under `{exclusion['independence_key']}`."
            )
    else:
        lines.append(
            "Exact duplicates are grouped by register duplicate group or source checksum; no "
            "duplicate evidence was presented as independent corroboration in this record set."
        )
    lines.extend(
        [
            "",
            "## Calculation guardrails",
            "",
            "Reported and recomputed values remain separate. Missing inputs remain null and block "
            "recomputation. Period, currency, sign and unit normalization, the formula/version, "
            "rounding and deterministic/model-assisted method are mandatory calculation fields.",
            "",
        ]
    )
    return "\n".join(lines)


def _merge_foundation_gaps(
    existing: list[JsonObject], generated: list[JsonObject]
) -> list[JsonObject]:
    retained = [
        item for item in existing if not str(item.get("origin", "")).startswith("foundation_")
    ]
    retained_ids = {str(item.get("gap_id")) for item in retained}
    conflicts = sorted(
        str(item.get("gap_id")) for item in generated if str(item.get("gap_id")) in retained_ids
    )
    if conflicts:
        raise EvidenceError(
            "analytical gaps conflict with foundation-owned gap IDs: " + ", ".join(conflicts)
        )
    return sorted((*retained, *generated), key=lambda item: str(item.get("gap_id")))


def build_evidence_foundation(run: str | Path) -> EvidenceFoundationOutcome:
    """Materialize gaps and validate structured records without completing intake/analysis."""

    run_path, manifest = load_manifest(run)
    run_id = str(manifest["run_id"])
    if manifest["stages"]["register"]["state"] != StageState.COMPLETED.value:
        raise EvidenceError("evidence foundation requires a completed source register")
    if manifest["stages"]["extract"]["state"] != StageState.COMPLETED.value:
        raise EvidenceError("evidence foundation requires completed extraction")

    input_artifacts = _input_artifacts(run_path)
    input_fingerprint = stable_json_checksum(
        {
            "artifacts": input_artifacts,
            "foundation_version": FOUNDATION_VERSION,
            "schema_version": 1,
        }
    )
    existing = load_record_sets(run_path, allow_missing=True)
    generated_gaps = _intake_gaps(run_path, run_id) + _extraction_gaps(run_path, run_id)
    existing["gaps"] = _merge_foundation_gaps(existing["gaps"], generated_gaps)
    for record_type in RECORD_PATHS:
        write_record_set(run_path, record_type, existing[record_type])
    record_artifacts = _record_artifacts(run_path)

    validation_path = run_path / "evidence" / "citation_validation.json"
    coverage_path = run_path / "evidence" / "evidence_coverage.md"
    prior = _optional_json(validation_path, run_id)
    if (
        prior is not None
        and prior.get("input_fingerprint") == input_fingerprint
        and prior.get("record_artifacts") == record_artifacts
        and coverage_path.is_file()
    ):
        return EvidenceFoundationOutcome(
            input_fingerprint=input_fingerprint,
            reused=True,
            run_path=run_path,
            summary=dict(prior.get("summary", {})),
            validation_passed=prior.get("status") == "passed",
        )

    record_sets = load_record_sets(run_path)
    report = validate_citations(run_path, record_sets)
    report.update(
        {
            "foundation_version": FOUNDATION_VERSION,
            "generated_at": utc_now(),
            "input_artifacts": input_artifacts,
            "input_fingerprint": input_fingerprint,
            "intake_stage_state": manifest["stages"]["intake"]["state"],
            "record_artifacts": record_artifacts,
            "untrusted_source_data_was_executed": False,
            "workstream_analysis_performed": False,
        }
    )
    atomic_write_json(validation_path, report)
    atomic_write_text(coverage_path, _coverage_markdown(report, record_sets))
    append_json_line(
        run_path / "logs" / "events.jsonl",
        {
            "event": "evidence_foundation_validated",
            "failed_citation_count": report["summary"]["failed_citation_count"],
            "input_fingerprint": input_fingerprint,
            "run_id": run_id,
            "status": report["status"],
            "timestamp": utc_now(),
            "workstream_analysis_performed": False,
        },
    )
    return EvidenceFoundationOutcome(
        input_fingerprint=input_fingerprint,
        reused=False,
        run_path=run_path,
        summary=dict(report["summary"]),
        validation_passed=report["status"] == "passed",
    )
