"""Resumable stage-state transitions and checksum invalidation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from dd_engine.artifacts import (
    aggregate_artifact_checksum,
    atomic_write_json,
    validate_run_artifact,
)
from dd_engine.constants import STAGE_ORDER, StageState
from dd_engine.errors import ArtifactValidationError, StageTransitionError
from dd_engine.runs import load_manifest, write_stage_checkpoint
from dd_engine.time import utc_now


def _require_stage(manifest: dict[str, Any], stage_name: str) -> dict[str, Any]:
    if stage_name not in STAGE_ORDER:
        raise StageTransitionError(f"unknown stage: {stage_name}")
    stage = manifest["stages"][stage_name]
    if not isinstance(stage, dict):
        raise StageTransitionError(f"corrupt stage record: {stage_name}")
    return stage


def _require_checksum(checksum: str) -> str:
    normalized = checksum.lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise StageTransitionError("checksum must be a 64-character SHA-256 hex digest")
    return normalized


def _persist(
    run_path: Path, manifest: dict[str, Any], changed_stages: Iterable[str]
) -> dict[str, Any]:
    manifest["updated_at"] = utc_now()
    atomic_write_json(run_path / "manifest.json", manifest)
    for stage_name in dict.fromkeys(changed_stages):
        write_stage_checkpoint(run_path, manifest, stage_name)
    return manifest


def _invalidate_downstream(manifest: dict[str, Any], stage_name: str, reason: str) -> list[str]:
    changed: list[str] = []
    now = utc_now()
    start = STAGE_ORDER.index(stage_name) + 1
    for downstream_name in STAGE_ORDER[start:]:
        downstream = manifest["stages"][downstream_name]
        if downstream["state"] == StageState.NOT_STARTED.value:
            continue
        downstream["state"] = StageState.INVALIDATED.value
        downstream["completed_at"] = None
        downstream["invalidated_at"] = now
        downstream["invalidation_reason"] = reason
        downstream["updated_at"] = now
        downstream["validation"] = {"checked_at": now, "errors": [reason], "passed": False}
        changed.append(downstream_name)
    return changed


def _require_upstream_complete(manifest: dict[str, Any], stage_name: str) -> None:
    for upstream_name in STAGE_ORDER[: STAGE_ORDER.index(stage_name)]:
        upstream_state = manifest["stages"][upstream_name]["state"]
        if upstream_state != StageState.COMPLETED.value:
            raise StageTransitionError(
                f"cannot start {stage_name}: upstream stage {upstream_name} is {upstream_state}"
            )


def start_stage(path: str | Path, stage_name: str, *, input_checksum: str) -> dict[str, Any]:
    """Start or safely resume a stage for a specific input checksum."""

    run_path, manifest = load_manifest(path)
    stage = _require_stage(manifest, stage_name)
    checksum = _require_checksum(input_checksum)
    changed = [stage_name]
    previous_checksum = stage["input_checksum"]
    if previous_checksum is not None and previous_checksum != checksum:
        reason = f"{stage_name} input checksum changed from {previous_checksum} to {checksum}"
        if stage["state"] != StageState.NOT_STARTED.value:
            stage["state"] = StageState.INVALIDATED.value
            stage["completed_at"] = None
            stage["invalidated_at"] = utc_now()
            stage["invalidation_reason"] = reason
            stage["validation"] = {
                "checked_at": utc_now(),
                "errors": [reason],
                "passed": False,
            }
        changed.extend(_invalidate_downstream(manifest, stage_name, reason))
    stage["input_checksum"] = checksum

    if stage["state"] == StageState.COMPLETED.value:
        return manifest
    if stage["state"] == StageState.RUNNING.value:
        return _persist(run_path, manifest, changed)
    if stage["state"] not in {
        StageState.NOT_STARTED.value,
        StageState.FAILED.value,
        StageState.INVALIDATED.value,
    }:
        raise StageTransitionError(f"cannot start {stage_name} from state {stage['state']}")

    _require_upstream_complete(manifest, stage_name)
    now = utc_now()
    stage["state"] = StageState.RUNNING.value
    stage["attempts"] += 1
    stage["started_at"] = now
    stage["updated_at"] = now
    stage["completed_at"] = None
    stage["error"] = None
    return _persist(run_path, manifest, changed)


def mark_stage_awaiting_input(path: str | Path, stage_name: str) -> dict[str, Any]:
    """Pause a running stage for explicit human input."""

    run_path, manifest = load_manifest(path)
    stage = _require_stage(manifest, stage_name)
    if stage["state"] != StageState.RUNNING.value:
        raise StageTransitionError(
            f"cannot await input for {stage_name} from state {stage['state']}"
        )
    stage["state"] = StageState.AWAITING_INPUT.value
    stage["updated_at"] = utc_now()
    return _persist(run_path, manifest, [stage_name])


def resume_stage(path: str | Path, stage_name: str) -> dict[str, Any]:
    """Resume a stage after explicit input has been supplied."""

    run_path, manifest = load_manifest(path)
    stage = _require_stage(manifest, stage_name)
    if stage["state"] != StageState.AWAITING_INPUT.value:
        raise StageTransitionError(f"cannot resume {stage_name} from state {stage['state']}")
    stage["state"] = StageState.RUNNING.value
    stage["updated_at"] = utc_now()
    return _persist(run_path, manifest, [stage_name])


def fail_stage(path: str | Path, stage_name: str, error: str) -> dict[str, Any]:
    """Persist a stage failure and its diagnostic without deleting partial artifacts."""

    if not error.strip():
        raise StageTransitionError("a failed stage requires a non-empty error")
    run_path, manifest = load_manifest(path)
    stage = _require_stage(manifest, stage_name)
    if stage["state"] not in {
        StageState.RUNNING.value,
        StageState.AWAITING_INPUT.value,
    }:
        raise StageTransitionError(f"cannot fail {stage_name} from state {stage['state']}")
    failure: dict[str, str] = {"at": utc_now(), "message": error}
    stage["state"] = StageState.FAILED.value
    stage["error"] = failure
    stage["error_history"].append(failure)
    stage["updated_at"] = failure["at"]
    return _persist(run_path, manifest, [stage_name])


def write_run_json_artifact(
    path: str | Path, relative_path: str | Path, payload: Mapping[str, Any]
) -> Path:
    """Write a JSON artifact inside a run while forcing run-ID provenance."""

    run_path, manifest = load_manifest(path)
    artifact_path = run_path / relative_path
    resolved = artifact_path.resolve(strict=False)
    if not resolved.is_relative_to(run_path) or resolved == run_path:
        raise ArtifactValidationError("artifact path must remain inside the run directory")
    if resolved in {run_path / "manifest.json"} or (run_path / "checkpoints") in resolved.parents:
        raise ArtifactValidationError("reserved state artifacts cannot be overwritten")
    value = dict(payload)
    supplied_run_id = value.get("run_id")
    if supplied_run_id not in {None, manifest["run_id"]}:
        raise ArtifactValidationError("artifact run_id does not match the run")
    value["run_id"] = manifest["run_id"]
    atomic_write_json(resolved, value)
    return resolved


def complete_stage(
    path: str | Path, stage_name: str, *, required_artifacts: Iterable[str | Path]
) -> dict[str, Any]:
    """Complete a running stage only after every required artifact validates."""

    run_path, manifest = load_manifest(path)
    stage = _require_stage(manifest, stage_name)
    if stage["state"] != StageState.RUNNING.value:
        raise StageTransitionError(f"cannot complete {stage_name} from state {stage['state']}")

    artifacts = list(required_artifacts)
    errors: list[str] = []
    metadata: list[dict[str, Any]] = []
    if not artifacts:
        errors.append("at least one required artifact must be declared")
    for artifact in artifacts:
        item, item_errors = validate_run_artifact(run_path, artifact, manifest["run_id"])
        errors.extend(f"{artifact}: {error}" for error in item_errors)
        if item is not None:
            metadata.append(item)
    checked_at = utc_now()
    stage["validation"] = {"checked_at": checked_at, "errors": errors, "passed": not errors}
    stage["updated_at"] = checked_at
    if errors:
        _persist(run_path, manifest, [stage_name])
        raise ArtifactValidationError("; ".join(errors))

    new_checksum = aggregate_artifact_checksum(metadata)
    old_checksum = stage["output_checksum"]
    changed = [stage_name]
    if old_checksum is not None and old_checksum != new_checksum:
        reason = f"{stage_name} output checksum changed from {old_checksum} to {new_checksum}"
        changed.extend(_invalidate_downstream(manifest, stage_name, reason))
    stage["artifacts"] = metadata
    stage["completed_at"] = checked_at
    stage["invalidated_at"] = None
    stage["invalidation_reason"] = None
    stage["output_checksum"] = new_checksum
    stage["state"] = StageState.COMPLETED.value
    stage["error"] = None
    return _persist(run_path, manifest, changed)


def overall_state(manifest: Mapping[str, Any]) -> str:
    """Summarize a manifest without hiding an adverse state."""

    states = [manifest["stages"][name]["state"] for name in STAGE_ORDER]
    for state in (
        StageState.FAILED.value,
        StageState.RUNNING.value,
        StageState.AWAITING_INPUT.value,
        StageState.INVALIDATED.value,
    ):
        if state in states:
            return state
    if all(state == StageState.COMPLETED.value for state in states):
        return StageState.COMPLETED.value
    return StageState.NOT_STARTED.value
