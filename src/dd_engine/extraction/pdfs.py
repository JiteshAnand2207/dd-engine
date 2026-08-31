"""Native PDF text extraction, local rendering, optional OCR and vision routing."""

from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import pypdfium2 as pdfium
from PIL import Image
from pypdf import PdfReader

from dd_engine.artifacts import atomic_write_bytes
from dd_engine.extraction.models import JsonObject, SourceExtraction, make_unit


@dataclass(frozen=True, slots=True)
class OCRCapability:
    """Observed optional local OCR capability included in cache identity."""

    available: bool
    command: str | None
    version: str | None

    def as_dict(self) -> JsonObject:
        return {
            "available": self.available,
            "command_name": Path(self.command).name if self.command else None,
            "version": self.version,
        }


def detect_ocr_capability(enabled: bool) -> OCRCapability:
    """Detect Tesseract without making it a required system dependency."""

    if not enabled:
        return OCRCapability(False, None, "disabled_by_configuration")
    command = shutil.which("tesseract")
    if command is None:
        return OCRCapability(False, None, "not_detected")
    try:
        result = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        version = (result.stdout or result.stderr).splitlines()[0].strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return OCRCapability(False, None, f"detection_failed:{exc}")
    return OCRCapability(result.returncode == 0, command, version or "unknown")


def _normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def _meaningful_characters(value: str) -> int:
    return len("".join(value.split()))


def _image_suffix(name: str) -> str:
    suffix = PurePosixPath(name).suffix.casefold()
    return suffix if suffix in {".bmp", ".gif", ".jp2", ".jpeg", ".jpg", ".png", ".tif", ".tiff"} else ".bin"


def _render_page(pdf: Any, page_index: int, scale: float) -> tuple[bytes, int, int]:
    page = pdf[page_index]
    try:
        bitmap = page.render(scale=scale, rotation=0)
        try:
            image = bitmap.to_pil()
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue(), image.width, image.height
        finally:
            bitmap.close()
    finally:
        page.close()


