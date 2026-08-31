"""Run-local JSONL storage and structural validation for Phase 7 records."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, TypeAlias

from dd_engine.artifacts import atomic_write_jsonl
from dd_engine.errors import EvidenceError
from dd_engine.evidence.models import (
    CALCULATION_METHODS,
    CLAIM_STATUSES,
    CLAIM_TYPES,
    CONTRADICTION_STATUSES,
    EVIDENCE_RELATIONSHIPS,
    GAP_STATUSES,
    MATERIALITY_LEVELS,
    RECOMPUTATION_STATUSES,
    WORKSTREAMS,
    Calculation,
    Claim,
    Contradiction,
    Evidence,
    Gap,
    Issue,
    JsonObject,
)
from dd_engine.runs import load_manifest

RECORD_PATHS = {
    "claims": "evidence/claims.jsonl",
    "evidence": "evidence/evidence.jsonl",
    "calculations": "evidence/calculations.jsonl",
    "contradictions": "evidence/contradictions.jsonl",
    "gaps": "evidence/gaps.jsonl",
    "issues": "evidence/issues.jsonl",
}
RECORD_ID_FIELDS = {
    "claims": "claim_id",
    "evidence": "evidence_id",
    "calculations": "calculation_id",
    "contradictions": "contradiction_id",
    "gaps": "gap_id",
    "issues": "issue_id",
}

RecordModel: TypeAlias = Claim | Evidence | Calculation | Contradiction | Gap | Issue
RecordInput: TypeAlias = Mapping[str, Any] | RecordModel


def _record_value(record: RecordInput) -> JsonObject:
    if isinstance(record, Mapping):
        return dict(record)
    return record.as_record()


def _load_jsonl(path: Path, run_id: str) -> list[JsonObject]:
    records: list[JsonObject] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise EvidenceError(f"{path} line {line_number} must contain a JSON object")
                if value.get("run_id") != run_id:
                    raise EvidenceError(f"{path} line {line_number} does not contain this run ID")
                records.append(value)
    except EvidenceError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read evidence record file {path}: {exc}") from exc
    return records


def load_record_sets(
    run: str | Path, *, allow_missing: bool = False
) -> dict[str, list[JsonObject]]:
    """Load all six run-local record files, allowing legitimately empty JSONL files."""

    run_path, manifest = load_manifest(run)
    result: dict[str, list[JsonObject]] = {}
    for record_type, relative_path in RECORD_PATHS.items():
        path = run_path / relative_path
        if not path.is_file():
            if allow_missing:
                result[record_type] = []
                continue
            raise EvidenceError(f"evidence record file is missing: {relative_path}")
        result[record_type] = _load_jsonl(path, str(manifest["run_id"]))
    return result


def write_record_set(
    run: str | Path,
    record_type: str,
    records: Iterable[RecordInput],
) -> Path:
    """Atomically replace one typed record set without permitting cross-run records."""

    if record_type not in RECORD_PATHS:
        raise EvidenceError(f"unknown evidence record type: {record_type}")
    run_path, manifest = load_manifest(run)
    run_id = str(manifest["run_id"])
    values: list[JsonObject] = []
    for record in records:
        value = _record_value(record)
        supplied = value.get("run_id")
        if supplied not in {None, run_id}:
            raise EvidenceError(f"{record_type} record belongs to another run")
        value["run_id"] = run_id
        values.append(value)
    path = run_path / RECORD_PATHS[record_type]
    atomic_write_jsonl(path, values)
    return path


def _error(
    record_type: str,
    record_id: str,
    code: str,
    message: str,
) -> JsonObject:
    return {
        "code": code,
        "message": message,
        "record_id": record_id,
        "record_type": record_type,
    }


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _confidence(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and 0 <= value <= 1


def _sequence(value: object) -> bool:
    return isinstance(value, list | tuple)


def _validate_claim(record: JsonObject, record_id: str) -> list[JsonObject]:
    errors: list[JsonObject] = []
    checks = (
        (_text(record.get("statement")), "statement", "a non-empty statement"),
        (record.get("claim_type") in CLAIM_TYPES, "claim_type", "a supported claim type"),
        (record.get("workstream") in WORKSTREAMS, "workstream", "a supported workstream"),
        (
            record.get("materiality") in MATERIALITY_LEVELS,
            "materiality",
            "a supported materiality",
        ),
        (_confidence(record.get("confidence")), "confidence", "a value between 0 and 1"),
        (record.get("status") in CLAIM_STATUSES, "status", "a supported claim status"),
        (
            type(record.get("required_independent_sources", 1)) is int
            and int(record.get("required_independent_sources", 1)) >= 1,
            "required_independent_sources",
            "a positive integer",
        ),
    )
    for valid, field, expectation in checks:
        if not valid:
            errors.append(
                _error("claims", record_id, f"invalid_{field}", f"{field} must be {expectation}")
            )
    return errors


def _validate_evidence(record: JsonObject, record_id: str) -> list[JsonObject]:
    errors: list[JsonObject] = []
    required_text = ("claim_id", "source_id", "source_checksum", "source_version_status")
    for field in required_text:
        if not _text(record.get(field)):
            errors.append(
                _error("evidence", record_id, f"invalid_{field}", f"{field} must be non-empty text")
            )
    checksum = record.get("source_checksum")
    if _text(checksum) and (
        len(str(checksum)) != 64
        or any(character not in "0123456789abcdef" for character in str(checksum).lower())
    ):
        errors.append(
            _error(
                "evidence", record_id, "invalid_source_checksum", "source_checksum is not SHA-256"
            )
        )
    if not isinstance(record.get("exact_locator"), dict):
        errors.append(
            _error(
                "evidence", record_id, "invalid_exact_locator", "exact_locator must be an object"
            )
        )
    if record.get("relationship") not in EVIDENCE_RELATIONSHIPS:
        errors.append(
            _error(
                "evidence",
                record_id,
                "invalid_relationship",
                "relationship must be supporting or contradicting",
            )
        )
    if not _confidence(record.get("extraction_confidence")):
        errors.append(
            _error(
                "evidence",
                record_id,
                "invalid_extraction_confidence",
                "extraction_confidence must be between 0 and 1",
            )
        )
    if record.get("extracted_value") is None and not _text(record.get("extracted_text")):
        errors.append(
            _error(
                "evidence",
                record_id,
                "missing_extracted_content",
                "extracted_value or extracted_text must preserve the cited source content",
            )
        )
    if not _sequence(record.get("extracted_unit_ids", [])):
        errors.append(
            _error(
                "evidence",
                record_id,
                "invalid_extracted_unit_ids",
                "extracted_unit_ids must be a list",
            )
        )
    return errors


def _validate_calculation(record: JsonObject, record_id: str) -> list[JsonObject]:
    errors: list[JsonObject] = []
    if not _text(record.get("description")):
        errors.append(
            _error("calculations", record_id, "invalid_description", "description is required")
        )
    inputs = record.get("source_inputs")
    if not _sequence(inputs) or not inputs:
        errors.append(
            _error(
                "calculations",
                record_id,
                "missing_source_inputs",
                "source_inputs must contain at least one reported or explicitly missing input",
            )
        )
        inputs = []
    input_ids: list[str] = []
    for index, raw_input in enumerate(inputs, start=1):
        if not isinstance(raw_input, dict):
            errors.append(
                _error(
                    "calculations",
                    record_id,
                    "invalid_source_input",
                    f"source input {index} must be an object",
                )
            )
            continue
        input_id = raw_input.get("input_id")
        if not _text(input_id):
            errors.append(
                _error(
                    "calculations",
                    record_id,
                    "invalid_input_id",
                    f"source input {index} requires a non-empty input_id",
                )
            )
        else:
            input_ids.append(str(input_id))
        if type(raw_input.get("missing")) is not bool:
            errors.append(
                _error(
                    "calculations",
                    record_id,
                    "missing_input_status",
                    f"source input {index} must explicitly set missing true or false",
                )
            )
            continue
        if raw_input["missing"]:
            if not _text(raw_input.get("missing_reason")):
                errors.append(
                    _error(
                        "calculations",
                        record_id,
                        "missing_input_reason",
                        f"source input {index} is missing but has no missing_reason",
                    )
                )
            if (
                raw_input.get("reported_value") is not None
                or raw_input.get("normalized_value") is not None
            ):
                errors.append(
                    _error(
                        "calculations",
                        record_id,
                        "missing_input_assumed_value",
                        f"source input {index} is missing and must not be assigned zero or "
                        "another value",
                    )
                )
        else:
            for field in ("source_id", "source_checksum", "source_version_status"):
                if not _text(raw_input.get(field)):
                    errors.append(
                        _error(
                            "calculations",
                            record_id,
                            f"invalid_input_{field}",
                            f"non-missing source input {index} requires {field}",
                        )
                    )
            if not isinstance(raw_input.get("locator"), dict):
                errors.append(
                    _error(
                        "calculations",
                        record_id,
                        "invalid_input_locator",
                        f"non-missing source input {index} requires a locator object",
                    )
                )
            if raw_input.get("normalized_value") is None:
                errors.append(
                    _error(
                        "calculations",
                        record_id,
                        "missing_normalized_value",
                        f"non-missing source input {index} requires normalized_value",
                    )
                )
    if len(input_ids) != len(set(input_ids)):
        errors.append(
            _error(
                "calculations", record_id, "duplicate_input_id", "source input IDs must be unique"
            )
        )

    normalisation = record.get("normalisation")
    if not isinstance(normalisation, dict):
        errors.append(
            _error(
                "calculations",
                record_id,
                "invalid_normalisation",
                "normalisation must explicitly describe period, currency, sign and units",
            )
        )
    else:
        for field in ("period", "currency", "sign", "units"):
            if not _text(normalisation.get(field)):
                errors.append(
                    _error(
                        "calculations",
                        record_id,
                        f"missing_normalisation_{field}",
                        f"normalisation.{field} must be explicit",
                    )
                )
    formula = record.get("formula")
    if (
        not isinstance(formula, dict)
        or not _text(formula.get("expression"))
        or not _text(formula.get("version"))
    ):
        errors.append(
            _error(
                "calculations",
                record_id,
                "invalid_formula",
                "formula must contain non-empty expression and version fields",
            )
        )
    result = record.get("result")
    if not isinstance(result, dict) or not {"reported_value", "recomputed_value"}.issubset(result):
        errors.append(
            _error(
                "calculations",
                record_id,
                "invalid_result",
                "result must preserve separate reported_value and recomputed_value fields",
            )
        )
    rounding = record.get("rounding")
    if (
        not isinstance(rounding, dict)
        or rounding.get("mode") not in {"half_even", "half_up", "none"}
        or type(rounding.get("decimal_places")) is not int
        or int(rounding.get("decimal_places", -1)) < 0
    ):
        errors.append(
            _error(
                "calculations",
                record_id,
                "invalid_rounding",
                "rounding requires mode and a non-negative decimal_places integer",
            )
        )
    if record.get("independent_recomputation_status") not in RECOMPUTATION_STATUSES:
        errors.append(
            _error(
                "calculations",
                record_id,
                "invalid_recomputation_status",
                "independent_recomputation_status is not recognized",
            )
        )
    if record.get("calculation_method") not in CALCULATION_METHODS:
        errors.append(
            _error(
                "calculations",
                record_id,
                "invalid_calculation_method",
                "calculation_method must be deterministic or model_assisted",
            )
        )
    return errors


def _validate_contradiction(record: JsonObject, record_id: str) -> list[JsonObject]:
    errors: list[JsonObject] = []
    if not _sequence(record.get("conflicting_claims")) or not _sequence(
        record.get("conflicting_values")
    ):
        errors.append(
            _error(
                "contradictions",
                record_id,
                "invalid_conflict",
                "conflicting_claims and conflicting_values must be lists",
            )
        )
    if not _sequence(record.get("source_ids")) or not _sequence(record.get("likely_explanations")):
        errors.append(
            _error(
                "contradictions",
                record_id,
                "invalid_explanation_sources",
                "source_ids and likely_explanations must be lists",
            )
        )
    if record.get("status") not in CONTRADICTION_STATUSES:
        errors.append(
            _error(
                "contradictions",
                record_id,
                "invalid_status",
                "status must be resolved or unresolved",
            )
        )
    return errors


def _validate_gap(record: JsonObject, record_id: str) -> list[JsonObject]:
    errors: list[JsonObject] = []
    for field in ("expected_information", "requested_follow_up"):
        if not _text(record.get(field)):
            errors.append(
                _error("gaps", record_id, f"invalid_{field}", f"{field} must be non-empty text")
            )
    if record.get("importance") not in MATERIALITY_LEVELS:
        errors.append(
            _error("gaps", record_id, "invalid_importance", "importance is not recognized")
        )
    if not _sequence(record.get("evidence_that_it_is_missing")) or not record.get(
        "evidence_that_it_is_missing"
    ):
        errors.append(
            _error(
                "gaps",
                record_id,
                "missing_absence_evidence",
                "evidence_that_it_is_missing must contain at least one audit fact",
            )
        )
    if not _sequence(record.get("affected_decision")):
        errors.append(
            _error(
                "gaps", record_id, "invalid_affected_decision", "affected_decision must be a list"
            )
        )
    if record.get("status") not in GAP_STATUSES:
        errors.append(_error("gaps", record_id, "invalid_status", "gap status is not recognized"))
    return errors


def _validate_issue(record: JsonObject, record_id: str) -> list[JsonObject]:
    errors: list[JsonObject] = []
    for field in ("conclusion", "transaction_implication", "recommended_action"):
        if not _text(record.get(field)):
            errors.append(
                _error("issues", record_id, f"invalid_{field}", f"{field} must be non-empty text")
            )
    if record.get("workstream") not in WORKSTREAMS:
        errors.append(
            _error("issues", record_id, "invalid_workstream", "workstream is not recognized")
        )
    if record.get("materiality") not in MATERIALITY_LEVELS:
        errors.append(
            _error("issues", record_id, "invalid_materiality", "materiality is not recognized")
        )
    if not _confidence(record.get("confidence")):
        errors.append(
            _error("issues", record_id, "invalid_confidence", "confidence must be between 0 and 1")
        )
    for field in ("supporting_evidence", "counterevidence", "calculations"):
        if not _sequence(record.get(field)):
            errors.append(
                _error("issues", record_id, f"invalid_{field}", f"{field} must be a list")
            )
    return errors


_VALIDATORS = {
    "claims": _validate_claim,
    "evidence": _validate_evidence,
    "calculations": _validate_calculation,
    "contradictions": _validate_contradiction,
    "gaps": _validate_gap,
    "issues": _validate_issue,
}


def validate_record_sets(
    record_sets: Mapping[str, list[JsonObject]], run_id: str
) -> list[JsonObject]:
    """Return all structural errors without dropping or repairing source-authored values."""

    errors: list[JsonObject] = []
    for record_type, validator in _VALIDATORS.items():
        records = record_sets.get(record_type, [])
        id_field = RECORD_ID_FIELDS[record_type]
        seen: set[str] = set()
        for index, record in enumerate(records, start=1):
            record_id = str(record.get(id_field) or f"line-{index}")
            if record.get("run_id") != run_id:
                errors.append(
                    _error(record_type, record_id, "run_id_mismatch", "record run_id is incorrect")
                )
            if not _text(record.get(id_field)):
                errors.append(
                    _error(
                        record_type,
                        record_id,
                        f"invalid_{id_field}",
                        f"{id_field} must be non-empty text",
                    )
                )
            elif record_id in seen:
                errors.append(
                    _error(
                        record_type,
                        record_id,
                        f"duplicate_{id_field}",
                        f"{id_field} must be unique within the run",
                    )
                )
            seen.add(record_id)
            errors.extend(validator(record, record_id))
    return errors
