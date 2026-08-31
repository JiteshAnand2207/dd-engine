from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest

from dd_engine.cli import main
from dd_engine.config import load_config
from dd_engine.errors import SourcePathError
from dd_engine.inventory import RegisterLimits, register_room
from dd_engine.inventory.archives import canonical_relative_path
from dd_engine.inventory.register import REGISTER_OUTPUTS, inventory_room
from dd_engine.runs import create_run, load_manifest

LIMITS = RegisterLimits(
    max_archive_members=50,
    max_archive_total_uncompressed_bytes=2 * 1024 * 1024,
    max_archive_member_uncompressed_bytes=512 * 1024,
)


def write_file(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def test_duplicates_versions_mismatch_and_empty_directory(tmp_path: Path) -> None:
    room = tmp_path / "room"
    write_file(room / "Financial" / "Loan_Summary.txt", b"same debt schedule\n")
    write_file(room / "Legal" / "Loan_Copy.txt", b"same debt schedule\n")
    write_file(room / "Legal" / "First" / "Registration.txt", b"first\n")
    write_file(room / "Tax" / "Second" / "Registration.txt", b"second\n")
    write_file(room / "Tax" / "Tax_Summary_Original.xlsx", b"Question,Answer\nVAT,Yes\n")
    write_file(room / "Tax" / "Tax_Summary_Rev2.xlsx", b"Question,Answer\nVAT,No\n")
    (room / "Legal" / "Empty Area").mkdir(parents=True)

    result = inventory_room(room, LIMITS)

    assert len(result.duplicate_groups) == 1
    assert len(result.same_basename_conflicts) == 1
    assert len(result.version_families) == 1
    assert len(result.near_duplicate_candidates) == 1
    assert result.empty_directories == ("Legal/Empty Area",)
    renamed = [item for item in result.sources if item["filename"].endswith(".xlsx")]
    assert {item["detected_type"] for item in renamed} == {"csv"}
    assert all(item["extension_type_mismatch"] is True for item in renamed)
    root_level = next(
        item for item in result.sources if item["relative_path"] == "Financial/Loan_Summary.txt"
    )
    assert root_level["folder_area"] == "Financial"
    exact = [item for item in result.sources if item["duplicate_group"]]
    assert sum(bool(item["include_in_analysis"]) for item in exact) == 1
    versioned = [item for item in result.sources if item["version_family"]]
    assert all(item["include_in_analysis"] for item in versioned)


def test_zip_traversal_absolute_and_symlink_members_are_blocked(tmp_path: Path) -> None:
    room = tmp_path / "room"
    room.mkdir()
    archive_path = room / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.txt", b"escape")
        archive.writestr("/absolute.txt", b"absolute")
        symlink = zipfile.ZipInfo("link.txt")
        symlink.create_system = 3
        symlink.external_attr = (0o120777 << 16) | 0xA000
        archive.writestr(symlink, b"../outside.txt")
        archive.writestr("safe.txt", b"safe")

    result = inventory_room(room, LIMITS)
    members = [item for item in result.sources if item["container_path"]]

    assert len(members) == 4
    assert sum(item["inventory_status"] == "blocked_unsafe" for item in members) == 3
    assert all("../" not in item["relative_path"] for item in members)
    assert not (tmp_path / "escape.txt").exists()
    assert result.summary["terminal_inventory_entries"] == len(result.sources)


def test_archive_member_size_and_count_limits_are_terminal(tmp_path: Path) -> None:
    room = tmp_path / "room"
    room.mkdir()
    archive_path = room / "bounded.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("large.txt", b"0123456789")
        archive.writestr("small.txt", b"ok")

    size_limited = inventory_room(
        room,
        RegisterLimits(10, 100, 5),
    )
    size_members = [item for item in size_limited.sources if item["container_path"]]
    assert [item["inventory_status"] for item in size_members] == [
        "blocked_unsafe",
        "registered",
    ]
    assert size_members[0]["sha256"] is None

    count_limited = inventory_room(
        room,
        RegisterLimits(1, 100, 20),
    )
    count_members = [item for item in count_limited.sources if item["container_path"]]
    assert all(item["inventory_status"] == "blocked_unsafe" for item in count_members)
    assert count_limited.summary["terminal_inventory_entries"] == 3

    total_limited = inventory_room(
        room,
        RegisterLimits(10, 11, 20),
    )
    total_members = [item for item in total_limited.sources if item["container_path"]]
    assert all(item["inventory_status"] == "blocked_unsafe" for item in total_members)
    assert total_limited.summary["terminal_inventory_entries"] == 3


def test_duplicate_zip_member_names_get_distinct_virtual_paths(tmp_path: Path) -> None:
    room = tmp_path / "room"
    room.mkdir()
    with (
        pytest.warns(UserWarning, match="Duplicate name"),
        zipfile.ZipFile(room / "duplicates.zip", "w") as archive,
    ):
        archive.writestr("same.txt", b"first")
        archive.writestr("same.txt", b"second")

    result = inventory_room(room, LIMITS)
    members = [item for item in result.sources if item["container_path"]]

    assert len({item["relative_path"] for item in members}) == 2
    assert members[1]["relative_path"].endswith("#entry-0002")
    assert all("duplicate_archive_member_name" in item["warnings"] for item in members)


def test_corrupted_file_does_not_fail_room(tmp_path: Path) -> None:
    room = tmp_path / "room"
    write_file(room / "good.txt", b"readable\n")
    write_file(room / "broken.pdf", b"%PDF-1.7\nthis is intentionally truncated")
    write_file(room / "broken.zip", b"PK\x03\x04truncated")
    write_file(room / "unknown.bin", b"\x00\x01\x02\x03")

    result = inventory_room(room, LIMITS)
    broken = next(item for item in result.sources if item["filename"] == "broken.pdf")
    broken_zip = next(item for item in result.sources if item["filename"] == "broken.zip")
    unsupported = next(item for item in result.sources if item["filename"] == "unknown.bin")

    assert broken["inventory_status"] == "registered_unreadable"
    assert broken["readability_status"] == "unreadable"
    assert broken["error"]
    assert broken_zip["inventory_status"] == "registered_unreadable"
    assert broken_zip["is_archive_container"] is True
    assert broken_zip["archive_member_count"] == 0
    assert unsupported["inventory_status"] == "registered_unsupported"
    assert result.summary["source_register_entries"] == 4
    assert result.summary["terminal_inventory_entries"] == 4

    run_path = create_run(load_config(cwd=tmp_path))
    register_room(run_path, room, LIMITS)
    _, manifest = load_manifest(run_path)
    assert manifest["stages"]["register"]["state"] == "completed"


def test_symlink_escape_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    room = tmp_path / "room"
    room.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    link = room / "escape.txt"
    try:
        os.symlink(outside, link)
    except OSError:
        link.write_text("simulated link placeholder", encoding="utf-8")
        original = Path.is_symlink
        monkeypatch.setattr(
            Path,
            "is_symlink",
            lambda self: self == link or original(self),
        )

    with pytest.raises(SourcePathError, match="symbolic-link"):
        inventory_room(room, LIMITS)


def test_source_ids_are_stable_for_an_unchanged_room(tmp_path: Path) -> None:
    room = tmp_path / "room"
    write_file(room / "Financial" / "A.txt", b"alpha")
    write_file(room / "Tax" / "B.txt", b"beta")

    first = inventory_room(room, LIMITS)
    second = inventory_room(room, LIMITS)

    first_ids = [(item["source_id"], item["identity_key"]) for item in first.sources]
    second_ids = [(item["source_id"], item["identity_key"]) for item in second.sources]
    assert first_ids == second_ids
    assert first.input_checksum == second.input_checksum


def test_register_stage_rerun_is_idempotent(tmp_path: Path) -> None:
    room = tmp_path / "room"
    write_file(room / "Financial" / "A.txt", b"alpha")
    run_path = create_run(load_config(cwd=tmp_path))

    first = register_room(run_path, room, LIMITS)
    before = {relative: (run_path / relative).read_bytes() for relative in REGISTER_OUTPUTS}
    second = register_room(run_path, room, LIMITS)
    after = {relative: (run_path / relative).read_bytes() for relative in REGISTER_OUTPUTS}
    _, manifest = load_manifest(run_path)

    assert first.reused is False
    assert second.reused is True
    assert before == after
    assert manifest["stages"]["register"]["attempts"] == 1
    assert manifest["stages"]["register"]["state"] == "completed"


def test_register_cli_accepts_explicit_room(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    room = tmp_path / "room"
    write_file(room / "Financial" / "A.txt", b"alpha")
    run_path = create_run(load_config(cwd=tmp_path))

    exit_code = main(["register", "--run", str(run_path), "--room", str(room), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["summary"]["source_register_entries"] == 1
    assert Path(payload["path"]).is_dir()


def test_cross_platform_relative_path_normalization() -> None:
    assert canonical_relative_path("Financial\\Sub Folder\\File.xlsx") == (
        "Financial/Sub Folder/File.xlsx"
    )
    assert canonical_relative_path("Legal/Sub Folder/File.pdf") == "Legal/Sub Folder/File.pdf"
    with pytest.raises(ValueError, match="absolute"):
        canonical_relative_path("C:\\room\\file.pdf")
    with pytest.raises(ValueError, match="traversal"):
        canonical_relative_path("../file.pdf")


def test_sibling_planted_directory_is_never_inventoried(tmp_path: Path) -> None:
    synthetic = tmp_path / "synthetic"
    room = synthetic / "data_room"
    write_file(room / "Financial" / "A.txt", b"alpha")
    write_file(synthetic / "planted_issues" / "do-not-read.txt", b"sealed")

    result = inventory_room(room, LIMITS)

    assert [item["relative_path"] for item in result.sources] == ["Financial/A.txt"]
    assert all("planted" not in item["relative_path"].casefold() for item in result.sources)


def test_repository_root_is_rejected(tmp_path: Path) -> None:
    room = tmp_path / "not-a-room"
    (room / ".git").mkdir(parents=True)

    with pytest.raises(SourcePathError, match="repository root"):
        inventory_room(room, LIMITS)


def test_complete_synthetic_room_registers_without_ground_truth_access() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    room = repository_root / "synthetic" / "data_room"

    result = inventory_room(
        room,
        RegisterLimits(
            max_archive_members=1_000,
            max_archive_total_uncompressed_bytes=256 * 1024 * 1024,
            max_archive_member_uncompressed_bytes=64 * 1024 * 1024,
        ),
    )

    assert result.summary["physical_files"] == 90
    assert result.summary["archive_members"] == 10
    assert result.summary["logical_source_items"] == 100
    assert result.summary["source_register_entries"] == 100
    assert result.summary["terminal_inventory_entries"] == 100
    assert result.summary["analysis_eligible_documents"] == 99
    container = next(item for item in result.sources if item["is_archive_container"])
    members = [item for item in result.sources if item["container_source_id"]]
    assert container["analysis_eligible"] is False
    assert container["include_in_analysis"] is False
    assert len(members) == 10
    assert all(item["relative_path"].startswith("zip://") for item in members)
