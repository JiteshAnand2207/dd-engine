from __future__ import annotations

from pathlib import Path

import pytest

from dd_engine.config import ConfigError, load_config


def test_configuration_loads_checked_in_defaults() -> None:
    config = load_config()

    assert config.schema_version == 1
    assert config.runs_dir == (Path.cwd() / "runs").resolve()
    assert config.telemetry_enabled is False
    assert config.external_logging_enabled is False
    assert config.require_api_key is False
    assert config.register.max_archive_members == 1_000
    assert config.register.max_archive_total_uncompressed_bytes == 256 * 1024 * 1024
    assert config.register.max_archive_member_uncompressed_bytes == 64 * 1024 * 1024
    assert config.extraction.native_first is True
    assert config.extraction.optional_ocr is True
    assert config.extraction.unsupported_policy == "quarantine"
    assert config.extraction.pdf_min_native_characters == 24
    assert config.extraction.render_scale == 2.0
    assert config.analysis.jurisdiction == "IE"
    assert config.analysis.workstreams == (
        "financial",
        "commercial",
        "legal_contractual",
        "operational_management",
        "it",
    )
    assert config.analysis.tax_mode == "standalone"
    assert config.reporting.report_format == "markdown"
    assert config.reporting.ic_brief_format == "pdf"
    assert config.reporting.ic_brief_pages == 2
    assert config.reporting.page_size == "A4"
    assert config.model_routing.deterministic_profile == "deterministic"
    assert config.model_routing.mechanical_profile == "economy_mechanical"
    assert config.model_routing.judgment_profile == "frontier_judgment"
    assert config.model_routing.red_team_profile == "frontier_red_team"
    assert config.model_routing.direct_api_enabled is False


def test_configuration_resolves_paths_from_config_location(tmp_path: Path) -> None:
    config_dir = tmp_path / "folder with spaces" / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "custom.toml"
    config_path.write_text(
        "[dd_engine]\n"
        "schema_version = 1\n"
        'runs_dir = "../local runs"\n'
        "telemetry_enabled = false\n"
        "external_logging_enabled = false\n"
        "public_research_enabled = false\n"
        "require_api_key = false\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.runs_dir == (config_dir / "../local runs").resolve()


@pytest.mark.parametrize(
    "line, message",
    [
        ("telemetry_enabled = true", "telemetry must remain disabled"),
        ("external_logging_enabled = true", "external logging must remain disabled"),
        ("require_api_key = true", "provider API keys cannot be required"),
        ("unknown_setting = true", "unknown dd_engine configuration key"),
    ],
)
def test_unsafe_or_unknown_configuration_is_rejected(
    tmp_path: Path, line: str, message: str
) -> None:
    config_path = tmp_path / "invalid.toml"
    config_path.write_text(f"[dd_engine]\nschema_version = 1\n{line}\n", encoding="utf-8")

    with pytest.raises(ConfigError, match=message):
        load_config(config_path)


def test_missing_explicit_configuration_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="configuration file not found"):
        load_config(tmp_path / "missing.toml")


@pytest.mark.parametrize(
    "section, message",
    [
        ("[extraction]\nnative_first = false", "extraction.native_first"),
        (
            "[extraction]\npdf_min_native_characters = 0",
            "extraction.pdf_min_native_characters",
        ),
        ("[extraction]\nrender_scale = 0", "extraction.render_scale"),
        ("[register]\nmax_archive_members = 0", "register.max_archive_members"),
        ("[analysis]\njurisdiction = 'US'", "analysis.jurisdiction"),
        ("[reporting]\nic_brief_pages = 3", "reporting.ic_brief_pages"),
        ("[model_routing]\ndirect_api_enabled = true", "model_routing.direct_api_enabled"),
    ],
)
def test_scaffold_section_values_are_validated(tmp_path: Path, section: str, message: str) -> None:
    config_path = tmp_path / "invalid-section.toml"
    config_path.write_text(f"[dd_engine]\nschema_version = 1\n{section}\n", encoding="utf-8")

    with pytest.raises(ConfigError, match=message):
        load_config(config_path)
