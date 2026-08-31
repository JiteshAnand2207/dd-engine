"""Run-directory creation and manifest loading."""

from __future__ import annotations

import re
import secrets
from pathlib import Path
from typing import Any

from dd_engine import __version__
from dd_engine.artifacts import append_json_line, atomic_write_json, load_json
from dd_engine.config import EngineConfig
from dd_engine.constants import RUN_DIRECTORY_NAMES, STAGE_ORDER, StageState
from dd_engine.errors import ArtifactError, RunError
from dd_engine.time import utc_now

RUN_ID_PATTERN = re.compile(r"^[0-9]{8}T[0-9]{12}Z-[a-f0-9]{12}$")


def new_run_id() -> str:
    """Create a sortable, unique and filesystem-safe run ID."""

    compact_time = utc_now().replace("-", "").replace(":", "").replace(".", "")
    return f"{compact_time}-{secrets.token_hex(6)}"


def _initial_stage() -> dict[str, Any]:
    return {
        "artifacts": [],
        "attempts": 0,
        "completed_at": None,
        "error": None,
        "error_history": [],
        "input_checksum": None,
        "invalidated_at": None,
        "invalidation_reason": None,
        "output_checksum": None,
        "started_at": None,
        "state": StageState.NOT_STARTED.value,
        "updated_at": None,
        "validation": {"checked_at": None, "errors": [], "passed": False},
    }


def _checkpoint_payload(manifest: dict[str, Any], stage_name: str) -> dict[str, Any]:
    return {
        "run_id": manifest["run_id"],
        "schema_version": manifest["schema_version"],
        "stage": stage_name,
        "stage_record": manifest["stages"][stage_name],
        "updated_at": manifest["updated_at"],
    }


def write_stage_checkpoint(run_path: Path, manifest: dict[str, Any], stage_name: str) -> None:
    """Write the auditable mirror of one stage record."""

    atomic_write_json(
        run_path / "checkpoints" / f"{stage_name}.json",
        _checkpoint_payload(manifest, stage_name),
    )


def create_run(config: EngineConfig, *, runs_root: Path | None = None) -> Path:
    """Create a complete run skeleton and its initial state artifacts."""

    root = (runs_root or config.runs_dir).expanduser().resolve(strict=False)
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RunError(f"cannot create runs directory {root}: {exc}") from exc
    if not root.is_dir():
        raise RunError(f"runs path is not a directory: {root}")

    run_path: Path | None = None
    run_id = ""
    for _ in range(32):
        run_id = new_run_id()
        candidate = root / run_id
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        except OSError as exc:
            raise RunError(f"cannot create run directory {candidate}: {exc}") from exc
        run_path = candidate
        break
    if run_path is None:
        raise RunError("could not allocate a unique run ID after 32 attempts")

    try:
        for directory_name in RUN_DIRECTORY_NAMES:
            (run_path / directory_name).mkdir()
        now = utc_now()
        manifest: dict[str, Any] = {
            "config": {
                "checksum": config.checksum,
                "external_logging_enabled": config.external_logging_enabled,
                "public_research_enabled": config.public_research_enabled,
                "require_api_key": config.require_api_key,
                "schema_version": config.schema_version,
                "telemetry_enabled": config.telemetry_enabled,
            },
            "created_at": now,
            "engine_version": __version__,
            "run_id": run_id,
            "schema_version": 1,
            "stage_order": list(STAGE_ORDER),
            "stages": {stage: _initial_stage() for stage in STAGE_ORDER},
            "updated_at": now,
        }
        atomic_write_json(run_path / "manifest.json", manifest)
        for stage_name in STAGE_ORDER:
            write_stage_checkpoint(run_path, manifest, stage_name)
        append_json_line(
            run_path / "logs" / "events.jsonl",
            {"event": "run_created", "run_id": run_id, "timestamp": now},
        )
    except (OSError, ArtifactError) as exc:
        raise RunError(
            f"run {run_id} was created but initialization failed; "
            f"partial artifacts were retained: {exc}"
        ) from exc
    return run_path


def normalize_run_path(path: str | Path) -> Path:
    """Resolve a run directory, accepting its manifest path as a convenience."""

    run_path = Path(path).expanduser().resolve(strict=False)
    if run_path.name == "manifest.json":
        run_path = run_path.parent
    return run_path


def load_manifest(path: str | Path) -> tuple[Path, dict[str, Any]]:
    """Load and structurally validate a run manifest."""

    run_path = normalize_run_path(path)
    if not run_path.is_dir():
        raise RunError(f"run directory not found: {run_path}")
    manifest_path = run_path / "manifest.json"
    try:
        manifest = load_json(manifest_path)
    except ArtifactError as exc:
        raise RunError(str(exc)) from exc

    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        raise RunError("manifest contains an invalid run_id")
    if run_path.name != run_id:
        raise RunError("run directory name does not match manifest run_id")
    if manifest.get("schema_version") != 1:
        raise RunError("unsupported run manifest schema version")

    missing_directories = [name for name in RUN_DIRECTORY_NAMES if not (run_path / name).is_dir()]
    if missing_directories:
        raise RunError(f"run is missing required directories: {', '.join(missing_directories)}")
    stages = manifest.get("stages")
    if (
        not isinstance(stages, dict)
        or set(stages) != set(STAGE_ORDER)
        or manifest.get("stage_order") != list(STAGE_ORDER)
    ):
        raise RunError("manifest has an invalid stage collection or ordering")
    for stage_name, stage in stages.items():
        if not isinstance(stage, dict) or stage.get("state") not in {
            state.value for state in StageState
        }:
            raise RunError(f"manifest has an invalid state for stage {stage_name}")
    return run_path, manifest
