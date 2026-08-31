"""Read-only source-room path boundary.

This module provides the Phase 4 boundary used before the source-register stage
walks a room. In particular, it performs no content execution or extraction,
does not follow link-like entries, and keeps sealed synthetic ground truth
unreachable through the normal source-room interface.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from dd_engine.errors import SourcePathError

FORBIDDEN_DIRECTORY_NAMES = frozenset({"planted_issues", "planted-issues"})


@dataclass(frozen=True, slots=True)
class DataRoomWalk:
    """A safe, deterministic snapshot of physical room paths."""

    root: Path
    files: tuple[Path, ...]
    directories: tuple[Path, ...]
    empty_directories: tuple[Path, ...]


def _has_forbidden_component(path: Path) -> bool:
    return any(part.casefold() in FORBIDDEN_DIRECTORY_NAMES for part in path.parts)


def _is_link_like(path: Path) -> bool:
    """Reject symlinks and Windows reparse points such as directory junctions."""

    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def validate_data_room_path(path: str | Path) -> Path:
    """Resolve an explicit room path and reject sealed-ground-truth access."""

    raw = str(path)
    if not raw.strip():
        raise SourcePathError("an explicit data-room path is required")
    candidate = Path(path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise SourcePathError(f"data-room path cannot be resolved: {candidate}: {exc}") from exc
    if not resolved.is_dir():
        raise SourcePathError(f"data-room path is not a directory: {resolved}")
    if _is_link_like(candidate):
        raise SourcePathError("the data-room root may not be a symbolic link")
    if _has_forbidden_component(resolved):
        raise SourcePathError("data-room path may not be planted_issues or any descendant")
    if (resolved / ".git").exists():
        raise SourcePathError("data-room path may not be a repository root")
    return resolved


def walk_data_room(path: str | Path) -> DataRoomWalk:
    """Return all physical files and directories without following links."""

    root = validate_data_room_path(path)
    discovered_files: list[Path] = []
    discovered_directories: list[Path] = []
    empty_directories: list[Path] = []
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        safe_directories: list[str] = []
        for name in sorted(directories):
            child = current_path / name
            if name.casefold() in FORBIDDEN_DIRECTORY_NAMES:
                raise SourcePathError(
                    f"forbidden planted-issues directory encountered inside room: {child}"
                )
            if _is_link_like(child):
                raise SourcePathError(
                    f"symbolic-link directory is forbidden in source room: {child}"
                )
            safe_directories.append(name)
        directories[:] = safe_directories
        if current_path != root:
            discovered_directories.append(current_path)
            if not directories and not files:
                empty_directories.append(current_path)
        for name in sorted(files):
            candidate = current_path / name
            if _is_link_like(candidate):
                raise SourcePathError(
                    f"symbolic-link file is forbidden in source room: {candidate}"
                )
            try:
                resolved = candidate.resolve(strict=True)
            except OSError as exc:
                raise SourcePathError(
                    f"source file cannot be resolved: {candidate}: {exc}"
                ) from exc
            if not resolved.is_relative_to(root):
                raise SourcePathError(f"source file escaped the explicit room root: {candidate}")
            if _has_forbidden_component(resolved):
                raise SourcePathError(f"forbidden planted-issues source path: {resolved}")
            discovered_files.append(resolved)

    def relative_key(item: Path) -> str:
        return item.relative_to(root).as_posix().casefold()

    return DataRoomWalk(
        root=root,
        files=tuple(sorted(discovered_files, key=relative_key)),
        directories=tuple(sorted(discovered_directories, key=relative_key)),
        empty_directories=tuple(sorted(empty_directories, key=relative_key)),
    )


def iter_data_room_files(path: str | Path) -> Iterator[Path]:
    """Yield files without following links or escaping the validated room root."""

    yield from walk_data_room(path).files
