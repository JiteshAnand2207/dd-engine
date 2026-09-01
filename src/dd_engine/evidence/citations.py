"""Format-native citation, claim coverage and duplicate-corroboration validation."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from openpyxl.utils.cell import range_boundaries

from dd_engine.artifacts import load_json
from dd_engine.errors import EvidenceError
from dd_engine.evidence.calculations import recompute_calculation
from dd_engine.evidence.models import MATERIAL_CLAIM_LEVELS, JsonObject
from dd_engine.evidence.store import load_record_sets, validate_record_sets
from dd_engine.runs import load_manifest


def _problem(code: str, message: str) -> JsonObject:
    return {"code": code, "message": message}


def _record_id(record: Mapping[str, Any], field: str, fallback: str) -> str:
    value = record.get(field)
    return str(value) if isinstance(value, str) and value else fallback


class CitationValidator:
    """Resolve citations only against the locked register and extraction artifacts."""

    def __init__(self, run: str | Path) -> None:
        self.run_path, self.manifest = load_manifest(run)
        self.run_id = str(self.manifest["run_id"])
        register = load_json(self.run_path / "source_register" / "source_register.json")
        extraction = load_json(self.run_path / "extracts" / "extraction_manifest.json")
        raw_sources = register.get("sources")
        if not isinstance(raw_sources, list):
            raise EvidenceError("source register has no source list")
        self.sources: dict[str, JsonObject] = {
            str(item["source_id"]): item
            for item in raw_sources
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }
        raw_extractions = extraction.get("sources")
        if not isinstance(raw_extractions, list):
            raise EvidenceError("extraction manifest has no source list")
        self.extractions: dict[str, JsonObject] = {
            str(item["source_id"]): item
            for item in raw_extractions
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }
        self.units_by_source: dict[str, list[JsonObject]] = defaultdict(list)
        self.units_by_id: dict[str, JsonObject] = {}
        self._load_units()

    def _load_units(self) -> None:
        path = self.run_path / "extracts" / "extracted_units.jsonl"
        try:
            with path.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise EvidenceError(
                            f"extracted unit line {line_number} is not a JSON object"
                        )
                    if value.get("run_id") != self.run_id:
                        raise EvidenceError(
                            f"extracted unit line {line_number} belongs to another run"
                        )
                    source_id = value.get("source_id")
                    unit_id = value.get("unit_id")
                    if not isinstance(source_id, str) or not isinstance(unit_id, str):
                        raise EvidenceError(
                            f"extracted unit line {line_number} has no stable source/unit ID"
                        )
                    self.units_by_source[source_id].append(value)
                    self.units_by_id[unit_id] = value
        except EvidenceError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise EvidenceError(f"cannot read extracted units: {exc}") from exc

    @staticmethod
    def _locator(unit: JsonObject) -> JsonObject:
        value = unit.get("locator")
        return value if isinstance(value, dict) else {}

    def _pdf_units(
        self, source: JsonObject, locator: JsonObject
    ) -> tuple[list[JsonObject], list[JsonObject]]:
        errors: list[JsonObject] = []
        if source.get("detected_type") != "pdf" or locator.get("type") != "pdf_page":
            return [], [
                _problem(
                    "invalid_pdf_locator",
                    "PDF citations require type=pdf_page and a PDF source",
                )
            ]
        page = locator.get("page_number")
        if type(page) is not int or page < 1:
            return [], [_problem("invalid_pdf_page", "PDF page_number must be a positive integer")]
        matches = [
            unit
            for unit in self.units_by_source.get(str(source["source_id"]), [])
            if self._locator(unit).get("type") == "pdf_page"
            and self._locator(unit).get("page_number") == page
        ]
        if not matches:
            errors.append(
                _problem("pdf_page_not_found", f"PDF page {page} does not exist in extraction")
            )
        return matches, errors

    def _spreadsheet_units(
        self, source: JsonObject, locator: JsonObject
    ) -> tuple[list[JsonObject], list[JsonObject]]:
        if source.get("detected_type") != "xlsx" or locator.get("type") != "spreadsheet_cell":
            return [], [
                _problem(
                    "invalid_spreadsheet_locator",
                    "XLSX citations require type=spreadsheet_cell and an XLSX source",
                )
            ]
        sheet = locator.get("sheet")
        coordinate = locator.get("range") or locator.get("cell")
        if not isinstance(sheet, str) or not sheet or not isinstance(coordinate, str):
            return [], [
                _problem(
                    "invalid_spreadsheet_address",
                    "spreadsheet locator requires sheet and cell/range",
                )
            ]
        try:
            min_col, min_row, max_col, max_row = range_boundaries(coordinate.replace("$", ""))
        except (TypeError, ValueError):
            return [], [
                _problem(
                    "invalid_spreadsheet_range", f"spreadsheet range is malformed: {coordinate!r}"
                )
            ]
        extraction = self.extractions.get(str(source["source_id"]), {})
        metrics = extraction.get("metrics") if isinstance(extraction, dict) else None
        coverage = metrics.get("spreadsheet_sheet_coverage") if isinstance(metrics, dict) else None
        sheets = [
            item for item in coverage or [] if isinstance(item, dict) and item.get("sheet") == sheet
        ]
        if not sheets:
            return [], [
                _problem(
                    "spreadsheet_sheet_not_found", f"spreadsheet sheet does not exist: {sheet!r}"
                )
            ]
        sheet_record = sheets[0]
        if max_col > int(sheet_record.get("max_column", 0)) or max_row > int(
            sheet_record.get("max_row", 0)
        ):
            return [], [
                _problem(
                    "spreadsheet_range_not_found",
                    f"spreadsheet range {coordinate!r} exceeds the extracted sheet dimensions",
                )
            ]
        matches: list[JsonObject] = []
        for unit in self.units_by_source.get(str(source["source_id"]), []):
            unit_locator = self._locator(unit)
            if unit_locator.get("type") != "spreadsheet_cell" or unit_locator.get("sheet") != sheet:
                continue
            cell = unit_locator.get("cell")
            if not isinstance(cell, str):
                continue
            try:
                cell_col, cell_row, _, _ = range_boundaries(cell.replace("$", ""))
            except (TypeError, ValueError):
                continue
            if min_col <= cell_col <= max_col and min_row <= cell_row <= max_row:
                matches.append(unit)
        if not matches:
            return [], [
                _problem(
                    "spreadsheet_range_has_no_extracted_values",
                    f"spreadsheet range {coordinate!r} exists but contains no extracted value",
                )
            ]
        workbook = locator.get("workbook")
        if workbook is not None and workbook != source.get("relative_path"):
            return matches, [
                _problem(
                    "spreadsheet_workbook_mismatch",
                    "spreadsheet locator workbook does not match the registered source path",
                )
            ]
        return matches, []

    def _docx_units(
        self, source: JsonObject, locator: JsonObject
    ) -> tuple[list[JsonObject], list[JsonObject]]:
        if source.get("detected_type") != "docx":
            return [], [_problem("invalid_docx_source", "DOCX locator requires a DOCX source")]
        locator_type = locator.get("type")
        units = self.units_by_source.get(str(source["source_id"]), [])
        if locator_type == "docx_paragraph":
            paragraph = locator.get("paragraph_index")
            if type(paragraph) is not int or paragraph < 1:
                return [], [
                    _problem(
                        "invalid_docx_paragraph", "DOCX paragraph_index must be a positive integer"
                    )
                ]
            matches = [
                unit
                for unit in units
                if self._locator(unit).get("type") == "docx_paragraph"
                and self._locator(unit).get("paragraph_index") == paragraph
            ]
            return (
                (matches, [])
                if matches
                else (
                    [],
                    [
                        _problem(
                            "docx_paragraph_not_found",
                            f"DOCX paragraph {paragraph} does not exist in extraction",
                        )
                    ],
                )
            )
        if locator_type == "docx_table_cell":
            table = locator.get("table_index")
            row = locator.get("row_index")
            cell = locator.get("cell_index")
            if type(table) is not int or table < 1 or type(row) is not int or row < 1:
                return [], [
                    _problem(
                        "invalid_docx_table_locator",
                        "DOCX table locator requires positive table_index and row_index",
                    )
                ]
            matches = [
                unit
                for unit in units
                if self._locator(unit).get("type") == "docx_table_cell"
                and self._locator(unit).get("table_index") == table
                and self._locator(unit).get("row_index") == row
                and (cell is None or self._locator(unit).get("cell_index") == cell)
            ]
            return (
                (matches, [])
                if matches
                else (
                    [],
                    [
                        _problem(
                            "docx_table_locator_not_found",
                            f"DOCX table {table}, row {row}, cell {cell!r} does not exist",
                        )
                    ],
                )
            )
        return [], [
            _problem(
                "invalid_docx_locator",
                "DOCX citations require type=docx_paragraph or docx_table_cell",
            )
        ]

    def _csv_units(
        self, source: JsonObject, locator: JsonObject
    ) -> tuple[list[JsonObject], list[JsonObject]]:
        if source.get("detected_type") != "csv" or locator.get("type") != "csv_cell":
            return [], [
                _problem(
                    "invalid_csv_locator", "CSV citations require type=csv_cell and a CSV source"
                )
            ]
        row = locator.get("row_index")
        column = locator.get("column_index")
        if type(row) is not int or row < 1 or type(column) is not int or column < 1:
            return [], [
                _problem(
                    "invalid_csv_address",
                    "CSV locator requires positive row_index and column_index",
                )
            ]
        matches = [
            unit
            for unit in self.units_by_source.get(str(source["source_id"]), [])
            if self._locator(unit).get("type") == "csv_cell"
            and self._locator(unit).get("row_index") == row
            and self._locator(unit).get("column_index") == column
        ]
        return (
            (matches, [])
            if matches
            else (
                [],
                [_problem("csv_cell_not_found", f"CSV row {row}, column {column} does not exist")],
            )
        )

    def _image_units(
        self, source: JsonObject, locator: JsonObject
    ) -> tuple[list[JsonObject], list[JsonObject]]:
        if (
            source.get("detected_type") not in {"jpeg", "png", "tiff"}
            or locator.get("type") != "image"
        ):
            return [], [
                _problem(
                    "invalid_image_locator",
                    "standalone image citations require type=image and an image source",
                )
            ]
        image_number = locator.get("image_number")
        region = locator.get("region")
        if type(image_number) is not int or image_number < 1 or not isinstance(region, dict):
            return [], [
                _problem(
                    "invalid_image_address",
                    "image locator requires a positive image_number and "
                    "intrinsic-coordinate region",
                )
            ]
        units = [
            unit
            for unit in self.units_by_source.get(str(source["source_id"]), [])
            if self._locator(unit).get("type") == "image"
            and self._locator(unit).get("image_number") == image_number
        ]
        if not units:
            return [], [_problem("image_not_found", f"image {image_number} does not exist")]
        values = [region.get(key) for key in ("x", "y", "width", "height")]
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values
        ):
            return units, [
                _problem(
                    "invalid_image_region",
                    "image region x/y/width/height must be non-negative integers",
                )
            ]
        x_value, y_value, width_value, height_value = values
        assert isinstance(x_value, int)
        assert isinstance(y_value, int)
        assert isinstance(width_value, int)
        assert isinstance(height_value, int)
        x, y, width, height = x_value, y_value, width_value, height_value
        content = units[0].get("content")
        max_width = content.get("width_pixels") if isinstance(content, dict) else None
        max_height = content.get("height_pixels") if isinstance(content, dict) else None
        if (
            width == 0
            or height == 0
            or not isinstance(max_width, int)
            or not isinstance(max_height, int)
            or x + width > max_width
            or y + height > max_height
        ):
            return units, [
                _problem(
                    "image_region_out_of_bounds",
                    "image region does not fit within the intrinsic source dimensions",
                )
            ]
        return units, []

    def _resolve_locator(
        self, source: JsonObject, locator: JsonObject
    ) -> tuple[list[JsonObject], list[JsonObject]]:
        detected_type = source.get("detected_type")
        if detected_type == "pdf":
            return self._pdf_units(source, locator)
        if detected_type == "xlsx":
            return self._spreadsheet_units(source, locator)
        if detected_type == "docx":
            return self._docx_units(source, locator)
        if detected_type == "csv":
            return self._csv_units(source, locator)
        if detected_type in {"jpeg", "png", "tiff"}:
            return self._image_units(source, locator)
        return [], [
            _problem(
                "unsupported_citation_source_type",
                f"source type {detected_type!r} has no Phase 7 citation resolver",
            )
        ]

    @staticmethod
    def _source_values(units: list[JsonObject]) -> list[object]:
        values: list[object] = []
        for unit in units:
            content = unit.get("content")
            if not isinstance(content, dict):
                continue
            values.append(content)
            for key in ("text", "value", "source_value", "cached_value"):
                if key in content:
                    values.append(content[key])
        return values

    def _validate_content(
        self, citation: Mapping[str, Any], units: list[JsonObject]
    ) -> list[JsonObject]:
        errors: list[JsonObject] = []
        unit_ids = citation.get("extracted_unit_ids", [])
        if isinstance(unit_ids, list | tuple):
            matching_ids = {str(unit.get("unit_id")) for unit in units}
            for unit_id in unit_ids:
                value = str(unit_id)
                known = self.units_by_id.get(value)
                if known is None:
                    errors.append(
                        _problem(
                            "extracted_unit_not_found", f"extracted unit does not exist: {value}"
                        )
                    )
                elif value not in matching_ids:
                    errors.append(
                        _problem(
                            "extracted_unit_locator_mismatch",
                            f"extracted unit {value} is outside the cited locator",
                        )
                    )
        source_values = self._source_values(units)
        extracted_text = citation.get("extracted_text")
        if (
            isinstance(extracted_text, str)
            and extracted_text
            and not any(
                isinstance(value, str) and extracted_text in value for value in source_values
            )
        ):
            errors.append(
                _problem(
                    "extracted_text_mismatch",
                    "extracted_text is not an exact span of the resolved source content",
                )
            )
        if citation.get("extracted_value") is not None:
            extracted_value = citation.get("extracted_value")
            if extracted_value not in source_values:
                errors.append(
                    _problem(
                        "extracted_value_mismatch",
                        "extracted_value does not equal a value at the resolved source locator",
                    )
                )
        return errors

    def _validate_one(
        self,
        *,
        citation: Mapping[str, Any],
        citation_id: str,
        citation_kind: str,
        claim_id: str | None,
        locator_field: str,
    ) -> JsonObject:
        errors: list[JsonObject] = []
        warnings: list[JsonObject] = []
        source_id = citation.get("source_id")
        source = self.sources.get(str(source_id)) if isinstance(source_id, str) else None
        if source is None:
            errors.append(
                _problem("source_id_not_found", f"source ID does not exist: {source_id!r}")
            )
            return {
                "citation_id": citation_id,
                "citation_kind": citation_kind,
                "claim_id": claim_id,
                "errors": errors,
                "independence_key": None,
                "locator": citation.get(locator_field),
                "source_id": source_id,
                "valid": False,
                "warnings": warnings,
            }

        registered_checksum = str(source.get("sha256"))
        supplied_checksum = citation.get("source_checksum")
        if supplied_checksum != registered_checksum:
            errors.append(
                _problem(
                    "source_checksum_mismatch",
                    f"citation checksum does not match register for {source_id}",
                )
            )
        extraction = self.extractions.get(str(source_id))
        if extraction is None or extraction.get("source_checksum") != registered_checksum:
            errors.append(
                _problem(
                    "extraction_source_checksum_mismatch",
                    f"extraction ledger does not match the registered checksum for {source_id}",
                )
            )

        registered_version = str(source.get("probable_version_status", "undetermined"))
        cited_version = citation.get("source_version_status")
        if cited_version != registered_version:
            errors.append(
                _problem(
                    "source_version_status_mismatch",
                    f"citation version status {cited_version!r} does not match "
                    f"{registered_version!r}",
                )
            )
        if registered_version == "potentially_superseded":
            if citation.get("supersession_acknowledged") is not True:
                errors.append(
                    _problem(
                        "silently_superseded_source",
                        "citation uses a potentially superseded source without explicit "
                        "acknowledgement",
                    )
                )
            else:
                warnings.append(
                    _problem(
                        "superseded_source_acknowledged",
                        "citation intentionally uses a potentially superseded source",
                    )
                )

        locator = citation.get(locator_field)
        matched_units: list[JsonObject] = []
        if not isinstance(locator, dict):
            errors.append(_problem("invalid_locator", "citation locator must be an object"))
        else:
            matched_units, locator_errors = self._resolve_locator(source, locator)
            errors.extend(locator_errors)
        for unit in matched_units:
            if unit.get("source_checksum") != registered_checksum:
                errors.append(
                    _problem(
                        "unit_source_checksum_mismatch",
                        f"extracted unit {unit.get('unit_id')} has a mismatched source checksum",
                    )
                )
        if citation_kind == "evidence" and matched_units:
            errors.extend(self._validate_content(citation, matched_units))
            extraction_confidence = citation.get("extraction_confidence")
            maximum_confidence = max(float(unit.get("confidence", 0)) for unit in matched_units)
            if (
                isinstance(extraction_confidence, int | float)
                and float(extraction_confidence) > maximum_confidence
            ):
                errors.append(
                    _problem(
                        "extraction_confidence_overstated",
                        "evidence confidence exceeds the resolved extraction unit confidence",
                    )
                )
        if citation_kind == "calculation_input" and matched_units:
            pseudo = {
                "extracted_value": citation.get("reported_value"),
                "extracted_text": citation.get("reported_text"),
                "extracted_unit_ids": citation.get("extracted_unit_ids", []),
            }
            errors.extend(self._validate_content(pseudo, matched_units))

        duplicate_group = source.get("duplicate_group")
        independence_key = (
            f"duplicate_group:{duplicate_group}"
            if duplicate_group
            else f"sha256:{registered_checksum}"
        )
        return {
            "citation_id": citation_id,
            "citation_kind": citation_kind,
            "claim_id": claim_id,
            "errors": errors,
            "independence_key": independence_key,
            "locator": locator,
            "source_id": source_id,
            "valid": not errors,
            "warnings": warnings,
        }

    def validate_reference(
        self,
        *,
        source_id: str,
        source_checksum: str,
        locator: Mapping[str, Any],
        extracted_text: str | None = None,
        extracted_value: object = None,
    ) -> JsonObject:
        """Validate one standalone source reference for an audit or disposition ledger."""

        source = self.sources.get(source_id)
        version = (
            str(source.get("probable_version_status", "undetermined"))
            if source is not None
            else "undetermined"
        )
        citation: JsonObject = {
            "exact_locator": dict(locator),
            "extracted_text": extracted_text,
            "extracted_unit_ids": [],
            "extracted_value": extracted_value,
            "extraction_confidence": 0,
            "source_checksum": source_checksum,
            "source_id": source_id,
            "source_version_status": version,
            "supersession_acknowledged": version == "potentially_superseded",
        }
        return self._validate_one(
            citation=citation,
            citation_id=f"standalone:{source_id}",
            citation_kind="evidence",
            claim_id=None,
            locator_field="exact_locator",
        )

    @staticmethod
    def _reference_error(
        record_type: str, record_id: str, field: str, missing_id: str
    ) -> JsonObject:
        return {
            "code": "dangling_record_reference",
            "field": field,
            "message": f"{field} references unknown ID {missing_id}",
            "record_id": record_id,
            "record_type": record_type,
        }

    def validate(self, record_sets: Mapping[str, list[JsonObject]]) -> JsonObject:
        """Validate complete record sets and report every failure in one auditable result."""

        record_errors = validate_record_sets(record_sets, self.run_id)
        claims = record_sets.get("claims", [])
        evidence_records = record_sets.get("evidence", [])
        calculations = record_sets.get("calculations", [])
        contradictions = record_sets.get("contradictions", [])
        gaps = record_sets.get("gaps", [])
        issues = record_sets.get("issues", [])

        claim_by_id = {
            str(item.get("claim_id")): item
            for item in claims
            if isinstance(item.get("claim_id"), str)
        }
        evidence_by_id = {
            str(item.get("evidence_id")): item
            for item in evidence_records
            if isinstance(item.get("evidence_id"), str)
        }
        calculation_by_id = {
            str(item.get("calculation_id")): item
            for item in calculations
            if isinstance(item.get("calculation_id"), str)
        }

        citation_results: list[JsonObject] = []
        reference_errors: list[JsonObject] = []
        for index, evidence in enumerate(evidence_records, start=1):
            evidence_id = _record_id(evidence, "evidence_id", f"evidence-line-{index}")
            claim_id = str(evidence.get("claim_id"))
            if claim_id not in claim_by_id:
                reference_errors.append(
                    self._reference_error("evidence", evidence_id, "claim_id", claim_id)
                )
            citation_results.append(
                self._validate_one(
                    citation=evidence,
                    citation_id=evidence_id,
                    citation_kind="evidence",
                    claim_id=claim_id,
                    locator_field="exact_locator",
                )
            )

        calculation_results: list[JsonObject] = []
        for index, calculation in enumerate(calculations, start=1):
            calculation_id = _record_id(calculation, "calculation_id", f"calculation-line-{index}")
            input_results: list[JsonObject] = []
            raw_inputs = calculation.get("source_inputs")
            inputs = raw_inputs if isinstance(raw_inputs, list | tuple) else []
            for input_index, source_input in enumerate(inputs, start=1):
                if not isinstance(source_input, dict) or source_input.get("missing") is True:
                    continue
                input_id = str(source_input.get("input_id", f"input-{input_index}"))
                input_results.append(
                    self._validate_one(
                        citation=source_input,
                        citation_id=f"{calculation_id}:{input_id}",
                        citation_kind="calculation_input",
                        claim_id=None,
                        locator_field="locator",
                    )
                )
            for claim_id in calculation.get("claim_ids", []):
                if str(claim_id) not in claim_by_id:
                    reference_errors.append(
                        self._reference_error(
                            "calculations", calculation_id, "claim_ids", str(claim_id)
                        )
                    )
            recomputation = recompute_calculation(calculation)
            calculation_results.append(
                {
                    "calculation_id": calculation_id,
                    "input_citations": input_results,
                    "recomputation": recomputation,
                    "valid": all(item["valid"] for item in input_results)
                    and not recomputation["errors"],
                }
            )
            citation_results.extend(input_results)

        valid_supporting: dict[str, list[JsonObject]] = defaultdict(list)
        for result, evidence in zip(
            citation_results[: len(evidence_records)], evidence_records, strict=False
        ):
            if result["valid"] and evidence.get("relationship") == "supporting":
                valid_supporting[str(evidence.get("claim_id"))].append(result)

        duplicate_exclusions: list[JsonObject] = []
        claim_results: list[JsonObject] = []
        for index, claim in enumerate(claims, start=1):
            claim_id = _record_id(claim, "claim_id", f"claim-line-{index}")
            supporting = valid_supporting.get(claim_id, [])
            by_independence: dict[str, list[str]] = defaultdict(list)
            for item in supporting:
                key = item.get("independence_key")
                if isinstance(key, str):
                    by_independence[key].append(str(item["citation_id"]))
            for key, evidence_ids in by_independence.items():
                if len(evidence_ids) > 1:
                    duplicate_exclusions.append(
                        {
                            "claim_id": claim_id,
                            "excluded_evidence_ids": evidence_ids[1:],
                            "independence_key": key,
                            "retained_evidence_id": evidence_ids[0],
                        }
                    )
            independent_count = len(by_independence)
            required = claim.get("required_independent_sources", 1)
            required_count = int(required) if type(required) is int and required >= 1 else 1
            material = (
                claim.get("materiality") in MATERIAL_CLAIM_LEVELS
                and claim.get("status") != "withdrawn"
            )
            errors: list[JsonObject] = []
            if material and not supporting:
                errors.append(
                    _problem(
                        "unsupported_material_claim",
                        "material claim has no valid supporting evidence citation",
                    )
                )
            if material and independent_count < required_count:
                errors.append(
                    _problem(
                        "insufficient_independent_sources",
                        f"material claim requires {required_count} independent source(s), "
                        f"found {independent_count}",
                    )
                )
            claim_results.append(
                {
                    "claim_id": claim_id,
                    "errors": errors,
                    "independent_supporting_source_count": independent_count,
                    "material": material,
                    "required_independent_sources": required_count,
                    "supporting_citation_count": len(supporting),
                    "valid": not errors,
                }
            )

        for index, contradiction in enumerate(contradictions, start=1):
            contradiction_id = _record_id(
                contradiction, "contradiction_id", f"contradiction-line-{index}"
            )
            for claim_id in contradiction.get("conflicting_claims", []):
                if str(claim_id) not in claim_by_id:
                    reference_errors.append(
                        self._reference_error(
                            "contradictions",
                            contradiction_id,
                            "conflicting_claims",
                            str(claim_id),
                        )
                    )
            for source_id in contradiction.get("source_ids", []):
                if str(source_id) not in self.sources:
                    reference_errors.append(
                        self._reference_error(
                            "contradictions", contradiction_id, "source_ids", str(source_id)
                        )
                    )

        for index, gap in enumerate(gaps, start=1):
            gap_id = _record_id(gap, "gap_id", f"gap-line-{index}")
            for source_id in gap.get("source_ids", []):
                if str(source_id) not in self.sources:
                    reference_errors.append(
                        self._reference_error("gaps", gap_id, "source_ids", str(source_id))
                    )

        for index, issue in enumerate(issues, start=1):
            issue_id = _record_id(issue, "issue_id", f"issue-line-{index}")
            for field in ("supporting_evidence", "counterevidence"):
                for evidence_id in issue.get(field, []):
                    if str(evidence_id) not in evidence_by_id:
                        reference_errors.append(
                            self._reference_error("issues", issue_id, field, str(evidence_id))
                        )
            for calculation_id in issue.get("calculations", []):
                if str(calculation_id) not in calculation_by_id:
                    reference_errors.append(
                        self._reference_error(
                            "issues", issue_id, "calculations", str(calculation_id)
                        )
                    )
            for claim_id in issue.get("claim_ids", []):
                if str(claim_id) not in claim_by_id:
                    reference_errors.append(
                        self._reference_error("issues", issue_id, "claim_ids", str(claim_id))
                    )

        failed_citations = [item for item in citation_results if not item["valid"]]
        material_results = [item for item in claim_results if item["material"]]
        supported_material = sum(item["valid"] for item in material_results)
        calculation_failures = [item for item in calculation_results if not item["valid"]]
        claim_failures = [item for item in claim_results if not item["valid"]]
        passed = not (
            record_errors
            or reference_errors
            or failed_citations
            or calculation_failures
            or claim_failures
        )
        material_total = len(material_results)
        return {
            "calculation_results": calculation_results,
            "claim_results": claim_results,
            "citation_results": citation_results,
            "duplicate_corroboration_exclusions": duplicate_exclusions,
            "failed_citations": failed_citations,
            "record_errors": record_errors,
            "reference_errors": reference_errors,
            "run_id": self.run_id,
            "schema_version": 1,
            "status": "passed" if passed else "failed",
            "summary": {
                "calculation_count": len(calculations),
                "calculation_failure_count": len(calculation_failures),
                "citation_count": len(citation_results),
                "claim_count": len(claims),
                "contradiction_count": len(contradictions),
                "duplicate_corroboration_exclusion_count": len(duplicate_exclusions),
                "evidence_count": len(evidence_records),
                "failed_citation_count": len(failed_citations),
                "gap_count": len(gaps),
                "issue_count": len(issues),
                "material_claim_count": material_total,
                "material_claim_coverage": (
                    supported_material / material_total if material_total else None
                ),
                "material_claims_supported": supported_material,
                "record_error_count": len(record_errors),
                "reference_error_count": len(reference_errors),
            },
        }


def validate_citations(
    run: str | Path,
    record_sets: Mapping[str, list[JsonObject]] | None = None,
) -> JsonObject:
    """Load record sets when needed and run all deterministic citation gates."""

    validator = CitationValidator(run)
    values = load_record_sets(validator.run_path) if record_sets is None else record_sets
    return validator.validate(values)
