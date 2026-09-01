"""Sequential Phase 8/9 orchestration and analysis-stage completion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dd_engine.analysis.context import AnalysisContext
from dd_engine.analysis.phase8 import PHASE8_VERSION, build_phase8
from dd_engine.analysis.phase9 import PHASE9_VERSION, build_phase9
from dd_engine.analysis.records import AnalysisRecords
from dd_engine.analysis.rendering import (
    render_customer_grouping,
    render_financial_calculations,
    render_workstream,
)
from dd_engine.analysis.validation import validate_analysis
from dd_engine.artifacts import (
    append_json_line,
    atomic_write_json,
    atomic_write_jsonl,
    atomic_write_text,
    file_sha256,
    load_json,
)
from dd_engine.constants import StageState
from dd_engine.errors import AnalysisError
from dd_engine.evidence.models import JsonObject
from dd_engine.evidence.pipeline import build_evidence_foundation
from dd_engine.evidence.store import RECORD_PATHS, load_record_sets, write_record_set
from dd_engine.extraction.models import stable_json_checksum
from dd_engine.runs import load_manifest
from dd_engine.runtime.logging import record_public_research
from dd_engine.state import complete_stage, fail_stage, reopen_completed_stage, start_stage
from dd_engine.time import utc_now

ANALYSIS_INPUT_VERSION = "phase8-phase9-input-v2"

PHASE8_OUTPUTS = (
    "workstreams/financial.json",
    "workstreams/financial.md",
    "workstreams/commercial.json",
    "workstreams/commercial.md",
    "workstreams/financial_calculations.md",
    "workstreams/customer_grouping.md",
    "workstreams/customer_grouping.json",
    "workstreams/phase_8_validation.json",
)
PHASE9_OUTPUTS = (
    "workstreams/legal_contractual.json",
    "workstreams/legal_contractual.md",
    "workstreams/operational_management.json",
    "workstreams/operational_management.md",
    "workstreams/it.json",
    "workstreams/it.md",
    "tax/tax-findings.json",
    "tax/tax-analysis.md",
    "workstreams/phase_9_validation.json",
    "workstreams/analysis_validation.json",
    "citations/index.jsonl",
)


@dataclass(frozen=True, slots=True)
class AnalysisOutcome:
    """Public result of one sequential analytical phase."""

    input_fingerprint: str
    phase: int
    reused: bool
    run_path: Path
    stage_state: str
    summary: dict[str, object]
    validation_passed: bool


def _require_ready(run_path: Path, manifest: dict[str, object]) -> None:
    stages = manifest["stages"]
    if not isinstance(stages, dict):
        raise AnalysisError("run manifest has no stages")
    intake = stages.get("intake")
    if not isinstance(intake, dict) or intake.get("state") != StageState.COMPLETED.value:
        raise AnalysisError(
            "analysis requires completed two-round intake; silence or an awaiting_input pause "
            "cannot be used to create workstream findings"
        )
    for round_number in (1, 2):
        answer_path = run_path / "intake" / f"round_{round_number}_answers.json"
        if not answer_path.is_file():
            raise AnalysisError(f"analysis requires explicit round-{round_number} answer ingestion")


def _input_fingerprint(run_path: Path) -> str:
    relative_paths = (
        "source_register/source_register.json",
        "source_register/version_families.json",
        "extracts/extraction_manifest.json",
        "extracts/extracted_units.jsonl",
        "intake/round_1_answers.json",
        "intake/round_2_answers.json",
    )
    artifacts = []
    for relative_path in relative_paths:
        path = run_path / relative_path
        if not path.is_file():
            raise AnalysisError(f"analysis input artifact is missing: {relative_path}")
        artifacts.append({"path": relative_path, "sha256": file_sha256(path)})
    return stable_json_checksum(
        {
            "analysis_input_version": ANALYSIS_INPUT_VERSION,
            "artifacts": artifacts,
            "phase8_version": PHASE8_VERSION,
            "phase9_version": PHASE9_VERSION,
        }
    )


def _remove_owned(records: dict[str, list[dict[str, object]]], phase: int) -> None:
    prefixes: tuple[str, ...]
    if phase == 8:
        prefixes = (
            "FIN-",
            "COMM-",
            "CLM-FIN-",
            "CLM-COMM-",
            "EVD-FIN-",
            "EVD-COMM-",
            "CALC-FIN-",
            "CALC-COMM-",
            "CON-FIN-",
            "CON-COMM-",
        )
        origins = {"phase8_analysis"}
    else:
        prefixes = (
            "LEGAL-",
            "TAX-",
            "OPS-",
            "IT-",
            "CLM-LEGAL-",
            "CLM-TAX-",
            "CLM-OPS-",
            "CLM-IT-",
            "EVD-LEGAL-",
            "EVD-TAX-",
            "EVD-OPS-",
            "EVD-IT-",
            "CALC-LEGAL-",
            "CALC-TAX-",
            "CALC-OPS-",
            "CALC-IT-",
            "CON-LEGAL-",
            "CON-TAX-",
            "CON-OPS-",
            "CON-IT-",
        )
        origins = {"phase9_analysis"}
    id_fields = {
        "claims": "claim_id",
        "evidence": "evidence_id",
        "calculations": "calculation_id",
        "contradictions": "contradiction_id",
        "issues": "issue_id",
    }
    for record_type, field in id_fields.items():
        records[record_type] = [
            item
            for item in records[record_type]
            if not str(item.get(field, "")).startswith(prefixes)
        ]
    records["gaps"] = [item for item in records["gaps"] if str(item.get("origin")) not in origins]


def _merge_records(
    run_path: Path,
    phase: int,
    generated: AnalysisRecords,
) -> dict[str, list[dict[str, object]]]:
    existing = load_record_sets(run_path)
    _remove_owned(existing, phase)
    for record_type in RECORD_PATHS:
        values = getattr(generated, record_type)
        existing[record_type].extend(values)
        write_record_set(run_path, record_type, existing[record_type])
    return existing


def _write_citation_index(run_path: Path, evidence: list[dict[str, object]]) -> None:
    (run_path / "citations").mkdir(exist_ok=True)
    atomic_write_jsonl(run_path / "citations" / "index.jsonl", evidence)


def _write_phase8(
    context: AnalysisContext,
    payloads: dict[str, dict[str, object]],
    records: dict[str, list[dict[str, object]]],
) -> None:
    financial = payloads["financial"]
    commercial = payloads["commercial"]
    grouping = payloads["customer_grouping"]
    atomic_write_json(context.run_path / "workstreams" / "financial.json", financial)
    atomic_write_json(context.run_path / "workstreams" / "commercial.json", commercial)
    atomic_write_json(context.run_path / "workstreams" / "customer_grouping.json", grouping)
    atomic_write_text(
        context.run_path / "workstreams" / "financial.md",
        render_workstream(financial, records["evidence"], title="Financial analysis"),
    )
    atomic_write_text(
        context.run_path / "workstreams" / "commercial.md",
        render_workstream(commercial, records["evidence"], title="Commercial analysis"),
    )
    atomic_write_text(
        context.run_path / "workstreams" / "financial_calculations.md",
        render_financial_calculations(context.run_id, records["calculations"]),
    )
    atomic_write_text(
        context.run_path / "workstreams" / "customer_grouping.md",
        render_customer_grouping(grouping),
    )


def _tax_links() -> list[JsonObject]:
    return [
        {
            "affected_workstreams": ["financial", "legal_contractual", "operational_management"],
            "tax_issue_id": "TAX-001",
        },
        {
            "affected_workstreams": ["financial", "legal_contractual"],
            "tax_issue_id": "TAX-002",
        },
        {
            "affected_workstreams": ["financial", "operational_management"],
            "tax_issue_id": "TAX-003",
        },
        {
            "affected_workstreams": ["financial", "legal_contractual"],
            "tax_issue_id": "TAX-004",
        },
    ]


def _write_phase9(
    context: AnalysisContext,
    payloads: dict[str, dict[str, object]],
    records: dict[str, list[dict[str, object]]],
) -> None:
    (context.run_path / "tax").mkdir(exist_ok=True)
    links = _tax_links()
    tax_findings = payloads["tax"].get("findings", [])
    if not isinstance(tax_findings, list):
        raise AnalysisError("Tax analytical payload has an invalid findings list")
    for finding in tax_findings:
        if not isinstance(finding, dict):
            raise AnalysisError("Tax analytical payload contains a non-object finding")
        finding["cross_workstream_links"] = next(
            (
                item["affected_workstreams"]
                for item in links
                if item["tax_issue_id"] == finding["issue_id"]
            ),
            [],
        )
    for workstream in ("legal_contractual", "operational_management", "it"):
        payloads[workstream]["tax_cross_workstream_links"] = [
            item for item in links if workstream in item["affected_workstreams"]
        ]
    locations = {
        "legal_contractual": (
            "workstreams/legal_contractual.json",
            "workstreams/legal_contractual.md",
            "Legal / contractual analysis",
        ),
        "operational_management": (
            "workstreams/operational_management.json",
            "workstreams/operational_management.md",
            "Operational / management analysis",
        ),
        "it": ("workstreams/it.json", "workstreams/it.md", "IT analysis"),
        "tax": ("tax/tax-findings.json", "tax/tax-analysis.md", "Tax analysis"),
    }
    for workstream, (json_path, markdown_path, title) in locations.items():
        payload = payloads[workstream]
        atomic_write_json(context.run_path / json_path, payload)
        atomic_write_text(
            context.run_path / markdown_path,
            render_workstream(payload, records["evidence"], title=title),
        )
    financial_path = context.run_path / "workstreams" / "financial.json"
    if financial_path.is_file():
        financial = load_json(financial_path)
        financial["tax_cross_workstream_links"] = links
        atomic_write_json(financial_path, financial)


def _existing_outcome(
    run_path: Path,
    phase: int,
    input_fingerprint: str,
) -> AnalysisOutcome | None:
    path = run_path / "workstreams" / f"phase_{phase}_validation.json"
    if not path.is_file():
        return None
    value = load_json(path)
    if value.get("input_fingerprint") != input_fingerprint or value.get("status") != "passed":
        return None
    _, manifest = load_manifest(run_path)
    if (
        phase == 9
        and manifest["stages"]["analyse"]["state"] != StageState.COMPLETED.value
    ):
        return None
    return AnalysisOutcome(
        input_fingerprint=input_fingerprint,
        phase=phase,
        reused=True,
        run_path=run_path,
        stage_state=str(manifest["stages"]["analyse"]["state"]),
        summary=dict(value.get("summary", {})),
        validation_passed=value.get("status") == "passed",
    )


def _research_not_performed(context: AnalysisContext) -> None:
    path = context.run_path / "logs" / "public-research-log.jsonl"
    if path.is_file() and path.stat().st_size:
        return
    record_public_research(
        context.run_path,
        {
            "action": "not_performed",
            "citations_supported": [],
            "claim_ids_supported": [],
            "conclusion": (
                "Source-room evidence was sufficient for the scoped analysis; public research "
                "remained disabled."
            ),
            "confidential_room_content_included": False,
            "purpose": "Phase 9 Irish legal/tax contextual research",
            "query": None,
            "result_used": False,
            "retrieved_page_sha256": None,
            "source_type": None,
            "timestamp": utc_now(),
            "url": None,
        },
    )


def analyse_run(run: str | Path, phase: int) -> AnalysisOutcome:
    """Run Phase 8, then Phase 9, preserving the mandatory sequential gate."""

    if phase not in {8, 9}:
        raise AnalysisError("analysis phase must be 8 or 9")
    run_path, manifest = load_manifest(run)
    _require_ready(run_path, manifest)
    build_evidence_foundation(run_path)
    input_fingerprint = _input_fingerprint(run_path)
    existing = _existing_outcome(run_path, phase, input_fingerprint)
    if existing is not None:
        return existing
    if phase == 9:
        phase8_path = run_path / "workstreams" / "phase_8_validation.json"
        if not phase8_path.is_file():
            raise AnalysisError("Phase 9 requires completed Phase 8 outputs")
        phase8 = load_json(phase8_path)
        if phase8.get("status") != "passed" or phase8.get("input_fingerprint") != input_fingerprint:
            raise AnalysisError("Phase 9 requires current, passing Phase 8 validation")

    analyse_state = str(manifest["stages"]["analyse"]["state"])
    if analyse_state in {
        StageState.NOT_STARTED.value,
        StageState.FAILED.value,
        StageState.INVALIDATED.value,
    }:
        start_stage(run_path, "analyse", input_checksum=input_fingerprint)
    elif analyse_state == StageState.COMPLETED.value:
        reopen_completed_stage(
            run_path,
            "analyse",
            "validated analysis artifact is stale for the current input fingerprint",
        )
    elif analyse_state != StageState.RUNNING.value:
        raise AnalysisError(f"cannot run Phase {phase} from analyse state {analyse_state}")

    context = AnalysisContext(run_path)
    try:
        generated, raw_payloads = build_phase8(context) if phase == 8 else build_phase9(context)
        payloads = {name: dict(value) for name, value in raw_payloads.items()}
        records = _merge_records(run_path, phase, generated)
        _write_citation_index(run_path, records["evidence"])
        if phase == 8:
            _write_phase8(context, payloads, records)
        else:
            _research_not_performed(context)
            _write_phase9(context, payloads, records)
        validation = validate_analysis(context, records, payloads, phase=phase)
        validation.update(
            {
                "analysis_input_version": ANALYSIS_INPUT_VERSION,
                "generated_at": utc_now(),
                "input_fingerprint": input_fingerprint,
                "public_research_performed": False,
                "untrusted_source_data_was_executed": False,
            }
        )
        validation_path = run_path / "workstreams" / f"phase_{phase}_validation.json"
        atomic_write_json(validation_path, validation)
        atomic_write_json(
            run_path / "evidence" / "citation_validation.json", validation["citation_validation"]
        )
        if validation["status"] != "passed":
            fail_stage(run_path, "analyse", f"Phase {phase} analytical validation failed")
            raise AnalysisError(f"Phase {phase} analytical validation failed")
        if phase == 9:
            atomic_write_json(run_path / "workstreams" / "analysis_validation.json", validation)
            complete_stage(
                run_path,
                "analyse",
                required_artifacts=[*PHASE8_OUTPUTS, *PHASE9_OUTPUTS],
            )
        append_json_line(
            run_path / "logs" / "events.jsonl",
            {
                "event": f"phase_{phase}_analysis_validated",
                "finding_count": validation["summary"]["finding_count"],
                "input_fingerprint": input_fingerprint,
                "run_id": context.run_id,
                "status": validation["status"],
                "timestamp": utc_now(),
            },
        )
        _, updated_manifest = load_manifest(run_path)
        return AnalysisOutcome(
            input_fingerprint=input_fingerprint,
            phase=phase,
            reused=False,
            run_path=run_path,
            stage_state=str(updated_manifest["stages"]["analyse"]["state"]),
            summary=dict(validation["summary"]),
            validation_passed=True,
        )
    except AnalysisError as exc:
        _, latest = load_manifest(run_path)
        if latest["stages"]["analyse"]["state"] == StageState.RUNNING.value:
            fail_stage(run_path, "analyse", f"Phase {phase} analysis failed: {exc}")
        raise
    except (OSError, KeyError, TypeError, ValueError) as exc:
        _, latest = load_manifest(run_path)
        if latest["stages"]["analyse"]["state"] == StageState.RUNNING.value:
            fail_stage(run_path, "analyse", f"Phase {phase} analysis failed: {exc}")
        raise AnalysisError(f"Phase {phase} analysis failed: {exc}") from exc
