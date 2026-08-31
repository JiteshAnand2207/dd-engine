from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from dd_engine.config import load_config
from dd_engine.runs import create_run, load_manifest
from dd_engine.state import (
    ArtifactValidationError,
    complete_stage,
    fail_stage,
    mark_stage_awaiting_input,
    resume_stage,
    start_stage,
    write_run_json_artifact,
)


def checksum(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def create_test_run(tmp_path: Path) -> Path:
    return create_run(load_config(cwd=tmp_path))


def test_stage_state_transitions_require_validated_artifacts(tmp_path: Path) -> None:
    run_path = create_test_run(tmp_path)
    start_stage(run_path, "register", input_checksum=checksum("source-v1"))
    mark_stage_awaiting_input(run_path, "register")
    resume_stage(run_path, "register")
    artifact = write_run_json_artifact(run_path, "source_register/register.json", {"documents": []})

    manifest = complete_stage(run_path, "register", required_artifacts=[artifact])

    assert manifest["stages"]["register"]["state"] == "completed"
    assert manifest["stages"]["register"]["validation"]["passed"] is True
    assert manifest["stages"]["register"]["artifacts"][0]["run_id"] == run_path.name


def test_completion_failure_never_marks_stage_complete(tmp_path: Path) -> None:
    run_path = create_test_run(tmp_path)
    start_stage(run_path, "register", input_checksum=checksum("source-v1"))

    with pytest.raises(ArtifactValidationError, match="required artifact"):
        complete_stage(run_path, "register", required_artifacts=["source_register/missing.json"])

    _, manifest = load_manifest(run_path)
    assert manifest["stages"]["register"]["state"] == "running"
    assert manifest["stages"]["register"]["validation"]["passed"] is False


def test_failed_stage_error_persists_and_stage_can_rerun(tmp_path: Path) -> None:
    run_path = create_test_run(tmp_path)
    source_checksum = checksum("source-v1")
    start_stage(run_path, "register", input_checksum=source_checksum)

    fail_stage(run_path, "register", "simulated parser failure")
    _, failed_manifest = load_manifest(run_path)
    failed = failed_manifest["stages"]["register"]
    assert failed["state"] == "failed"
    assert failed["error"]["message"] == "simulated parser failure"
    assert failed["error_history"][0]["message"] == "simulated parser failure"

    rerun_manifest = start_stage(run_path, "register", input_checksum=source_checksum)
    rerun = rerun_manifest["stages"]["register"]
    assert rerun["state"] == "running"
    assert rerun["attempts"] == 2
    assert rerun["error"] is None
    assert rerun["error_history"][0]["message"] == "simulated parser failure"


def test_upstream_checksum_change_invalidates_completed_downstream(tmp_path: Path) -> None:
    run_path = create_test_run(tmp_path)
    first_source = checksum("source-v1")
    start_stage(run_path, "register", input_checksum=first_source)
    register_artifact = write_run_json_artifact(
        run_path, "source_register/register.json", {"version": 1}
    )
    register_manifest = complete_stage(run_path, "register", required_artifacts=[register_artifact])
    register_output = register_manifest["stages"]["register"]["output_checksum"]

    start_stage(run_path, "extract", input_checksum=register_output)
    extract_artifact = write_run_json_artifact(run_path, "extracts/index.json", {"items": []})
    complete_stage(run_path, "extract", required_artifacts=[extract_artifact])

    changed_manifest = start_stage(run_path, "register", input_checksum=checksum("source-v2"))

    assert changed_manifest["stages"]["register"]["state"] == "running"
    assert changed_manifest["stages"]["extract"]["state"] == "invalidated"
    assert "checksum changed" in changed_manifest["stages"]["extract"]["invalidation_reason"]


def test_artifact_with_wrong_run_id_is_rejected(tmp_path: Path) -> None:
    run_path = create_test_run(tmp_path)

    with pytest.raises(ArtifactValidationError, match="does not match"):
        write_run_json_artifact(
            run_path,
            "source_register/register.json",
            {"run_id": "another-run", "documents": []},
        )
