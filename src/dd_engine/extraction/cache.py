"""Run-local extraction cache keyed by source hash, version and configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dd_engine.artifacts import atomic_write_json, file_sha256, load_json
from dd_engine.errors import ArtifactError
from dd_engine.extraction.models import SourceExtraction, stable_json_checksum


class ExtractionCache:
    """Validate and persist source-level extraction results inside one run."""

    def __init__(
        self,
        *,
        run_path: Path,
        extractor_version: str,
        config_fingerprint: str,
    ) -> None:
        self.run_path = run_path
        self.root = run_path / "extracts" / "cache"
        self.extractor_version = extractor_version
        self.config_fingerprint = config_fingerprint

    def key(self, source_checksum: str) -> str:
        return stable_json_checksum(
            {
                "config_fingerprint": self.config_fingerprint,
                "extractor_version": self.extractor_version,
                "source_checksum": source_checksum,
            }
        )

    def _path(self, source: dict[str, Any]) -> Path:
        checksum = str(source["sha256"])
        # Keep Windows test/run paths below legacy MAX_PATH while retaining the
        # complete checksum and cache key inside the validated cache record.
        return self.root / checksum[:16] / self.key(checksum)[:16] / f"{source['source_id']}.json"

    def _valid_asset(self, relative_path: object, expected_hash: object) -> bool:
        if not isinstance(relative_path, str) or not isinstance(expected_hash, str):
            return False
        candidate = (self.run_path / relative_path).resolve(strict=False)
        if not candidate.is_relative_to(self.run_path) or not candidate.is_file():
            return False
        try:
            return file_sha256(candidate) == expected_hash
        except OSError:
            return False

    def load(self, source: dict[str, Any]) -> SourceExtraction | None:
        """Return a verified hit, or ``None`` for any stale/incomplete entry."""

        path = self._path(source)
        if not path.is_file():
            return None
        try:
            payload = load_json(path)
        except ArtifactError:
            return None
        expected = {
            "cache_key": self.key(str(source["sha256"])),
            "config_fingerprint": self.config_fingerprint,
            "extractor_version": self.extractor_version,
            "relative_path": source["relative_path"],
            "source_checksum": source["sha256"],
            "source_id": source["source_id"],
        }
        if any(payload.get(key) != value for key, value in expected.items()):
            return None
        result = payload.get("result")
        if not isinstance(result, dict):
            return None
        for task in result.get("vision_tasks", []):
            if not isinstance(task, dict):
                return None
            asset = task.get("asset")
            if not isinstance(asset, dict) or not self._valid_asset(
                asset.get("path"), asset.get("sha256")
            ):
                return None
        for unit in result.get("units", []):
            if not isinstance(unit, dict):
                return None
            content = unit.get("content")
            if not isinstance(content, dict):
                return None
            asset_path = content.get("asset_path")
            if asset_path is not None and not self._valid_asset(
                asset_path, content.get("asset_checksum")
            ):
                return None
        try:
            return SourceExtraction.from_cache_payload(result)
        except (KeyError, TypeError, ValueError):
            return None

    def store(self, source: dict[str, Any], result: SourceExtraction) -> None:
        """Atomically persist a source result after its referenced assets exist."""

        path = self._path(source)
        atomic_write_json(
            path,
            {
                "cache_key": self.key(str(source["sha256"])),
                "config_fingerprint": self.config_fingerprint,
                "extractor_version": self.extractor_version,
                "relative_path": source["relative_path"],
                "result": result.as_cache_payload(),
                "run_id": self.run_path.name,
                "source_checksum": source["sha256"],
                "source_id": source["source_id"],
            },
        )
