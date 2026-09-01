"""Human-readable workstream rendering from validated structured records."""

from __future__ import annotations

from collections.abc import Mapping

from dd_engine.evidence.models import JsonObject


def _locator(value: object) -> str:
    if not isinstance(value, dict):
        return "invalid locator"
    locator_type = value.get("type")
    if locator_type == "pdf_page":
        return f"page {value.get('page_number')}"
    if locator_type == "spreadsheet_cell":
        return f"{value.get('sheet')}!{value.get('range') or value.get('cell')}"
    if locator_type == "docx_paragraph":
        return f"paragraph {value.get('paragraph_index')}"
    if locator_type == "docx_table_cell":
        return (
            f"table {value.get('table_index')}, row {value.get('row_index')}, "
            f"cell {value.get('cell_index')}"
        )
    if locator_type == "csv_cell":
        return f"row {value.get('row_index')}, column {value.get('column_index')}"
    if locator_type == "image":
        return f"image {value.get('image_number')}, region {value.get('region')}"
    return str(value)


def _citation_lines(identifiers: list[str], evidence_by_id: Mapping[str, JsonObject]) -> list[str]:
    if not identifiers:
        return ["- None identified."]
    lines: list[str] = []
    for evidence_id in identifiers:
        evidence = evidence_by_id.get(evidence_id, {})
        lines.append(
            f"- `{evidence_id}` — `{evidence.get('source_id')}` / "
            f"{_locator(evidence.get('exact_locator'))}"
        )
    return lines


def render_workstream(
    payload: JsonObject,
    evidence_records: list[JsonObject],
    *,
    title: str,
) -> str:
    """Render findings while keeping source fact visibly separate from analysis."""

    evidence_by_id = {str(item.get("evidence_id")): item for item in evidence_records}
    lines = [
        f"# {title}",
        "",
        f"Run ID: `{payload['run_id']}`",
        "",
        "This is decision-oriented commercial due diligence, not a document summary. "
        "Source facts are separated from analytical conclusions. No independent valuation is "
        "provided.",
        "",
    ]
    if payload.get("irish_jurisdiction_scope"):
        lines.extend(["## Scope", "", str(payload["irish_jurisdiction_scope"]), ""])
    findings = payload.get("findings", [])
    lines.extend(["## Material findings", ""])
    if not findings:
        lines.extend(
            [
                "No source-backed material finding was generated. This is a scope limitation, not "
                "a clean conclusion.",
                "",
            ]
        )
    for finding in findings:
        lines.extend(
            [
                f"### {finding['issue_id']} — {str(finding['materiality']).upper()}",
                "",
                f"**Conclusion:** {finding['analysis_conclusion']}",
                "",
                f"**Source fact:** {finding['source_fact']}",
                "",
                f"**Analysis:** {finding['analytical_reasoning']}",
                "",
                f"**Why it matters:** {finding['why_it_matters']}",
                "",
                f"**Transaction implication:** {finding['transaction_implication']}",
                "",
                f"**Confidence:** {float(finding['confidence']):.0%}",
                "",
            ]
        )
        if finding.get("uncertainty"):
            lines.extend([f"**Uncertainty/limitation:** {finding['uncertainty']}", ""])
        if finding.get("calculation_ids"):
            values = ", ".join(f"`{item}`" for item in finding["calculation_ids"])
            lines.extend([f"**Recomputations:** {values}", ""])
        lines.extend(["**Supporting citations:**", ""])
        lines.extend(
            _citation_lines(list(finding.get("supporting_evidence_ids", [])), evidence_by_id)
        )
        lines.extend(["", "**Contradictory or limiting citations:**", ""])
        lines.extend(_citation_lines(list(finding.get("counterevidence_ids", [])), evidence_by_id))
        lines.extend(["", f"**Exact next action:** {finding['action']}", ""])

    lines.extend(["## Coverage and explicit limitations", ""])
    lines.extend(["| Topic | Status | Linked issues |", "|---|---|---|"])
    for item in payload.get("coverage", []):
        issues = ", ".join(item.get("issue_ids", [])) or "None"
        lines.append(f"| {item.get('topic')} | {item.get('status')} | {issues} |")
    lines.extend(["", "## General limitations", ""])
    for limitation in payload.get("limitations", []):
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def render_financial_calculations(run_id: str, calculations: list[JsonObject]) -> str:
    lines = [
        "# Financial calculations",
        "",
        f"Run ID: `{run_id}`",
        "",
        "Reported and recomputed values remain separate. Every input resolves to a validated "
        "source locator.",
        "",
        "| Calculation | Description | Reported | Recomputed | Variance | Status |",
        "|---|---|---:|---:|---:|---|",
    ]
    for calculation in calculations:
        if not str(calculation.get("calculation_id", "")).startswith(("CALC-FIN", "CALC-COMM")):
            continue
        result = calculation.get("result", {})
        lines.append(
            f"| `{calculation['calculation_id']}` | {calculation['description']} | "
            f"{result.get('reported_value')} | {result.get('recomputed_value')} | "
            f"{result.get('variance')} | {calculation.get('independent_recomputation_status')} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_customer_grouping(payload: JsonObject) -> str:
    lines = [
        "# Customer grouping decisions",
        "",
        f"Run ID: `{payload['run_id']}`",
        "",
        str(payload["rule"]),
        "",
        "| Candidate group | Group name | Decision | Members | Evidence basis |",
        "|---|---|---|---|---|",
    ]
    for decision in payload.get("decisions", []):
        members = ", ".join(decision.get("members", []))
        lines.append(
            f"| {decision.get('candidate_group_id')} | {decision.get('group_name')} | "
            f"{decision.get('decision')} | {members} | {decision.get('evidence_basis')} |"
        )
    lines.append("")
    return "\n".join(lines)
