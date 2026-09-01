"""Read-only analytical index over locked register and extraction artifacts."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from openpyxl.utils.cell import column_index_from_string, coordinate_from_string

from dd_engine.artifacts import load_json
from dd_engine.errors import AnalysisError
from dd_engine.evidence.models import JsonObject
from dd_engine.runs import load_manifest


def _normalized(value: object) -> str:
    return re.sub(r"[\s_\\/\-]+", " ", str(value or "")).strip().casefold()


def unit_value(unit: JsonObject) -> object:
    """Return the immutable extracted value used for analytical matching."""

    content = unit.get("content")
    if not isinstance(content, dict):
        return None
    for key in ("source_value", "value", "text", "cached_value"):
        value = content.get(key)
        if value is not None:
            return value
    return None


def numeric_value(unit: JsonObject) -> float | None:
    """Convert a directly extracted cell value to float without treating blanks as zero."""

    content = unit.get("content")
    if not isinstance(content, dict):
        return None
    candidates = (content.get("source_value"), content.get("value"), content.get("cached_value"))
    for value in candidates:
        if isinstance(value, bool) or value is None or value == "":
            continue
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            continue
    return None


@dataclass(frozen=True, slots=True)
class SheetRef:
    """One extracted sheet-like grid and its coordinate-indexed cells."""

    source_id: str
    sheet: str
    cells: dict[str, JsonObject]

    def cell(self, coordinate: str) -> JsonObject | None:
        return self.cells.get(coordinate.upper())

    def values(self) -> list[str]:
        return [_normalized(unit_value(unit)) for unit in self.cells.values()]


class AnalysisContext:
    """Load source identity, extracted units, answers and version evidence once."""

    def __init__(self, run: str | Path) -> None:
        self.run_path, self.manifest = load_manifest(run)
        self.run_id = str(self.manifest["run_id"])
        register = load_json(self.run_path / "source_register" / "source_register.json")
        raw_sources = register.get("sources")
        if not isinstance(raw_sources, list):
            raise AnalysisError("source register has no source list")
        self.sources: dict[str, JsonObject] = {
            str(item["source_id"]): item
            for item in raw_sources
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }
        self.units: list[JsonObject] = []
        self.units_by_source: dict[str, list[JsonObject]] = defaultdict(list)
        self._load_units()
        self.sheets = self._build_sheets()
        self.answers = self._load_answers()
        self.version_families = load_json(
            self.run_path / "source_register" / "version_families.json"
        ).get("version_families", [])

    def _load_units(self) -> None:
        path = self.run_path / "extracts" / "extracted_units.jsonl"
        try:
            with path.open(encoding="utf-8") as handle:
                for number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    value = json.loads(line)
                    if not isinstance(value, dict) or value.get("run_id") != self.run_id:
                        raise AnalysisError(f"invalid extracted unit at line {number}")
                    self.units.append(value)
                    self.units_by_source[str(value.get("source_id"))].append(value)
        except AnalysisError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise AnalysisError(f"cannot load extracted units: {exc}") from exc

    def _build_sheets(self) -> list[SheetRef]:
        grouped: dict[tuple[str, str], dict[str, JsonObject]] = defaultdict(dict)
        for unit in self.units:
            locator = unit.get("locator")
            if not isinstance(locator, dict) or locator.get("type") not in {
                "spreadsheet_cell",
                "csv_cell",
            }:
                continue
            cell = locator.get("cell")
            if not isinstance(cell, str):
                continue
            sheet = str(locator.get("sheet") or "CSV")
            grouped[(str(unit["source_id"]), sheet)][cell.upper()] = unit
        return [
            SheetRef(source_id=source_id, sheet=sheet, cells=cells)
            for (source_id, sheet), cells in sorted(grouped.items())
        ]

    def _load_answers(self) -> list[JsonObject]:
        result: list[JsonObject] = []
        for round_number in (1, 2):
            path = self.run_path / "intake" / f"round_{round_number}_answers.json"
            if not path.is_file():
                continue
            payload = load_json(path)
            raw = payload.get("answers")
            if isinstance(raw, list):
                result.extend(item for item in raw if isinstance(item, dict))
        return result

    def source(self, source_id: str) -> JsonObject:
        try:
            return self.sources[source_id]
        except KeyError as exc:
            raise AnalysisError(f"unknown source ID: {source_id}") from exc

    def source_path(self, source_id: str) -> str:
        return str(self.source(source_id).get("relative_path", ""))

    def sheets_with(self, *labels: str, path_hint: str | None = None) -> list[SheetRef]:
        """Find grids containing every semantic label, independent of filename."""

        wanted = [_normalized(label) for label in labels]
        result: list[SheetRef] = []
        for sheet in self.sheets:
            if path_hint and _normalized(path_hint) not in _normalized(
                self.source_path(sheet.source_id)
            ):
                continue
            values = sheet.values()
            if all(any(label in value for value in values) for label in wanted):
                result.append(sheet)
        return result

    def units_matching(
        self,
        pattern: str,
        *,
        path_hint: str | None = None,
        locator_type: str | None = None,
        flags: int = re.I,
    ) -> list[tuple[JsonObject, re.Match[str]]]:
        """Return exact units and matches; extracted text remains data, never instructions."""

        compiled = re.compile(pattern, flags)
        result: list[tuple[JsonObject, re.Match[str]]] = []
        for unit in self.units:
            if path_hint and _normalized(path_hint) not in _normalized(
                str(unit.get("relative_path"))
            ):
                continue
            locator = unit.get("locator")
            if locator_type and (
                not isinstance(locator, dict) or locator.get("type") != locator_type
            ):
                continue
            value = unit_value(unit)
            if not isinstance(value, str):
                continue
            match = compiled.search(value)
            if match:
                result.append((unit, match))
        return result

    def cell_matching(self, pattern: str, *, path_hint: str | None = None) -> JsonObject | None:
        compiled = re.compile(pattern, re.I)
        for unit in self.units:
            locator = unit.get("locator")
            if not isinstance(locator, dict) or locator.get("type") not in {
                "spreadsheet_cell",
                "csv_cell",
            }:
                continue
            if path_hint and _normalized(path_hint) not in _normalized(unit.get("relative_path")):
                continue
            value = unit_value(unit)
            if value is not None and compiled.search(str(value)):
                return unit
        return None

    @staticmethod
    def offset_cell(sheet: SheetRef, anchor: JsonObject, column_offset: int) -> JsonObject | None:
        locator = anchor.get("locator")
        coordinate = locator.get("cell") if isinstance(locator, dict) else None
        if not isinstance(coordinate, str):
            return None
        column, row = coordinate_from_string(coordinate)
        index = column_index_from_string(column) + column_offset
        if index < 1:
            return None
        letters = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            letters = chr(65 + remainder) + letters
        return sheet.cell(f"{letters}{row}")

    @staticmethod
    def sheet_for_unit(sheets: list[SheetRef], unit: JsonObject) -> SheetRef | None:
        locator = unit.get("locator")
        if not isinstance(locator, dict):
            return None
        source_id = str(unit.get("source_id"))
        sheet_name = str(locator.get("sheet") or "CSV")
        return next(
            (
                sheet
                for sheet in sheets
                if sheet.source_id == source_id and sheet.sheet == sheet_name
            ),
            None,
        )

    def exact_unit(self, source_id: str, coordinate: str, sheet: str | None = None) -> JsonObject:
        for grid in self.sheets:
            if grid.source_id == source_id and (sheet is None or grid.sheet == sheet):
                unit = grid.cell(coordinate)
                if unit is not None:
                    return unit
        raise AnalysisError(f"extracted cell not found: {source_id} {sheet or '*'}!{coordinate}")

    def text_units(self, *, path_hint: str | None = None) -> list[JsonObject]:
        return [
            unit
            for unit in self.units
            if isinstance(unit_value(unit), str)
            and (
                path_hint is None
                or _normalized(path_hint) in _normalized(str(unit.get("relative_path")))
            )
        ]

    def unresolved_answer_ids(self) -> list[str]:
        return sorted(
            str(answer.get("question_id"))
            for answer in self.answers
            if answer.get("resolution_status") in {"open", "narrowed"}
        )
