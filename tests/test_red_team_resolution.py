from __future__ import annotations

import json
from pathlib import Path

import pytest

from dd_engine.config import load_config
from dd_engine.errors import RedTeamResolutionError
from dd_engine.extraction import extract_run
from dd_engine.inventory import RegisterLimits, register_room
from dd_engine.red_team import reconcile_red_team
from dd_engine.runs import create_run

LIMITS = RegisterLimits(
    max_archive_members=20,
    max_archive_total_uncompressed_bytes=1024 * 1024,
    max_archive_member_uncompressed_bytes=1024 * 1024,
)


def _resolution_run(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    room = tmp_path / "room"
    room.mkdir()
    (room / "evidence.csv").write_text("Metric,Value\nObserved,42\n", encoding="utf-8")
    config = load_config(cwd=tmp_path)
    run_path = create_run(config, runs_root=tmp_path / "runs")
    register_room(run_path, room, LIMITS)
    extract_run(run_path, room, config)
    register = json.loads(
        (run_path / "source_register" / "source_register.json").read_text(encoding="utf-8")
    )
    return run_path, register["sources"][0]


def test_resolution_requires_complete_validated_challenge_coverage(tmp_path: Path) -> None:
    run_path, source = _resolution_run(tmp_path)
    challenge_id = "CH-ALPHA"
    challenge_path = run_path / "red_team" / "independent_challenge_log.json"
    challenge_path.write_text(
        json.dumps(
            {
                "challenges": [{"challenge_id": challenge_id}],
                "run_id": run_path.name,
                "schema_version": 1,
            }
        ),
        encoding="utf-8",
    )
    input_path = tmp_path / "resolution.json"
    input_path.write_text(
        json.dumps(
            {
                "dispositions": [
                    {
                        "challenge_id": challenge_id,
                        "decision": "The original source supports the corrected disposition.",
                        "files_changed": ["src/dd_engine/example.py"],
                        "outcome": "accepted",
                        "regenerated_artifacts": ["outputs/example.md"],
                        "regression_tests": ["tests/test_example.py::test_source_check"],
                        "root_causes": ["reasoning"],
                        "verification_evidence": [
                            {
                                "kind": "source",
                                "locator": {
                                    "column_index": 2,
                                    "row_index": 2,
                                    "type": "csv_cell",
                                },
                                "observation": "The cited cell contains the observed value.",
                                "source_id": source["source_id"],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = reconcile_red_team(run_path, input_path)

    assert result["summary"] == {
        "accepted": 1,
        "rejected": 0,
        "total": 1,
        "unresolved": 0,
    }
    evidence = result["dispositions"][0]["verification_evidence"][0]
    assert evidence["source_checksum"] == source["sha256"]
    assert evidence["citation_validation"] == "passed"
    assert (run_path / "red_team" / "red_team_resolution.json").is_file()
    assert challenge_id in (run_path / "red_team" / "red_team_resolution.md").read_text(
        encoding="utf-8"
    )


def test_resolution_rejects_missing_challenge_disposition(tmp_path: Path) -> None:
    run_path, _ = _resolution_run(tmp_path)
    (run_path / "red_team" / "independent_challenge_log.json").write_text(
        json.dumps({"challenges": [{"challenge_id": "CH-ALPHA"}], "run_id": run_path.name}),
        encoding="utf-8",
    )
    input_path = tmp_path / "empty-resolution.json"
    input_path.write_text(json.dumps({"dispositions": []}), encoding="utf-8")

    with pytest.raises(RedTeamResolutionError, match="non-empty list"):
        reconcile_red_team(run_path, input_path)
