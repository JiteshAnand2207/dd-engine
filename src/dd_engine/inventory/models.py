"""Typed values shared by the source-register implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

SourceRecord = dict[str, Any]


@dataclass(frozen=True, slots=True)
class RegisterLimits:
    """Hard limits applied before archive member decompression."""

    max_archive_members: int
    max_archive_total_uncompressed_bytes: int
    max_archive_member_uncompressed_bytes: int

    def as_dict(self) -> dict[str, int]:
        """Return a stable serializable representation."""

        return {
            "max_archive_member_uncompressed_bytes": (self.max_archive_member_uncompressed_bytes),
            "max_archive_members": self.max_archive_members,
            "max_archive_total_uncompressed_bytes": (self.max_archive_total_uncompressed_bytes),
        }


@dataclass(frozen=True, slots=True)
class ContentInspection:
    """Content-signature and structural-readability result."""

    detected_mime_type: str | None
    detected_type: str
    readability_status: str
    error: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ArchiveMember:
    """One central-directory file entry and its bounded inspection result."""

    archive_member_index: int
    archive_member_name: str
    compressed_size_bytes: int
    crc32: str
    data: bytes | None
    error: str | None
    modified_time: str | None
    size_bytes: int
    virtual_path: str
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArchiveInspection:
    """A ZIP inspection that never writes or extracts member data."""

    directories: tuple[dict[str, Any], ...]
    error: str | None
    members: tuple[ArchiveMember, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InventoryResult:
    """All deterministic data needed to write register artifacts."""

    archive_directories: tuple[dict[str, Any], ...]
    duplicate_groups: tuple[dict[str, Any], ...]
    empty_directories: tuple[str, ...]
    input_checksum: str
    near_duplicate_candidates: tuple[dict[str, Any], ...]
    physical_directories: tuple[dict[str, Any], ...]
    same_basename_conflicts: tuple[dict[str, Any], ...]
    sources: tuple[SourceRecord, ...]
    summary: dict[str, int]
    version_families: tuple[dict[str, Any], ...]


@dataclass(frozen=True, slots=True)
class RegistrationOutcome:
    """Public result returned by an idempotent register-stage invocation."""

    input_checksum: str
    reused: bool
    run_path: Path
    summary: dict[str, int]
