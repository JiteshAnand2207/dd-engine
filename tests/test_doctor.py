from __future__ import annotations

import json
from pathlib import Path

import pytest

from dd_engine.cli import main
from dd_engine.doctor import format_doctor_report, run_doctor


def test_doctor_covers_required_environment_checks(tmp_path: Path) -> None:
    report = run_doctor(cwd=tmp_path)
    names = {check.name for check in report.checks}

    assert report.exit_code == 0
    assert names == {
        "Python version",
        "Required packages",
        "Optional OCR support",
        "Optional PDF rendering support",
        "Optional document conversion support",
        "Filesystem access",
        "Configuration",
        "API-key requirement",
        "Operating system",
    }
    output = format_doctor_report(report)
    assert "no provider API key is read or required" in output
    assert "Summary:" in output


def test_doctor_has_no_hidden_api_key_requirement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    report = run_doctor(cwd=tmp_path)

    key_check = next(check for check in report.checks if check.name == "API-key requirement")
    assert key_check.status == "pass"
    assert report.exit_code == 0


def test_doctor_json_output_is_machine_readable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("[dd_engine]\nschema_version = 1\n", encoding="utf-8")

    exit_code = main(["doctor", "--config", str(config_path), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["counts"]["fail"] == 0
