"""Verbatim deal-lead answer ingestion and conservative normalization."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from dd_engine.artifacts import file_sha256
from dd_engine.errors import IntakeError
from dd_engine.intake.models import JsonObject
from dd_engine.time import utc_now

_NON_ANSWER = re.compile(
    r"^(?:n/?a|none|unknown|not\s+known|not\s+available|unavailable|cannot\s+answer|tbc|tbd)[.!]?$",
    re.I,
)
_CROSS_REFERENCE = re.compile(r"\b(?:see|refer(?:red)?\s+to|per)\s+[^.;\n]+", re.I)
_VAGUE = re.compile(
    r"\b(?:as\s+discussed|probably|possibly|we\s+(?:think|believe)|"
    r"management\s+believes?|in\s+progress|to\s+follow|will\s+provide|"
    r"not\s+sure|unclear|tbc|tbd)\b",
    re.I,
)
_EXPLICITLY_UNRESOLVED = re.compile(
    r"(?:\bno\b[^.\n]{0,160}\b(?:supplied|provided|included|available|obtained|received)\b|"
    r"\bnot\b[^.\n]{0,100}\b(?:supplied|provided|established|confirmed|evidenced|"
    r"verified|available|obtained|received|resolved)\b|"
    r"\b(?:keep|leave|remain|remains|treat)\b[^.\n]{0,100}\b(?:open|unresolved|"
    r"unestablished|outstanding)\b)",
    re.I,
)

ANSWER_NORMALIZATION_VERSION = "answer-normalization-v2"


def normalize_answer(verbatim: str | None) -> tuple[JsonObject, list[str], str]:
    """Normalize only what is explicit, retaining ambiguity and never completing an answer."""

    if verbatim is None or not verbatim.strip():
        return (
            {"kind": "unanswered", "value": None},
            ["No answer was supplied; the engine inferred nothing from silence."],
            "open",
        )
    stripped = verbatim.strip()
    if _NON_ANSWER.fullmatch(stripped):
        return (
            {"kind": "explicit_non_answer", "value": stripped},
            ["The reply explicitly does not provide the requested fact."],
            "open",
        )
    if _EXPLICITLY_UNRESOLVED.search(stripped):
        return (
            {"kind": "explicitly_unresolved", "value": stripped},
            [
                "The reply explicitly says that requested evidence or confirmation is absent "
                "or that the matter remains open."
            ],
            "open",
        )
    cross_reference = _CROSS_REFERENCE.search(stripped)
    if cross_reference:
        return (
            {
                "kind": "cross_reference",
                "reference_text": cross_reference.group(0),
                "value": stripped,
            },
            [
                "The referenced location must be resolved to a registered source and does not "
                "automatically close the question."
            ],
            "narrowed",
        )
    if _VAGUE.search(stripped):
        return (
            {"kind": "vague_or_deferred", "value": stripped},
            ["The reply is qualified, deferred or lacks a source-verifiable fact."],
            "open",
        )
    if len(stripped.split()) < 3:
        return (
            {"kind": "short_ambiguous_reply", "value": stripped},
            ["The short reply does not establish whether all requested elements were answered."],
            "narrowed",
        )
    return {"kind": "substantive_text", "value": stripped}, [], "closed"


def _load_answer_input(path: Path, run_id: str, round_number: int) -> JsonObject:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise IntakeError(f"cannot read answer input {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IntakeError("answer input must be a JSON object")
    supplied_run_id = value.get("run_id")
    if supplied_run_id not in {None, run_id}:
        raise IntakeError("answer input belongs to another run")
    supplied_round = value.get("round_number")
    if supplied_round not in {None, round_number}:
        raise IntakeError("answer input round_number does not match the requested round")
    return value


def _answer_map(value: JsonObject) -> dict[str, str | None]:
    raw_answers = value.get("answers")
    if isinstance(raw_answers, dict):
        result: dict[str, str | None] = {}
        for question_id, answer in raw_answers.items():
            if answer is not None and not isinstance(answer, str):
                raise IntakeError(f"answer for {question_id} must be text or null")
            result[str(question_id)] = answer
        return result
    if not isinstance(raw_answers, list):
        raise IntakeError("answer input must contain an answers object or list")
    result = {}
    for item in raw_answers:
        if not isinstance(item, dict):
            raise IntakeError("answer list contains a non-object record")
        question_id = item.get("question_id")
        if not isinstance(question_id, str) or not question_id:
            raise IntakeError("every answer record requires a question_id")
        if question_id in result:
            raise IntakeError(f"duplicate answer for {question_id}")
        answer = item.get("answer")
        if answer is not None and not isinstance(answer, str):
            raise IntakeError(f"answer for {question_id} must be text or null")
        result[question_id] = answer
    return result


def ingest_answer_records(
    *,
    answer_path: Path,
    run_id: str,
    round_number: int,
    questions: list[JsonObject],
    previous_records: list[JsonObject] | None = None,
) -> tuple[JsonObject, list[str], list[str]]:
    """Create one immutable-provenance record per question, including unanswered ones."""

    value = _load_answer_input(answer_path, run_id, round_number)
    provided = _answer_map(value)
    known_ids = {str(question.get("question_id")) for question in questions}
    unknown_ids = sorted(set(provided) - known_ids)
    if unknown_ids:
        raise IntakeError(f"answer input contains unknown question ID(s): {', '.join(unknown_ids)}")
    answered_by = value.get("answered_by")
    if answered_by is not None and not isinstance(answered_by, str):
        raise IntakeError("answered_by must be text when supplied")
    answered_at = value.get("answered_at")
    if answered_at is not None and not isinstance(answered_at, str):
        raise IntakeError("answered_at must be text when supplied")

    input_sha256 = file_sha256(answer_path)
    ingested_at = utc_now()
    previous = {str(item.get("question_id")): item for item in (previous_records or [])}
    changed_ids: list[str] = []
    invalidation_targets: list[str] = []
    records: list[JsonObject] = []
    for question in questions:
        question_id = str(question["question_id"])
        verbatim = provided.get(question_id)
        normalized, ambiguity, status = normalize_answer(verbatim)
        old = previous.get(question_id)
        if old is not None and (
            old.get("verbatim_answer") != verbatim
            or old.get("normalised_interpretation") != normalized
            or old.get("resolution_status") != status
        ):
            changed_ids.append(question_id)
            raw_targets = question.get("invalidate_if_answer_changes_evidence", [])
            if isinstance(raw_targets, list):
                for target in raw_targets:
                    value_target = str(target)
                    if value_target not in invalidation_targets:
                        invalidation_targets.append(value_target)
        gap = question.get("structured_gap")
        affected_gaps = []
        if isinstance(gap, dict) and gap.get("gap_id"):
            affected_gaps.append(str(gap["gap_id"]))
        raw_stages = question.get("invalidate_if_answer_changes_evidence", [])
        affected_stages = [str(item) for item in raw_stages] if isinstance(raw_stages, list) else []
        records.append(
            {
                "affected_claims": [],
                "affected_gaps": affected_gaps,
                "affected_stages": affected_stages,
                "ambiguity": ambiguity,
                "normalised_interpretation": normalized,
                "provenance": {
                    "answer_input_filename": answer_path.name,
                    "answer_input_sha256": input_sha256,
                    "answered_at": answered_at,
                    "answered_by": answered_by,
                    "ingested_at": ingested_at,
                    "source_kind": "deal_lead_answer_file",
                },
                "question_id": question_id,
                "resolution_status": status,
                "round_number": round_number,
                "verbatim_answer": verbatim,
                "verbatim_answer_sha256": (
                    hashlib.sha256(verbatim.encode("utf-8")).hexdigest()
                    if verbatim is not None
                    else None
                ),
            }
        )
    return (
        {
            "answer_input_sha256": input_sha256,
            "answer_normalization_version": ANSWER_NORMALIZATION_VERSION,
            "answered_at": answered_at,
            "answered_by": answered_by,
            "answers": records,
            "explicit_ingestion": True,
            "ingested_at": ingested_at,
            "round_number": round_number,
            "run_id": run_id,
            "schema_version": 1,
            "status_counts": {
                status: sum(record["resolution_status"] == status for record in records)
                for status in ("closed", "narrowed", "open")
            },
        },
        changed_ids,
        invalidation_targets,
    )


def answer_records(payload: JsonObject) -> list[JsonObject]:
    """Validate and return the record list from a stored answer artifact."""

    value = payload.get("answers")
    if not isinstance(value, list):
        raise IntakeError("stored answer artifact has no answer list")
    records: list[JsonObject] = []
    for item in value:
        if not isinstance(item, dict):
            raise IntakeError("stored answer artifact contains a non-object record")
        records.append(item)
    return records
