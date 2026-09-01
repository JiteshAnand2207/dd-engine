"""Two-round intake orchestration, durable pauses and selective resumption."""

from __future__ import annotations

from pathlib import Path

from dd_engine.artifacts import (
    append_json_line,
    atomic_write_json,
    atomic_write_text,
    file_sha256,
    load_json,
)
from dd_engine.constants import STAGE_ORDER, StageState
from dd_engine.errors import IntakeError
from dd_engine.extraction.models import stable_json_checksum
from dd_engine.intake.answers import (
    ANSWER_NORMALIZATION_VERSION,
    answer_records,
    ingest_answer_records,
    normalize_answer,
)
from dd_engine.intake.generation import (
    ROUND_LIMITS,
    generate_candidates,
    question_fingerprint,
    question_support_is_valid,
)
from dd_engine.intake.models import IntakeOutcome, JsonObject
from dd_engine.intake.observations import load_observations
from dd_engine.intake.rendering import (
    render_questions_markdown,
    render_unresolved_markdown,
    unresolved_records,
)
from dd_engine.runs import load_manifest
from dd_engine.state import (
    complete_stage,
    invalidate_from_stage,
    mark_stage_awaiting_input,
    reopen_completed_stage,
    resume_stage,
    start_stage,
)
from dd_engine.time import utc_now

INTAKE_GENERATOR_VERSION = "6.0.0"
INTAKE_SCHEMA_VERSION = 1
INTAKE_OUTPUTS = (
    "intake/round_1_questions.md",
    "intake/round_1_questions.json",
    "intake/round_1_answers.json",
    "intake/round_2_questions.md",
    "intake/round_2_questions.json",
    "intake/round_2_answers.json",
    "intake/unresolved_questions.md",
)


def _question_json_path(run_path: Path, round_number: int) -> Path:
    return run_path / "intake" / f"round_{round_number}_questions.json"


def _question_md_path(run_path: Path, round_number: int) -> Path:
    return run_path / "intake" / f"round_{round_number}_questions.md"


def _answer_json_path(run_path: Path, round_number: int) -> Path:
    return run_path / "intake" / f"round_{round_number}_answers.json"


def _input_artifacts(run_path: Path, round_number: int) -> list[JsonObject]:
    relative_paths = [
        "source_register/source_register.json",
        "source_register/room_structure.json",
        "source_register/version_families.json",
        "extracts/extraction_manifest.json",
        "extracts/extracted_units.jsonl",
        "extracts/needs_vision.json",
    ]
    if round_number == 2:
        relative_paths.append("intake/round_1_answers.json")
    records: list[JsonObject] = []
    for relative_path in relative_paths:
        path = run_path / relative_path
        if not path.is_file():
            raise IntakeError(f"intake input artifact is missing: {relative_path}")
        records.append({"path": relative_path, "sha256": file_sha256(path)})
    return records


def _input_fingerprint(run_path: Path, round_number: int) -> tuple[str, list[JsonObject]]:
    artifacts = _input_artifacts(run_path, round_number)
    return (
        stable_json_checksum(
            {
                "artifacts": artifacts,
                "generator_version": INTAKE_GENERATOR_VERSION,
                "round_number": round_number,
                "schema_version": INTAKE_SCHEMA_VERSION,
            }
        ),
        artifacts,
    )


def _question_list(payload: JsonObject) -> list[JsonObject]:
    raw = payload.get("questions")
    if not isinstance(raw, list):
        raise IntakeError("question artifact has no questions list")
    questions: list[JsonObject] = []
    for item in raw:
        if not isinstance(item, dict):
            raise IntakeError("question artifact contains a non-object question")
        questions.append(item)
    return questions


def _load_questions(run_path: Path, run_id: str, round_number: int) -> JsonObject:
    path = _question_json_path(run_path, round_number)
    if not path.is_file():
        raise IntakeError(f"round {round_number} questions have not been generated")
    payload = load_json(path)
    if payload.get("run_id") != run_id or payload.get("round_number") != round_number:
        raise IntakeError(f"round {round_number} question artifact does not match this run")
    _question_list(payload)
    return payload


