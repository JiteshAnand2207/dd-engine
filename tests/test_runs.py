from __future__ import annotations

import json
from pathlib import Path

from dd_engine.config import load_config
from dd_engine.constants import RUN_DIRECTORY_NAMES, STAGE_ORDER
from dd_engine.runs import RUN_ID_PATTERN, create_run, load_manifest


def test_run_creation_has_complete_structure_and_provenance(tmp_path: Path) -> None:
    config = load_config(cwd=tmp_path)

    run_path = create_run(config)
    _, manifest = load_manifest(run_path)
    run_id = manifest["run_id"]

    assert run_path.parent == tmp_path / "runs"
    assert RUN_ID_PATTERN.fullmatch(run_id)
    assert (run_path / "manifest.json").is_file()
    assert all((run_path / name).is_dir() for name in RUN_DIRECTORY_NAMES)
    assert list(manifest["stage_order"]) == list(STAGE_ORDER)
    assert all(manifest["stages"][stage]["state"] == "not_started" for stage in STAGE_ORDER)

    for checkpoint in (run_path / "checkpoints").glob("*.json"):
        assert json.loads(checkpoint.read_text(encoding="utf-8"))["run_id"] == run_id
    event = json.loads((run_path / "logs" / "events.jsonl").read_text(encoding="utf-8"))
    assert event["run_id"] == run_id


def test_run_ids_are_unique(tmp_path: Path) -> None:
    config = load_config(cwd=tmp_path)

    run_paths = {create_run(config) for _ in range(40)}

    assert len(run_paths) == 40
    assert len({path.name for path in run_paths}) == 40


def test_cross_platform_paths_with_spaces_and_unicode(tmp_path: Path) -> None:
    runs_root = tmp_path / "portable path" / "diligence-Δ"
    config = load_config(cwd=tmp_path)

    run_path = create_run(config, runs_root=runs_root)
    loaded_path, manifest = load_manifest(run_path / "manifest.json")

    assert loaded_path == run_path.resolve()
    assert loaded_path.parent == runs_root.resolve()
    assert manifest["run_id"] == run_path.name
