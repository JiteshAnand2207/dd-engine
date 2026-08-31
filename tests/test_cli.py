from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from dd_engine.cli import NOT_IMPLEMENTED_EXIT, main
from dd_engine.config import load_config
from dd_engine.constants import STAGE_ORDER
from dd_engine.runs import create_run


def test_module_cli_starts() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "dd_engine", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "doctor" in result.stdout
    assert "init-run" in result.stdout
    assert "status" in result.stdout


def test_init_run_and_status_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["init-run", "--runs-root", str(tmp_path / "runs"), "--json"])
    captured = capsys.readouterr()
    created = json.loads(captured.out)

    assert exit_code == 0
    run_path = Path(created["path"])

    status_exit = main(["status", "--run", str(run_path), "--json"])
    captured = capsys.readouterr()
    status = json.loads(captured.out)
    assert status_exit == 0
    assert status["run_id"] == created["run_id"]
    assert status["overall_state"] == "not_started"
    assert set(status["stages"].values()) == {"not_started"}


@pytest.mark.parametrize("stage_name", STAGE_ORDER[2:])
def test_later_stage_commands_report_not_implemented(
    stage_name: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_path = create_run(load_config(cwd=tmp_path))
    arguments = [stage_name, "--run", str(run_path)]
    exit_code = main(arguments)

    captured = capsys.readouterr()
    assert exit_code == NOT_IMPLEMENTED_EXIT
    assert f"{stage_name}: stage not implemented" in captured.err
    assert "success" not in captured.err.lower()
