"""Local environment capability and safety checks."""

from __future__ import annotations

import importlib.metadata
import os
import platform
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from dd_engine.config import EngineConfig, load_config
from dd_engine.errors import ConfigError

CheckStatus = Literal["pass", "warn", "fail"]


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    """One stable doctor result."""

    name: str
    status: CheckStatus
    summary: str
    fallback: str | None = None


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """Complete environment report."""

    checks: tuple[DoctorCheck, ...]

    @property
    def exit_code(self) -> int:
        return 1 if any(check.status == "fail" for check in self.checks) else 0

    def as_dict(self) -> dict[str, object]:
        counts = {
            status: sum(check.status == status for check in self.checks)
            for status in ("pass", "warn", "fail")
        }
        return {
            "checks": [asdict(check) for check in self.checks],
            "counts": counts,
            "ok": self.exit_code == 0,
        }


def _python_check() -> DoctorCheck:
    version = ".".join(str(part) for part in sys.version_info[:3])
    if sys.version_info >= (3, 11):  # noqa: UP036 - doctor must report the explicit gate
        return DoctorCheck("Python version", "pass", f"Python {version} (requires >=3.11)")
    return DoctorCheck("Python version", "fail", f"Python {version}; Python 3.11+ required")


def _required_packages_check() -> DoctorCheck:
    required_packages = (
        "openpyxl",
        "Pillow",
        "pypdf",
        "pypdfium2",
        "python-docx",
        "reportlab",
    )
    missing: list[str] = []
    for package in required_packages:
        try:
            importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            missing.append(package)
    if missing:
        return DoctorCheck(
            "Required packages", "fail", f"missing required package(s): {', '.join(missing)}"
        )
    return DoctorCheck(
        "Required packages",
        "pass",
        "required local extraction, rendering, generation and validation packages are installed",
    )


def _pdf_rendering_check() -> DoctorCheck:
    try:
        version = importlib.metadata.version("pypdfium2")
    except importlib.metadata.PackageNotFoundError:
        return DoctorCheck(
            "Optional PDF rendering support",
            "fail",
            "bundled local PDF renderer is missing",
        )
    return DoctorCheck(
        "Optional PDF rendering support",
        "pass",
        f"bundled local pypdfium2 renderer available: {version}",
    )


def _optional_tool_check(
    *, name: str, executables: tuple[str, ...], available_summary: str, fallback: str
) -> DoctorCheck:
    found = next((executable for executable in executables if shutil.which(executable)), None)
    if found:
        return DoctorCheck(name, "pass", f"{available_summary}: {found}")
    return DoctorCheck(name, "warn", "optional capability not detected", fallback)


def _nearest_existing_directory(path: Path) -> Path | None:
    candidate = path
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:
            return None
        candidate = parent
    return candidate if candidate.is_dir() else candidate.parent


def _filesystem_check(config: EngineConfig | None, cwd: Path) -> DoctorCheck:
    target = config.runs_dir if config is not None else cwd
    existing = _nearest_existing_directory(target)
    if existing is None:
        return DoctorCheck("Filesystem access", "fail", f"no accessible parent for {target}")
    try:
        if not os.access(cwd, os.R_OK):
            raise PermissionError(f"working directory is not readable: {cwd}")
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=".dd-engine-doctor-", dir=existing, delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write("local filesystem check")
        temporary_path.read_text(encoding="utf-8")
        temporary_path.unlink()
    except OSError as exc:
        return DoctorCheck("Filesystem access", "fail", f"read/write check failed: {exc}")
    return DoctorCheck(
        "Filesystem access", "pass", f"readable workspace; writable run parent: {existing}"
    )


def _config_check(config: EngineConfig | None, error: str | None) -> DoctorCheck:
    if config is None:
        return DoctorCheck("Configuration", "fail", error or "configuration is invalid")
    source = str(config.source_path) if config.source_path else "safe built-in defaults"
    return DoctorCheck("Configuration", "pass", f"schema {config.schema_version} valid ({source})")


def _api_key_check(config: EngineConfig | None) -> DoctorCheck:
    if config is not None and config.require_api_key:
        return DoctorCheck("API-key requirement", "fail", "configuration requires an API key")
    return DoctorCheck(
        "API-key requirement",
        "pass",
        (
            "no provider API key is read or required; model access belongs to the "
            "authenticated harness"
        ),
    )


def run_doctor(config_path: str | Path | None = None, *, cwd: Path | None = None) -> DoctorReport:
    """Inspect local capabilities without calling a network or model service."""

    working_dir = (cwd or Path.cwd()).resolve()
    config: EngineConfig | None = None
    config_error: str | None = None
    try:
        config = load_config(config_path, cwd=working_dir)
    except ConfigError as exc:
        config_error = str(exc)

    checks = (
        _python_check(),
        _required_packages_check(),
        _optional_tool_check(
            name="Optional OCR support",
            executables=("tesseract",),
            available_summary="local OCR executable detected",
            fallback=(
                "image-only material will be rendered locally and placed in the pending vision "
                "queue without a fabricated result"
            ),
        ),
        _pdf_rendering_check(),
        _optional_tool_check(
            name="Optional document conversion support",
            executables=("soffice", "libreoffice", "pandoc"),
            available_summary="local document converter detected",
            fallback=(
                "native parsers remain the default; formats needing conversion will be "
                "quarantined or escalated explicitly"
            ),
        ),
        _filesystem_check(config, working_dir),
        _config_check(config, config_error),
        _api_key_check(config),
        DoctorCheck(
            "Operating system",
            "pass",
            (
                f"{platform.system()} {platform.release()} | {platform.machine()} | "
                f"{platform.platform()}"
            ),
        ),
    )
    return DoctorReport(checks=checks)


def format_doctor_report(report: DoctorReport) -> str:
    """Render a human-readable doctor report."""

    lines = ["dd-engine doctor"]
    for check in report.checks:
        lines.append(f"[{check.status.upper():4}] {check.name}: {check.summary}")
        if check.fallback:
            lines.append(f"       Fallback: {check.fallback}")
    pass_count = sum(check.status == "pass" for check in report.checks)
    warn_count = sum(check.status == "warn" for check in report.checks)
    fail_count = sum(check.status == "fail" for check in report.checks)
    lines.append(f"Summary: {pass_count} passed, {warn_count} warnings, {fail_count} failed")
    return "\n".join(lines)