def _load_answers_optional(run_path: Path, run_id: str, round_number: int) -> JsonObject | None:
    path = _answer_json_path(run_path, round_number)
    if not path.is_file():
        return None
    payload = load_json(path)
    if payload.get("run_id") != run_id or payload.get("round_number") != round_number:
        raise IntakeError(f"round {round_number} answer artifact does not match this run")
    answer_records(payload)
    return payload


def _validate_generated_questions(questions: list[JsonObject], round_number: int) -> None:
    if not questions:
        raise IntakeError("no supported material intake question could be generated")
    if len(questions) > ROUND_LIMITS[round_number]:
        raise IntakeError(f"round {round_number} exceeds its question limit")
    identifiers = [str(item.get("question_id")) for item in questions]
    if len(set(identifiers)) != len(identifiers):
        raise IntakeError("generated questions contain duplicate IDs")
    fingerprints = [question_fingerprint(item) for item in questions]
    if len(set(fingerprints)) != len(fingerprints):
        raise IntakeError("generated questions contain duplicates")
    for question in questions:
        if question.get("round_number") != round_number:
            raise IntakeError("generated question has the wrong round number")
        if not question_support_is_valid(question):
            raise IntakeError(
                f"{question.get('question_id')} lacks source support or an essential context gap"
            )


def _round_payloads(run_path: Path, run_id: str) -> list[tuple[JsonObject, JsonObject | None]]:
    payloads: list[tuple[JsonObject, JsonObject | None]] = []
    for round_number in (1, 2):
        question_path = _question_json_path(run_path, round_number)
        if not question_path.is_file():
            continue
        questions = _load_questions(run_path, run_id, round_number)
        if questions.get("status") == "invalidated":
            continue
        answers = _load_answers_optional(run_path, run_id, round_number)
        if answers is not None and answers.get("status") == "invalidated":
            answers = None
        payloads.append((questions, answers))
    return payloads


def _write_unresolved(run_path: Path, run_id: str) -> int:
    records = unresolved_records(_round_payloads(run_path, run_id))
    atomic_write_text(
        run_path / "intake" / "unresolved_questions.md",
        render_unresolved_markdown(run_id, records),
    )
    return len(records)


def _existing_question_outcome(
    run_path: Path,
    manifest: JsonObject,
    round_number: int,
    input_fingerprint: str,
) -> IntakeOutcome | None:
    path = _question_json_path(run_path, round_number)
    if not path.is_file():
        return None
    payload = _load_questions(run_path, str(manifest["run_id"]), round_number)
    if payload.get("status") == "invalidated":
        return None
    if payload.get("input_fingerprint") != input_fingerprint:
        raise IntakeError(
            f"round {round_number} question inputs changed; regenerate from an "
            "invalidated intake stage"
        )
    questions = _question_list(payload)
    unresolved_count = len(unresolved_records(_round_payloads(run_path, str(manifest["run_id"]))))
    return IntakeOutcome(
        action="questions_generated",
        question_count=len(questions),
        reused=True,
        round_number=round_number,
        run_path=run_path,
        stage_state=str(manifest["stages"]["intake"]["state"]),
        unresolved_count=unresolved_count,
    )


