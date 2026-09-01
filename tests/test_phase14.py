from __future__ import annotations

import json
import re
import subprocess
import sys
import tracemalloc
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from openpyxl import Workbook
from pypdf import PdfWriter

from dd_engine.analysis import analyse_run
from dd_engine.config import EngineConfig, load_config
from dd_engine.errors import RunError
from dd_engine.extraction import extract_run, ingest_vision_review
from dd_engine.intake import generate_intake_questions, ingest_intake_answers
from dd_engine.inventory import RegisterLimits, register_room
from dd_engine.reporting import generate_report, validate_report_outputs
from dd_engine.runs import create_run, load_manifest

ROOT = Path(__file__).resolve().parents[1]
SHADOW_ROOM = ROOT / "synthetic" / "shadow" / "data_room"
SHADOW_MANIFEST = ROOT / "synthetic" / "shadow" / "room_manifest.json"
LIMITS = RegisterLimits(
    max_archive_members=1000,
    max_archive_total_uncompressed_bytes=256 * 1024 * 1024,
    max_archive_member_uncompressed_bytes=64 * 1024 * 1024,
)


def _config_without_ocr(cwd: Path) -> EngineConfig:
    config = load_config(cwd=cwd)
    return replace(config, extraction=replace(config.extraction, optional_ocr=False))


def _answer_round(run_path: Path, target: Path, round_number: int) -> None:
    questions = json.loads(
        (run_path / "intake" / f"round_{round_number}_questions.json").read_text(
            encoding="utf-8"
        )
    )["questions"]
    topic_answers = {
        "transaction-perimeter": (
            "Phase 14 perimeter: acquire all shares in the fictional shadow target."
        ),
        "price-structure-assumptions": (
            "Phase 14 price: no committee price is supplied; use completion mechanics."
        ),
        "investment-thesis": (
            "Phase 14 thesis: test recurring revenue, retention and bounded liabilities."
        ),
        "scope-materiality": (
            "Phase 14 scope: cut-off 1 September 2026; prioritize critical and high matters."
        ),
    }
    target.write_text(
        json.dumps(
            {
                "answered_by": "Phase 14 saved-answer rehearsal",
                "answers": [
                    {
                        "answer": (
                            topic_answers.get(str(item.get("topic_key")))
                            or "The source-room record is the complete test-only response; keep "
                            "every documented limitation open for the investment committee."
                        ),
                        "question_id": item["question_id"],
                    }
                    for item in questions
                ],
            }
        ),
        encoding="utf-8",
    )
    ingest_intake_answers(run_path, round_number, target)


