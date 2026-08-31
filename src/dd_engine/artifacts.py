"""Safe local artifact writing, hashing and validation."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from dd_engine.errors import ArtifactError


def file_sha256(path: Path) -> str:
    """Hash a file without loading it fully into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON through an adjacent temporary file and atomically replace it."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_text(path: Path, value: str) -> None:
    """Write UTF-8 text through an adjacent file and atomically replace it."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_bytes(path: Path, value: bytes) -> None:
    """Write binary content through an adjacent file and atomically replace it."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    """Append one local JSONL event."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_json(path: Path) -> dict[str, Any]:
    """Load an object-shaped JSON file with a useful error."""

    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ArtifactError(f"JSON artifact must contain an object: {path}")
    return value


def _resolved_artifact(run_path: Path, artifact: str | Path) -> Path:
    candidate = Path(artifact)
    if not candidate.is_absolute():
        candidate = run_path / candidate
    root = run_path.resolve(strict=True)
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root) or resolved == root:
        raise ArtifactError(f"artifact must remain inside the run directory: {artifact}")
    return resolved


def _validate_jsonl_run_id(path: Path, run_id: str) -> list[str]:
    errors: list[str] = []
    try:
        with path.open(encoding="utf-8") as handle:
            lines = [line for line in handle if line.strip()]
        if not lines:
            return ["JSONL artifact has no records"]
        for number, line in enumerate(lines, start=1):
            value = json.loads(line)
            if not isinstance(value, dict) or value.get("run_id") != run_id:
                errors.append(f"JSONL record {number} does not contain the run ID")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSONL: {exc}")
    return errors


def validate_run_artifact(
    run_path: Path, artifact: str | Path, run_id: str
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate a required artifact and return hash metadata plus errors."""

    try:
        path = _resolved_artifact(run_path, artifact)
    except (ArtifactError, OSError) as exc:
        return None, [str(exc)]
    if not path.is_file():
        return None, [f"required artifact is missing or not a file: {path}"]
    if path.stat().st_size == 0:
        return None, [f"required artifact is empty: {path}"]

    errors: list[str] = []
    if path.suffix.lower() == ".json":
        try:
            value = load_json(path)
            if value.get("run_id") != run_id:
                errors.append("JSON artifact does not contain the run ID")
        except ArtifactError as exc:
            errors.append(str(exc))
    elif path.suffix.lower() == ".jsonl":
        errors.extend(_validate_jsonl_run_id(path, run_id))
    else:
        try:
            if run_id not in path.read_text(encoding="utf-8"):
                errors.append("text artifact does not contain the run ID")
        except UnicodeError:
            errors.append("binary artifact requires a format-specific run-ID validator")
        except OSError as exc:
            errors.append(f"cannot read artifact: {exc}")

    if errors:
        return None, errors
    relative_path = path.relative_to(run_path.resolve(strict=True)).as_posix()
    metadata: dict[str, Any] = {
        "path": relative_path,
        "run_id": run_id,
        "sha256": file_sha256(path),
        "size_bytes": path.stat().st_size,
    }
    return metadata, []


def aggregate_artifact_checksum(artifacts: Iterable[Mapping[str, Any]]) -> str:
    """Hash a normalized list of artifact metadata."""

    normalized = sorted(
        ({"path": item["path"], "sha256": item["sha256"]} for item in artifacts),
        key=lambda item: str(item["path"]),
    )
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
