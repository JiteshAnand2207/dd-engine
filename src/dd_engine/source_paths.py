"""Read-only source-room path boundary.

This module intentionally contains no extraction or source-register behavior.
It provides the Phase 3 safety gate that later stages must use before walking a
room.  In particular, sealed synthetic ground truth is unreachable through the
normal source-room interface.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from dd_engine.errors import SourcePathError

FORBIDDEN_DIRECTORY_NAMES = frozenset({"planted_issues", "planted-issues"})


def _has_forbidden_component(path: Path) -> bool:
    return any(part.casefold() in FORBIDDEN_DIRECTORY_NAMES for part in path.parts)


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
    if candidate.is_symlink():
        raise SourcePathError("the data-room root may not be a symbolic link")
    if _has_forbidden_component(resolved):
        raise SourcePathError("data-room path may not be planted_issues or any descendant")
    return resolved


def iter_data_room_files(path: str | Path) -> Iterator[Path]:
    """Yield files without following links or escaping the validated room root."""

    root = validate_data_room_path(path)
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        safe_directories: list[str] = []
        for name in sorted(directories):
            child = current_path / name
            if name.casefold() in FORBIDDEN_DIRECTORY_NAMES:
                raise SourcePathError(
                    f"forbidden planted-issues directory encountered inside room: {child}"
                )
            if child.is_symlink():
                raise SourcePathError(
                    f"symbolic-link directory is forbidden in source room: {child}"
                )
            safe_directories.append(name)
        directories[:] = safe_directories
        for name in sorted(files):
            candidate = current_path / name
            if candidate.is_symlink():
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
            yield resolved
