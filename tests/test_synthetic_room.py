from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_synthetic_room_has_exact_composition() -> None:
    manifest = json.loads(
        (REPOSITORY_ROOT / "synthetic" / "room_manifest.json").read_text(encoding="utf-8")
    )
    room = REPOSITORY_ROOT / "synthetic" / "data_room"
    visible = [path for path in room.rglob("*") if path.is_file()]

    assert len(visible) == 90
    assert manifest["counts"]["visible_files"] == 90
    assert manifest["counts"]["zip_members"] == 10
    assert manifest["counts"]["logical_documents"] == 100
    assert manifest["counts"]["logical_by_workstream"] == {
        "financial": 27,
        "legal": 43,
        "tax": 30,
    }


def test_checked_in_synthetic_room_validator_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_synthetic_room.py",
            "--room",
            "synthetic/data_room",
            "--manifest",
            "synthetic/room_manifest.json",
            "--canonical",
            "synthetic/canonical_dataset.json",
            "--issues",
            "synthetic/planted_issues/issues.json",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Summary: PASS" in result.stdout
