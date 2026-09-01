"""Validate the checked-in self-service evaluator delivery package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

RUN_ID_PATTERN = re.compile(r"Completed demonstration run ID:\s*`([^`]+)`")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:\\Users\\jites", re.IGNORECASE),
    re.compile(r"/Users/", re.IGNORECASE),
    re.compile(r"/home/", re.IGNORECASE),
)
FORBIDDEN_CONTENT = (
    "planted_issues",
    "expected_findings",
    "expected_calculations",
    "generator truth",
    "gavin response",
    "fabricated gavin",
)
REQUIRED_DELIVERABLES = (
    "Source register",
    "Extraction summary",
    "Round 1 questions",
    "TEST-ONLY SYNTHETIC ANSWERS, Round 1",
    "Round 2 questions",
    "TEST-ONLY SYNTHETIC ANSWERS, Round 2",
    "Final unresolved-information register",
    "Evidence ledger",
    "Contradiction ledger",
    "Calculation ledger",
    "Financial workstream",
    "Commercial workstream",
    "Legal/contractual workstream",
    "Operational/management workstream",
    "IT workstream",
    "Tax workstream",
    "Full due-diligence report",
    "Exactly two-page IC brief PDF",
    "Run/model/cost log",
    "Public-research log",
    "Final validation results",
)
EXPECTED_PACKAGE_FILES = frozenset(
    {
        "README.md",
        "citations/index.jsonl",
        "evidence/calculations.jsonl",
        "evidence/citation_validation.json",
        "evidence/contradictions.jsonl",
        "evidence/evidence.jsonl",
        "extracts/extraction_manifest.json",
        "intake/round_1_questions.json",
        "intake/round_1_questions.md",
        "intake/round_2_questions.json",
        "intake/round_2_questions.md",
        "intake/TEST_ONLY_SYNTHETIC_ANSWERS_round_1.json",
        "intake/TEST_ONLY_SYNTHETIC_ANSWERS_round_2.json",
        "intake/unresolved_questions.md",
        "logs/public-research-log.jsonl",
        "logs/run-log.jsonl",
        "logs/run-log.md",
        "outputs/due_diligence_report.md",
        "outputs/ic_brief.md",
        "outputs/ic_brief.pdf",
        "outputs/report_validation.json",
        "source_register/source_register.csv",
        "source_register/source_register.json",
        "source_register/source_register.md",
        "tax/tax-analysis.md",
        "tax/tax-findings.json",
        "workstreams/commercial.json",
        "workstreams/commercial.md",
        "workstreams/financial.json",
        "workstreams/financial.md",
        "workstreams/it.json",
        "workstreams/it.md",
        "workstreams/legal_contractual.json",
        "workstreams/legal_contractual.md",
        "workstreams/operational_management.json",
        "workstreams/operational_management.md",
    }
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] in {"Shipped artifact", "---"}:
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    return rows


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    repo_root = manifest_path.parent
    package = repo_root / "example_outputs"
    text = manifest_path.read_text(encoding="utf-8")
    errors: list[str] = []

    run_match = RUN_ID_PATTERN.search(text)
    if run_match is None:
        errors.append("manifest does not declare the completed demonstration run ID")
        run_id = ""
    else:
        run_id = run_match.group(1)

    rows = _table_rows(text)
    if not rows:
        errors.append("manifest contains no five-column shipped-artifact rows")
    labels = {row[0] for row in rows}
    for required in REQUIRED_DELIVERABLES:
        if not any(label.startswith(required) for label in labels):
            errors.append(f"missing required deliverable row: {required}")

    manifest_paths: set[str] = set()
    checked_files = 0
    for deliverable, raw_path, row_run_id, raw_checksum, status in rows:
        relative = raw_path.strip("`")
        manifest_paths.add(relative)
        candidate = (repo_root / relative).resolve()
        try:
            candidate.relative_to(repo_root)
        except ValueError:
            errors.append(f"path escapes repository: {relative}")
            continue
        if not relative.startswith("example_outputs/"):
            errors.append(f"shipped artifact is outside example_outputs: {relative}")
        if not candidate.is_file():
            errors.append(f"missing file for {deliverable}: {relative}")
            continue
        checked_files += 1
        checksum = raw_checksum.strip("`")
        if not SHA256_PATTERN.fullmatch(checksum):
            errors.append(f"file row lacks SHA-256 for {relative}")
        elif _sha256(candidate) != checksum:
            errors.append(f"checksum mismatch for {relative}")
        if row_run_id != run_id:
            errors.append(f"run ID mismatch for {relative}: {row_run_id}")
        if not status.startswith("PASS"):
            errors.append(f"validation status must be PASS for {relative}")

    actual_paths = {
        path.relative_to(repo_root).as_posix()
        for path in package.rglob("*")
        if path.is_file()
    }
    expected_paths = {f"example_outputs/{item}" for item in EXPECTED_PACKAGE_FILES}
    if actual_paths != expected_paths:
        errors.append(
            "example_outputs file allowlist mismatch: "
            f"unexpected={sorted(actual_paths - expected_paths)}, "
            f"missing={sorted(expected_paths - actual_paths)}"
        )
    if manifest_paths != expected_paths:
        errors.append(
            "manifest does not enumerate every shipped artifact: "
            f"unlisted={sorted(expected_paths - manifest_paths)}, "
            f"missing_files={sorted(manifest_paths - expected_paths)}"
        )

    validation = _json(package / "outputs" / "report_validation.json")
    summary = validation.get("summary", {})
    pdf_check = validation.get("checks", {}).get("pdf", {})
    if validation.get("run_id") != run_id or validation.get("status") != "passed":
        errors.append("packaged report validation does not pass for the declared run")
    if summary.get("structured_failed_citation_count") != 0:
        errors.append("packaged report validation contains failed citations")
    if summary.get("calculation_failure_count") != 0:
        errors.append("packaged report validation contains failed calculations")
    if summary.get("brief_page_count") != 2 or pdf_check.get("a4_pages") is not True:
        errors.append("packaged IC brief is not exactly two A4 pages")
    if validation.get("release_ready") is not False:
        errors.append("release_ready must remain false without independent red-team proof")
    if validation.get("independent_red_team_performed") is not False:
        errors.append("independent red-team status must remain false")
    if "Overall release status: **BLOCKED**" not in text:
        errors.append("manifest must mark overall release status BLOCKED")

    register = _json(package / "source_register" / "source_register.json")
    sources = register.get("sources", register.get("records", []))
    if not isinstance(sources, list) or len(sources) != 52:
        errors.append("packaged source register must contain exactly 52 logical sources")

    answer_files = (
        package / "intake" / "TEST_ONLY_SYNTHETIC_ANSWERS_round_1.json",
        package / "intake" / "TEST_ONLY_SYNTHETIC_ANSWERS_round_2.json",
    )
    for answer_file in answer_files:
        if "TEST-ONLY" not in answer_file.read_text(encoding="utf-8"):
            errors.append(f"test-only answer label missing from {answer_file.name}")
    if "TEST-ONLY SYNTHETIC ANSWERS" not in (package / "README.md").read_text(
        encoding="utf-8"
    ):
        errors.append("package README does not prominently label the synthetic answers")

    prohibited_hits: list[str] = []
    for path in package.rglob("*"):
        if not path.is_file() or path.suffix.lower() == ".pdf":
            continue
        content = path.read_text(encoding="utf-8")
        if any(pattern.search(content) for pattern in ABSOLUTE_PATH_PATTERNS):
            prohibited_hits.append(f"absolute path: {path.relative_to(repo_root).as_posix()}")
        lowered = content.lower()
        if any(term in lowered for term in FORBIDDEN_CONTENT):
            relative_path = path.relative_to(repo_root).as_posix()
            prohibited_hits.append(f"prohibited reference: {relative_path}")
    if prohibited_hits:
        errors.append("; ".join(prohibited_hits))

    return {
        "status": "passed" if not errors else "failed",
        "manifest": manifest_path.relative_to(repo_root).as_posix(),
        "run_id": run_id,
        "deliverable_rows": len(rows),
        "checked_files": checked_files,
        "release_ready": validation.get("release_ready"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("DELIVERY_MANIFEST.md"))
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = validate_manifest(arguments.manifest)
    if arguments.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Delivery manifest validation: {result['status']}")
        print(f"Run ID: {result['run_id']}")
        print(f"Rows: {result['deliverable_rows']}; files checked: {result['checked_files']}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
