"""Non-executing content signatures, readability checks and cautious classification."""

from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from PIL import Image
from pypdf import PdfReader

from dd_engine.inventory.models import ContentInspection

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
DOCM_MIME = "application/vnd.ms-word.document.macroEnabled.12"
XLSM_MIME = "application/vnd.ms-excel.sheet.macroEnabled.12"
PPTM_MIME = "application/vnd.ms-powerpoint.presentation.macroEnabled.12"

_EXPECTED_TYPES: dict[str, frozenset[str]] = {
    ".csv": frozenset({"csv"}),
    ".docx": frozenset({"docx"}),
    ".docm": frozenset({"docm"}),
    ".jpeg": frozenset({"jpeg"}),
    ".jpg": frozenset({"jpeg"}),
    ".pdf": frozenset({"pdf"}),
    ".png": frozenset({"png"}),
    ".pptx": frozenset({"pptx"}),
    ".pptm": frozenset({"pptm"}),
    ".txt": frozenset({"text"}),
    ".xlsx": frozenset({"xlsx"}),
    ".xlsm": frozenset({"xlsm"}),
    ".zip": frozenset({"zip"}),
}
_ACTIVE_EXTENSIONS = frozenset(
    {".bat", ".cmd", ".docm", ".exe", ".js", ".ps1", ".py", ".vbs", ".xlsm"}
)


def _office_zip_type(names: set[str]) -> tuple[str, str] | None:
    if "word/document.xml" in names:
        if "word/vbaProject.bin" in names:
            return "docm", DOCM_MIME
        return "docx", DOCX_MIME
    if "xl/workbook.xml" in names:
        if "xl/vbaProject.bin" in names:
            return "xlsm", XLSM_MIME
        return "xlsx", XLSX_MIME
    if "ppt/presentation.xml" in names:
        if "ppt/vbaProject.bin" in names:
            return "pptm", PPTM_MIME
        return "pptx", PPTX_MIME
    return None


def _inspect_zip(handle: str | Path | BinaryIO) -> ContentInspection:
    try:
        with zipfile.ZipFile(handle) as archive:
            names = {name.replace("\\", "/") for name in archive.namelist()}
            office_type = _office_zip_type(names)
            if office_type is not None:
                detected_type, mime_type = office_type
                return ContentInspection(mime_type, detected_type, "readable")
            return ContentInspection("application/zip", "zip", "readable")
    except Exception as exc:
        return ContentInspection(
            "application/zip",
            "zip",
            "unreadable",
            error=f"invalid ZIP structure: {exc}",
        )


def _looks_like_csv(payload: bytes) -> bool:
    if not payload or b"\x00" in payload:
        return False
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False
    try:
        rows = list(csv.reader(io.StringIO(text[:65536])))[:20]
    except csv.Error:
        return False
    populated = [row for row in rows if any(value.strip() for value in row)]
    return len(populated) >= 2 and max((len(row) for row in populated), default=0) >= 2


def _basic_signature(payload: bytes) -> tuple[str | None, str]:
    if payload.startswith(b"%PDF-"):
        return PDF_MIME, "pdf"
    if payload.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpeg"
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if payload.startswith(b"PK\x03\x04") or payload.startswith(b"PK\x05\x06"):
        return "application/zip", "zip"
    if payload.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "application/x-ole-storage", "legacy_office"
    if payload.startswith(b"MZ"):
        return "application/vnd.microsoft.portable-executable", "executable"
    if _looks_like_csv(payload):
        return "text/csv", "csv"
    if payload and b"\x00" not in payload:
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            return "text/plain", "text"
    return "application/octet-stream", "binary"


def _inspect_pdf(handle: str | Path | BinaryIO) -> ContentInspection:
    try:
        reader = PdfReader(handle, strict=True)
        if reader.is_encrypted:
            return ContentInspection(PDF_MIME, "pdf", "encrypted", "encrypted PDF")
        len(reader.pages)
    except Exception as exc:
        return ContentInspection(PDF_MIME, "pdf", "unreadable", f"invalid PDF: {exc}")
    return ContentInspection(PDF_MIME, "pdf", "readable")


def _inspect_image(handle: str | Path | BinaryIO, detected_type: str) -> ContentInspection:
    mime_type = "image/jpeg" if detected_type == "jpeg" else "image/png"
    try:
        with Image.open(handle) as image:
            image.verify()
    except Exception as exc:
        return ContentInspection(
            mime_type,
            detected_type,
            "unreadable",
            f"invalid image: {exc}",
        )
    return ContentInspection(mime_type, detected_type, "readable")


