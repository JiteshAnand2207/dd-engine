from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from dd_engine.analysis import analyse_run
from dd_engine.config import EngineConfig, load_config
from dd_engine.errors import AnalysisError, ReportError
from dd_engine.extraction import extract_run
from dd_engine.intake import generate_intake_questions, ingest_intake_answers
from dd_engine.inventory import RegisterLimits, register_room
from dd_engine.reporting import generate_report, validate_report_outputs
from dd_engine.runs import create_run, load_manifest

LIMITS = RegisterLimits(
    max_archive_members=500,
    max_archive_total_uncompressed_bytes=128 * 1024 * 1024,
    max_archive_member_uncompressed_bytes=32 * 1024 * 1024,
)


def _config_without_ocr(root: Path) -> EngineConfig:
    config = load_config(cwd=root)
    return replace(config, extraction=replace(config.extraction, optional_ocr=False))


def _question_ids(run_path: Path, round_number: int) -> list[str]:
    payload = json.loads(
        (run_path / "intake" / f"round_{round_number}_questions.json").read_text(encoding="utf-8")
    )
    return [str(item["question_id"]) for item in payload["questions"]]


def _answer_round(run_path: Path, tmp_path: Path, round_number: int) -> None:
    answer_path = tmp_path / f"round-{round_number}-answers.json"
    answer_path.write_text(
        json.dumps(
            {
                "answered_by": "Phase analysis test deal lead",
                "answers": [
                    {
                        "answer": (
                            "For this deterministic test, the deal lead confirms the source-room "
                            "record is the complete answer and requests that every documented "
                            "limitation remain open."
                        ),
                        "question_id": question_id,
                    }
                    for question_id in _question_ids(run_path, round_number)
                ],
            }
        ),
        encoding="utf-8",
    )
    ingest_intake_answers(run_path, round_number, answer_path)


