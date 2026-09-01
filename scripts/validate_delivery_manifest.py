"""Validate the checked-in Phase 15 delivery manifest and candidate package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

RUN_ID_PATTERN = re.compile(r"Final synthetic run ID:\s*`([^`]+)`")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE),
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
)
REQUIRED_DELIVERABLES = (
    "Repository README",
    "Synthetic data room",
    "Planted-issue note",
    "Due-diligence report",
    "IC brief PDF",
    "Source register",
    "Intake round one",
    "Intake round two",
    "Red-team challenge log",
    "Red-team resolution log",
    "Run log",
    "Public-research log",
    "Delivery notes",
    "Acceptance evidence",
    "Clean-clone evidence",
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
        if len(cells) != 7 or cells[0] in {"Deliverable", "---"}:
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
    text = manifest_path.read_text(encoding="utf-8")
    errors: list[str] = []

    run_match = RUN_ID_PATTERN.search(text)
    if run_match is None:
        errors.append("manifest does not declare the final synthetic run ID")
        run_id = ""
    else:
        run_id = run_match.group(1)

    rows = _table_rows(text)
    if not rows:
        errors.append("manifest contains no seven-column deliverable rows")

    labels = {row[0] for row in rows}
    for required in REQUIRED_DELIVERABLES:
        if not any(label.startswith(required) for label in labels):
            errors.append(f"missing required deliverable row: {required}")

    checked_files = 0
    for deliverable, raw_path, row_run_id, raw_checksum, status, _stage, _limit in rows:
        relative = raw_path.strip("`")
        candidate = (repo_root / relative).resolve()
        try:
            candidate.relative_to(repo_root)
        except ValueError:
            errors.append(f"path escapes repository: {relative}")
            continue
        if not candidate.exists():
            errors.append(f"missing path for {deliverable}: {relative}")
            continue
        checksum = raw_checksum.strip("`")
        if candidate.is_file():
            checked_files += 1
            if not SHA256_PATTERN.fullmatch(checksum):
                errors.append(f"file row lacks SHA-256 for {relative}")
            elif _sha256(candidate) != checksum:
                errors.append(f"checksum mismatch for {relative}")
        elif not checksum.lower().startswith("n/a"):
            errors.append(f"directory row must use n/a checksum: {relative}")
        if relative.startswith("examples/approved-output/run/") and row_run_id != run_id:
            errors.append(f"run ID mismatch for {relative}: {row_run_id}")
        if not status:
            errors.append(f"validation status is empty for {relative}")

    package = repo_root / "examples" / "approved-output" / "run"
    validation = _json(package / "outputs" / "report_validation.json")
    summary = validation.get("summary", {})
    pdf_check = validation.get("checks", {}).get("pdf", {})
    if validation.get("run_id") != run_id or validation.get("status") != "passed":
        errors.append("packaged report validation does not pass for the declared run")
    if summary.get("structured_failed_citation_count") != 0:
        errors.append("packaged report validation contains failed citations")
    if summary.get("calculation_failure_count") != 0:
        errors.append("packaged report validation contains failed calculations")
    if pdf_check.get("page_count") != 2 or pdf_check.get("a4_pages") is not True:
        errors.append("packaged IC brief is not exactly two A4 pages")

    isolation_names = (
        "packet-allowlist.json",
        "sealed-packet-manifest.json",
        "isolation-manifest.json",
    )
    isolation_present = [name for name in isolation_names if (package / "red_team" / name).exists()]
    if len(isolation_present) != len(isolation_names):
        if validation.get("release_ready") is not False:
            errors.append("release_ready must be false while red-team isolation proof is absent")
        if validation.get("independent_red_team_performed") is not False:
            errors.append("independent_red_team_performed must be false without isolation proof")
        if "Overall release status: **BLOCKED**" not in text:
            errors.append("manifest must mark overall release status BLOCKED")

    register = _json(package / "source_register" / "source_register.json")
    sources = register.get("sources", register.get("records", []))
    if not isinstance(sources, list) or len(sources) != 100:
        errors.append("packaged source register must contain exactly 100 logical sources")

    absolute_path_hits: list[str] = []
    for path in package.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(content) for pattern in ABSOLUTE_PATH_PATTERNS):
            absolute_path_hits.append(path.relative_to(repo_root).as_posix())
    if absolute_path_hits:
        errors.append("absolute local paths in package: " + ", ".join(absolute_path_hits))

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
