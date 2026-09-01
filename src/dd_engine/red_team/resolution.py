"""Validate every red-team challenge disposition against run-local evidence."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from dd_engine.artifacts import atomic_write_json, atomic_write_text, file_sha256, load_json
from dd_engine.errors import RedTeamResolutionError
from dd_engine.evidence.citations import CitationValidator
from dd_engine.runs import load_manifest
from dd_engine.time import utc_now

JsonObject = dict[str, Any]

OUTCOMES = frozenset({"accepted", "rejected", "unresolved"})
ROOT_CAUSES = frozenset(
    {
        "inventory",
        "extraction",
        "version selection",
        "calculation",
        "retrieval/evidence packaging",
        "intake",
        "reasoning",
        "drafting",
        "citation validation",
        "output formatting",
    }
)


def _challenge_log(red_team_dir: Path) -> Path:
    candidates = sorted(red_team_dir.glob("*_challenge_log.json"))
    if len(candidates) != 1:
        raise RedTeamResolutionError(
            "red-team reconciliation requires exactly one JSON challenge log"
        )
    return candidates[0]


def _nonempty_strings(value: object, field: str, challenge_id: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise RedTeamResolutionError(f"{challenge_id} requires non-empty {field}")
    return [str(item).strip() for item in value]


def _validate_artifact_reference(run_path: Path, evidence: JsonObject) -> None:
    raw_path = evidence.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise RedTeamResolutionError("artifact verification evidence requires path")
    resolved = (run_path / raw_path).resolve(strict=False)
    if not resolved.is_relative_to(run_path) or not resolved.is_file():
        raise RedTeamResolutionError(f"verification artifact is missing or unsafe: {raw_path}")
    observed = file_sha256(resolved)
    supplied = evidence.get("sha256")
    if supplied not in {None, observed}:
        raise RedTeamResolutionError(f"verification artifact checksum mismatch: {raw_path}")
    evidence["path"] = resolved.relative_to(run_path).as_posix()
    evidence["sha256"] = observed


def _validate_source_reference(
    validator: CitationValidator, evidence: JsonObject, challenge_id: str
) -> None:
    source_id = evidence.get("source_id")
    locator = evidence.get("locator")
    if not isinstance(source_id, str) or not isinstance(locator, dict):
        raise RedTeamResolutionError(
            f"{challenge_id} source verification evidence requires source_id and locator"
        )
    source = validator.sources.get(source_id)
    if source is None:
        raise RedTeamResolutionError(f"{challenge_id} references unknown source {source_id}")
    registered_checksum = str(source["sha256"])
    supplied_checksum = evidence.get("source_checksum")
    if supplied_checksum not in {None, registered_checksum}:
        raise RedTeamResolutionError(
            f"{challenge_id} source checksum does not match the register for {source_id}"
        )
    evidence["source_checksum"] = registered_checksum
    result = validator.validate_reference(
        source_id=source_id,
        source_checksum=registered_checksum,
        locator=locator,
        extracted_text=(
            str(evidence["extracted_text"])
            if isinstance(evidence.get("extracted_text"), str)
            else None
        ),
        extracted_value=evidence.get("extracted_value"),
    )
    if not result["valid"]:
        codes = ", ".join(str(item["code"]) for item in result["errors"])
        raise RedTeamResolutionError(
            f"{challenge_id} has an invalid source citation for {source_id}: {codes}"
        )
    evidence["citation_validation"] = "passed"


def _validate_disposition(
    run_path: Path,
    validator: CitationValidator,
    disposition: JsonObject,
) -> None:
    challenge_id = str(disposition.get("challenge_id", ""))
    outcome = disposition.get("outcome")
    if outcome not in OUTCOMES:
        raise RedTeamResolutionError(f"{challenge_id} has invalid outcome {outcome!r}")
    decision = disposition.get("decision")
    if not isinstance(decision, str) or not decision.strip():
        raise RedTeamResolutionError(f"{challenge_id} requires a decision explanation")
    root_causes = disposition.get("root_causes")
    if not isinstance(root_causes, list) or not root_causes:
        raise RedTeamResolutionError(f"{challenge_id} requires root_causes")
    invalid_causes = [cause for cause in root_causes if cause not in ROOT_CAUSES]
    if invalid_causes:
        raise RedTeamResolutionError(
            f"{challenge_id} has invalid root cause(s): {', '.join(map(str, invalid_causes))}"
        )
    evidence_items = disposition.get("verification_evidence")
    if not isinstance(evidence_items, list) or not evidence_items:
        raise RedTeamResolutionError(f"{challenge_id} requires verification_evidence")
    for raw_evidence in evidence_items:
        if not isinstance(raw_evidence, dict):
            raise RedTeamResolutionError(f"{challenge_id} contains non-object evidence")
        observation = raw_evidence.get("observation")
        if not isinstance(observation, str) or not observation.strip():
            raise RedTeamResolutionError(f"{challenge_id} evidence requires an observation")
        kind = raw_evidence.get("kind")
        if kind == "source":
            _validate_source_reference(validator, raw_evidence, challenge_id)
        elif kind == "artifact":
            _validate_artifact_reference(run_path, raw_evidence)
        else:
            raise RedTeamResolutionError(f"{challenge_id} evidence has invalid kind {kind!r}")
    disposition["files_changed"] = _nonempty_strings(
        disposition.get("files_changed"), "files_changed", challenge_id
    )
    disposition["regression_tests"] = _nonempty_strings(
        disposition.get("regression_tests"), "regression_tests", challenge_id
    )
    disposition["regenerated_artifacts"] = _nonempty_strings(
        disposition.get("regenerated_artifacts"), "regenerated_artifacts", challenge_id
    )


def _locator_text(locator: object) -> str:
    if not isinstance(locator, dict):
        return "unspecified locator"
    if locator.get("type") == "pdf_page":
        return f"page {locator.get('page_number')}"
    if locator.get("type") == "spreadsheet_cell":
        return f"{locator.get('sheet')}!{locator.get('cell') or locator.get('range')}"
    if locator.get("type") == "docx_paragraph":
        return f"paragraph {locator.get('paragraph_index')}"
    if locator.get("type") == "csv_cell":
        return f"row {locator.get('row_index')}, column {locator.get('column_index')}"
    if locator.get("type") == "image":
        return f"image {locator.get('image_number')}"
    return str(locator.get("type") or "structured locator")


def _render_markdown(payload: JsonObject) -> str:
    summary = payload["summary"]
    lines = [
        "# Independent red-team resolution",
        "",
        f"Run ID: `{payload['run_id']}`",
        "",
        (
            f"Disposition: {summary['accepted']} accepted, {summary['rejected']} rejected, "
            f"{summary['unresolved']} unresolved ({summary['total']} total)."
        ),
        "",
        "The red-team labels were treated as hypotheses. Each decision below was checked against "
        "the registered original source or a hashed run artifact and its validated extraction. "
        "Accepted challenges were corrected in the pipeline and not only in final Markdown.",
        "",
    ]
    for disposition in payload["dispositions"]:
        lines.extend(
            [
                f"## {disposition['challenge_id']} — {str(disposition['outcome']).upper()}",
                "",
                str(disposition["decision"]),
                "",
                "Verification evidence:",
                "",
            ]
        )
        for evidence in disposition["verification_evidence"]:
            if evidence["kind"] == "source":
                citation = f"{evidence['source_id']} ({_locator_text(evidence['locator'])})"
            else:
                citation = f"`{evidence['path']}` ({evidence.get('locator', 'artifact')})"
            lines.append(f"- {citation}: {evidence['observation']}")
        lines.extend(
            [
                "",
                f"Root cause: {', '.join(disposition['root_causes'])}.",
                "",
                "Files changed: " + ", ".join(f"`{item}`" for item in disposition["files_changed"]),
                "",
                "Regression test: "
                + ", ".join(f"`{item}`" for item in disposition["regression_tests"]),
                "",
                "Regenerated artifacts: "
                + ", ".join(f"`{item}`" for item in disposition["regenerated_artifacts"]),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def reconcile_red_team(run: str | Path, disposition_file: str | Path) -> JsonObject:
    """Validate complete dispositions and write the canonical JSON and Markdown pair."""

    run_path, manifest = load_manifest(run)
    run_id = str(manifest["run_id"])
    input_path = Path(disposition_file).expanduser().resolve(strict=False)
    if not input_path.is_file():
        raise RedTeamResolutionError(f"red-team disposition file not found: {input_path}")
    payload = load_json(input_path)
    if payload.get("run_id") not in {None, run_id}:
        raise RedTeamResolutionError("red-team dispositions belong to another run")
    dispositions = payload.get("dispositions")
    if not isinstance(dispositions, list) or not dispositions:
        raise RedTeamResolutionError("red-team dispositions require a non-empty list")
    if not all(isinstance(item, dict) for item in dispositions):
        raise RedTeamResolutionError("red-team disposition list contains a non-object")

    red_team_dir = run_path / "red_team"
    challenge_path = _challenge_log(red_team_dir)
    challenge_payload = load_json(challenge_path)
    challenges = challenge_payload.get("challenges")
    if not isinstance(challenges, list):
        raise RedTeamResolutionError("red-team challenge log has no challenge list")
    challenge_ids = [str(item.get("challenge_id")) for item in challenges if isinstance(item, dict)]
    disposition_ids = [str(item.get("challenge_id")) for item in dispositions]
    if len(disposition_ids) != len(set(disposition_ids)):
        raise RedTeamResolutionError("red-team dispositions contain duplicate challenge IDs")
    if set(disposition_ids) != set(challenge_ids):
        missing = sorted(set(challenge_ids) - set(disposition_ids))
        extra = sorted(set(disposition_ids) - set(challenge_ids))
        raise RedTeamResolutionError(
            f"red-team disposition coverage mismatch; missing={missing}, extra={extra}"
        )
    ordered = {challenge_id: index for index, challenge_id in enumerate(challenge_ids)}
    dispositions.sort(key=lambda item: ordered[str(item["challenge_id"])])
    validator = CitationValidator(run_path)
    for disposition in dispositions:
        _validate_disposition(run_path, validator, disposition)

    counts = Counter(str(item["outcome"]) for item in dispositions)
    payload.update(
        {
            "challenge_log_path": challenge_path.relative_to(run_path).as_posix(),
            "challenge_log_sha256": file_sha256(challenge_path),
            "dispositions": dispositions,
            "generated_at": utc_now(),
            "run_id": run_id,
            "schema_version": 1,
            "summary": {
                "accepted": counts["accepted"],
                "rejected": counts["rejected"],
                "total": len(dispositions),
                "unresolved": counts["unresolved"],
            },
        }
    )
    json_path = red_team_dir / "red_team_resolution.json"
    markdown_path = red_team_dir / "red_team_resolution.md"
    atomic_write_json(json_path, payload)
    atomic_write_text(markdown_path, _render_markdown(payload))
    return payload