@pytest.fixture(scope="module")
def shadow_run(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("phase14-shadow")
    config = _config_without_ocr(ROOT)
    run_path = create_run(config, runs_root=root / "runs")
    register_room(run_path, SHADOW_ROOM, LIMITS)
    extract_run(run_path, SHADOW_ROOM, config)
    vision_queue = json.loads(
        (run_path / "extracts" / "needs_vision.json").read_text(encoding="utf-8")
    )
    if vision_queue["tasks"]:
        vision_input = root / "vision-review.json"
        vision_input.write_text(
            json.dumps(
                {
                    "reviewer": "Phase 14 saved-answer rehearsal",
                    "run_id": run_path.name,
                    "results": [
                        {
                            "confidence": 0.99,
                            "task_id": item["task_id"],
                            "transcription": (
                                "Fictional image-only facility letter; synthetic balance "
                                "EUR 710,000."
                            ),
                        }
                        for item in vision_queue["tasks"]
                    ],
                }
            ),
            encoding="utf-8",
        )
        ingest_vision_review(run_path, vision_input)
    generate_intake_questions(run_path, 1)
    _answer_round(run_path, root / "round-1.json", 1)
    generate_intake_questions(run_path, 2)
    _answer_round(run_path, root / "round-2.json", 2)
    assert analyse_run(run_path, 8).validation_passed
    assert analyse_run(run_path, 9).validation_passed
    assert generate_report(run_path).validation_passed
    assert validate_report_outputs(run_path).validation_passed
    return run_path


def test_shadow_room_is_independent_and_complete() -> None:
    manifest = json.loads(SHADOW_MANIFEST.read_text(encoding="utf-8"))
    paths = [item["path"] for item in manifest["files"]]
    assert manifest["company"] == "Orchard Lantern Systems Limited"
    assert manifest["physical_file_count"] == 48
    assert manifest["logical_source_count"] == 52
    assert len(manifest["zip_members"]) == 4
    assert all(
        token.casefold() not in " ".join(paths).casefold()
        for token in ("Larkspur", "Harbourlight", "Mosaic", "Juniper", "Statutory_Accounts")
    )
    assert manifest["quirks"]["missing_expected_document"] == "monthly bank statements"


def test_shadow_full_flow_uses_content_not_primary_paths(shadow_run: Path) -> None:
    register = json.loads(
        (shadow_run / "source_register" / "source_register.json").read_text(encoding="utf-8")
    )
    extraction = json.loads(
        (shadow_run / "extracts" / "extraction_manifest.json").read_text(encoding="utf-8")
    )
    assert register["summary"]["logical_source_items"] == 52
    assert register["summary"]["exact_duplicate_groups"] >= 1
    assert register["summary"]["archive_members"] == 4
    assert extraction["summary"]["sources_terminal"] == 52
    assert extraction["summary"]["spreadsheet_hidden_sheets"] >= 1
    assert extraction["summary"]["prompt_injection_like_sources"] == 1
    assert extraction["summary"]["vision_queue_count"] == 0
    reviewed_queue = json.loads(
        (shadow_run / "extracts" / "needs_vision.json").read_text(encoding="utf-8")
    )
    assert reviewed_queue["reviewed_count"] == 1
    by_path = {item["relative_path"]: item for item in register["sources"]}
    assert by_path["04_Compliance_Archive/Damaged-Source.pdf"]["inventory_status"] == (
        "registered_unreadable"
    )
    misleading = by_path["04_Compliance_Archive/Mislabelled-Register.xlsx"]
    assert misleading["detected_type"] == "csv"
    assert misleading["extension_type_mismatch"] is True

    findings: dict[str, list[dict[str, object]]] = {}
    for name, relative_path in {
        "financial": "workstreams/financial.json",
        "commercial": "workstreams/commercial.json",
        "legal_contractual": "workstreams/legal_contractual.json",
        "operational_management": "workstreams/operational_management.json",
        "it": "workstreams/it.json",
        "tax": "tax/tax-findings.json",
    }.items():
        findings[name] = json.loads((shadow_run / relative_path).read_text(encoding="utf-8"))[
            "findings"
        ]
        assert findings[name], f"shadow analysis produced no {name} finding"
    rendered = json.dumps(findings)
    assert all(name not in rendered for name in ("Harbourlight", "Mosaic", "Juniper"))
    assert "Firbank Holdings" in rendered
    validation = json.loads(
        (shadow_run / "outputs" / "report_validation.json").read_text(encoding="utf-8")
    )
    assert validation["status"] == "passed"
    assert validation["summary"]["brief_page_count"] == 2
    assert validation["summary"]["material_finding_citation_coverage"] == 1.0
    report = (shadow_run / "outputs" / "due_diligence_report.md").read_text(encoding="utf-8")
    rendered_workstreams = json.dumps(findings)
    assert "Phase 14 perimeter: acquire all shares" in report
    assert "Phase 14 price: no committee price" in report
    assert "Phase 14 thesis: test recurring revenue" in report
    assert "Phase 14 scope: cut-off 1 September 2026" in report
    assert "Investment thesis not supplied" not in report
    assert "Probability-weighted pipeline is understated by EUR 60,000" in report
    assert "revenue revenue" not in report.casefold()
    assert "remains pending visual review" not in rendered_workstreams.casefold()
    assert "No visual-review task remains pending" in report


def test_150_logical_source_scale_cache_and_memory(tmp_path: Path) -> None:
    room = tmp_path / "scale-room"
    manifest_path = tmp_path / "scale-manifest.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_phase14_rooms.py"),
            "--scale-root",
            str(room),
            "--scale-manifest",
            str(manifest_path),
        ],
        check=True,
        cwd=ROOT,
    )
    config = _config_without_ocr(ROOT)
    run_path = create_run(config, runs_root=tmp_path / "runs")
    tracemalloc.start()
    registration = register_room(run_path, room, LIMITS)
    extraction = extract_run(run_path, room, config)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert registration.summary["logical_source_items"] == 150
    assert registration.summary["physical_files"] == 140
    assert registration.summary["archive_members"] == 10
    assert registration.summary["exact_duplicate_groups"] >= 1
    registered = json.loads(
        (run_path / "source_register" / "source_register.json").read_text(encoding="utf-8")
    )["sources"]
    assert all(re.fullmatch(r"[0-9a-f]{64}", str(item["sha256"])) for item in registered)
    assert extraction.summary["sources_terminal"] == 150
    assert extraction.summary["source_status_counts"]["failed"] == 1
    assert peak < 512 * 1024 * 1024
    assert extract_run(run_path, room, config).reused is True

    changed = room / "Batch-02" / "Record-001.csv"
    changed.write_text("Record,Period,Value\nSCALE-001,2024,999999\n", encoding="utf-8")
    register_room(run_path, room, LIMITS)
    refreshed = extract_run(run_path, room, config)
    assert refreshed.reused is False
    assert refreshed.summary["cache_hits"] >= 140
    assert refreshed.summary["cache_misses"] == 1


