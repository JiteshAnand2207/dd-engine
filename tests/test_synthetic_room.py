from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from dd_engine.source_paths import (
    EMPTY_DIRECTORY_MARKER,
    EMPTY_DIRECTORY_MARKER_CONTENT,
    is_logically_empty_directory,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_synthetic_room_has_exact_composition() -> None:
    manifest = json.loads(
        (REPOSITORY_ROOT / "synthetic" / "room_manifest.json").read_text(encoding="utf-8")
    )
    room = REPOSITORY_ROOT / "synthetic" / "data_room"
    visible = [
        path
        for path in room.rglob("*")
        if path.is_file() and path.name != EMPTY_DIRECTORY_MARKER
    ]

    assert len(visible) == 90
    assert manifest["counts"]["visible_files"] == 90
    assert manifest["counts"]["zip_members"] == 10
    assert manifest["counts"]["logical_documents"] == 100
    assert manifest["counts"]["logical_by_workstream"] == {
        "financial": 27,
        "legal": 43,
        "tax": 30,
    }


def test_checked_in_empty_directory_markers_are_logically_empty_and_git_tracked() -> None:
    marker_paths = (
        REPOSITORY_ROOT
        / "synthetic"
        / "data_room"
        / "Legal"
        / "Legal 2.1"
        / EMPTY_DIRECTORY_MARKER,
        REPOSITORY_ROOT
        / "synthetic"
        / "shadow"
        / "data_room"
        / "03_People_Systems"
        / "Intentionally Empty"
        / EMPTY_DIRECTORY_MARKER,
    )

    assert all(path.read_bytes() == EMPTY_DIRECTORY_MARKER_CONTENT for path in marker_paths)
    assert all(is_logically_empty_directory(path.parent) for path in marker_paths)
    for marker in marker_paths:
        ignored = subprocess.run(
            [
                "git",
                "check-ignore",
                "--quiet",
                "--",
                marker.relative_to(REPOSITORY_ROOT).as_posix(),
            ],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert ignored.returncode == 1, ignored.stdout + ignored.stderr


def test_same_seed_generations_preserve_marker_deterministically(tmp_path: Path) -> None:
    issues_path = tmp_path / "test-only-issues.json"
    issues_path.write_text(
        json.dumps({"issue_count": 10, "issues": [{} for _ in range(10)]}), encoding="utf-8"
    )
    generated: list[Path] = []
    for name in ("first", "second"):
        root = tmp_path / name
        room = root / "data_room"
        metadata = root / "metadata"
        subprocess.run(
            [
                sys.executable,
                "scripts/generate_synthetic_room.py",
                "--output",
                str(room),
                "--metadata-root",
                str(metadata),
                "--issues",
                str(issues_path),
                "--seed",
                "314159",
            ],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        generated.append(root)

    def tree(root: Path) -> list[tuple[str, bytes]]:
        return [
            (path.relative_to(root).as_posix(), path.read_bytes())
            for path in sorted(root.rglob("*"))
            if path.is_file()
        ]

    assert tree(generated[0]) == tree(generated[1])
    assert (
        generated[0] / "data_room" / "Legal" / "Legal 2.1" / EMPTY_DIRECTORY_MARKER
    ).read_bytes() == EMPTY_DIRECTORY_MARKER_CONTENT


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
            "--public-only",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Summary: PASS" in result.stdout