def _run_ocr(capability: OCRCapability, image_path: Path) -> tuple[str | None, str | None]:
    if not capability.available or capability.command is None:
        return None, None
    try:
        result = subprocess.run(
            [capability.command, str(image_path), "stdout", "--psm", "6"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"optional local OCR failed: {exc}"
    if result.returncode != 0:
        diagnostic = (result.stderr or "unknown Tesseract error").strip().splitlines()[0]
        return None, f"optional local OCR exited {result.returncode}: {diagnostic}"
    return _normalize_text(result.stdout), None


def _image_metadata(payload: bytes) -> JsonObject:
    metadata: JsonObject = {"size_bytes": len(payload)}
    try:
        with Image.open(io.BytesIO(payload)) as image:
            metadata.update(
                {
                    "format": image.format,
                    "height_pixels": image.height,
                    "mode": image.mode,
                    "width_pixels": image.width,
                }
            )
    except Exception as exc:
        metadata["metadata_warning"] = f"embedded image metadata unreadable: {exc}"
    return metadata


def extract_pdf(
    *,
    payload: bytes,
    source: JsonObject,
    run_id: str,
    run_path: Path,
    config_namespace: str,
    min_native_characters: int,
    render_scale: float,
    ocr: OCRCapability,
) -> SourceExtraction:
    """Extract page-addressed PDF evidence and queue only unresolved visual pages."""

    reader = PdfReader(io.BytesIO(payload), strict=False)
    if reader.is_encrypted:
        raise ValueError("encrypted PDF cannot be extracted without a supplied password")
    page_count = len(reader.pages)
    pdfium_document = pdfium.PdfDocument(payload)
    units: list[JsonObject] = []
    tasks: list[JsonObject] = []
    warnings: list[str] = []
    page_failures: list[JsonObject] = []
    metrics: JsonObject = {
        "pdf_embedded_images": 0,
        "pdf_pages_failed": 0,
        "pdf_pages_image_only": 0,
        "pdf_pages_low_text": 0,
        "pdf_pages_native_text": 0,
        "pdf_pages_ocr": 0,
        "pdf_pages_total": page_count,
        "pdf_pages_vision_queued": 0,
    }
    try:
        try:
            page_labels = list(reader.page_labels)
        except Exception:
            page_labels = []
        for page_index, page in enumerate(reader.pages):
            page_number = page_index + 1
            page_label = page_labels[page_index] if page_index < len(page_labels) else None
            try:
                native_text = _normalize_text(page.extract_text() or "")
            except Exception as exc:
                native_text = ""
                page_failures.append(
                    {"page_number": page_number, "reason": f"native text extraction failed: {exc}"}
                )
            native_characters = _meaningful_characters(native_text)
            if native_characters == 0:
                classification = "image_only"
                metrics["pdf_pages_image_only"] += 1
            elif native_characters < min_native_characters:
                classification = "low_text"
                metrics["pdf_pages_low_text"] += 1
            else:
                classification = "native_text"
                metrics["pdf_pages_native_text"] += 1

            extraction_method = "pypdf_native_text"
            confidence = 0.98
            final_text = native_text
            unit_warnings: list[str] = []
            limitation = None
            if classification != "native_text":
                relative_render = (
                    Path("extracts")
                    / "rendered_pages"
                    / config_namespace
                    / str(source["source_id"])
                    / f"page-{page_number:04d}.png"
                )
                render_path = run_path / relative_render
                try:
                    rendered, width, height = _render_page(
                        pdfium_document, page_index, render_scale
                    )
                    atomic_write_bytes(render_path, rendered)
                    rendered_checksum = hashlib.sha256(rendered).hexdigest()
                except Exception as exc:
                    page_failures.append(
                        {"page_number": page_number, "reason": f"local PDF rendering failed: {exc}"}
                    )
                    metrics["pdf_pages_failed"] += 1
                    continue

                ocr_text, ocr_error = _run_ocr(ocr, render_path)
                if ocr_error:
                    unit_warnings.append(ocr_error)
                    warnings.append(ocr_error)
                if ocr_text and _meaningful_characters(ocr_text) >= min_native_characters:
                    final_text = ocr_text
                    extraction_method = "tesseract_local_ocr"
                    confidence = 0.75
                    metrics["pdf_pages_ocr"] += 1
                    limitation = "text was recovered by optional local OCR from a rendered page"
                else:
                    extraction_method = "pypdf_page_inspection"
                    confidence = 0.2 if classification == "image_only" else 0.4
                    limitation = "visual page content remains unreviewed and is queued for vision"
                    unit_warnings.append(f"pdf_page_{classification}")
                    task: JsonObject = {
                        "asset": {
                            "height_pixels": height,
                            "mime_type": "image/png",
                            "path": relative_render.as_posix(),
                            "sha256": rendered_checksum,
                            "width_pixels": width,
                        },
                        "limitation": limitation,
                        "locator": {
                            "page_label": page_label,
                            "page_number": page_number,
                            "type": "pdf_page",
                        },
                        "model_result": None,
                        "relative_path": source["relative_path"],
                        "requested_route": "codex_or_claude_vision_review",
                        "run_id": run_id,
                        "source_checksum": source["sha256"],
                        "source_id": source["source_id"],
                        "status": "pending",
                        "task_id": f"VISION-{source['source_id']}-PAGE-{page_number:04d}",
                        "untrusted_source_data": True,
                    }
                    tasks.append(task)
                    metrics["pdf_pages_vision_queued"] += 1

            units.append(
                make_unit(
                    run_id=run_id,
                    source=source,
                    ordinal=len(units) + 1,
                    unit_type="pdf_page",
                    locator={
                        "page_label": page_label,
                        "page_number": page_number,
                        "type": "pdf_page",
                    },
                    extraction_method=extraction_method,
                    confidence=confidence,
                    content={
                        "native_character_count": native_characters,
                        "page_classification": classification,
                        "text": final_text,
                    },
                    warnings=unit_warnings,
                    limitation=limitation,
                )
            )

            try:
                page_images = list(page.images)
            except Exception as exc:
                page_images = []
                message = f"page {page_number} embedded images could not be extracted: {exc}"
                warnings.append(message)
            for image_number, image_file in enumerate(page_images, start=1):
                image_payload = bytes(image_file.data)
                suffix = _image_suffix(str(image_file.name))
                relative_asset = (
                    Path("extracts")
                    / "cache"
                    / "assets"
                    / config_namespace
                    / str(source["source_id"])
                    / f"pdf-page-{page_number:04d}-image-{image_number:04d}{suffix}"
                )
                atomic_write_bytes(run_path / relative_asset, image_payload)
                asset_checksum = hashlib.sha256(image_payload).hexdigest()
                content = _image_metadata(image_payload)
                content.update(
                    {
                        "asset_checksum": asset_checksum,
                        "asset_path": relative_asset.as_posix(),
                        "original_resource_name": str(image_file.name),
                    }
                )
                units.append(
                    make_unit(
                        run_id=run_id,
                        source=source,
                        ordinal=len(units) + 1,
                        unit_type="pdf_embedded_image",
                        locator={
                            "image_number": image_number,
                            "page_label": page_label,
                            "page_number": page_number,
                            "type": "pdf_image",
                        },
                        extraction_method="pypdf_embedded_image",
                        confidence=0.95,
                        content=content,
                        warnings=(
                            [str(content["metadata_warning"])]
                            if "metadata_warning" in content
                            else []
                        ),
                    )
                )
                metrics["pdf_embedded_images"] += 1
    finally:
        pdfium_document.close()

    metrics["pdf_page_failures"] = page_failures
    metrics["pdf_pages_failed"] = len({item["page_number"] for item in page_failures})
    extracted_pages = page_count - int(metrics["pdf_pages_failed"])
    native_or_ocr_pages = int(metrics["pdf_pages_native_text"]) + int(metrics["pdf_pages_ocr"])
    if extracted_pages == 0:
        status = "failed"
        failure_reason = "no PDF page could be extracted or rendered"
    elif tasks and native_or_ocr_pages == 0 and not page_failures:
        status = "queued_for_vision"
        failure_reason = None
    elif tasks or page_failures:
        status = "partially_extracted"
        failure_reason = None
    else:
        status = "successfully_extracted"
        failure_reason = None

    if int(metrics["pdf_pages_ocr"]):
        primary_method = "pypdf_with_pdfium_and_optional_ocr"
    elif tasks:
        primary_method = "pypdf_with_pdfium_vision_routing"
    else:
        primary_method = "pypdf_native_text"
    limitation = None
    if tasks:
        limitation = f"{len(tasks)} page(s) await vision review; no model result was fabricated"
    elif page_failures:
        limitation = f"{len(page_failures)} PDF page extraction/rendering failure(s) recorded"
    return SourceExtraction(
        status=status,
        primary_method=primary_method,
        units=units,
        vision_tasks=tasks,
        warnings=list(dict.fromkeys(warnings)),
        limitation=limitation,
        failure_reason=failure_reason,
        metrics=metrics,
    )
