"""CLI for deterministic stages and validated analytical workstreams."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from dd_engine import __version__
from dd_engine.analysis import analyse_run
from dd_engine.config import load_config
from dd_engine.constants import STAGE_ORDER
from dd_engine.doctor import format_doctor_report, run_doctor
from dd_engine.errors import DDEngineError
from dd_engine.evidence import build_evidence_foundation
from dd_engine.extraction import extract_run
from dd_engine.intake import generate_intake_questions, ingest_intake_answers
from dd_engine.inventory import RegisterLimits, register_room
from dd_engine.reporting import generate_report, validate_report_outputs
from dd_engine.runs import create_run, load_manifest
from dd_engine.state import overall_state


def _add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, help="path to dd-engine TOML configuration")


def build_parser() -> argparse.ArgumentParser:
    """Build the public CLI parser."""

    parser = argparse.ArgumentParser(
        prog="python -m dd_engine",
        description="Codex-native local-first due-diligence engine",
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

    evidence_parser = subparsers.add_parser(
        "evidence",
        help="build and validate the extraction-dependent evidence/calculation foundation",
    )
    evidence_parser.add_argument("--run", required=True, type=Path, help="run directory")
    evidence_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    for stage_name in STAGE_ORDER:
        stage_parser = subparsers.add_parser(
            stage_name,
            help=(
                "inventory the complete source room"
                if stage_name == "register"
                else (
                    "extract all registered sources with durable locators"
                    if stage_name == "extract"
                    else (
                        "generate or ingest one evidence-grounded intake round"
                        if stage_name == "intake"
                        else (
                            "run Phase 8 then Phase 9 analytical workstreams"
                            if stage_name == "analyse"
                            else (
                                "generate the Phase 10 report and two-page IC brief"
                                if stage_name == "report"
                                else "run fail-closed Phase 10 final validation"
                            )
                        )
                    )
                )
            ),
        )
        stage_parser.add_argument("--run", required=True, type=Path, help="run directory")
        if stage_name in {"register", "extract"}:
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
        elif stage_name == "intake":
            stage_parser.add_argument(
                "--round",
                required=True,
                type=int,
                choices=(1, 2),
                dest="round_number",
                help="intake round to generate or answer",
            )
            stage_parser.add_argument(
                "--answers",
                type=Path,
                help="explicit JSON deal-lead answer file; omit to generate questions",
            )
            stage_parser.add_argument(
                "--json", action="store_true", help="emit machine-readable JSON"
            )
        elif stage_name == "analyse":
            stage_parser.add_argument(
                "--phase",
                required=True,
                type=int,
                choices=(8, 9),
                help="run Phase 8 first, then Phase 9",
            )
            stage_parser.add_argument(
                "--json", action="store_true", help="emit machine-readable JSON"
            )
        else:
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


def _extract_command(arguments: argparse.Namespace) -> int:
    config = load_config(arguments.config)
    outcome = extract_run(arguments.run, arguments.room, config)
    payload = {
        "input_checksum": outcome.input_checksum,
        "path": str(outcome.run_path / "extracts"),
        "reused": outcome.reused,
        "run_id": outcome.run_path.name,
        "summary": outcome.summary,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        action = "Reused" if outcome.reused else "Completed"
        print(f"{action} extraction for run {outcome.run_path.name}")
        print(f"Path: {outcome.run_path / 'extracts'}")
        print(
            "Sources: "
            f"{outcome.summary['sources_terminal']}/{outcome.summary['sources_total']} terminal; "
            f"{outcome.summary['vision_queue_count']} vision task(s) pending"
        )
    return 0


def _intake_command(arguments: argparse.Namespace) -> int:
    outcome = (
        ingest_intake_answers(arguments.run, arguments.round_number, arguments.answers)
        if arguments.answers is not None
        else generate_intake_questions(arguments.run, arguments.round_number)
    )
    payload = {
        "action": outcome.action,
        "path": str(outcome.run_path / "intake"),
        "question_count": outcome.question_count,
        "reused": outcome.reused,
        "round_number": outcome.round_number,
        "run_id": outcome.run_path.name,
        "stage_state": outcome.stage_state,
        "unresolved_count": outcome.unresolved_count,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        action = "Reused" if outcome.reused else "Completed"
        print(f"{action} intake {outcome.action} for round {outcome.round_number}")
        print(f"Path: {outcome.run_path / 'intake'}")
        print(f"Run state: {outcome.stage_state}")
        print(f"Questions: {outcome.question_count}; unresolved: {outcome.unresolved_count}")
    return 0


def _evidence_command(arguments: argparse.Namespace) -> int:
    outcome = build_evidence_foundation(arguments.run)
    payload = {
        "input_fingerprint": outcome.input_fingerprint,
        "path": str(outcome.run_path / "evidence"),
        "reused": outcome.reused,
        "run_id": outcome.run_path.name,
        "summary": outcome.summary,
        "validation_passed": outcome.validation_passed,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        action = "Reused" if outcome.reused else "Completed"
        print(f"{action} evidence foundation for run {outcome.run_path.name}")
        print(f"Path: {outcome.run_path / 'evidence'}")
        print(
            "Records: "
            f"{outcome.summary['claim_count']} claims; "
            f"{outcome.summary['evidence_count']} evidence; "
            f"{outcome.summary['calculation_count']} calculations; "
            f"{outcome.summary['gap_count']} gaps"
        )
        print(f"Citation validation: {'passed' if outcome.validation_passed else 'failed'}")
    return 0 if outcome.validation_passed else 1


def _analyse_command(arguments: argparse.Namespace) -> int:
    outcome = analyse_run(arguments.run, arguments.phase)
    payload = {
        "input_fingerprint": outcome.input_fingerprint,
        "path": str(outcome.run_path / "workstreams"),
        "phase": outcome.phase,
        "reused": outcome.reused,
        "run_id": outcome.run_path.name,
        "stage_state": outcome.stage_state,
        "summary": outcome.summary,
        "validation_passed": outcome.validation_passed,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        action = "Reused" if outcome.reused else "Completed"
        print(f"{action} Phase {outcome.phase} analysis for run {outcome.run_path.name}")
        print(f"Path: {outcome.run_path / 'workstreams'}")
        print(f"Analysis stage: {outcome.stage_state}")
        print(f"Findings: {outcome.summary.get('finding_count', 0)}")
        print(f"Validation: {'passed' if outcome.validation_passed else 'failed'}")
    return 0 if outcome.validation_passed else 1


def _report_command(arguments: argparse.Namespace) -> int:
    outcome = generate_report(arguments.run)
    payload = {
        "input_fingerprint": outcome.input_fingerprint,
        "path": str(outcome.run_path / "outputs"),
        "reused": outcome.reused,
        "run_id": outcome.run_path.name,
        "stage_state": outcome.stage_state,
        "summary": outcome.summary,
        "validation_passed": outcome.validation_passed,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        action = "Reused" if outcome.reused else "Completed"
        print(f"{action} Phase 10 report for run {outcome.run_path.name}")
        print(f"Path: {outcome.run_path / 'outputs'}")
        print(f"Report words: {outcome.summary.get('report_word_count', 0)}")
        print(f"IC brief pages: {outcome.summary.get('brief_page_count', 0)}")
        print(f"Validation: {'passed' if outcome.validation_passed else 'failed'}")
    return 0 if outcome.validation_passed else 1


def _validate_command(arguments: argparse.Namespace) -> int:
    outcome = validate_report_outputs(arguments.run)
    payload = {
        "input_fingerprint": outcome.input_fingerprint,
        "path": str(outcome.run_path / "outputs" / "report_validation.json"),
        "reused": outcome.reused,
        "run_id": outcome.run_path.name,
        "stage_state": outcome.stage_state,
        "summary": outcome.summary,
        "validation_passed": outcome.validation_passed,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        action = "Reused" if outcome.reused else "Completed"
        print(f"{action} Phase 10 final validation for run {outcome.run_path.name}")
        print(f"Path: {outcome.run_path / 'outputs' / 'report_validation.json'}")
        print(f"Validation: {'passed' if outcome.validation_passed else 'failed'}")
    return 0 if outcome.validation_passed else 1


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
        if arguments.command == "extract":
            return _extract_command(arguments)
        if arguments.command == "intake":
            return _intake_command(arguments)
        if arguments.command == "evidence":
            return _evidence_command(arguments)
        if arguments.command == "analyse":
            return _analyse_command(arguments)
        if arguments.command == "report":
            return _report_command(arguments)
        if arguments.command == "validate":
            return _validate_command(arguments)
    except (DDEngineError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error(f"unknown command: {arguments.command}")
    return 2