def generate_intake_questions(run: str | Path, round_number: int) -> IntakeOutcome:
    """Generate one evidence-grounded round and put the run in a real human pause."""

    if round_number not in {1, 2}:
        raise IntakeError("intake round must be 1 or 2")
    run_path, manifest = load_manifest(run)
    run_id = str(manifest["run_id"])
    if manifest["stages"]["register"]["state"] != StageState.COMPLETED.value:
        raise IntakeError("intake requires a completed source register")
    if manifest["stages"]["extract"]["state"] != StageState.COMPLETED.value:
        raise IntakeError("intake requires completed local extraction inputs")
    fingerprint, input_artifacts = _input_fingerprint(run_path, round_number)

    existing = _existing_question_outcome(run_path, manifest, round_number, fingerprint)
    if existing is not None:
        return existing

    intake_state = str(manifest["stages"]["intake"]["state"])
    if round_number == 1:
        if intake_state in {
            StageState.NOT_STARTED.value,
            StageState.FAILED.value,
            StageState.INVALIDATED.value,
        }:
            manifest = start_stage(run_path, "intake", input_checksum=fingerprint)
        elif intake_state != StageState.RUNNING.value:
            raise IntakeError(f"cannot generate round one from intake state {intake_state}")
    else:
        round_one_answers = _load_answers_optional(run_path, run_id, 1)
        if round_one_answers is None:
            raise IntakeError("round two requires explicit round-one answer ingestion")
        if intake_state != StageState.RUNNING.value:
            raise IntakeError(f"cannot generate round two from intake state {intake_state}")

    observations = load_observations(run_path, run_id)
    round_one_questions: list[JsonObject] | None = None
    round_one_answer_records: list[JsonObject] | None = None
    if round_number == 2:
        round_one_question_payload = _load_questions(run_path, run_id, 1)
        round_one_answer_payload = _load_answers_optional(run_path, run_id, 1)
        if round_one_answer_payload is None:
            raise IntakeError("round two requires round-one answers")
        round_one_questions = _question_list(round_one_question_payload)
        round_one_answer_records = answer_records(round_one_answer_payload)
    questions, excluded = generate_candidates(
        observations,
        round_number=round_number,
        round_one_questions=round_one_questions,
        round_one_answers=round_one_answer_records,
    )
    _validate_generated_questions(questions, round_number)
    generated_at = utc_now()
    payload: JsonObject = {
        "evidence_scope": (
            "complete register plus early material extraction signals"
            if round_number == 1
            else "complete register, full extraction and verbatim round-one answers"
        ),
        "excluded_candidates": excluded,
        "generated_at": generated_at,
        "generator_version": INTAKE_GENERATOR_VERSION,
        "input_artifacts": input_artifacts,
        "input_fingerprint": fingerprint,
        "question_count": len(questions),
        "question_limit": ROUND_LIMITS[round_number],
        "questions": questions,
        "round_number": round_number,
        "run_id": run_id,
        "schema_version": INTAKE_SCHEMA_VERSION,
        "status": "awaiting_input",
        "untrusted_source_data_was_executed": False,
    }
    atomic_write_json(_question_json_path(run_path, round_number), payload)
    atomic_write_text(
        _question_md_path(run_path, round_number),
        render_questions_markdown(
            run_id=run_id,
            round_number=round_number,
            generated_at=generated_at,
            questions=questions,
            excluded_candidates=excluded,
        ),
    )
    unresolved_count = _write_unresolved(run_path, run_id)
    manifest = mark_stage_awaiting_input(run_path, "intake")
    append_json_line(
        run_path / "logs" / "events.jsonl",
        {
            "event": "intake_questions_generated",
            "input_fingerprint": fingerprint,
            "question_count": len(questions),
            "round_number": round_number,
            "run_id": run_id,
            "stage_state": StageState.AWAITING_INPUT.value,
            "timestamp": utc_now(),
        },
    )
    return IntakeOutcome(
        action="questions_generated",
        question_count=len(questions),
        reused=False,
        round_number=round_number,
        run_path=run_path,
        stage_state=str(manifest["stages"]["intake"]["state"]),
        unresolved_count=unresolved_count,
    )


def _invalidate_round_two(run_path: Path, run_id: str, reason: str) -> None:
    invalidated_at = utc_now()
    question_path = _question_json_path(run_path, 2)
    if question_path.is_file():
        payload = _load_questions(run_path, run_id, 2)
        payload["invalidated_at"] = invalidated_at
        payload["invalidation_reason"] = reason
        payload["status"] = "invalidated"
        atomic_write_json(question_path, payload)
        original = _question_md_path(run_path, 2).read_text(encoding="utf-8")
        if not original.startswith("# INVALIDATED"):
            atomic_write_text(
                _question_md_path(run_path, 2),
                f"# INVALIDATED\n\n{reason}\n\n{original}",
            )
    answer_path = _answer_json_path(run_path, 2)
    if answer_path.is_file():
        answers = _load_answers_optional(run_path, run_id, 2)
        if answers is not None:
            answers["invalidated_at"] = invalidated_at
            answers["invalidation_reason"] = reason
            answers["status"] = "invalidated"
            atomic_write_json(answer_path, answers)


def _earliest_real_stage(targets: list[str]) -> str | None:
    real = [target for target in targets if target in STAGE_ORDER and target != "intake"]
    if not real:
        return None
    return min(real, key=STAGE_ORDER.index)


