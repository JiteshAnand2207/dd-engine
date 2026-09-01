"""Fail-closed validation for Phase 10 report and IC-brief artifacts."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from dd_engine.evidence.citations import validate_citations
from dd_engine.evidence.models import JsonObject
from dd_engine.reporting.pdf import A4_SIZE, BOTTOM, FOOTER_FONT_SIZE, PageLayout
from dd_engine.reporting.rendering import (
    BRIEF_SECTION_HEADINGS,
    REPORT_SECTION_HEADINGS,
    calculation_citations,
    citations_for_ids,
    evidence_index,
    findings_summary,
    human_citation,
    sorted_findings,
)
from dd_engine.time import utc_now

_PLACEHOLDERS = re.compile(
    r"(?:\bTODO\b|\bTBD\b|\bPLACEHOLDER\b|lorem ipsum|stage not implemented|"
    r"\[insert[^\]]*\]|<placeholder>)",
    re.I,
)
_SOURCE_CITATION = re.compile(r"\[(SRC-\d{4}), ([^\]]+)\]")
_FONT_SIZE = re.compile(rb"/[A-Za-z0-9]+\s+([0-9]+(?:\.[0-9]+)?)\s+Tf")
_FINDING_LABELS = (
    "**Conclusion:**",
    "**Evidence:**",
    "**Counterevidence/limitation:**",
    "**Recomputed value where relevant:**",
    "**Why it matters:**",
    "**Transaction implication:**",
    "**Recommended action/protection:**",
    "**Confidence:**",
    "**Citation:**",
)


def _problem(code: str, message: str, *, record_id: str | None = None) -> JsonObject:
    value: JsonObject = {"code": code, "message": message}
    if record_id is not None:
        value["record_id"] = record_id
    return value


def _ordered_headings(text: str, headings: Sequence[str]) -> tuple[bool, list[str]]:
    missing: list[str] = []
    positions: list[int] = []
    for heading in headings:
        position = text.find(heading)
        if position < 0:
            missing.append(heading)
        positions.append(position)
    ordered = not missing and positions == sorted(positions)
    return ordered, missing


def _pdf_checks(path: Path, run_id: str, layouts: Sequence[PageLayout] | None) -> JsonObject:
    errors: list[str] = []
    page_results: list[JsonObject] = []
    minimum_font = 999.0
    source_token_count = 0
    out_of_bounds_anchors = 0
    try:
        reader = PdfReader(path)
    except (OSError, ValueError) as exc:
        return {
            "a4_pages": False,
            "errors": [f"cannot parse IC brief PDF: {exc}"],
            "page_count": 0,
            "passed": False,
        }
    metadata: Mapping[str, Any] = reader.metadata or {}
    metadata_text = " ".join(str(value) for value in metadata.values())
    if run_id not in metadata_text:
        errors.append("PDF metadata does not contain the run ID")
    expected_width, expected_height = A4_SIZE
    for number, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        a4 = abs(width - expected_width) <= 1 and abs(height - expected_height) <= 1
        if not a4:
            errors.append(f"page {number} is not ISO A4")
        text = page.extract_text() or ""
        source_token_count += text.count("SRC-")
        if len(text.strip()) < 100:
            errors.append(f"page {number} contains too little extractable text")
        contents = page.get_contents()
        if contents is not None:
            for match in _FONT_SIZE.finditer(contents.get_data()):
                minimum_font = min(minimum_font, float(match.group(1)))

        def visitor(
            visitor_text: str,
            cm: list[float],
            tm: list[float],
            font_dict: dict[str, Any] | None,
            font_size: float,
            *,
            width_bound: float = width,
            height_bound: float = height,
        ) -> None:
            del cm, font_dict, font_size
            nonlocal out_of_bounds_anchors
            if not visitor_text.strip():
                return
            if len(tm) >= 6 and not (
                -1 <= tm[4] <= width_bound + 1 and -1 <= tm[5] <= height_bound + 1
            ):
                out_of_bounds_anchors += 1

        page.extract_text(visitor_text=visitor)
        page_results.append(
            {
                "a4": a4,
                "height_points": round(height, 3),
                "page_number": number,
                "text_character_count": len(text),
                "width_points": round(width, 3),
            }
        )
    if len(reader.pages) != 2:
        errors.append(f"IC brief PDF has {len(reader.pages)} pages; exactly 2 required")
    if minimum_font == 999.0:
        errors.append("no PDF font-size operators were found")
        minimum_font = 0.0
    elif minimum_font + 0.01 < FOOTER_FONT_SIZE:
        errors.append(
            f"minimum PDF font size is {minimum_font:.2f}pt; {FOOTER_FONT_SIZE:.2f}pt required"
        )
    if source_token_count == 0:
        errors.append("IC brief PDF contains no human-readable source citations")
    if out_of_bounds_anchors:
        errors.append(f"PDF contains {out_of_bounds_anchors} text anchor(s) outside the media box")
    layout_values = []
    if layouts is not None:
        layout_values = [
            {
                "bottom_y": round(layout.bottom_y, 2),
                "frame_overflow": layout.bottom_y < BOTTOM,
                "line_count": layout.line_count,
                "page_number": layout.page_number,
            }
            for layout in layouts
        ]
        if any(bool(item["frame_overflow"]) for item in layout_values):
            errors.append("deterministic renderer reported a page-frame overflow")
    return {
        "a4_pages": all(bool(item["a4"]) for item in page_results),
        "errors": errors,
        "layout": layout_values,
        "minimum_font_size_points": round(minimum_font, 2),
        "out_of_bounds_text_anchors": out_of_bounds_anchors,
        "page_count": len(reader.pages),
        "pages": page_results,
        "passed": not errors,
        "source_citation_token_count": source_token_count,
    }


def _all_allowed_citations(records: Mapping[str, list[JsonObject]]) -> set[str]:
    result = {
        human_citation(item.get("source_id"), item.get("exact_locator"))
        for item in records.get("evidence", [])
    }
    for calculation in records.get("calculations", []):
        result.update(calculation_citations(calculation))
    return result


def validate_report_bundle(
    *,
    run_path: Path,
    run_id: str,
    payloads: Mapping[str, JsonObject],
    records: Mapping[str, list[JsonObject]],
    report_text: str,
    brief_text: str,
    outstanding_text: str,
    input_fingerprint: str,
    layouts: Sequence[PageLayout] | None = None,
    generated_at: str | None = None,
) -> JsonObject:
    """Validate every Phase 10 fail-closed condition and return a full ledger."""

    errors: list[JsonObject] = []
    report_ordered, report_missing = _ordered_headings(report_text, REPORT_SECTION_HEADINGS)
    brief_ordered, brief_missing = _ordered_headings(brief_text, BRIEF_SECTION_HEADINGS)
    if not report_ordered:
        errors.append(
            _problem("required_report_sections", "report sections are missing or out of order")
        )
    if not brief_ordered:
        errors.append(
            _problem(
                "required_brief_sections", "IC brief sections are missing or out of order"
            )
        )

    citation_report = validate_citations(run_path, records)
    if citation_report.get("status") != "passed":
        errors.append(
            _problem("citation_validation_failed", "structured citation validation failed")
        )
    valid_evidence_ids = {
        str(item.get("citation_id"))
        for item in citation_report.get("citation_results", [])
        if isinstance(item, dict)
        and item.get("citation_kind") == "evidence"
        and item.get("valid") is True
    }
    evidence_by_id = evidence_index(records.get("evidence", []))
    material_findings = [
        (workstream, finding)
        for workstream, finding in sorted_findings(payloads)
        if finding.get("materiality") in {"critical", "high"}
    ]
    supported_material = 0
    material_failures: list[JsonObject] = []
    material_format_failures: list[JsonObject] = []
    for _, finding in material_findings:
        issue_id = str(finding.get("issue_id"))
        supporting = finding.get("supporting_evidence_ids")
        identifiers = [str(item) for item in supporting] if isinstance(supporting, list) else []
        citations = citations_for_ids(identifiers, evidence_by_id)
        finding_valid = bool(identifiers) and all(
            item in valid_evidence_ids for item in identifiers
        )
        finding_present = f"### {issue_id} -" in report_text
        citations_present = bool(citations) and all(item in report_text for item in citations)
        if finding_valid and finding_present and citations_present:
            supported_material += 1
        else:
            material_failures.append(
                {
                    "citations_present": citations_present,
                    "finding_present": finding_present,
                    "issue_id": issue_id,
                    "valid_structured_support": finding_valid,
                }
            )
            errors.append(
                _problem(
                    "material_claim_without_valid_citation",
                    f"{issue_id} lacks complete valid report citation support",
                    record_id=issue_id,
                )
            )
        marker = f"### {issue_id} -"
        block_start = report_text.find(marker)
        block_end = report_text.find("\n### ", block_start + len(marker))
        section_end = report_text.find("\n## ", block_start + len(marker))
        candidate_ends = [value for value in (block_end, section_end) if value >= 0]
        block = report_text[block_start : min(candidate_ends) if candidate_ends else None]
        missing_labels = [label for label in _FINDING_LABELS if label not in block]
        if block_start < 0 or missing_labels:
            material_format_failures.append(
                {"issue_id": issue_id, "missing_labels": missing_labels}
            )
            errors.append(
                _problem(
                    "material_finding_format",
                    f"{issue_id} does not contain the complete material-finding format",
                    record_id=issue_id,
                )
            )

    allowed_citations = _all_allowed_citations(records)
    dangling_display = [
        match.group(0)
        for match in _SOURCE_CITATION.finditer(report_text + "\n" + brief_text)
        if match.group(0) not in allowed_citations
    ]
    if dangling_display:
        errors.append(
            _problem(
                "unvalidated_human_citation",
                "one or more displayed citations are not backed by a validated structured locator",
            )
        )

    calculation_results = [
        item for item in citation_report.get("calculation_results", []) if isinstance(item, dict)
    ]
    calculation_failures: list[str] = []
    for item in calculation_results:
        calculation_id = str(item.get("calculation_id"))
        if item.get("valid") is not True or calculation_id not in report_text:
            calculation_failures.append(calculation_id)
    if calculation_failures:
        errors.append(
            _problem(
                "untraced_headline_calculation",
                "one or more headline calculations are invalid or absent from the report",
            )
        )

    placeholder_hits: dict[str, list[str]] = {}
    for name, text in {
        "due_diligence_report.md": report_text,
        "ic_brief.md": brief_text,
        "outstanding_information.md": outstanding_text,
    }.items():
        hits = sorted(set(match.group(0) for match in _PLACEHOLDERS.finditer(text)))
        if hits:
            placeholder_hits[name] = hits
    if placeholder_hits:
        errors.append(_problem("placeholder_text", "placeholder text remains in Phase 10 output"))

    pdf = _pdf_checks(run_path / "outputs" / "ic_brief.pdf", run_id, layouts)
    if pdf.get("passed") is not True:
        errors.append(_problem("ic_brief_pdf", "IC brief PDF failed page/layout validation"))
    brief_citation_failures: list[str] = []
    for _, finding in material_findings:
        if finding.get("materiality") != "critical":
            continue
        raw_supporting = finding.get("supporting_evidence_ids")
        supporting = (
            [str(value) for value in raw_supporting] if isinstance(raw_supporting, list) else []
        )
        citations = citations_for_ids(supporting, evidence_by_id)
        if not any(citation in brief_text for citation in citations):
            brief_citation_failures.append(str(finding.get("issue_id")))
    if brief_citation_failures:
        errors.append(
            _problem(
                "ic_brief_missing_citations",
                "one or more critical IC-brief findings lacks a displayed source citation",
            )
        )

    word_count = len(re.findall(r"\b[\w][\w'-]*\b", report_text))
    citation_summary = citation_report.get("summary")
    citation_summary_obj = citation_summary if isinstance(citation_summary, dict) else {}
    summary = {
        "brief_page_count": pdf.get("page_count"),
        "calculation_count": len(calculation_results),
        "calculation_failure_count": len(calculation_failures),
        "displayed_source_citation_count": len(_SOURCE_CITATION.findall(report_text)),
        "finding_counts": findings_summary(payloads),
        "material_finding_count": len(material_findings),
        "material_finding_citation_coverage": (
            supported_material / len(material_findings) if material_findings else None
        ),
        "report_word_count": word_count,
        "structured_citation_count": citation_summary_obj.get("citation_count"),
        "structured_failed_citation_count": citation_summary_obj.get("failed_citation_count"),
    }
    return {
        "checks": {
            "headline_calculations": {
                "failed_ids": calculation_failures,
                "passed": not calculation_failures,
                "traced_count": len(calculation_results) - len(calculation_failures),
            },
            "human_citations": {
                "dangling": sorted(set(dangling_display)),
                "passed": not dangling_display,
            },
            "ic_brief_citations": {
                "failed_issue_ids": brief_citation_failures,
                "passed": not brief_citation_failures,
            },
            "material_claim_citations": {
                "failures": material_failures,
                "passed": not material_failures,
                "supported": supported_material,
                "total": len(material_findings),
            },
            "material_finding_format": {
                "failures": material_format_failures,
                "passed": not material_format_failures,
                "total": len(material_findings),
            },
            "pdf": pdf,
            "placeholders": {"hits": placeholder_hits, "passed": not placeholder_hits},
            "required_sections": {
                "brief_missing": brief_missing,
                "brief_ordered": brief_ordered,
                "passed": report_ordered and brief_ordered,
                "report_missing": report_missing,
                "report_ordered": report_ordered,
            },
            "structured_citations": citation_report,
        },
        "errors": errors,
        "generated_at": generated_at or utc_now(),
        "input_fingerprint": input_fingerprint,
        "run_id": run_id,
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "summary": summary,
    }