@pytest.fixture(scope="module")
def analysed_run(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("analysis-ready")
    room = Path(__file__).resolve().parents[1] / "synthetic" / "data_room"
    config = _config_without_ocr(root)
    run_path = create_run(config, runs_root=root / "runs")
    register_room(run_path, room, LIMITS)
    extract_run(run_path, room, config)

    generate_intake_questions(run_path, 1)
    with pytest.raises(AnalysisError, match="completed two-round intake"):
        analyse_run(run_path, 8)
    assert not (run_path / "workstreams" / "financial.json").exists()

    _answer_round(run_path, root, 1)
    generate_intake_questions(run_path, 2)
    _answer_round(run_path, root, 2)

    phase8 = analyse_run(run_path, 8)
    assert phase8.validation_passed
    assert phase8.stage_state == "running"
    phase9 = analyse_run(run_path, 9)
    assert phase9.validation_passed
    assert phase9.stage_state == "completed"
    return run_path


def _payload(run_path: Path, relative_path: str) -> dict[str, object]:
    return json.loads((run_path / relative_path).read_text(encoding="utf-8"))


def _finding(payload: dict[str, object], issue_id: str) -> dict[str, object]:
    findings = payload["findings"]
    assert isinstance(findings, list)
    return next(item for item in findings if item["issue_id"] == issue_id)


def test_phase8_outputs_and_recomputations(analysed_run: Path) -> None:
    for relative_path in (
        "workstreams/financial.json",
        "workstreams/financial.md",
        "workstreams/commercial.json",
        "workstreams/commercial.md",
        "workstreams/financial_calculations.md",
        "workstreams/customer_grouping.md",
    ):
        assert (analysed_run / relative_path).is_file()

    financial = _payload(analysed_run, "workstreams/financial.json")
    commercial = _payload(analysed_run, "workstreams/commercial.json")
    assert "EUR 180,000" in str(_finding(financial, "FIN-002")["analysis_conclusion"])
    assert "EUR 1,665,000" in str(_finding(financial, "FIN-003")["analysis_conclusion"])
    assert "EUR 176,500" in str(_finding(financial, "FIN-004")["analysis_conclusion"])
    assert "EUR 2,220,000" in str(_finding(financial, "FIN-005")["analysis_conclusion"])
    assert "EUR 37,500" in str(_finding(financial, "FIN-007")["analysis_conclusion"])
    assert "30.7%" in str(_finding(commercial, "COMM-001")["analysis_conclusion"])

    grouping = _payload(analysed_run, "workstreams/customer_grouping.json")
    decisions = grouping["decisions"]
    assert isinstance(decisions, list)
    mosaic = next(item for item in decisions if item["group_name"] == "Mosaic Arc Group")
    assert mosaic["decision"] == "confirmed"
    assert sorted(mosaic["members"]) == [
        "Mosaic North Retail Limited",
        "Mosaic South Trading Limited",
    ]
    assert all(
        item["decision"] == "no_grouping_required"
        for item in decisions
        if item["group_name"] != "Mosaic Arc Group"
    )


def test_phase9_outputs_versions_tax_and_privacy(analysed_run: Path) -> None:
    for relative_path in (
        "workstreams/legal_contractual.json",
        "workstreams/legal_contractual.md",
        "workstreams/operational_management.json",
        "workstreams/operational_management.md",
        "workstreams/it.json",
        "workstreams/it.md",
        "tax/tax-findings.json",
        "tax/tax-analysis.md",
        "citations/index.jsonl",
    ):
        assert (analysed_run / relative_path).is_file()

    legal = _payload(analysed_run, "workstreams/legal_contractual.json")
    tax = _payload(analysed_run, "tax/tax-findings.json")
    it = _payload(analysed_run, "workstreams/it.json")
    assert "prior written customer consent" in str(
        _finding(legal, "LEGAL-001")["analysis_conclusion"]
    )
    assert "twelve months" in str(_finding(legal, "LEGAL-002")["analysis_conclusion"])
    assert "EUR 8,000" in str(_finding(tax, "TAX-001")["analysis_conclusion"])
    assert "EUR 401,700" in str(_finding(tax, "TAX-002")["analysis_conclusion"])
    assert "EUR 1,584,000" in str(_finding(tax, "TAX-003")["analysis_conclusion"])
    assert "three priority-one" in str(_finding(it, "IT-002")["analysis_conclusion"])

    versions = legal["effective_version_decisions"]
    assert isinstance(versions, list)
    assert all(item["source_ids"] for item in versions)

    validation = _payload(analysed_run, "workstreams/phase_9_validation.json")
    assert validation["status"] == "passed"
    assert validation["pii_handling_checks"] == {"hits": {}, "passed": True}
    assert validation["citation_validation"]["status"] == "passed"
    assert validation["tax_recomputation_checks"]["passed"] is True
    assert validation["amendment_version_checks"]["passed"] is True

    research_log = (analysed_run / "logs" / "public-research-log.jsonl").read_text(encoding="utf-8")
    assert '"action":"not_performed"' in research_log
    _, manifest = load_manifest(analysed_run)
    assert manifest["stages"]["report"]["state"] == "not_started"
    assert manifest["stages"]["validate"]["state"] == "not_started"


def _copy_run(source: Path, destination_root: Path) -> Path:
    destination = destination_root / source.name
    shutil.copytree(source, destination)
    return destination


def test_phase10_generates_complete_validated_bundle(analysed_run: Path) -> None:
    report = generate_report(analysed_run)
    validation = validate_report_outputs(analysed_run)

    assert report.validation_passed
    assert validation.validation_passed
    for relative_path in (
        "outputs/due_diligence_report.md",
        "outputs/ic_brief.md",
        "outputs/ic_brief.pdf",
        "outputs/outstanding_information.md",
        "outputs/report_validation.json",
    ):
        assert (analysed_run / relative_path).is_file()

    result = _payload(analysed_run, "outputs/report_validation.json")
    assert result["status"] == "passed"
    summary = result["summary"]
    assert summary["brief_page_count"] == 2
    assert summary["material_finding_citation_coverage"] == 1.0
    assert summary["calculation_failure_count"] == 0
    assert result["checks"]["material_finding_format"]["passed"] is True
    assert result["checks"]["pdf"]["minimum_font_size_points"] >= 7.5
    reader = PdfReader(analysed_run / "outputs" / "ic_brief.pdf")
    assert len(reader.pages) == 2
    assert all(
        abs(float(page.mediabox.width) - 595.2756) < 1
        and abs(float(page.mediabox.height) - 841.8898) < 1
        for page in reader.pages
    )
    _, manifest = load_manifest(analysed_run)
    assert manifest["stages"]["report"]["state"] == "completed"
    assert manifest["stages"]["validate"]["state"] == "completed"
    assert generate_report(analysed_run).reused is True
    assert validate_report_outputs(analysed_run).reused is True


def test_phase10_fails_closed_when_material_support_is_removed(
    analysed_run: Path, tmp_path: Path
) -> None:
    copied = _copy_run(analysed_run, tmp_path)
    financial_path = copied / "workstreams" / "financial.json"
    financial = json.loads(financial_path.read_text(encoding="utf-8"))
    finding = next(item for item in financial["findings"] if item["issue_id"] == "FIN-002")
    finding["supporting_evidence_ids"] = []
    financial_path.write_text(json.dumps(financial), encoding="utf-8")

    with pytest.raises(ReportError, match="report validation failed"):
        generate_report(copied)
    _, manifest = load_manifest(copied)
    assert manifest["stages"]["report"]["state"] == "failed"


@pytest.mark.parametrize(
    ("relative_path", "old", "new", "error_code"),
    (
        (
            "outputs/due_diligence_report.md",
            "## 9. Tax",
            "## Tax section removed",
            "required_report_sections",
        ),
        (
            "outputs/outstanding_information.md",
            "# Outstanding information",
            "# Outstanding information\n\nTODO",
            "placeholder_text",
        ),
        (
            "outputs/due_diligence_report.md",
            "CALC-FIN-001",
            "REMOVED-CALCULATION-001",
            "untraced_headline_calculation",
        ),
    ),
)
def test_phase10_final_validation_rejects_tampered_text_outputs(
    analysed_run: Path,
    tmp_path: Path,
    relative_path: str,
    old: str,
    new: str,
    error_code: str,
) -> None:
    copied = _copy_run(analysed_run, tmp_path)
    path = copied / relative_path
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8")

    with pytest.raises(ReportError, match="final validation failed"):
        validate_report_outputs(copied)
    result = _payload(copied, "outputs/report_validation.json")
    assert result["status"] == "failed"
    assert error_code in {item["code"] for item in result["errors"]}


def test_phase10_final_validation_rejects_three_page_brief(
    analysed_run: Path, tmp_path: Path
) -> None:
    copied = _copy_run(analysed_run, tmp_path)
    pdf_path = copied / "outputs" / "ic_brief.pdf"
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_blank_page(
        width=reader.pages[0].mediabox.width,
        height=reader.pages[0].mediabox.height,
    )
    with pdf_path.open("wb") as handle:
        writer.write(handle)

    with pytest.raises(ReportError, match="final validation failed"):
        validate_report_outputs(copied)
    result = _payload(copied, "outputs/report_validation.json")
    assert result["status"] == "failed"
    assert result["checks"]["pdf"]["page_count"] == 3
    assert result["checks"]["pdf"]["passed"] is False
