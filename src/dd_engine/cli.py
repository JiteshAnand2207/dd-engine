"""Command-line interface for the Phase 4 engine foundation."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from dd_engine import __version__
from dd_engine.config import load_config
from dd_engine.constants import STAGE_ORDER
from dd_engine.doctor import format_doctor_report, run_doctor
from dd_engine.errors import DDEngineError
from dd_engine.inventory import RegisterLimits, register_room
from dd_engine.runs import create_run, load_manifest
from dd_engine.state import overall_state

NOT_IMPLEMENTED_EXIT = 3


def _add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, help="path to dd-engine TOML configuration")


def build_parser() -> argparse.ArgumentParser:
    """Build the public CLI parser."""

    parser = argparse.ArgumentParser(
        prog="python -m dd_engine",
        description="Codex-native due-diligence engine foundation",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser("doctor", help="validate the local environment")
    _add_config_argument(doctor_parser)
    doctor_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    init_parser = subparsers.add_parser("init-run", help="create a new resumable run")
    _add_config_argument(init_parser)
    init_parser.add_argument("--runs-root", type=Path, help="override the configured runs root")
    init_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    status_parser = subparsers.add_parser("status", help="show persistent run state")
    status_parser.add_argument("--run", required=True, type=Path, help="run directory or manifest")
    status_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    for stage_name in STAGE_ORDER:
        stage_parser = subparsers.add_parser(
            stage_name,
            help=(
                "inventory the complete source room"
                if stage_name == "register"
                else f"run the {stage_name} stage (interface only in Phase 4)"
            ),
        )
        stage_parser.add_argument("--run", required=True, type=Path, help="run directory")
        if stage_name == "register":
            stage_parser.add_argument(
                "--room",
                "--data-room",
                dest="room",
                required=True,
                type=Path,
                help="explicit read-only source-room directory",
            )
            _add_config_argument(stage_parser)
            stage_parser.add_argument(
                "--json", action="store_true", help="emit machine-readable JSON"
            )
    return parser


def _doctor_command(arguments: argparse.Namespace) -> int:
    report = run_doctor(arguments.config)
    if arguments.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        print(format_doctor_report(report))
    return report.exit_code


def _init_run_command(arguments: argparse.Namespace) -> int:
    config = load_config(arguments.config)
    run_path = create_run(config, runs_root=arguments.runs_root)
    _, manifest = load_manifest(run_path)
    if arguments.json:
        print(json.dumps({"path": str(run_path), "run_id": manifest["run_id"]}, sort_keys=True))
    else:
        print(f"Run created: {run_path}")
        print(f"Run ID: {manifest['run_id']}")
    return 0


def _status_command(arguments: argparse.Namespace) -> int:
    run_path, manifest = load_manifest(arguments.run)
    state = overall_state(manifest)
    if arguments.json:
        payload = {
            "overall_state": state,
            "path": str(run_path),
            "run_id": manifest["run_id"],
            "stages": {name: manifest["stages"][name]["state"] for name in STAGE_ORDER},
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Run ID: {manifest['run_id']}")
        print(f"Path: {run_path}")
        print(f"Overall state: {state}")
        print("Stages:")
        for stage_name in STAGE_ORDER:
            print(f"  {stage_name:<9} {manifest['stages'][stage_name]['state']}")
    return 0


def _register_command(arguments: argparse.Namespace) -> int:
    config = load_config(arguments.config)
    limits = RegisterLimits(
        max_archive_members=config.register.max_archive_members,
        max_archive_total_uncompressed_bytes=(config.register.max_archive_total_uncompressed_bytes),
        max_archive_member_uncompressed_bytes=(
            config.register.max_archive_member_uncompressed_bytes
        ),
    )
    outcome = register_room(arguments.run, arguments.room, limits)
    payload = {
        "input_checksum": outcome.input_checksum,
        "path": str(outcome.run_path / "source_register"),
        "reused": outcome.reused,
        "run_id": outcome.run_path.name,
        "summary": outcome.summary,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        action = "Reused" if outcome.reused else "Completed"
        print(f"{action} source register for run {outcome.run_path.name}")
        print(f"Path: {outcome.run_path / 'source_register'}")
        print(
            "Sources: "
            f"{outcome.summary['source_register_entries']} registered; "
            f"{outcome.summary['terminal_inventory_entries']} terminal"
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.command is None:
        parser.print_help()
        return 0
    try:
        if arguments.command == "doctor":
            return _doctor_command(arguments)
        if arguments.command == "init-run":
            return _init_run_command(arguments)
        if arguments.command == "status":
            return _status_command(arguments)
        if arguments.command == "register":
            return _register_command(arguments)
        if arguments.command in STAGE_ORDER:
            print(f"{arguments.command}: stage not implemented", file=sys.stderr)
            return NOT_IMPLEMENTED_EXIT
    except (DDEngineError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error(f"unknown command: {arguments.command}")
    return 2
