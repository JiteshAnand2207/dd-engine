# dd-engine

`dd-engine` is the local deterministic foundation for a Codex-native
due-diligence workflow. Codex is the primary harness; Claude Code can follow the
same file-backed operating contract. Python never invokes a model API, and the
required path uses no provider API key, Docker, database or cloud service.

Phase 4 adds the complete deterministic source-register and safe-ingestion
layer. It inventories physical files, empty folders and bounded ZIP members,
classifies content signatures, records failures, duplicates and version
candidates, and writes seven run-local register artifacts. Extraction and all
later analytical stages remain interfaces only.

## Requirements and installation

Use Python 3.11 or later in an isolated environment:

```text
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Activate `.venv` using the command appropriate to the local shell before the two
`pip` commands, or call its Python executable directly. Document generation and
validation use pinned pure-Python packages; no Office application or mandatory
system utility is required. The exact versions and build backend are pinned in
`pyproject.toml`.

## Synthetic room validation

The canonical structured dataset, generated room, machine-readable manifest and
sealed issue key live beneath `synthetic/`, but only `synthetic/data_room/` is a
source-room input. Routine development and source-register work must use the
public-only validator, which does not open the sealed key:

```text
python scripts/validate_synthetic_room.py --room synthetic/data_room --manifest synthetic/room_manifest.json --canonical synthetic/canonical_dataset.json --public-only
```

Sealed deterministic regeneration and issue scoring remain a separate,
explicitly authorized post-analysis maintenance operation. The room contains
exactly 90 visible files: 27 Financial, 33 Legal and 30 Tax. The Legal ZIP has 10
file members. All names, people, identifiers and figures are fictional;
`.invalid` domains and `SYN` identifiers are used deliberately.

`synthetic/planted_issues/` is sealed ground truth. It may be read by the
explicit post-analysis validator, but never by registration, extraction,
drafting or red-team reasoning.

## Configuration

`dd-engine.toml` is the checked-in safe default. Relative `runs_dir` values are
resolved from the configuration file's directory. Unknown settings are rejected.
Telemetry, external logging and provider API-key requirements cannot be enabled.
Public research is disabled by default and is not implemented in Phase 4. The
`[register]` section configures maximum archive member count, total declared and
observed uncompressed bytes, and per-member uncompressed bytes. Limit breaches
are registered as terminal blocked rows rather than silently omitted.

## Run procedure

From the repository root:

```text
python -m dd_engine doctor
python -m dd_engine init-run
python -m dd_engine register --run runs/<run_id> --room /absolute/or/relative/path/to/room
python -m dd_engine status --run runs/<run_id>
```

`init-run` prints the absolute run path and immutable run ID. `--runs-root` can
select a different local output directory. `--config` can select another TOML
file. `doctor`, `init-run`, `register` and `status` also accept `--json`.

The register stage writes under `runs/<run_id>/source_register/`:

```text
source_register.json
source_register.csv
source_register.md
room_structure.json
duplicate_groups.json
version_families.json
unreadable_sources.json
```

ZIP containers remain source rows but are marked ineligible for document
analysis. Direct members use `zip://container.zip!/member` paths and are never
extracted to disk. Exact duplicate rows are retained while only one
representative is marked for later analysis; version candidates are retained and
never described as authoritative.

The future stage interfaces are:

```text
python -m dd_engine extract --run runs/<run_id>
python -m dd_engine intake --run runs/<run_id>
python -m dd_engine analyse --run runs/<run_id>
python -m dd_engine report --run runs/<run_id>
python -m dd_engine validate --run runs/<run_id>
```

In Phase 4 each command in this future-stage list exits with status 3 and `stage not implemented`. This is an
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
