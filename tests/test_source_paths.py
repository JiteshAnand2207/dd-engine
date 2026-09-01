from __future__ import annotations

from pathlib import Path

import pytest

from dd_engine.errors import SourcePathError
from dd_engine.source_paths import iter_data_room_files, validate_data_room_path


def test_explicit_room_walk_cannot_reach_sibling_ground_truth(tmp_path: Path) -> None:
    room = tmp_path / "synthetic" / "data_room"
    room.mkdir(parents=True)
    source = room / "Financial" / "accounts.pdf"
    source.parent.mkdir()
    source.write_bytes(b"fixture")
    planted = tmp_path / "synthetic" / "planted_issues"
    planted.mkdir()
    (planted / "issues.json").write_text("{}", encoding="utf-8")

    files = list(iter_data_room_files(room))

    assert files == [source.resolve()]
    assert validate_data_room_path(room) == room.resolve()


def test_ground_truth_path_is_rejected_as_a_room(tmp_path: Path) -> None:
    planted = tmp_path / "synthetic" / "planted_issues"
    planted.mkdir(parents=True)

    with pytest.raises(SourcePathError, match="planted_issues"):
        validate_data_room_path(planted)


def test_nested_ground_truth_directory_fails_closed(tmp_path: Path) -> None:
    room = tmp_path / "room"
    hidden_ground_truth = room / "planted_issues"
    hidden_ground_truth.mkdir(parents=True)
    (hidden_ground_truth / "issues.json").write_text("{}", encoding="utf-8")

    with pytest.raises(SourcePathError, match="forbidden planted-issues"):
        list(iter_data_room_files(room))


def test_shadow_ground_truth_path_is_rejected_as_a_room(tmp_path: Path) -> None:
    truth = tmp_path / "synthetic" / "shadow_ground_truth"
    truth.mkdir(parents=True)
    (truth / "issues.json").write_text("{}", encoding="utf-8")

    with pytest.raises(SourcePathError):
        validate_data_room_path(truth)


def test_relative_room_path_is_resolved_from_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    room = tmp_path / "relative room"
    room.mkdir()
    monkeypatch.chdir(tmp_path)

    assert validate_data_room_path(Path("relative room")) == room.resolve()
