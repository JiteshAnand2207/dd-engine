"""Deterministic Phase 8/9 analytical quality, citation and privacy gates."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping

from dd_engine.analysis.context import AnalysisContext
from dd_engine.evidence.citations import validate_citations
from dd_engine.evidence.models import JsonObject

_PII_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(r"(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){9,}"),
    "synthetic_personal_identifier": re.compile(r"\bSYN\d{6,}[A-Z]?\b", re.I),
}
_HEDGES = re.compile(r"\b(?:may|might|could)\b", re.I)


def _problem(code: str, message: str, *, record_id: str | None = None) -> JsonObject:
    value: JsonObject = {"code": code, "message": message}
    if record_id is not None:
        value["record_id"] = record_id
    return value


def validate_analysis(
    context: AnalysisContext,
    record_sets: Mapping[str, list[JsonObject]],
    payloads: Mapping[str, JsonObject],
    *,
    phase: int,
) -> JsonObject:
    """Run all workstream gates and return a complete, non-suppressed result."""

    citation_report = validate_citations(context.run_path, record_sets)
    errors: list[JsonObject] = []
    warnings: list[JsonObject] = []
    valid_evidence_ids = {
        str(item["citation_id"])
        for item in citation_report["citation_results"]
        if item["citation_kind"] == "evidence" and item["valid"]
    }
    issue_ids: set[str] = set()
    for workstream, payload in payloads.items():
        if payload.get("run_id") != context.run_id:
            errors.append(_problem("workstream_run_id_mismatch", workstream))
        coverage = payload.get("coverage")
        if workstream != "customer_grouping" and not isinstance(coverage, list):
            errors.append(_problem("missing_workstream_coverage", workstream))
        for finding in payload.get("findings", []):
            issue_id = str(finding.get("issue_id"))
            if issue_id in issue_ids:
                errors.append(_problem("duplicate_issue_id", issue_id, record_id=issue_id))
            issue_ids.add(issue_id)
            for field in (
                "analysis_conclusion",
                "analytical_reasoning",
                "source_fact",
                "why_it_matters",
                "transaction_implication",
                "action",
            ):
                if not isinstance(finding.get(field), str) or not str(finding[field]).strip():
                    errors.append(
                        _problem(
                            "missing_finding_field", f"{issue_id} lacks {field}", record_id=issue_id
                        )
                    )
            supporting = finding.get("supporting_evidence_ids")
            if finding.get("materiality") in {"high", "critical"} and (
                not isinstance(supporting, list)
                or not supporting
                or any(str(item) not in valid_evidence_ids for item in supporting)
            ):
                errors.append(
                    _problem(
                        "material_finding_without_valid_citation",
                        f"{issue_id} lacks complete valid citation support",
                        record_id=issue_id,
                    )
                )
            conclusion = str(finding.get("analysis_conclusion", ""))
            if _HEDGES.search(conclusion) and not finding.get("uncertainty"):
                errors.append(
                    _problem(
                        "unexplained_hedging",
                        f"{issue_id} uses may/might/could without explicit uncertainty",
                        record_id=issue_id,
                    )
                )
            if workstream == "legal_contractual" and finding.get("opinion_status") != (
                "commercial_diligence_not_formal_legal_opinion"
            ):
                errors.append(
                    _problem(
                        "unsupported_legal_conclusion_scope",
                        f"{issue_id} does not declare the commercial-diligence boundary",
                        record_id=issue_id,
                    )
                )
            if workstream == "tax" and finding.get("opinion_status") != (
                "commercial_tax_diligence_not_formal_tax_opinion"
            ):
                errors.append(
                    _problem(
                        "unsupported_tax_conclusion_scope",
                        f"{issue_id} does not declare the tax-diligence boundary",
                        record_id=issue_id,
                    )
                )
            if workstream == "tax" and (
                not isinstance(finding.get("cross_workstream_links"), list)
                or not finding["cross_workstream_links"]
            ):
                errors.append(
                    _problem(
                        "missing_tax_cross_workstream_link",
                        f"{issue_id} has no affected-workstream link",
                        record_id=issue_id,
                    )
                )

    serialized = json.dumps(payloads, sort_keys=True, ensure_ascii=False).replace(
        context.run_id, "RUN_ID"
    )
    privacy_hits = {
        name: sorted(set(pattern.findall(serialized)))
        for name, pattern in _PII_PATTERNS.items()
        if pattern.search(serialized)
    }
    if privacy_hits:
        errors.append(
            _problem(
                "pii_in_workstream_output",
                "structured workstream output contains personal-data-like values",
            )
        )

    cross_reference_observed = bool(
        context.units_matching(r"see legal 2\.1", locator_type="spreadsheet_cell")
        or context.units_matching(r"see legal 2\.1", locator_type="docx_table_cell")
    )
    gap_ids = {str(item.get("gap_id")) for item in record_sets.get("gaps", [])}
    questionnaire_reference_passed = (
        not cross_reference_observed or "GAP-MISSING-CROSS-REFERENCE" in gap_ids
    )
    if not questionnaire_reference_passed:
        errors.append(
            _problem(
                "unresolved_questionnaire_cross_reference_not_tracked",
                "a missing legal 2.1 reference is not represented as a gap",
            )
        )

    version_failures = [
        item
        for item in citation_report["failed_citations"]
        if any(
            error["code"] in {"silently_superseded_source", "source_version_status_mismatch"}
            for error in item["errors"]
        )
    ]
    if version_failures:
        errors.append(_problem("amendment_version_check_failed", "version-aware citations failed"))

    calculation_failures = [
        item for item in citation_report["calculation_results"] if not item["valid"]
    ]
    tax_calculation_failures = [
        item for item in calculation_failures if str(item["calculation_id"]).startswith("CALC-TAX")
    ]
    if tax_calculation_failures:
        errors.append(
            _problem("tax_recomputation_check_failed", "one or more Tax calculations failed")
        )

    if citation_report["status"] != "passed":
        errors.append(
            _problem("citation_validation_failed", "structured citation validation failed")
        )
    if context.unresolved_answer_ids():
        warnings.append(
            _problem(
                "unresolved_intake_answers",
                "explicitly ingested open/narrowed answers remain limitations: "
                + ", ".join(context.unresolved_answer_ids()),
            )
        )
    return {
        "amendment_version_checks": {
            "failed_count": len(version_failures),
            "passed": not version_failures,
        },
        "citation_validation": citation_report,
        "errors": errors,
        "missing_evidence_checks": {
            "gap_count": len(record_sets.get("gaps", [])),
            "passed": all(
                isinstance(payload.get("coverage"), list)
                for key, payload in payloads.items()
                if key != "customer_grouping"
            ),
        },
        "phase": phase,
        "pii_handling_checks": {"hits": privacy_hits, "passed": not privacy_hits},
        "questionnaire_reference_checks": {
            "missing_reference_observed": cross_reference_observed,
            "passed": questionnaire_reference_passed,
        },
        "run_id": context.run_id,
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "summary": {
            "error_count": len(errors),
            "finding_count": sum(len(payload.get("findings", [])) for payload in payloads.values()),
            "material_finding_count": sum(
                finding.get("materiality") in {"high", "critical"}
                for payload in payloads.values()
                for finding in payload.get("findings", [])
            ),
            "warning_count": len(warnings),
        },
        "tax_recomputation_checks": {
            "failed_count": len(tax_calculation_failures),
            "passed": not tax_calculation_failures,
        },
        "unsupported_legal_conclusion_check": {
            "passed": not any(
                error["code"] == "unsupported_legal_conclusion_scope" for error in errors
            )
        },
        "warnings": warnings,
    }
