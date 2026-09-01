"""Render Phase 10 Markdown outputs from validated structured records."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from dd_engine.evidence.models import JsonObject

REPORT_SECTION_HEADINGS = (
    "## 1. Executive summary",
    "## 2. Transaction context, scope and limitations",
    "## 3. Key findings and decision implications",
    "## 4. Financial",
    "## 5. Commercial",
    "## 6. Legal/contractual",
    "## 7. Operational/management",
    "## 8. IT",
    "## 9. Tax",
    "## 10. Outstanding information and conditions",
    "## 11. Methodology and appendices",
)

BRIEF_SECTION_HEADINGS = (
    "## Transaction and thesis",
    "## Most material findings",
    "## Headline financial reconciliation",
    "## Go/no-go conditions",
    "## Price/structure protections",
    "## Critical unanswered questions",
    "## Immediate next actions",
)

WORKSTREAM_ORDER = (
    "financial",
    "commercial",
    "legal_contractual",
    "operational_management",
    "it",
    "tax",
)

WORKSTREAM_TITLES = {
    "financial": "Financial",
    "commercial": "Commercial",
    "legal_contractual": "Legal/contractual",
    "operational_management": "Operational/management",
    "it": "IT",
    "tax": "Tax",
}

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _plain(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _initial_capital(value: object) -> str:
    text = _plain(value)
    return text[:1].upper() + text[1:]


def _table(value: object) -> str:
    return _plain(value).replace("|", "\\|")


def _objects(value: object) -> list[JsonObject]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _currency(value: object, currency: object = "EUR") -> str:
    if value is None:
        return "not reported"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int | float):
        if currency == "EUR":
            return f"EUR {value:,.2f}".replace(".00", "")
        return f"{value:,.2f}".replace(".00", "")
    return _plain(value)


def _locator_text(locator: object) -> str:
    if not isinstance(locator, dict):
        return "invalid locator"
    locator_type = locator.get("type")
    if locator_type == "pdf_page":
        return f"p. {locator.get('page_number')}"
    if locator_type == "spreadsheet_cell":
        cell_range = str(locator.get("range") or locator.get("cell") or "")
        cell_label = "cells" if ":" in cell_range else "cell"
        return f"sheet \u201c{locator.get('sheet')}\u201d, {cell_label} {cell_range}"
    if locator_type == "docx_paragraph":
        return f"paragraph {locator.get('paragraph_index')}"
    if locator_type == "docx_table_cell":
        return (
            f"table {locator.get('table_index')}, row {locator.get('row_index')}, "
            f"cell {locator.get('cell_index')}"
        )
    if locator_type == "csv_cell":
        return f"row {locator.get('row_index')}, column {locator.get('column_index')}"
    if locator_type == "image":
        image_number = locator.get("image_number") or locator.get("image_index") or 1
        return f"image {image_number}"
    return _plain(locator)


def human_citation(source_id: object, locator: object) -> str:
    """Format one already-validated native locator for a human reader."""

    return f"[{source_id}, {_locator_text(locator)}]"


def evidence_index(records: Sequence[JsonObject]) -> dict[str, JsonObject]:
    return {
        str(item.get("evidence_id")): item
        for item in records
        if isinstance(item.get("evidence_id"), str)
    }


def citations_for_ids(
    identifiers: Sequence[str], evidence_by_id: Mapping[str, JsonObject]
) -> list[str]:
    result: list[str] = []
    for identifier in identifiers:
        evidence = evidence_by_id.get(identifier)
        if evidence is None:
            continue
        citation = human_citation(evidence.get("source_id"), evidence.get("exact_locator"))
        if citation not in result:
            result.append(citation)
    return result


def calculation_citations(calculation: JsonObject) -> list[str]:
    result: list[str] = []
    for item in _objects(calculation.get("source_inputs")):
        citation = human_citation(item.get("source_id"), item.get("locator"))
        if citation not in result:
            result.append(citation)
    return result


def findings_by_workstream(payloads: Mapping[str, JsonObject]) -> list[tuple[str, JsonObject]]:
    result: list[tuple[str, JsonObject]] = []
    for workstream in WORKSTREAM_ORDER:
        payload = payloads.get(workstream, {})
        for finding in _objects(payload.get("findings")):
            result.append((workstream, finding))
    return result


def sorted_findings(payloads: Mapping[str, JsonObject]) -> list[tuple[str, JsonObject]]:
    indexed = list(enumerate(findings_by_workstream(payloads)))
    indexed.sort(
        key=lambda item: (
            _SEVERITY_ORDER.get(str(item[1][1].get("materiality")), 9),
            WORKSTREAM_ORDER.index(item[1][0]),
            item[0],
        )
    )
    return [item for _, item in indexed]


def _answer_value(answers: Mapping[str, JsonObject], question_id: str) -> str:
    answer = answers.get(question_id, {})
    return _plain(answer.get("verbatim_answer"))


def _answer_for_topic(
    questions: Sequence[JsonObject],
    answers: Mapping[str, JsonObject],
    topic_key: str,
) -> str:
    """Resolve a deal-context answer by semantic topic rather than generated position."""

    question = next((item for item in questions if item.get("topic_key") == topic_key), None)
    if not isinstance(question, dict) or not isinstance(question.get("question_id"), str):
        return ""
    return _answer_value(answers, str(question["question_id"]))


def _calculation_text(
    identifiers: Sequence[str], calculations_by_id: Mapping[str, JsonObject]
) -> str:
    if not identifiers:
        return "Not applicable to this finding."
    values: list[str] = []
    for identifier in identifiers:
        calculation = calculations_by_id.get(identifier)
        if calculation is None:
            values.append(f"{identifier}: calculation record unavailable")
            continue
        result = calculation.get("result")
        result_obj = result if isinstance(result, dict) else {}
        formula = calculation.get("formula")
        formula_obj = formula if isinstance(formula, dict) else {}
        currency = calculation.get("currency")
        citations = " ".join(calculation_citations(calculation))
        values.append(
            f"{identifier}: reported {_currency(result_obj.get('reported_value'), currency)}; "
            f"recomputed {_currency(result_obj.get('recomputed_value'), currency)}; "
            f"variance {_currency(result_obj.get('variance'), currency)}; "
            f"formula `{_plain(formula_obj.get('expression'))}`. "
            f"{citations}"
        )
    return " ".join(values)


def _finding_block(
    finding: JsonObject,
    evidence_by_id: Mapping[str, JsonObject],
    calculations_by_id: Mapping[str, JsonObject],
) -> list[str]:
    supporting_ids = _strings(finding.get("supporting_evidence_ids"))
    counter_ids = _strings(finding.get("counterevidence_ids"))
    supporting_citations = citations_for_ids(supporting_ids, evidence_by_id)
    counter_citations = citations_for_ids(counter_ids, evidence_by_id)
    uncertainty = _plain(finding.get("uncertainty"))
    counter_text = " ".join(counter_citations)
    if uncertainty:
        counter_text = f"{uncertainty} {counter_text}".strip()
    elif not counter_text:
        counter_text = "No contrary source was identified in the validated record."
    citation_text = " ".join(supporting_citations)
    calculation_ids = _strings(finding.get("calculation_ids"))
    return [
        f"### {finding.get('issue_id')} - {_plain(finding.get('materiality')).upper()}",
        "",
        f"**Conclusion:** {_plain(finding.get('analysis_conclusion'))}",
        "",
        f"**Evidence:** {_plain(finding.get('source_fact'))} {citation_text}",
        "",
        f"**Counterevidence/limitation:** {counter_text}",
        "",
        "**Recomputed value where relevant:** "
        f"{_calculation_text(calculation_ids, calculations_by_id)}",
        "",
        f"**Why it matters:** {_plain(finding.get('why_it_matters'))}",
        "",
        f"**Transaction implication:** {_plain(finding.get('transaction_implication'))}",
        "",
        f"**Recommended action/protection:** {_plain(finding.get('action'))}",
        "",
        f"**Confidence:** {float(finding.get('confidence', 0)):.0%}",
        "",
        f"**Citation:** {citation_text}",
        "",
    ]


def _critical_conditions(findings: Sequence[tuple[str, JsonObject]]) -> list[str]:
    conditions: list[str] = []
    for _, finding in findings:
        if finding.get("materiality") != "critical":
            continue
        value = _plain(finding.get("action"))
        if value and value not in conditions:
            conditions.append(value)
    return conditions


def _lever_label(value: str) -> str:
    return value.replace("_", " ").strip()


def _brief_critical_conditions(
    critical: Sequence[tuple[str, JsonObject]],
) -> list[str]:
    conditions: list[str] = []
    for _, finding in critical:
        issue_id = _plain(finding.get("issue_id"))
        levers = [_lever_label(value) for value in _strings(finding.get("transaction_levers"))]
        lever_text = ", ".join(levers) if levers else "completion protection"
        conditions.append(
            f"{issue_id}: require {lever_text} and completion of the finding's stated action."
        )
    return conditions


def _brief_protection_map(
    critical: Sequence[tuple[str, JsonObject]],
) -> list[str]:
    issues_by_lever: dict[str, list[str]] = {}
    for _, finding in critical:
        issue_id = _plain(finding.get("issue_id"))
        for raw_lever in _strings(finding.get("transaction_levers")):
            lever = _lever_label(raw_lever)
            issue_ids = issues_by_lever.setdefault(lever, [])
            if issue_id not in issue_ids:
                issue_ids.append(issue_id)
    return [
        f"{lever.capitalize()}: {', '.join(issue_ids)}."
        for lever, issue_ids in issues_by_lever.items()
    ]


def _limitation_topics(payloads: Mapping[str, JsonObject]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for workstream in WORKSTREAM_ORDER:
        for item in _objects(payloads.get(workstream, {}).get("coverage")):
            if item.get("status") == "limitation":
                result.append((WORKSTREAM_TITLES[workstream], _plain(item.get("topic"))))
    return result


def render_outstanding_information(
    *,
    run_id: str,
    payloads: Mapping[str, JsonObject],
    gaps: Sequence[JsonObject],
    questions: Sequence[JsonObject],
    answers: Mapping[str, JsonObject],
) -> str:
    findings = sorted_findings(payloads)
    answered_by = sorted(
        {
            _plain((answer.get("provenance") or {}).get("answered_by"))
            for answer in answers.values()
            if isinstance(answer.get("provenance"), dict)
        }
    )
    management_answered = any("not management" not in value.casefold() for value in answered_by)
    lines = [
        "# Outstanding information and transaction conditions",
        "",
        f"Run ID: `{run_id}`",
        "",
        "## Management response status",
        "",
    ]
    if management_answered:
        lines.append("At least one ingested answer is attributed to management or the deal lead.")
    else:
        lines.append(
            "No management response was used for this synthetic report. Both rounds were answered "
            "by a Phase 10 synthetic test operator so that the analytical pipeline could be "
            "exercised; those answers are assumptions or explicit non-availability statements, "
            "not management evidence."
        )
    lines.extend(["", "## Go/no-go and pre-completion conditions", ""])
    for number, condition in enumerate(_critical_conditions(findings), start=1):
        lines.append(f"{number}. {condition}")
    lines.extend(["", "## Open evidence gaps", ""])
    open_gaps = [gap for gap in gaps if gap.get("status") in {"open", "narrowed"}]
    if not open_gaps:
        lines.append("No open structured gap is recorded.")
    for gap in open_gaps:
        lines.extend(
            [
                f"### {gap.get('gap_id')} - {_plain(gap.get('importance')).upper()}",
                "",
                f"- Information required: {_plain(gap.get('expected_information'))}",
                f"- Why absent: {'; '.join(_strings(gap.get('evidence_that_it_is_missing')))}",
                f"- Decision affected: {', '.join(_strings(gap.get('affected_decision')))}",
                f"- Follow-up: {_plain(gap.get('requested_follow_up'))}",
                "",
            ]
        )
    lines.extend(["## What was asked of management", ""])
    lines.extend(
        [
            "| ID | Priority | Question | Response provenance/status | Supporting source IDs |",
            "|---|---|---|---|---|",
        ]
    )
    for question in questions:
        question_id = str(question.get("question_id"))
        answer = answers.get(question_id, {})
        provenance = answer.get("provenance")
        provenance_obj = provenance if isinstance(provenance, dict) else {}
        answer_status = (
            f"{_plain(provenance_obj.get('answered_by'))}; "
            f"engine status {_plain(answer.get('resolution_status'))}"
            if answer
            else "No answer ingested"
        )
        sources = ", ".join(f"`{item}`" for item in _strings(question.get("supporting_source_ids")))
        lines.append(
            f"| {question_id} | {_table(question.get('priority'))} | "
            f"{_table(question.get('exact_question'))} | {_table(answer_status)} | "
            f"{sources or 'None'} |"
        )
    lines.extend(["", "## Coverage limitations without a source-backed adverse conclusion", ""])
    for workstream, topic in _limitation_topics(payloads):
        lines.append(f"- {workstream}: `{topic}`. Absence of evidence is not a clean conclusion.")
    lines.append("")
    return "\n".join(lines)


def render_due_diligence_report(
    *,
    run_id: str,
    payloads: Mapping[str, JsonObject],
    records: Mapping[str, list[JsonObject]],
    questions: Sequence[JsonObject],
    answers: Mapping[str, JsonObject],
    register_summary: Mapping[str, object],
    extraction_summary: Mapping[str, object],
    citation_summary: Mapping[str, object],
    red_team_resolution: Mapping[str, object] | None = None,
) -> str:
    evidence_by_id = evidence_index(records.get("evidence", []))
    calculations_by_id = {
        str(item.get("calculation_id")): item for item in records.get("calculations", [])
    }
    findings = sorted_findings(payloads)
    material_findings = [
        item for item in findings if item[1].get("materiality") in {"critical", "high"}
    ]
    transaction = _answer_for_topic(questions, answers, "transaction-perimeter") or (
        "Transaction perimeter not supplied."
    )
    price = _answer_for_topic(questions, answers, "price-structure-assumptions") or (
        "No price/structure assumption supplied."
    )
    thesis = _answer_for_topic(questions, answers, "investment-thesis") or (
        "Investment thesis not supplied."
    )
    scope = _answer_for_topic(questions, answers, "scope-materiality") or (
        "Cut-off and materiality not supplied."
    )
    critical = [item for item in findings if item[1].get("materiality") == "critical"]
    high = [item for item in findings if item[1].get("materiality") == "high"]
    raw_coverage = citation_summary.get("material_claim_coverage")
    material_coverage = float(raw_coverage) if isinstance(raw_coverage, int | float) else 0.0
    lines = [
        "# Due diligence report",
        "",
        f"Run ID: `{run_id}`",
        "",
        "Audience: Investment Committee | Purpose: acquisition go/no-go and price/structure "
        "decision support",
        "",
        REPORT_SECTION_HEADINGS[0],
        "",
        "**Recommendation: continue only on a conditional and protected basis; do not sign or "
        "close unconditionally on the current evidence.** The business shows statutory growth, "
        "but the current transaction case is exposed to unsupported earnings, an incorrect "
        "working-capital schedule, incomplete debt evidence, customer concentration/consent risk, "
        "unreconciled tax positions and untested IT resilience. The appropriate IC posture is "
        "therefore a conditional go for further diligence and negotiation, with a no-go if the "
        "listed consent, debt, earnings, tax and resilience conditions are not satisfied.",
        "",
        "This report does not provide an independent valuation opinion. No committee price was "
        "provided; quantified matters are presented as adjustments, exposures or completion "
        "mechanics rather than as a valuation conclusion.",
        "",
        f"The validated record contains **{len(critical)} critical** and **{len(high)} high** "
        f"findings. Material claim citation coverage is "
        f"**{material_coverage:.1%}**.",
        "",
        "### Headline reconciliation",
        "",
        "| Decision item | Adviser conclusion |",
        "|---|---|",
    ]
    headline_findings = [
        finding
        for _, finding in findings
        if finding.get("materiality") == "critical" and _strings(finding.get("calculation_ids"))
    ]
    for finding in headline_findings:
        issue_id = str(finding.get("issue_id"))
        citations = " ".join(
            citations_for_ids(_strings(finding.get("supporting_evidence_ids")), evidence_by_id)
        )
        lines.append(f"| `{issue_id}` | {_table(finding.get('analysis_conclusion'))} {citations} |")
    lines.extend(
        [
            "",
            REPORT_SECTION_HEADINGS[1],
            "",
            "### Transaction context",
            "",
            f"- Perimeter/structure answer: {transaction}",
            f"- Price/consideration answer: {price}",
            f"- Investment thesis answer: {thesis}",
            f"- Cut-off/materiality answer: {scope}",
            "",
            "The above are test-operator answers or IC assumptions, not source-room facts and not "
            "management representations. The synthetic run received no management response.",
            "",
            "### Scope performed",
            "",
            f"The engine registered {register_summary.get('source_register_entries', 'unknown')} "
            f"logical sources and terminally processed "
            f"{extraction_summary.get('sources_terminal', 'unknown')} sources. Analysis covers the "
            "five formal workstreams plus the standalone Tax module. Public research was disabled.",
            "",
            "### Principal limitations",
            "",
            (
                f"- {extraction_summary.get('vision_queue_count')} visual-review tasks remain "
                "pending; no unreviewed visual content is treated as evidence."
                if extraction_summary.get("vision_queue_count")
                else "- No visual-review task remains pending; reviewed visual evidence is "
                "limited to its recorded transcription and citation."
            ),
            "- One corrupt legacy PDF could not be read safely.",
            "- No monthly management-account pack, complete lender schedule, official current CRO "
            "extract, complete IP/privacy evidence, or tested disaster-recovery evidence was "
            "supplied.",
            "- Legal and Tax analysis is commercial Irish due diligence, not a formal legal or "
            "tax opinion.",
            (
                "- Red-team challenges have been dispositioned and reconciled. The run still "
                "does not prove the brand-new-context/allowlisted-packet isolation gate unless "
                "the required isolation manifests are also present and validated."
                if red_team_resolution
                else "- No validated red-team resolution artifact is present."
            ),
            "",
            REPORT_SECTION_HEADINGS[2],
            "",
            "The committee should focus negotiation and diligence resources on the following "
            "critical/high conclusions; each is repeated in full in its workstream section.",
            "",
            "| Severity | Workstream | Issue | Conclusion | Decision implication | Citation |",
            "|---|---|---|---|---|---|",
        ]
    )
    for workstream, finding in material_findings:
        citations = " ".join(
            citations_for_ids(_strings(finding.get("supporting_evidence_ids")), evidence_by_id)
        )
        lines.append(
            f"| {_table(finding.get('materiality')).upper()} | {WORKSTREAM_TITLES[workstream]} | "
            f"`{finding.get('issue_id')}` | {_table(finding.get('analysis_conclusion'))} | "
            f"{_table(finding.get('transaction_implication'))} | {citations} |"
        )
    for section_number, workstream in enumerate(WORKSTREAM_ORDER, start=4):
        lines.extend(["", REPORT_SECTION_HEADINGS[section_number - 1], ""])
        payload = payloads.get(workstream, {})
        if workstream in {"legal_contractual", "tax"}:
            lines.extend(
                [
                    "This section is commercial diligence in an Irish transaction context, not a "
                    "formal Irish legal or tax opinion.",
                    "",
                ]
            )
        for finding in _objects(payload.get("findings")):
            lines.extend(_finding_block(finding, evidence_by_id, calculations_by_id))
        limitation_topics = [
            _plain(item.get("topic"))
            for item in _objects(payload.get("coverage"))
            if item.get("status") == "limitation"
        ]
        if limitation_topics:
            lines.extend(
                [
                    "### Matters not established in this workstream",
                    "",
                    "The following topics lacked enough source evidence for an adverse or clean "
                    f"conclusion: {', '.join(limitation_topics)}.",
                    "",
                ]
            )
    open_gaps = [
        gap for gap in records.get("gaps", []) if gap.get("status") in {"open", "narrowed"}
    ]
    lines.extend(
        [
            REPORT_SECTION_HEADINGS[9],
            "",
            f"There are {len(open_gaps)} open/narrowed structured gaps. In addition, all "
            f"{len(questions)} intake questions require management confirmation because the "
            "ingested answers came from a "
            "synthetic test operator, not management. See `outputs/outstanding_information.md` for "
            "the complete request list and provenance.",
            "",
            "### Conditions to proceed",
            "",
        ]
    )
    for number, condition in enumerate(_critical_conditions(findings), start=1):
        lines.append(f"{number}. {condition}")
    lines.extend(["", "### Open structured gaps", ""])
    for gap in open_gaps:
        lines.append(
            f"- `{gap.get('gap_id')}` ({_plain(gap.get('importance'))}): "
            f"{_plain(gap.get('expected_information'))} Next action: "
            f"{_plain(gap.get('requested_follow_up'))}"
        )
    lines.extend(
        [
            "",
            REPORT_SECTION_HEADINGS[10],
            "",
            "### Methodology",
            "",
            "The report was assembled from validated structured workstream findings, typed claims, "
            "native-locator evidence, deterministic calculations, contradictions, gaps and "
            "verbatim intake records. Source-room content was treated as untrusted data and was "
            "not executed. "
            "Reported values remain separate from recomputed values. Exact duplicates do not count "
            "as independent corroboration. Potentially superseded sources require acknowledgement.",
            "",
            "### Appendix A - Headline calculations",
            "",
            "| Calculation | Description | Reported | Recomputed | Variance | Input citations |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for calculation in records.get("calculations", []):
        result = calculation.get("result")
        result_obj = result if isinstance(result, dict) else {}
        citations = " ".join(calculation_citations(calculation))
        lines.append(
            f"| `{calculation.get('calculation_id')}` | {_table(calculation.get('description'))} | "
            f"{_currency(result_obj.get('reported_value'), calculation.get('currency'))} | "
            f"{_currency(result_obj.get('recomputed_value'), calculation.get('currency'))} | "
            f"{_currency(result_obj.get('variance'), calculation.get('currency'))} | {citations} |"
        )
    lines.extend(
        [
            "",
            "### Appendix B - Unresolved contradictions",
            "",
            "| ID | Values | Likely explanation | Status |",
            "|---|---|---|---|",
        ]
    )
    for contradiction in records.get("contradictions", []):
        values = contradiction.get("conflicting_values")
        explanations = contradiction.get("likely_explanations")
        lines.append(
            f"| `{contradiction.get('contradiction_id')}` | {_table(values)} | "
            f"{_table(' '.join(_strings(explanations)))} | {_table(contradiction.get('status'))} |"
        )
    lines.extend(
        [
            "",
            "### Appendix C - Citation and validation coverage",
            "",
            f"- Material claims: {citation_summary.get('material_claim_count')}",
            f"- Material claims supported: {citation_summary.get('material_claims_supported')}",
            f"- Citation checks: {citation_summary.get('citation_count')}",
            f"- Failed citation checks: {citation_summary.get('failed_citation_count')}",
            f"- Calculation records: {citation_summary.get('calculation_count')}",
            f"- Calculation failures: {citation_summary.get('calculation_failure_count')}",
            "",
            "### Appendix D - Management questions and red-team status",
            "",
            f"Two rounds asked {len(questions)} questions. Full wording, evidence links and "
            "response provenance are reproduced in `outputs/outstanding_information.md`.",
            "",
        ]
    )
    if red_team_resolution:
        summary = red_team_resolution.get("summary")
        summary_obj = summary if isinstance(summary, dict) else {}
        lines.extend(
            [
                (
                    f"The resolution ledger records {summary_obj.get('accepted', 0)} accepted, "
                    f"{summary_obj.get('rejected', 0)} rejected and "
                    f"{summary_obj.get('unresolved', 0)} unresolved challenges. The standalone "
                    "`red_team/red_team_resolution.md` contains full verification evidence, files "
                    "changed, regressions and regenerated artifacts."
                ),
                "",
                "| Challenge | Outcome | Root cause | Resolution |",
                "|---|---|---|---|",
            ]
        )
        for disposition in _objects(red_team_resolution.get("dispositions")):
            lines.append(
                f"| `{disposition.get('challenge_id')}` | "
                f"{_table(disposition.get('outcome')).upper()} | "
                f"{_table(', '.join(_strings(disposition.get('root_causes'))))} | "
                f"{_table(disposition.get('decision'))} |"
            )
        lines.append("")
    else:
        lines.extend(
            [
                "No challenge outcome is implied without a validated resolution ledger.",
                "",
            ]
        )
    return "\n".join(lines)


def build_ic_brief_content(
    *,
    run_id: str,
    payloads: Mapping[str, JsonObject],
    records: Mapping[str, list[JsonObject]],
    answers: Mapping[str, JsonObject],
    questions: Sequence[JsonObject] = (),
) -> JsonObject:
    evidence_by_id = evidence_index(records.get("evidence", []))
    findings = sorted_findings(payloads)
    critical = [item for item in findings if item[1].get("materiality") == "critical"]
    headline: list[JsonObject] = []
    headline_findings = [
        finding
        for _, finding in findings
        if finding.get("materiality") == "critical" and _strings(finding.get("calculation_ids"))
    ]
    for finding in headline_findings:
        issue_id = str(finding.get("issue_id"))
        headline.append(
            {
                "issue_id": issue_id,
                "text": _plain(finding.get("analysis_conclusion")),
                "citations": citations_for_ids(
                    _strings(finding.get("supporting_evidence_ids")), evidence_by_id
                ),
            }
        )
    material: list[JsonObject] = []
    for workstream, finding in critical:
        material.append(
            {
                "issue_id": finding.get("issue_id"),
                "text": _plain(finding.get("analysis_conclusion")),
                "workstream": WORKSTREAM_TITLES[workstream],
                "citations": citations_for_ids(
                    _strings(finding.get("supporting_evidence_ids")), evidence_by_id
                ),
            }
        )
    conditions = _brief_critical_conditions(critical)
    protections = _brief_protection_map(critical)
    unanswered = [
        f"{finding.get('issue_id')}: {_plain(finding.get('uncertainty') or finding.get('action'))}"
        for _, finding in critical
    ]
    high_findings = [item for item in findings if item[1].get("materiality") == "high"]
    actions: list[str] = []
    action_workstreams: set[str] = set()
    for workstream, finding in high_findings:
        if workstream in action_workstreams:
            continue
        actions.append(_plain(finding.get("action")))
        action_workstreams.add(workstream)
    for _, finding in high_findings:
        value = _plain(finding.get("action"))
        if value not in actions and len(actions) < 6:
            actions.append(value)
    return {
        "actions": actions,
        "conditions": conditions,
        "headline": headline,
        "material_findings": material,
        "price_protections": protections,
        "recommendation": (
            "Conditional go for diligence and negotiation; no-go for unconditional signing or "
            "closing until consent, earnings, debt, tax and IT-resilience conditions are satisfied."
        ),
        "run_id": run_id,
        "thesis": _answer_for_topic(questions, answers, "investment-thesis")
        or "Investment thesis not supplied.",
        "transaction": (
            _answer_for_topic(questions, answers, "transaction-perimeter")
            or "Transaction perimeter not supplied."
        ),
        "unanswered": unanswered,
    }


def render_ic_brief_markdown(content: JsonObject) -> str:
    lines = [
        "# Investment Committee brief",
        "",
        f"Run ID: `{content['run_id']}`",
        "",
        BRIEF_SECTION_HEADINGS[0],
        "",
        f"**Recommendation:** {_plain(content.get('recommendation'))}",
        "",
        f"**Transaction:** {_plain(content.get('transaction'))}",
        "",
        f"**Thesis:** {_plain(content.get('thesis'))}",
        "",
        "No independent valuation opinion is provided; no committee price was supplied.",
        "",
        BRIEF_SECTION_HEADINGS[1],
        "",
    ]
    for finding_item in _objects(content.get("material_findings")):
        citations = " ".join(_strings(finding_item.get("citations")))
        lines.append(
            f"- **{finding_item.get('issue_id')} / {finding_item.get('workstream')}:** "
            f"{_plain(finding_item.get('text'))} "
            f"{citations}"
        )
    lines.extend(["", BRIEF_SECTION_HEADINGS[2], "", "| Item | Reconciliation |", "|---|---|"])
    for headline_item in _objects(content.get("headline")):
        citations = " ".join(_strings(headline_item.get("citations")))
        lines.append(
            f"| `{headline_item.get('issue_id')}` | "
            f"{_table(headline_item.get('text'))} {citations} |"
        )
    lines.extend(["", BRIEF_SECTION_HEADINGS[3], ""])
    for condition in _strings(content.get("conditions")):
        lines.append(f"- {condition}")
    lines.extend(["", BRIEF_SECTION_HEADINGS[4], ""])
    for protection in _strings(content.get("price_protections")):
        lines.append(f"- {_initial_capital(protection)}")
    lines.extend(["", BRIEF_SECTION_HEADINGS[5], ""])
    for question in _strings(content.get("unanswered")):
        lines.append(f"- {question}")
    lines.extend(["", BRIEF_SECTION_HEADINGS[6], ""])
    for action in _strings(content.get("actions")):
        lines.append(f"- {action}")
    lines.append("")
    return "\n".join(lines)


def findings_summary(payloads: Mapping[str, JsonObject]) -> dict[str, Any]:
    """Return deterministic severity/workstream counts for validation and CLI reporting."""

    severity: dict[str, int] = {}
    workstream: dict[str, int] = {}
    for name, finding in findings_by_workstream(payloads):
        level = str(finding.get("materiality"))
        severity[level] = severity.get(level, 0) + 1
        workstream[name] = workstream.get(name, 0) + 1
    return {"by_severity": severity, "by_workstream": workstream}
