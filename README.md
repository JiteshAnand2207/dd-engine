# dd-engine

`dd-engine` is the local deterministic foundation for a Codex-native
due-diligence workflow. Codex is the primary harness; Claude Code can follow the
same file-backed operating contract. Python never invokes a model API, and the
required path uses no provider API key, Docker, database or cloud service.

Phase 2 implements environment checks, run creation and persistent status. The
analytical stage commands expose their future interfaces but deliberately return
`stage not implemented` with a nonzero exit code.

## Requirements and installation

Use Python 3.11 or later in an isolated environment:

```text
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Activate `.venv` using the command appropriate to the local shell before the two
`pip` commands, or call its Python executable directly. Runtime code uses only
the Python standard library. The exact development tool versions and build
backend are pinned in `pyproject.toml`.

## Configuration

`dd-engine.toml` is the checked-in safe default. Relative `runs_dir` values are
resolved from the configuration file's directory. Unknown settings are rejected.
Telemetry, external logging and provider API-key requirements cannot be enabled.
Public research is disabled by default and is not implemented in Phase 2.

## Run procedure

From the repository root:

```text
python -m dd_engine doctor
python -m dd_engine init-run
python -m dd_engine status --run runs/<run_id>
```

`init-run` prints the absolute run path and immutable run ID. `--runs-root` can
select a different local output directory. `--config` can select another TOML
file. `doctor`, `init-run` and `status` also accept `--json`.

The future stage interfaces are:

```text
python -m dd_engine register --run runs/<run_id>
python -m dd_engine extract --run runs/<run_id>
python -m dd_engine intake --run runs/<run_id>
python -m dd_engine analyse --run runs/<run_id>
python -m dd_engine report --run runs/<run_id>
python -m dd_engine validate --run runs/<run_id>
```

In Phase 2 each exits with status 3 and `stage not implemented`. This is an
intentional scope boundary, not a successful stage result.

## Run structure and resumption

Every run contains `manifest.json` and the directories `checkpoints`, `logs`,
`source_register`, `extracts`, `intake`, `evidence`, `workstreams`, `red_team` and
`outputs`. Stage states are `not_started`, `running`, `awaiting_input`,
`completed`, `failed` and `invalidated`.

State writes are atomic. Required artifacts must exist, be nonempty, contain the
run ID and pass format-level validation before completion. Failure diagnostics
and error history are retained for safe reruns. A changed stage input/output
checksum invalidates affected downstream results.

Source rooms are read-only and must remain outside the run directory. Arbitrary
runs, real rooms, secrets, caches, renders, OCR caches and local logs are ignored
by Git. Only the specifically allowlisted approved synthetic/example locations
may be committed later.

## Development verification

```text
python -m pytest
python -m ruff check .
python -m mypy
```

Missing optional OCR, PDF rendering or document conversion tools are doctor
warnings with stated fallbacks, not installation failures. See `AGENTS.md` and
`CLAUDE.md` for the full evidence, privacy and honesty contract.