def ingest_intake_answers(
    run: str | Path, round_number: int, answer_file: str | Path
) -> IntakeOutcome:
    """Ingest an explicit answer file, resume safely and preserve every reply verbatim."""

    if round_number not in {1, 2}:
        raise IntakeError("intake round must be 1 or 2")
    run_path, manifest = load_manifest(run)
    run_id = str(manifest["run_id"])
    answer_path = Path(answer_file).expanduser().resolve(strict=False)
    if not answer_path.is_file():
        raise IntakeError(f"answer file not found: {answer_path}")
    question_payload = _load_questions(run_path, run_id, round_number)
    if question_payload.get("status") == "invalidated":
        raise IntakeError(f"round {round_number} questions are invalidated and must be regenerated")
    questions = _question_list(question_payload)
    stored = _load_answers_optional(run_path, run_id, round_number)
    incoming_hash = file_sha256(answer_path)
    intake_state = str(manifest["stages"]["intake"]["state"])

    if (
        stored is not None
        and stored.get("answer_input_sha256") == incoming_hash
        and stored.get("answer_normalization_version") == ANSWER_NORMALIZATION_VERSION
    ):
        unresolved_count = _write_unresolved(run_path, run_id)
        if intake_state == StageState.AWAITING_INPUT.value:
            manifest = resume_stage(run_path, "intake")
            if round_number == 2:
                manifest = complete_stage(run_path, "intake", required_artifacts=INTAKE_OUTPUTS)
        return IntakeOutcome(
            action="answers_ingested",
            question_count=len(questions),
            reused=True,
            round_number=round_number,
            run_path=run_path,
            stage_state=str(manifest["stages"]["intake"]["state"]),
            unresolved_count=unresolved_count,
        )

    revision = stored is not None
    if not revision and intake_state != StageState.AWAITING_INPUT.value:
        raise IntakeError(
            f"round {round_number} answers require an awaiting_input pause; current state "
            f"is {intake_state}"
        )
    if revision and intake_state == StageState.COMPLETED.value:
        manifest = reopen_completed_stage(
            run_path,
            "intake",
            f"round {round_number} deal-lead answer file changed",
        )
        intake_state = StageState.RUNNING.value
    elif revision and intake_state not in {
        StageState.RUNNING.value,
        StageState.AWAITING_INPUT.value,
    }:
        raise IntakeError(f"cannot revise answers from intake state {intake_state}")

    previous_records = answer_records(stored) if stored is not None else None
    payload, changed_ids, invalidation_targets = ingest_answer_records(
        answer_path=answer_path,
        run_id=run_id,
        round_number=round_number,
        questions=questions,
        previous_records=previous_records,
    )
    payload["status"] = "ingested"
    atomic_write_json(_answer_json_path(run_path, round_number), payload)

    round_two_invalidated = (
        revision and round_number == 1 and _question_json_path(run_path, 2).is_file()
    )
    if round_two_invalidated:
        reason = (
            "round-one answer evidence changed for "
            + ", ".join(changed_ids)
            + "; round two must be regenerated"
        )
        if intake_state == StageState.AWAITING_INPUT.value:
            manifest = resume_stage(run_path, "intake")
        _invalidate_round_two(run_path, run_id, reason)

    unresolved_count = _write_unresolved(run_path, run_id)
    if manifest["stages"]["intake"]["state"] == StageState.AWAITING_INPUT.value:
        manifest = resume_stage(run_path, "intake")
    if round_number == 2 and not round_two_invalidated:
        manifest = complete_stage(
            run_path,
            "intake",
            required_artifacts=INTAKE_OUTPUTS,
            invalidate_downstream_on_change=not revision,
        )

    earliest = _earliest_real_stage(invalidation_targets)
    if revision and changed_ids and earliest is not None:
        reason = (
            f"deal-lead answer evidence changed for {', '.join(changed_ids)}; "
            f"selective invalidation starts at {earliest}"
        )
        manifest = invalidate_from_stage(run_path, earliest, reason)

    append_json_line(
        run_path / "logs" / "events.jsonl",
        {
            "changed_question_ids": changed_ids,
            "event": "intake_answers_ingested",
            "explicit_ingestion": True,
            "round_number": round_number,
            "run_id": run_id,
            "stage_state": manifest["stages"]["intake"]["state"],
            "timestamp": utc_now(),
        },
    )
    return IntakeOutcome(
        action="answers_ingested",
        question_count=len(questions),
        reused=False,
        round_number=round_number,
        run_path=run_path,
        stage_state=str(manifest["stages"]["intake"]["state"]),
        unresolved_count=unresolved_count,
    )