def _finish_inspection(inspection: ContentInspection, filename: str) -> ContentInspection:
    suffix = PurePosixPath(filename.replace("\\", "/")).suffix.casefold()
    warnings = list(inspection.warnings)
    if suffix in _ACTIVE_EXTENSIONS or inspection.detected_type in {"docm", "pptm", "xlsm"}:
        warnings.append("active_content_not_executed")
    if inspection.detected_type in {"binary", "executable", "legacy_office"}:
        return ContentInspection(
            inspection.detected_mime_type,
            inspection.detected_type,
            "unsupported",
            inspection.error,
            tuple(dict.fromkeys((*warnings, "unsupported_content_type"))),
        )
    return ContentInspection(
        inspection.detected_mime_type,
        inspection.detected_type,
        inspection.readability_status,
        inspection.error,
        tuple(dict.fromkeys(warnings)),
    )


def inspect_file(path: Path) -> ContentInspection:
    """Inspect signatures and structure without executing or extracting content."""

    try:
        with path.open("rb") as handle:
            prefix = handle.read(65536)
    except OSError as exc:
        return ContentInspection(None, "not_inspected", "unreadable", f"cannot read file: {exc}")
    _, detected_type = _basic_signature(prefix)
    if detected_type == "pdf":
        inspection = _inspect_pdf(path)
    elif detected_type in {"jpeg", "png"}:
        inspection = _inspect_image(path, detected_type)
    elif detected_type == "zip":
        inspection = _inspect_zip(path)
    else:
        mime_type, final_type = _basic_signature(prefix)
        inspection = ContentInspection(mime_type, final_type, "readable")
    return _finish_inspection(inspection, path.name)


def inspect_bytes(payload: bytes, filename: str) -> ContentInspection:
    """Inspect one bounded in-memory archive member without executing it."""

    _, detected_type = _basic_signature(payload[:65536])
    if detected_type == "pdf":
        inspection = _inspect_pdf(io.BytesIO(payload))
    elif detected_type in {"jpeg", "png"}:
        inspection = _inspect_image(io.BytesIO(payload), detected_type)
    elif detected_type == "zip":
        inspection = _inspect_zip(io.BytesIO(payload))
    else:
        mime_type, final_type = _basic_signature(payload[:65536])
        inspection = ContentInspection(mime_type, final_type, "readable")
    return _finish_inspection(inspection, filename)


def extension_type_mismatch(extension: str, detected_type: str) -> bool | None:
    """Compare a content-derived type with a known extension, or return unknown."""

    expected = _EXPECTED_TYPES.get(extension.casefold())
    if expected is None or detected_type == "not_inspected":
        return None
    return detected_type not in expected


def classify_document(logical_path: str) -> tuple[str, float, str]:
    """Return a conservative filename/path-derived document class."""

    normalized = re.sub(r"[^a-z0-9]+", " ", logical_path.casefold())
    rules: tuple[tuple[tuple[str, ...], str, float], ...] = (
        (("questionnaire", "request list", "response summary"), "questionnaire", 0.85),
        (("statutory accounts", "management accounts"), "financial_statements", 0.85),
        (("trial balance",), "trial_balance", 0.9),
        (("aged debtors", "aged creditors", "working capital"), "working_capital_schedule", 0.85),
        (("loan", " hp "), "debt_document", 0.75),
        (("invoice",), "invoice", 0.85),
        (("employee", "contractor", "payslip", "work permit"), "workforce_record", 0.8),
        (("insurance",), "insurance_record", 0.85),
        (("board", "shareholder", "cap table", "constitution"), "corporate_governance", 0.8),
        (("registration", "licence", "cro search"), "registration_or_licence", 0.8),
        (("tax", "vat3", "paye", "ct return", "ros "), "tax_record", 0.8),
        (("contract", "agreement", "amendment", "lease"), "contract_or_agreement", 0.75),
        (("photo", "screenshot"), "image_record", 0.75),
    )
    padded = f" {normalized} "
    for needles, document_class, confidence in rules:
        for needle in needles:
            if needle in padded:
                return document_class, confidence, f"path keyword: {needle.strip()}"
    return "unknown", 0.0, "no deterministic filename/path rule matched"


def classify_workstream(logical_path: str) -> tuple[str, float, str]:
    """Return a likely workstream derived only from path tokens."""

    normalized = logical_path.replace("\\", "/").casefold()
    token_rules: tuple[tuple[tuple[str, ...], str], ...] = (
        (("/vat", "tax/", "paye", "/ct_", "/ros"), "tax"),
        (("hosting", "cyber", "security", "recovery"), "it"),
        (("customer", "revenue", "pipeline"), "commercial"),
        (("employee", "contractor", "payslip", "hr_", "work permit"), "operational_management"),
    )
    padded = f"/{normalized}"
    for needles, workstream in token_rules:
        for needle in needles:
            if needle in padded:
                return workstream, 0.75, f"path keyword: {needle.strip('/')}"
    first = normalized.removeprefix("zip://").split("/", 1)[0]
    folder_rules = {
        "financial": "financial",
        "legal": "legal_contractual",
        "tax": "tax",
    }
    if first in folder_rules:
        return folder_rules[first], 0.7, f"top-level folder: {first}"
    return "unknown", 0.0, "no deterministic path rule matched"
