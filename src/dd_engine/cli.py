"""CLI for deterministic stages and validated analytical workstreams."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
from collections.abc import Callable, Sequence
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
from dd_engine.runtime import (
    LocalTaskSession,
    audit_run_logs,
    record_public_research,
    record_task_from_file,
    start_local_task,
)
from dd_engine.state import overall_state
from dd_engine.time import utc_now


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

    task_log_parser = subparsers.add_parser(
        "log-task", help="append one validated harness/model task record"
    )
    task_log_parser.add_argument("--run", required=True, type=Path, help="run directory")
    task_log_parser.add_argument("--input", required=True, type=Path, help="task JSON file")
    task_log_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    research_log_parser = subparsers.add_parser(
        "log-research", help="append one validated privacy-safe public-research record"
    )
    research_log_parser.add_argument("--run", required=True, type=Path, help="run directory")
    research_log_parser.add_argument("--input", required=True, type=Path, help="research JSON file")
    research_log_parser.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON"
    )

    audit_log_parser = subparsers.add_parser(
        "audit-logs", help="validate task coverage, usage honesty and research privacy"
    )
    audit_log_parser.add_argument("--run", required=True, type=Path, help="run directory")
    audit_log_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

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
    started_at = utc_now()
    started_monotonic = time.perf_counter()
    config = load_config(arguments.config)
    run_path = create_run(config, runs_root=arguments.runs_root)
    _, manifest = load_manifest(run_path)
    session = LocalTaskSession(
        run_path=run_path,
        stage="init",
        task_id=f"TASK-INIT-{secrets.token_hex(8)}",
        task_name="initialise_run",
        purpose="Create the immutable run ID, local directories, manifest and checkpoints.",
        started_at=started_at,
        source_ids_supplied=[],
        _started_monotonic=started_monotonic,
    )
    session.finish(
        output_artifact_paths=[
            "manifest.json",
            *[f"checkpoints/{stage}.json" for stage in STAGE_ORDER],
        ]
    )
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


def _log_task_command(arguments: argparse.Namespace) -> int:
    record = record_task_from_file(arguments.run, arguments.input)
    if arguments.json:
        print(json.dumps(record, indent=2, sort_keys=True))
    else:
        print(f"Logged task {record['task_id']} for run {record['run_id']}")
    return 0


def _log_research_command(arguments: argparse.Namespace) -> int:
    record = record_public_research(arguments.run, arguments.input)
    if arguments.json:
        print(json.dumps(record, indent=2, sort_keys=True))
    else:
        print(f"Logged public-research action {record['action']} for run {record['run_id']}")
    return 0


def _audit_logs_command(arguments: argparse.Namespace) -> int:
    result = audit_run_logs(arguments.run)
    if arguments.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Run-log audit: {result['status']}")
        print(f"Task records: {result['task_record_count']}")
        print(f"Path: {Path(arguments.run) / 'logs' / 'run-log-validation.json'}")
    return 0 if result["status"] == "passed" else 1


def _existing_outputs(run_path: Path, candidates: Sequence[str]) -> list[str]:
    return [path for path in candidates if (run_path / path).is_file()]


def _logged_output_paths(arguments: argparse.Namespace) -> list[str]:
    run_path, manifest = load_manifest(arguments.run)
    command = str(arguments.command)
    if command in STAGE_ORDER:
        stage = manifest["stages"][command]
        artifacts = stage.get("artifacts") if isinstance(stage, dict) else None
        if isinstance(artifacts, list) and artifacts:
            return [
                str(item["path"])
                for item in artifacts
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            ]
    if command == "intake":
        round_number = int(arguments.round_number)
        suffix = "answers.json" if arguments.answers is not None else "questions.json"
        return _existing_outputs(
            run_path,
            [
                f"intake/round_{round_number}_{suffix}",
                f"intake/round_{round_number}_questions.md",
                "intake/unresolved_items.json",
            ],
        )
    if command == "evidence":
        return _existing_outputs(
            run_path,
            [
                "evidence/claims.jsonl",
                "evidence/evidence.jsonl",
                "evidence/calculations.jsonl",
                "evidence/contradictions.jsonl",
                "evidence/gaps.jsonl",
                "evidence/issues.jsonl",
                "evidence/citation_validation.json",
                "evidence/evidence_coverage.md",
            ],
        )
    if command == "analyse":
        phase = int(arguments.phase)
        candidates = (
            [
                "workstreams/financial.json",
                "workstreams/financial.md",
                "workstreams/commercial.json",
                "workstreams/commercial.md",
                "workstreams/financial_calculations.md",
                "workstreams/customer_grouping.json",
                "workstreams/customer_grouping.md",
                "workstreams/phase_8_validation.json",
            ]
            if phase == 8
            else [
                "workstreams/legal_contractual.json",
                "workstreams/legal_contractual.md",
                "workstreams/operational_management.json",
                "workstreams/operational_management.md",
                "workstreams/it.json",
                "workstreams/it.md",
                "tax/tax-findings.json",
                "tax/tax-analysis.md",
                "workstreams/phase_9_validation.json",
                "workstreams/analysis_validation.json",
            ]
        )
        return _existing_outputs(run_path, candidates)
    return []


def _logged_task_identity(arguments: argparse.Namespace) -> tuple[str, str, str]:
    command = str(arguments.command)
    if command == "intake":
        action = "ingest_answers" if arguments.answers is not None else "generate_questions"
        task_name = f"intake_round_{arguments.round_number}_{action}"
        purpose = (
            f"{action.replace('_', ' ').capitalize()} for evidence-grounded intake round "
            f"{arguments.round_number}."
        )
        return "intake", task_name, purpose
    if command == "analyse":
        return (
            "analyse",
            f"analyse_phase_{arguments.phase}",
            f"Execute and validate the local Phase {arguments.phase} analysis pipeline.",
        )
    purposes = {
        "status": "Read the persistent run state without changing source-room data.",
        "register": "Inventory, hash and safely inspect the complete source room.",
        "extract": "Run native local extraction and materialize pending vision tasks.",
        "evidence": "Build and validate structured evidence, calculations and gaps.",
        "report": "Assemble and fail-closed validate the Phase 10 candidate report bundle.",
        "validate": "Revalidate the candidate report bundle and delivery checks.",
    }
    return command, command, purposes[command]


def _logged_source_ids(arguments: argparse.Namespace) -> list[str]:
    """Return registered source IDs actually supplied to a local stage."""

    if arguments.command in {"register", "status"}:
        return []
    run_path, _ = load_manifest(arguments.run)
    register_path = run_path / "source_register" / "source_register.json"
    if not register_path.is_file():
        return []
    payload = json.loads(register_path.read_text(encoding="utf-8"))
    sources = payload.get("sources") if isinstance(payload, dict) else None
    if not isinstance(sources, list):
        return []
    return sorted(
        {
            str(source["source_id"])
            for source in sources
            if isinstance(source, dict) and isinstance(source.get("source_id"), str)
        }
    )


def _run_logged_command(
    arguments: argparse.Namespace, handler: Callable[[argparse.Namespace], int]
) -> int:
    stage, task_name, purpose = _logged_task_identity(arguments)
    session = start_local_task(
        arguments.run,
        stage=stage,
        task_name=task_name,
        purpose=purpose,
        source_ids_supplied=_logged_source_ids(arguments),
    )
    try:
        exit_code = handler(arguments)
        if exit_code == 0:
            session.finish(output_artifact_paths=_logged_output_paths(arguments))
        else:
            session.finish(error=f"command returned exit code {exit_code}")
        return exit_code
    except Exception as exc:
        session.finish(error=exc)
        raise


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
            return _run_logged_command(arguments, _status_command)
        if arguments.command == "register":
            return _run_logged_command(arguments, _register_command)
        if arguments.command == "extract":
            return _run_logged_command(arguments, _extract_command)
        if arguments.command == "intake":
            return _run_logged_command(arguments, _intake_command)
        if arguments.command == "evidence":
            return _run_logged_command(arguments, _evidence_command)
        if arguments.command == "analyse":
            return _run_logged_command(arguments, _analyse_command)
        if arguments.command == "report":
            return _run_logged_command(arguments, _report_command)
        if arguments.command == "validate":
            return _run_logged_command(arguments, _validate_command)
        if arguments.command == "log-task":
            return _log_task_command(arguments)
        if arguments.command == "log-research":
            return _log_research_command(arguments)
        if arguments.command == "audit-logs":
            return _audit_logs_command(arguments)
    except (DDEngineError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error(f"unknown command: {arguments.command}")
    return 2