def renormalize_intake_answers(run: str | Path) -> JsonObject:
    """Reapply the current conservative policy without altering verbatim answers.

    This is an explicit migration path for a normalization-policy correction. It preserves
    answer provenance and invalidates downstream analysis through the normal stage checksum
    mechanism when the interpretation changes.
    """

    run_path, manifest = load_manifest(run)
    run_id = str(manifest["run_id"])
    payloads: list[tuple[int, JsonObject]] = []
    input_artifacts: list[JsonObject] = []
    for round_number in (1, 2):
        _load_questions(run_path, run_id, round_number)
        answers = _load_answers_optional(run_path, run_id, round_number)
        if answers is None or answers.get("status") == "invalidated":
            raise IntakeError(
                "answer renormalization requires valid, explicitly ingested answers for both rounds"
            )
        payloads.append((round_number, answers))
        for path in (
            _question_json_path(run_path, round_number),
            _answer_json_path(run_path, round_number),
        ):
            input_artifacts.append(
                {"path": path.relative_to(run_path).as_posix(), "sha256": file_sha256(path)}
            )

    fingerprint = stable_json_checksum(
        {
            "answer_normalization_version": ANSWER_NORMALIZATION_VERSION,
            "artifacts": input_artifacts,
            "operation": "renormalize_existing_intake_answers",
        }
    )
    state = str(manifest["stages"]["intake"]["state"])
    if state == StageState.COMPLETED.value:
        manifest = reopen_completed_stage(
            run_path,
            "intake",
            f"answer policy migrated to {ANSWER_NORMALIZATION_VERSION}",
        )
    elif state == StageState.AWAITING_INPUT.value:
        manifest = resume_stage(run_path, "intake")
    elif state in {
        StageState.NOT_STARTED.value,
        StageState.FAILED.value,
        StageState.INVALIDATED.value,
    }:
        manifest = start_stage(run_path, "intake", input_checksum=fingerprint)
    elif state != StageState.RUNNING.value:
        raise IntakeError(f"cannot renormalize answers from intake state {state}")

    changed_question_ids: list[str] = []
    renormalized_at = utc_now()
    for round_number, payload in payloads:
        records = answer_records(payload)
        for record in records:
            normalized, ambiguity, resolution_status = normalize_answer(
                record.get("verbatim_answer")
            )
            if (
                record.get("normalised_interpretation") != normalized
                or record.get("ambiguity") != ambiguity
                or record.get("resolution_status") != resolution_status
            ):
                changed_question_ids.append(str(record.get("question_id")))
            record["normalised_interpretation"] = normalized
            record["ambiguity"] = ambiguity
            record["resolution_status"] = resolution_status
        payload["answer_normalization_version"] = ANSWER_NORMALIZATION_VERSION
        payload["renormalized_at"] = renormalized_at
        payload["status_counts"] = {
            resolution_status: sum(
                record.get("resolution_status") == resolution_status for record in records
            )
            for resolution_status in ("closed", "narrowed", "open")
        }
        atomic_write_json(_answer_json_path(run_path, round_number), payload)

    unresolved_count = _write_unresolved(run_path, run_id)
    manifest = complete_stage(run_path, "intake", required_artifacts=INTAKE_OUTPUTS)
    append_json_line(
        run_path / "logs" / "events.jsonl",
        {
            "answer_normalization_version": ANSWER_NORMALIZATION_VERSION,
            "changed_question_ids": changed_question_ids,
            "event": "intake_answers_renormalized",
            "run_id": run_id,
            "stage_state": manifest["stages"]["intake"]["state"],
            "timestamp": renormalized_at,
        },
    )
    return {
        "answer_normalization_version": ANSWER_NORMALIZATION_VERSION,
        "changed_question_ids": changed_question_ids,
        "run_id": run_id,
        "stage_state": manifest["stages"]["intake"]["state"],
        "unresolved_count": unresolved_count,
    }