def _write_bad_input_room(room: Path) -> None:
    room.mkdir()
    (room / "a.csv").write_text("Metric,Value\nObserved,42\n", encoding="utf-8")
    (room / "duplicate-renamed.csv").write_bytes((room / "a.csv").read_bytes())
    (room / "unsupported.bin").write_bytes(b"\x00\x01\x02unsupported")
    (room / "empty.txt").write_bytes(b"")
    (room / "corrupt.pdf").write_bytes(b"%PDF-1.7\nincomplete")
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    writer.encrypt("synthetic-password")
    with (room / "encrypted.pdf").open("wb") as handle:
        writer.write(handle)
    (room / "one").mkdir()
    (room / "two").mkdir()
    (room / "one" / "same.csv").write_text("A,B\n1,2\n", encoding="utf-8")
    (room / "two" / "same.csv").write_text("A,B\n3,4\n", encoding="utf-8")
    with zipfile.ZipFile(room / "unsafe.zip", "w") as archive:
        archive.writestr("../escape.csv", "A,B\n5,6\n")
        archive.writestr("safe/member.csv", "A,B\n7,8\n")
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Large within limit")
    sheet.append([f"Column {column}" for column in range(16)])
    for row in range(2500):
        sheet.append([row * 16 + column for column in range(16)])
    workbook.save(room / "large.xlsx")
    shutil_source = SHADOW_ROOM / "04_Compliance_Archive" / "Scan-47.pdf"
    (room / "image-only.pdf").write_bytes(shutil_source.read_bytes())


def test_bad_input_matrix_and_interrupted_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    room = tmp_path / "bad-input-room"
    _write_bad_input_room(room)
    config = _config_without_ocr(ROOT)
    run_path = create_run(config, runs_root=tmp_path / "runs")
    register_room(run_path, room, LIMITS)
    register = json.loads(
        (run_path / "source_register" / "source_register.json").read_text(encoding="utf-8")
    )
    by_name = {item["filename"]: item for item in register["sources"]}
    assert by_name["unsupported.bin"]["inventory_status"] == "registered_unsupported"
    assert by_name["corrupt.pdf"]["inventory_status"] == "registered_unreadable"
    assert by_name["encrypted.pdf"]["readability_status"] == "encrypted"
    assert by_name["empty.txt"]["inventory_status"] == "registered_unsupported"
    assert register["summary"]["exact_duplicate_groups"] >= 1
    assert register["summary"]["same_basename_conflicts"] == 1
    assert any(item["inventory_status"] == "blocked_unsafe" for item in register["sources"])

    import dd_engine.extraction.pipeline as extraction_pipeline

    original_dispatch = extraction_pipeline._dispatch
    interrupted = False

    def interrupt_once(**kwargs: object) -> object:
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise KeyboardInterrupt("simulated interruption")
        return original_dispatch(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(extraction_pipeline, "_dispatch", interrupt_once)
    with pytest.raises(KeyboardInterrupt, match="simulated interruption"):
        extract_run(run_path, room, config)
    _, manifest = load_manifest(run_path)
    assert manifest["stages"]["extract"]["state"] == "running"
    monkeypatch.setattr(extraction_pipeline, "_dispatch", original_dispatch)
    resumed = extract_run(run_path, room, config)
    assert resumed.summary["sources_terminal"] == register["summary"]["logical_source_items"]
    assert resumed.summary["vision_queue_count"] >= 1
    assert resumed.summary["spreadsheet_cell_units"] >= 40_000


def test_read_only_output_failure_is_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "read-only-output"
    root.mkdir()
    original_mkdir = Path.mkdir

    def permission_denied(
        self: Path,
        mode: int = 0o777,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        if self.parent == root:
            raise PermissionError("simulated read-only output directory")
        original_mkdir(self, mode=mode, parents=parents, exist_ok=exist_ok)

    monkeypatch.setattr(Path, "mkdir", permission_denied)
    with pytest.raises(RunError, match="cannot create run directory"):
        create_run(_config_without_ocr(ROOT), runs_root=root)
