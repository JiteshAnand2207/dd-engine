#!/usr/bin/env python3
"""Validate the complete fictional Phase 3 synthetic data room."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from PIL import Image, ImageStat
from pypdf import PdfReader
from pypdf.errors import PdfReadError

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_synthetic_room import DEFAULT_SEED, generate, sha256_file  # noqa: E402

EXPECTED_VISIBLE = 90
EXPECTED_MEMBERS = 10
EXPECTED_LOGICAL = 100
EXPECTED_VISIBLE_FOLDERS = {"financial": 27, "legal": 33, "tax": 30}
EXPECTED_LOGICAL_WORKSTREAMS = {"financial": 27, "legal": 43, "tax": 30}
EXPECTED_LOGICAL_FORMATS = {
    "csv": 1,
    "docx": 5,
    "jpg": 2,
    "pdf": 64,
    "png": 2,
    "xlsx": 25,
    "zip": 1,
}
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    passed: bool
    detail: str


class Validator:
    def __init__(self) -> None:
        self.checks: list[Check] = []

    def require(self, name: str, condition: bool, detail: str) -> None:
        self.checks.append(Check(name, bool(condition), detail))

    @property
    def ok(self) -> bool:
        return all(check.passed for check in self.checks)


def stable_json_load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def safe_room_path(path: Path) -> Path:
    if not str(path).strip():
        raise ValueError("an explicit data-room path is required")
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"data-room path is not a directory: {resolved}")
    if any(part.casefold() == "planted_issues" for part in resolved.parts):
        raise ValueError("data-room path may not be planted_issues or any descendant")
    return resolved


def iter_visible_files(room: Path) -> list[Path]:
    files = []
    for path in room.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlinks are forbidden in the synthetic room: {path}")
        if path.is_file():
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(room):
                raise ValueError(f"file escaped data-room root: {path}")
            files.append(resolved)
    return sorted(files, key=lambda item: item.relative_to(room).as_posix())


def logical_bytes(room: Path, logical_path: str) -> bytes:
    if "!" not in logical_path:
        return (room / logical_path).read_bytes()
    container, member = logical_path.split("!", 1)
    with zipfile.ZipFile(room / container) as archive:
        return archive.read(member)


def text_from_pdf(payload: bytes) -> str:
    reader = PdfReader(io.BytesIO(payload), strict=True)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def text_from_docx(payload: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.startswith("word/") and name.endswith(".xml")
        ]
        parts = []
        for name in names:
            root = ElementTree.fromstring(archive.read(name))
            parts.extend(
                element.text or "" for element in root.iter() if element.tag.endswith("}t")
            )
        return " ".join(parts)


def text_from_xlsx(payload: bytes) -> str:
    if not payload.startswith(b"PK"):
        return payload.decode("utf-8", errors="replace")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        parts = []
        for name in archive.namelist():
            if name.endswith(".xml"):
                parts.append(archive.read(name).decode("utf-8", errors="replace"))
        return " ".join(parts)


def extract_logical_text(room: Path, logical_path: str) -> str:
    payload = logical_bytes(room, logical_path)
    suffix = Path(logical_path.split("!", 1)[-1]).suffix.casefold()
    if suffix == ".pdf":
        return text_from_pdf(payload)
    if suffix == ".docx":
        return text_from_docx(payload)
    if suffix == ".xlsx":
        return text_from_xlsx(payload)
    if suffix in {".csv", ".txt"}:
        return payload.decode("utf-8", errors="replace")
    return ""


def xlsx_rows(payload: bytes, sheet_number: int = 1) -> list[list[Any]]:
    if not payload.startswith(b"PK"):
        decoded = payload.decode("utf-8")
        return [row for row in csv.reader(io.StringIO(decoded))]
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        root = ElementTree.fromstring(archive.read(f"xl/worksheets/sheet{sheet_number}.xml"))
        rows: list[list[Any]] = []
        for row in root.findall(".//x:sheetData/x:row", NS):
            values: list[Any] = []
            expected_column = 1
            for cell in row.findall("x:c", NS):
                reference = cell.attrib["r"]
                letters = re.match(r"[A-Z]+", reference)
                if letters is None:
                    continue
                column = 0
                for character in letters.group(0):
                    column = column * 26 + ord(character) - 64
                while expected_column < column:
                    values.append(None)
                    expected_column += 1
                if cell.attrib.get("t") == "inlineStr":
                    node = cell.find("x:is/x:t", NS)
                    value: Any = node.text if node is not None else ""
                else:
                    node = cell.find("x:v", NS)
                    raw = node.text if node is not None else ""
                    try:
                        number = float(raw)
                        value = int(number) if number.is_integer() else number
                    except ValueError:
                        value = raw
                values.append(value)
                expected_column = column + 1
            rows.append(values)
        return rows


def find_row(rows: Iterable[Sequence[Any]], label: str) -> Sequence[Any]:
    target = normalize_text(label)
    for row in rows:
        if row and normalize_text(str(row[0])) == target:
            return row
    raise KeyError(f"row not found: {label}")


def pdf_image_only(payload: bytes) -> tuple[bool, int, int]:
    reader = PdfReader(io.BytesIO(payload), strict=True)
    text_chars = 0
    image_count = 0
    for page in reader.pages:
        text_chars += len((page.extract_text() or "").strip())
        resources = page.get("/Resources")
        if resources is None:
            continue
        xobjects = resources.get("/XObject")
        if xobjects is None:
            continue
        xobjects = xobjects.get_object()
        for obj in xobjects.values():
            resolved = obj.get_object()
            if resolved.get("/Subtype") == "/Image":
                image_count += 1
    return text_chars == 0 and image_count >= len(reader.pages), len(reader.pages), image_count


def validate_counts(
    v: Validator, room: Path, manifest: dict[str, Any], visible: list[Path]
) -> None:
    counts = manifest.get("counts", {})
    v.require(
        "visible file count",
        len(visible) == EXPECTED_VISIBLE == counts.get("visible_files"),
        (
            f"observed={len(visible)}, manifest={counts.get('visible_files')}, "
            f"expected={EXPECTED_VISIBLE}"
        ),
    )
    entries = manifest.get("entries", [])
    logical = len(entries)
    members = sum(not entry.get("visible", True) for entry in entries)
    v.require(
        "ZIP member count",
        members == EXPECTED_MEMBERS == counts.get("zip_members"),
        f"observed={members}, expected={EXPECTED_MEMBERS}",
    )
    v.require(
        "logical document count",
        logical == EXPECTED_LOGICAL == counts.get("logical_documents"),
        f"observed={logical}, expected={EXPECTED_LOGICAL}",
    )
    folder_counts = Counter(path.relative_to(room).parts[0].casefold() for path in visible)
    v.require(
        "visible folder counts",
        dict(folder_counts) == EXPECTED_VISIBLE_FOLDERS == counts.get("visible_by_folder"),
        f"observed={dict(folder_counts)}",
    )
    workstreams = Counter(entry["workstream"] for entry in entries)
    v.require(
        "logical workstream counts",
        dict(workstreams) == EXPECTED_LOGICAL_WORKSTREAMS == counts.get("logical_by_workstream"),
        f"observed={dict(workstreams)}",
    )
    formats = Counter(entry["declared_format"] for entry in entries)
    v.require(
        "logical format mix",
        dict(sorted(formats.items()))
        == EXPECTED_LOGICAL_FORMATS
        == counts.get("logical_by_format"),
        f"observed={dict(sorted(formats.items()))}",
    )


def validate_manifest_hashes(
    v: Validator, room: Path, manifest: dict[str, Any], visible: list[Path]
) -> None:
    entries = manifest["entries"]
    visible_entries = {entry["path"]: entry for entry in entries if entry.get("visible", True)}
    observed_paths = {path.relative_to(room).as_posix() for path in visible}
    v.require(
        "manifest path coverage",
        set(visible_entries) == observed_paths,
        f"manifest={len(visible_entries)}, observed={len(observed_paths)}",
    )
    errors = []
    for relative, entry in visible_entries.items():
        path = room / relative
        if sha256_file(path) != entry["sha256"] or path.stat().st_size != entry["size_bytes"]:
            errors.append(relative)
    for entry in entries:
        if entry.get("visible", True):
            continue
        payload = logical_bytes(room, entry["path"])
        if (
            hashlib.sha256(payload).hexdigest() != entry["sha256"]
            or len(payload) != entry["size_bytes"]
        ):
            errors.append(entry["path"])
    v.require(
        "manifest hashes and sizes",
        not errors,
        "all 100 logical artifacts match" if not errors else f"mismatches={errors}",
    )


def validate_zip(v: Validator, room: Path, manifest: dict[str, Any]) -> None:
    zip_paths = [path for path in room.rglob("*.zip") if path.is_file()]
    safe = True
    member_names: list[str] = []
    if len(zip_paths) == 1:
        with zipfile.ZipFile(zip_paths[0]) as archive:
            member_names = [info.filename for info in archive.infolist() if not info.is_dir()]
            safe = all(
                not name.startswith(("/", "\\")) and ".." not in Path(name).parts
                for name in member_names
            )
    declared = sorted(
        entry["member_path"] for entry in manifest["entries"] if not entry.get("visible", True)
    )
    v.require(
        "single safe ZIP",
        len(zip_paths) == 1 and safe,
        f"containers={len(zip_paths)}, safe_paths={safe}",
    )
    v.require(
        "ZIP has exactly ten declared members",
        len(member_names) == 10 and sorted(member_names) == declared,
        f"members={len(member_names)}",
    )


def validate_structure_and_quirks(v: Validator, room: Path, manifest: dict[str, Any]) -> None:
    required_dirs = [
        room / "Financial",
        room / "Legal",
        room / "Tax",
        room / "Legal/Work Permits",
        room / "Legal/Business Registration",
        room / "Tax/Trial Balance",
        room / "Tax/Invoice Samples",
    ]
    v.require(
        "required folders",
        all(path.is_dir() for path in required_dirs),
        "all required nested folders exist",
    )
    empty = room / "Legal/Legal 2.1"
    v.require(
        "empty referenced folder",
        empty.is_dir() and not any(empty.iterdir()),
        "Legal/Legal 2.1 exists and is empty",
    )

    visible_entries = [entry for entry in manifest["entries"] if entry.get("visible", True)]
    groups: dict[str, list[str]] = defaultdict(list)
    for entry in visible_entries:
        groups[entry["sha256"]].append(entry["path"])
    duplicates = [paths for paths in groups.values() if len(paths) > 1]
    v.require(
        "exact duplicate with different name",
        any(len({Path(path).name for path in paths}) > 1 for paths in duplicates),
        f"duplicate_groups={len(duplicates)}",
    )
    quirk_set = {quirk for entry in manifest["entries"] for quirk in entry.get("quirks", [])}
    for quirk in (
        "near_duplicate",
        "superseded_version",
        "wrong_folder_document",
        "partially_corrupted",
        "contains_unredacted_employee_list",
        "ambiguous_see_legal_2_1",
    ):
        v.require(f"quirk: {quirk}", quirk in quirk_set, "declared and evidence-linked in manifest")
    basenames: dict[str, list[str]] = defaultdict(list)
    for path in room.rglob("*"):
        if path.is_file():
            basenames[path.name].append(path.relative_to(room).as_posix())
    same_name = {name: paths for name, paths in basenames.items() if len(paths) > 1}
    v.require(
        "same basename in different directories",
        "Registration.pdf" in same_name,
        f"matches={same_name.get('Registration.pdf', [])}",
    )

    mismatch = room / "Tax/Trial Balance/Trial_Balance_2024.xlsx"
    csv_ok = False
    try:
        rows = list(csv.reader(io.StringIO(mismatch.read_text(encoding="utf-8"))))
        csv_ok = not mismatch.read_bytes().startswith(b"PK") and len(rows) >= 5
    except (OSError, UnicodeError, csv.Error):
        pass
    v.require(
        "CSV bytes with XLSX extension",
        csv_ok,
        "extension mismatch is intentional and parseable as CSV",
    )

    working = room / "Financial/Working_Capital_Calculation.xlsx"
    hidden_sheet = False
    hidden_row = False
    formula_error = False
    with zipfile.ZipFile(working) as archive:
        workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
        sheet_xml = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        hidden_sheet = 'state="hidden"' in workbook_xml
        hidden_row = 'r="8" hidden="1"' in sheet_xml
        formula_error = "SUM(B5:B7)" in sheet_xml and "SUM(B5:B8)" not in sheet_xml
    v.require("hidden spreadsheet sheet", hidden_sheet, "Assumptions sheet is hidden")
    v.require("hidden spreadsheet row", hidden_row, "prepayments row is hidden")
    v.require("incorrect formula range", formula_error, "calculation deliberately stops at B7")

    request_rows = xlsx_rows((room / "Financial/Financial_Request_List.xlsx").read_bytes())
    vendor_answers = [
        str(row[2])
        for row in request_rows
        if len(row) > 2 and re.fullmatch(r"F-\d{2}", str(row[0]))
    ]
    sparse_answers = [
        answer
        for answer in vendor_answers
        if normalize_text(answer).startswith(("n/a", "none", "see legal 2.1"))
    ]
    sparse_categories = {
        category
        for category in ("n/a", "none", "see legal 2.1")
        if any(normalize_text(answer).startswith(category) for answer in sparse_answers)
    }
    v.require(
        "sparse request-list vendor answers",
        len(vendor_answers) == 10 and 5 <= len(sparse_answers) <= 7 and len(sparse_categories) == 3,
        (
            f"answers={len(vendor_answers)}, sparse={len(sparse_answers)}, "
            f"categories={sorted(sparse_categories)}"
        ),
    )

    entries_by_path = {entry["path"]: entry for entry in manifest["entries"]}
    original_response_path = "Tax/Tax_Response_Summary_Original.xlsx"
    revised_response_path = "Tax/Tax_Response_Summary_Rev2.xlsx"
    response_question = "Have any VAT returns been amended?"
    original_answer = find_row(
        xlsx_rows((room / original_response_path).read_bytes()), response_question
    )[1]
    revised_answer = find_row(
        xlsx_rows((room / revised_response_path).read_bytes()), response_question
    )[1]
    original_vat_path = "Tax/VAT/VAT3_2025_P2.pdf"
    amended_vat_path = "Tax/VAT/VAT3_2025_P2_AMENDED.pdf"
    amended_text = text_from_pdf((room / amended_vat_path).read_bytes())
    version_pairs_ok = (
        normalize_text(str(original_answer)) != normalize_text(str(revised_answer))
        and entries_by_path[revised_response_path].get("supersedes") == original_response_path
        and entries_by_path[amended_vat_path].get("supersedes") == original_vat_path
        and "original payable" in normalize_text(amended_text)
        and "amended payable" in normalize_text(amended_text)
    )
    v.require(
        "original/Rev2 answers and original/amended tax documents",
        version_pairs_ok,
        "changed response and precedence links are explicit for both version pairs",
    )


def validate_formats(v: Validator, room: Path, manifest: dict[str, Any]) -> None:
    failures = []
    corrupt_expected = "Legal/Legacy/Unreadable_Policy_Archive.pdf"
    image_only_entries = [
        entry for entry in manifest["entries"] if "image_only_pdf" in entry.get("quirks", [])
    ]
    image_only_errors = []
    for entry in image_only_entries:
        try:
            valid, pages, images = pdf_image_only(logical_bytes(room, entry["path"]))
            if not valid:
                image_only_errors.append(f"{entry['path']} pages={pages} images={images}")
        except Exception as exc:  # format validation must report all fixture errors
            image_only_errors.append(f"{entry['path']}: {exc}")
    v.require(
        "image-only PDFs are raster-only",
        not image_only_errors and len(image_only_entries) == 3,
        f"documents={len(image_only_entries)}, errors={image_only_errors}",
    )

    corrupt_failed = False
    try:
        PdfReader(room / corrupt_expected, strict=True)
    except Exception:
        corrupt_failed = True
    v.require("intended unreadable file", corrupt_failed, "corrupt legacy PDF fails strict parsing")

    for entry in manifest["entries"]:
        logical_path = entry["path"]
        suffix = entry["declared_format"]
        if logical_path == corrupt_expected or "extension_mismatch" in entry.get("quirks", []):
            continue
        payload = logical_bytes(room, logical_path)
        try:
            if suffix == "pdf":
                reader = PdfReader(io.BytesIO(payload), strict=True)
                if not reader.pages:
                    raise ValueError("PDF has no pages")
            elif suffix == "docx":
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    if "word/document.xml" not in archive.namelist():
                        raise ValueError("DOCX document.xml missing")
            elif suffix == "xlsx":
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    if "xl/workbook.xml" not in archive.namelist():
                        raise ValueError("XLSX workbook.xml missing")
            elif suffix in {"jpg", "png"}:
                with Image.open(io.BytesIO(payload)) as image:
                    image.verify()
            elif suffix == "csv":
                list(csv.reader(io.StringIO(payload.decode("utf-8"))))
            elif suffix == "zip":
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    if archive.testzip() is not None:
                        raise ValueError("ZIP CRC failure")
        except Exception as exc:
            failures.append(f"{logical_path}: {exc}")
    v.require(
        "valid format mix",
        not failures,
        "all intended-readable files pass structural checks"
        if not failures
        else f"failures={failures}",
    )

    photos = [
        room / "Financial/Loan Letters/Phone_Photo_Term_Loan.jpg",
        room / "Financial/Loan Letters/Phone_Photo_Innovation_Loan.jpg",
    ]
    photo_details = []
    photos_ok = True
    hashes = set()
    for photo in photos:
        with Image.open(photo) as image:
            hashes.add(hashlib.sha256(photo.read_bytes()).hexdigest())
            gray = image.convert("L")
            variance = ImageStat.Stat(gray).var[0]
            photo_details.append((image.format, image.size, round(variance, 1)))
            photos_ok = (
                photos_ok
                and image.format == "JPEG"
                and image.width >= 1400
                and image.height >= 1000
                and variance > 500
            )
    v.require(
        "two genuine phone-photo JPEGs", photos_ok and len(hashes) == 2, f"details={photo_details}"
    )


def validate_ground_truth(v: Validator, room: Path, issues: dict[str, Any]) -> None:
    errors = []
    recovered = 0
    for issue in issues.get("issues", []):
        issue_ok = True
        evidence_items = issue.get("evidence", [])
        if not evidence_items:
            issue_ok = False
        for evidence in evidence_items:
            try:
                text = extract_logical_text(room, evidence["path"])
                if normalize_text(evidence["contains"]) not in normalize_text(text):
                    issue_ok = False
                    errors.append(f"{issue['id']} missing signal in {evidence['path']}")
            except Exception as exc:
                issue_ok = False
                errors.append(f"{issue['id']} evidence error: {exc}")
        if issue_ok:
            recovered += 1
    expected = issues.get("issue_count")
    v.require(
        "planted-issue evidence recovery",
        expected == 10 and recovered == expected and not errors,
        f"recovered={recovered}/{expected}"
        if not errors
        else f"recovered={recovered}/{expected}; errors={errors}",
    )


def validate_baseline(
    v: Validator,
    room: Path,
    manifest: dict[str, Any],
    canonical: dict[str, Any],
    issues: dict[str, Any],
) -> None:
    errors = []
    for year in canonical["financial_years"]:
        path = room / f"Financial/Statutory Accounts/Statutory_Accounts_{year['year']}.pdf"
        text = normalize_text(text_from_pdf(path.read_bytes()))
        for field in ("revenue", "gross_profit", "ebitda"):
            token = f"eur {year[field]:,}".casefold()
            if token not in text:
                errors.append(f"{year['year']} {field}")
    try:
        revenue_rows = xlsx_rows((room / "Financial/Revenue_by_Customer.xlsx").read_bytes())
        total = find_row(revenue_rows, "Total")
        if (
            total[1] != canonical["financial_years"][-1]["revenue"]
            or total[2] != canonical["management_accounts"]["revenue"]
        ):
            errors.append("revenue by customer totals")
        debtor_total = find_row(
            xlsx_rows((room / "Financial/Aged_Debtors.xlsx").read_bytes()), "Total trade debtors"
        )[-1]
        if debtor_total != canonical["working_capital"]["trade_debtors"]:
            errors.append("aged debtors total")
        creditor_total = find_row(
            xlsx_rows((room / "Financial/Aged_Creditors.xlsx").read_bytes()),
            "Total trade creditors",
        )[-1]
        if creditor_total != canonical["working_capital"]["trade_creditors"]:
            errors.append("aged creditors total")
        other_total = find_row(
            xlsx_rows((room / "Financial/Other_Debtors_and_Prepayments.xlsx").read_bytes()), "Total"
        )[1]
        if (
            other_total
            != canonical["working_capital"]["other_debtors"]
            + canonical["working_capital"]["prepayments"]
        ):
            errors.append("other debtors total")
        fixed_total = find_row(
            xlsx_rows((room / "Financial/Fixed_Asset_Register.xlsx").read_bytes()), "Total"
        )[3]
        if fixed_total != sum(asset["nbv"] for asset in canonical["fixed_assets"]):
            errors.append("fixed asset NBV")
        paye_total = find_row(
            xlsx_rows((room / "Financial/PAYE_Headcount_by_Client.xlsx").read_bytes()),
            "Total PAYE headcount",
        )[1]
        if paye_total != canonical["tax"]["paye"]["registered_headcount"]:
            errors.append("PAYE headcount")
        loan_total = find_row(
            xlsx_rows((room / "Financial/Loan_Summary.xlsx").read_bytes()), "Total loans"
        )[2]
        if loan_total != sum(item["balance"] for item in canonical["debt"]["loans"]):
            errors.append("loan total")
        hp_total = find_row(
            xlsx_rows((room / "Financial/HP_Summary.xlsx").read_bytes()), "Total HP exposure"
        )[2]
        if hp_total != sum(item["balance"] for item in canonical["debt"]["hp_agreements"]):
            errors.append("HP total")
    except (KeyError, IndexError, ValueError, zipfile.BadZipFile) as exc:
        errors.append(f"workbook baseline parse: {exc}")
    issue_ids = [issue["id"] for issue in issues["issues"]]
    declared = manifest.get("intentional_contradictions", [])
    if declared != issue_ids or len(set(declared)) != len(declared):
        errors.append("intentional contradiction allowlist")
    v.require(
        "baseline financial consistency",
        not errors,
        "canonical tie-outs pass; only sealed allowlisted contradictions remain"
        if not errors
        else f"errors={errors}",
    )


def validate_provenance(
    v: Validator, room: Path, manifest: dict[str, Any], canonical: dict[str, Any]
) -> None:
    errors = []
    if not manifest.get("provenance", {}).get("entirely_fictional"):
        errors.append("manifest fiction flag")
    provenance = canonical.get("provenance", {})
    if (
        provenance.get("real_source_material_used") is not False
        or provenance.get("external_research_used") is not False
    ):
        errors.append("canonical provenance")
    company = canonical.get("company", {})
    if "SYN" not in company.get("registration_id", "") or "SYN" not in company.get("vat_id", ""):
        errors.append("synthetic registration identifiers")
    emails = [employee["work_email"] for employee in canonical.get("employees", [])] + [
        employee["personal_email"] for employee in canonical.get("employees", [])
    ]
    if any(not email.endswith(".invalid") for email in emails):
        errors.append("non-reserved email domain")
    if any(path.is_symlink() for path in room.rglob("*")):
        errors.append("symlink present")
    v.require(
        "fictional provenance and no real client data",
        not errors,
        "synthetic identifiers, reserved domains and no external source use"
        if not errors
        else f"errors={errors}",
    )


def tree_fingerprint(root: Path) -> list[tuple[str, str, int]]:
    result = []
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        result.append((path.relative_to(root).as_posix(), sha256_file(path), path.stat().st_size))
    return result


def validate_determinism(
    v: Validator, room: Path, manifest_path: Path, issues_path: Path, seed: int
) -> None:
    with tempfile.TemporaryDirectory(prefix="dd-synthetic-determinism-") as temporary:
        root = Path(temporary)
        roots = []
        for name in ("first", "second"):
            metadata = root / name / "synthetic"
            output = metadata / "data_room"
            generate(output, metadata, issues_path, seed)
            roots.append(metadata)
        manifests_equal = (roots[0] / "room_manifest.json").read_bytes() == (
            roots[1] / "room_manifest.json"
        ).read_bytes()
        trees_equal = tree_fingerprint(roots[0] / "data_room") == tree_fingerprint(
            roots[1] / "data_room"
        )
        checked_in_equal = manifest_path.read_bytes() == (
            roots[0] / "room_manifest.json"
        ).read_bytes() and tree_fingerprint(room) == tree_fingerprint(roots[0] / "data_room")
    v.require(
        "deterministic regeneration",
        manifests_equal and trees_equal and checked_in_equal,
        (
            f"fresh_manifests={manifests_equal}, fresh_trees={trees_equal}, "
            f"checked_in_match={checked_in_equal}"
        ),
    )


def validate(
    room_path: Path,
    manifest_path: Path,
    canonical_path: Path,
    issues_path: Path | None,
    *,
    check_determinism: bool,
    public_only: bool,
    seed: int,
) -> tuple[Validator, dict[str, Any]]:
    room = safe_room_path(room_path)
    manifest = stable_json_load(manifest_path)
    canonical = stable_json_load(canonical_path)
    validator = Validator()
    visible = iter_visible_files(room)
    validate_counts(validator, room, manifest, visible)
    validate_manifest_hashes(validator, room, manifest, visible)
    validate_zip(validator, room, manifest)
    validate_structure_and_quirks(validator, room, manifest)
    validate_formats(validator, room, manifest)
    validate_provenance(validator, room, manifest, canonical)
    canonical_hash_ok = sha256_file(canonical_path) == manifest["canonical_dataset"]["sha256"]
    planted_issue_count: int | None = None
    if public_only:
        validator.require(
            "public metadata integrity",
            canonical_hash_ok,
            f"canonical={canonical_hash_ok}; sealed metadata deliberately not accessed",
        )
    else:
        if issues_path is None:
            raise ValueError("sealed validation requires an explicit issues path")
        issues = stable_json_load(issues_path)
        validate_ground_truth(validator, room, issues)
        validate_baseline(validator, room, manifest, canonical, issues)
        issues_hash_ok = sha256_file(issues_path) == manifest["sealed_issue_config"]["sha256"]
        validator.require(
            "metadata integrity",
            canonical_hash_ok and issues_hash_ok,
            f"canonical={canonical_hash_ok}, sealed_issues={issues_hash_ok}",
        )
        planted_issue_count = issues["issue_count"]
        if check_determinism:
            validate_determinism(validator, room, manifest_path, issues_path, seed)
    size_bytes = sum(path.stat().st_size for path in visible)
    summary = {
        "ok": validator.ok,
        "room": str(room),
        "visible_files": len(visible),
        "logical_documents": len(manifest["entries"]),
        "planted_issue_count": planted_issue_count,
        "public_only": public_only,
        "size_bytes": size_bytes,
        "counts": manifest["counts"],
        "checks": [asdict(check) for check in validator.checks],
    }
    return validator, summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--room", type=Path, required=True, help="explicit generated data-room path"
    )
    parser.add_argument("--manifest", type=Path, default=Path("synthetic/room_manifest.json"))
    parser.add_argument("--canonical", type=Path, default=Path("synthetic/canonical_dataset.json"))
    parser.add_argument(
        "--issues",
        type=Path,
        default=None,
        help="explicit sealed post-analysis issue key (required unless --public-only)",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="validate public room metadata without reading sealed planted-issue ground truth",
    )
    parser.add_argument(
        "--check-determinism",
        action="store_true",
        help="regenerate twice and compare manifests and every room file",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.public_only and args.check_determinism:
        print(
            "validation failed: deterministic regeneration requires sealed generator inputs; "
            "omit --check-determinism in public-only mode",
            file=sys.stderr,
        )
        return 1
    try:
        validator, summary = validate(
            args.room,
            args.manifest,
            args.canonical,
            args.issues,
            check_determinism=args.check_determinism,
            public_only=args.public_only,
            seed=args.seed,
        )
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        zipfile.BadZipFile,
        PdfReadError,
    ) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Synthetic room validation")
        for check in validator.checks:
            status = "PASS" if check.passed else "FAIL"
            print(f"[{status}] {check.name}: {check.detail}")
        print(
            f"Summary: {'PASS' if validator.ok else 'FAIL'} | "
            f"{len(validator.checks)} checks | {summary['size_bytes']} bytes"
        )
    return 0 if validator.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
