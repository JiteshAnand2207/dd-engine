"""Strict, dependency-free configuration loading."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dd_engine.errors import ConfigError

CONFIG_FILENAME = "dd-engine.toml"
CONFIG_SCHEMA_VERSION = 1
_ALLOWED_KEYS = {
    "schema_version",
    "runs_dir",
    "telemetry_enabled",
    "external_logging_enabled",
    "public_research_enabled",
    "require_api_key",
}
_ALLOWED_SECTIONS = {"dd_engine", "extraction", "analysis", "reporting", "model_routing"}
_WORKSTREAMS = (
    "financial",
    "commercial",
    "legal_contractual",
    "operational_management",
    "it",
)


@dataclass(frozen=True, slots=True)
class ExtractionConfig:
    """Validated extraction scaffold settings; no extraction is implemented yet."""

    native_first: bool
    optional_ocr: bool
    unsupported_policy: str


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    """Validated analysis scaffold settings; no analysis is implemented yet."""

    jurisdiction: str
    workstreams: tuple[str, ...]
    tax_mode: str


@dataclass(frozen=True, slots=True)
class ReportingConfig:
    """Validated reporting scaffold settings; no reporting is implemented yet."""

    report_format: str
    ic_brief_format: str
    ic_brief_pages: int
    page_size: str


@dataclass(frozen=True, slots=True)
class ModelRoutingConfig:
    """Logical harness route defaults without provider credentials or model calls."""

    deterministic_profile: str
    mechanical_profile: str
    judgment_profile: str
    red_team_profile: str
    direct_api_enabled: bool


@dataclass(frozen=True, slots=True)
class EngineConfig:
    """Validated configuration used by deterministic local code."""

    schema_version: int
    runs_dir: Path
    telemetry_enabled: bool
    external_logging_enabled: bool
    public_research_enabled: bool
    require_api_key: bool
    extraction: ExtractionConfig
    analysis: AnalysisConfig
    reporting: ReportingConfig
    model_routing: ModelRoutingConfig
    source_path: Path | None

    @property
    def checksum(self) -> str:
        """Return a stable checksum of behavior-affecting values."""

        values = {
            "external_logging_enabled": self.external_logging_enabled,
            "public_research_enabled": self.public_research_enabled,
            "require_api_key": self.require_api_key,
            "runs_dir": str(self.runs_dir),
            "schema_version": self.schema_version,
            "telemetry_enabled": self.telemetry_enabled,
            "extraction": asdict(self.extraction),
            "analysis": asdict(self.analysis),
            "reporting": asdict(self.reporting),
            "model_routing": asdict(self.model_routing),
        }
        encoded = json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def _require_bool(section: dict[str, Any], key: str, default: bool) -> bool:
    value = section.get(key, default)
    if type(value) is not bool:
        raise ConfigError(f"dd_engine.{key} must be true or false")
    return value


def _section(document: dict[str, Any], name: str) -> dict[str, Any]:
    value = document.get(name, {})
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be a TOML table")
    return value


def _reject_unknown(section: dict[str, Any], name: str, allowed: set[str]) -> None:
    unknown = sorted(set(section) - allowed)
    if unknown:
        raise ConfigError(f"unknown {name} configuration key(s): {', '.join(unknown)}")


def _require_locked_value(
    section: dict[str, Any], section_name: str, key: str, default: Any
) -> Any:
    value = section.get(key, default)
    if value != default:
        raise ConfigError(f"{section_name}.{key} must be {default!r} in Phase 3")
    return value


def _build_extraction(section: dict[str, Any]) -> ExtractionConfig:
    _reject_unknown(section, "extraction", {"native_first", "optional_ocr", "unsupported_policy"})
    return ExtractionConfig(
        native_first=_require_locked_value(section, "extraction", "native_first", True),
        optional_ocr=_require_locked_value(section, "extraction", "optional_ocr", True),
        unsupported_policy=_require_locked_value(
            section, "extraction", "unsupported_policy", "quarantine"
        ),
    )


def _build_analysis(section: dict[str, Any]) -> AnalysisConfig:
    _reject_unknown(section, "analysis", {"jurisdiction", "workstreams", "tax_mode"})
    raw_workstreams = section.get("workstreams", list(_WORKSTREAMS))
    if not isinstance(raw_workstreams, list) or tuple(raw_workstreams) != _WORKSTREAMS:
        raise ConfigError("analysis.workstreams must contain the five locked formal workstreams")
    return AnalysisConfig(
        jurisdiction=_require_locked_value(section, "analysis", "jurisdiction", "IE"),
        workstreams=tuple(raw_workstreams),
        tax_mode=_require_locked_value(section, "analysis", "tax_mode", "standalone"),
    )


def _build_reporting(section: dict[str, Any]) -> ReportingConfig:
    _reject_unknown(
        section,
        "reporting",
        {"report_format", "ic_brief_format", "ic_brief_pages", "page_size"},
    )
    return ReportingConfig(
        report_format=_require_locked_value(section, "reporting", "report_format", "markdown"),
        ic_brief_format=_require_locked_value(section, "reporting", "ic_brief_format", "pdf"),
        ic_brief_pages=_require_locked_value(section, "reporting", "ic_brief_pages", 2),
        page_size=_require_locked_value(section, "reporting", "page_size", "A4"),
    )


def _build_model_routing(section: dict[str, Any]) -> ModelRoutingConfig:
    _reject_unknown(
        section,
        "model_routing",
        {
            "deterministic_profile",
            "mechanical_profile",
            "judgment_profile",
            "red_team_profile",
            "direct_api_enabled",
        },
    )
    return ModelRoutingConfig(
        deterministic_profile=_require_locked_value(
            section, "model_routing", "deterministic_profile", "deterministic"
        ),
        mechanical_profile=_require_locked_value(
            section, "model_routing", "mechanical_profile", "economy_mechanical"
        ),
        judgment_profile=_require_locked_value(
            section, "model_routing", "judgment_profile", "frontier_judgment"
        ),
        red_team_profile=_require_locked_value(
            section, "model_routing", "red_team_profile", "frontier_red_team"
        ),
        direct_api_enabled=_require_locked_value(
            section, "model_routing", "direct_api_enabled", False
        ),
    )


def _build_config(
    document: dict[str, Any], *, source_path: Path | None, base_dir: Path
) -> EngineConfig:
    section = _section(document, "dd_engine")
    unknown = sorted(set(section) - _ALLOWED_KEYS)
    if unknown:
        raise ConfigError(f"unknown dd_engine configuration key(s): {', '.join(unknown)}")

    schema_version = section.get("schema_version", CONFIG_SCHEMA_VERSION)
    if type(schema_version) is not int or schema_version != CONFIG_SCHEMA_VERSION:
        raise ConfigError(f"dd_engine.schema_version must be {CONFIG_SCHEMA_VERSION}")

    raw_runs_dir = section.get("runs_dir", "runs")
    if not isinstance(raw_runs_dir, str) or not raw_runs_dir.strip():
        raise ConfigError("dd_engine.runs_dir must be a non-empty path string")
    if "\x00" in raw_runs_dir:
        raise ConfigError("dd_engine.runs_dir contains a null byte")

    runs_dir = Path(raw_runs_dir).expanduser()
    if not runs_dir.is_absolute():
        runs_dir = base_dir / runs_dir
    runs_dir = runs_dir.resolve(strict=False)

    telemetry_enabled = _require_bool(section, "telemetry_enabled", False)
    external_logging_enabled = _require_bool(section, "external_logging_enabled", False)
    public_research_enabled = _require_bool(section, "public_research_enabled", False)
    require_api_key = _require_bool(section, "require_api_key", False)

    if telemetry_enabled:
        raise ConfigError("telemetry must remain disabled")
    if external_logging_enabled:
        raise ConfigError("external logging must remain disabled")
    if require_api_key:
        raise ConfigError("provider API keys cannot be required")

    return EngineConfig(
        schema_version=schema_version,
        runs_dir=runs_dir,
        telemetry_enabled=telemetry_enabled,
        external_logging_enabled=external_logging_enabled,
        public_research_enabled=public_research_enabled,
        require_api_key=require_api_key,
        extraction=_build_extraction(_section(document, "extraction")),
        analysis=_build_analysis(_section(document, "analysis")),
        reporting=_build_reporting(_section(document, "reporting")),
        model_routing=_build_model_routing(_section(document, "model_routing")),
        source_path=source_path,
    )


def load_config(path: str | Path | None = None, *, cwd: Path | None = None) -> EngineConfig:
    """Load a TOML config, or safe built-in defaults when no file is present."""

    working_dir = (cwd or Path.cwd()).resolve()
    explicit = path is not None
    config_path = Path(path).expanduser() if path is not None else working_dir / CONFIG_FILENAME
    if not config_path.is_absolute():
        config_path = working_dir / config_path
    config_path = config_path.resolve(strict=False)

    if not config_path.exists():
        if explicit:
            raise ConfigError(f"configuration file not found: {config_path}")
        return _build_config({}, source_path=None, base_dir=working_dir)
    if not config_path.is_file():
        raise ConfigError(f"configuration path is not a file: {config_path}")

    try:
        with config_path.open("rb") as handle:
            document = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"cannot read configuration: {exc}") from exc

    unknown_sections = sorted(set(document) - _ALLOWED_SECTIONS)
    if unknown_sections:
        raise ConfigError(f"unknown configuration section(s): {', '.join(unknown_sections)}")
    return _build_config(document, source_path=config_path, base_dir=config_path.parent)
