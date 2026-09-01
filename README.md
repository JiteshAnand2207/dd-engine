# dd-engine

`dd-engine` is the local deterministic core for a Codex-native
due-diligence workflow. Codex is the primary harness; Claude Code can follow the
same file-backed operating contract. Python never invokes a model API, and the
required path uses no provider API key, Docker, database or cloud service.

Phases 8 and 9 add sequential financial, commercial, Irish legal/contractual,
operational/management and IT analysis plus the standalone Tax module to the
Phase 7 evidence foundation. Findings separate source fact from inference, retain
reported and recomputed values, and cannot run until both intake rounds have
explicitly ingested answers. Phase 10 assembles the full adviser report and
exactly two-page A4 investment-committee brief, then validates the candidate
bundle fail closed. Phase 11 adds the three-class model-routing contract,
complete local task/research ledgers and one Codex-first, Claude-compatible
runtime flow. Phase 14 adds a filename-independent shadow-room rehearsal, a
150-logical-source stress corpus, hostile-input regressions and documented
clean-clone/manual-audit evidence. Phase 15 adds the evaluator handover package
and release audit. The included synthetic candidate is deliberately not labelled
release-ready because the historical red-team artifacts do not prove a brand-new
non-inheriting context.

## Clone, requirements and installation

Install Git and Python 3.11 or later. Clone and enter the repository:

```text
git clone https://github.com/JiteshAnand2207/dd-engine.git
cd dd-engine
```

Create an isolated environment. On Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m dd_engine doctor --json
```

On macOS or Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m dd_engine doctor --json
```

If `py -3.11` is unavailable on Windows, use the installed Python 3.11+ launcher
or call `.venv`'s Python executable directly. Document generation, extraction,
spreadsheet parsing and PDF rendering use pinned local Python packages; no Office
application or mandatory system utility is required. Tesseract OCR is optional;
missing OCR leaves explicit vision tasks. The exact versions and build backend
are pinned in `pyproject.toml`.

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

The independent Phase 14 shadow room has a different fictional company,
periods, people, values, names and issue distribution. Generate its public room
and the separate 150-logical-source corpus with:

```text
python scripts/generate_phase14_rooms.py --shadow-root synthetic/shadow --scale-root synthetic/scale_150
```

Only `synthetic/shadow/data_room/` and its public room manifest may be inspected
during the shadow rehearsal. `synthetic/shadow_ground_truth/` is a sealed scoring
boundary: do not open, list, hash, search or otherwise inspect it until the
fresh-context analysis is complete. The scale corpus deliberately uses small
files while exercising registration, SHA-256 hashing, ten in-memory ZIP members,
extraction, cache reuse/invalidation and failure isolation beyond 100 sources.

## Configuration

`dd-engine.toml` is the checked-in safe default. Relative `runs_dir` values are
resolved from the configuration file's directory. Unknown settings are rejected.
Telemetry, external logging and provider API-key requirements cannot be enabled.
Public research is disabled by default. Phase 9 logs that it was not performed;
any future enabled research must use non-confidential queries and a local query,
timestamp, purpose, URL and conclusion ledger. The
`[register]` section configures maximum archive member count, total declared and
observed uncompressed bytes, and per-member uncompressed bytes. Limit breaches
are registered as terminal blocked rows rather than silently omitted.

The `[extraction]` section locks deterministic-first handling, controls optional
OCR, sets the native-PDF text threshold and PDF render scale, and uses an
explicit unsupported-format quarantine policy. These values, detected OCR
capability and extractor/dependency versions form the cache fingerprint.

## Primary runtime flow

For a complete clean-clone run, open this repository in Codex and send this
instruction, replacing the room path with the real absolute path:

```text
Follow prompts/runtime/run_engine.md exactly. ROOM_PATH is
<ABSOLUTE_PATH_TO_DATA_ROOM>. Use runs as RUNS_ROOT. Stop at both intake gates.
```

The master prompt is [prompts/runtime/run_engine.md](prompts/runtime/run_engine.md).
It requires the room path, rejects unsafe room/run overlap and owns the full
doctor-through-delivery sequence. The room is read-only; use a separate run
directory for every deal. The operator sequence, answer-file format, routing and
logging contracts are in [the runtime guide](docs/runtime-flow.md). Claude Code
may use the same prompt and CLI. Codex remains primary; neither harness is assumed
to expose an exact model ID, selectable cheaper tier, token counts, billing or
automatic isolated-task creation.

The checked-in [routing policy](config/model-routing.yaml) has exactly three
classes: `local_deterministic`, `economical_reasoning` and
`frontier_judgment`. Local work is an honest zero-model route. A cheaper model is
used only when the active harness actually exposes one. Python never resolves or
calls a model.

## Run procedure

From the repository root:

```text
python -m dd_engine doctor
python -m dd_engine init-run
python -m dd_engine register --run runs/<run_id> --room /absolute/or/relative/path/to/room
python -m dd_engine extract --run runs/<run_id> --room /absolute/or/relative/path/to/room
python -m dd_engine intake --run runs/<run_id> --round 1
python -m dd_engine evidence --run runs/<run_id>
python -m dd_engine status --run runs/<run_id>
```

`init-run` prints the absolute run path and immutable run ID. Pass that run path
(or its exact `runs/<run_id>` equivalent) to every later command; a bare run ID
is not accepted. `--runs-root` can select a different local output directory.
`--config` can select another TOML
file. `doctor`, `init-run`, `register`, `extract`, `intake`, `evidence` and `status`
also accept `--json`.

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

The extract stage writes under `runs/<run_id>/extracts/`:

```text
extraction_manifest.json
extracted_units.jsonl
extraction_failures.json
needs_vision.json
rendered_pages/
cache/
```

Every registered source receives one terminal extraction status. Units retain
the source ID/hash/path, a format-native locator, method, confidence,
warning/limitation and extracted-content checksum. ZIP members are read in
memory and keep `zip://...!/member` virtual paths. Source bytes are hash-checked
before per-source cache reuse. Cache identity includes the source checksum,
extractor version and extraction configuration/capability fingerprint.

PDF locators use real one-based page numbers. DOCX uses structural paragraph,
heading and table/row/cell locators and does not invent page numbers. Workbook
units retain hidden sheet/row/column state, formulas, cached values, merged/named
ranges and number formats; the engine never recalculates a workbook. Pending
vision tasks point only to local rendered assets and always have a null model
result until a separate Codex/Claude vision-review task records one in a future
phase.

The intake stage writes under `runs/<run_id>/intake/`:

```text
round_1_questions.md
round_1_questions.json
round_1_answers.json       created only by explicit ingestion
round_2_questions.md
round_2_questions.json
round_2_answers.json       created only by explicit ingestion
unresolved_questions.md
```

Generating a round changes the run to `awaiting_input`. It never creates or
infers an answer. Send the generated Markdown packet to the deal lead and ingest
their reply from a JSON file:

```text
python -m dd_engine intake --run runs/<run_id> --round 1 --answers /path/to/round_1_reply.json
python -m dd_engine intake --run runs/<run_id> --round 2
python -m dd_engine intake --run runs/<run_id> --round 2 --answers /path/to/round_2_reply.json
```

The answer input is an object whose `answers` value is either a mapping from
question ID to verbatim text, or a list of objects with `question_id` and
`answer`. Optional `answered_by`, `answered_at`, `run_id` and `round_number`
fields add provenance. Missing questions are recorded as unanswered; `N/A`,
`None`, cross-references, partial and vague replies remain open or narrowed.

Round one is capped at 12 questions and round two at 15. Every question records
its evidence/gap, decision relevance, expected answer and invalidation scope.
Excluded candidates retain a reason. Re-ingesting the identical answer hash is
idempotent; changed answers invalidate only their declared affected stages and
dependants.

The evidence foundation can be refreshed after extraction and after either intake
answer ingestion. Running it while intake is paused records silence, vague replies,
pending vision and extraction failures as gaps; it does not complete intake or
start analysis. It writes under `runs/<run_id>/evidence/`:

```text
claims.jsonl
evidence.jsonl
calculations.jsonl
contradictions.jsonl
gaps.jsonl
issues.jsonl
citation_validation.json
evidence_coverage.md
```

Empty analytical record files are intentional until a Codex workstream supplies
records. Citation validation checks source/checksum identity, PDF pages, XLSX
sheets/cells/ranges, DOCX paragraphs/tables, CSV rows/columns and intrinsic image
regions. A citation to a potentially superseded source fails unless the record
explicitly acknowledges that status. Exact duplicates share one independence key.

Calculation records require explicit period, currency, sign and unit
normalisation; a versioned formula; separate reported and recomputed values;
rounding; source inputs and locators; and a deterministic or model-assisted method.
A missing input stays null and blocks recomputation rather than becoming zero.

After both intake rounds have been explicitly answered, run analysis in order:

```text
python -m dd_engine analyse --run runs/<run_id> --phase 8
python -m dd_engine analyse --run runs/<run_id> --phase 9
```

Phase 8 writes `workstreams/financial.json`, `financial.md`,
`commercial.json`, `commercial.md`, `financial_calculations.md` and
`customer_grouping.md`. Phase 9 writes the legal/contractual,
operational/management and IT JSON/Markdown pairs plus `tax/tax-findings.json`
and `tax/tax-analysis.md`. Both phases validate citations and required analytical
fields; Phase 9 completes the `analyse` stage. Neither analysis phase creates a
report. Generate and revalidate the Phase 10 bundle with:

```text
python -m dd_engine report --run runs/<run_id>
python -m dd_engine validate --run runs/<run_id>
```

`report` requires current passing Phase 8/9 outputs and writes
`outputs/due_diligence_report.md`, `outputs/ic_brief.md`,
`outputs/ic_brief.pdf`, `outputs/outstanding_information.md` and
`outputs/report_validation.json`. Material claims must resolve through the
native citation engine, every calculation must retain its trace, and required
sections/placeholders are checked. The deterministic PDF renderer fails before
overflow and the validator requires exactly two ISO A4 pages. `validate` repeats
the bundle checks independently. A passing Phase 10 validation does not imply
that the later independent red-team/reconciliation gate has run.

Every documented CLI stage invocation appends a privacy-safe zero-model record to
`logs/run-log.jsonl` and refreshes `logs/run-log.md`. Record actual harness
reasoning with `log-task`, public research with `log-research`, and reconcile all
completed stages with:

```text
python -m dd_engine log-task --run runs/<run_id> --input /path/to/task.json
python -m dd_engine log-research --run runs/<run_id> --input /path/to/research.json
python -m dd_engine audit-logs --run runs/<run_id> --json
```

Unavailable model IDs, tokens and API-equivalent costs remain null with explicit
reasons. API-equivalent cost is calculated only from usage and a versioned rate
card; subscription is recorded as a billing mode, not converted into a fictional
per-task charge. Logs contain identifiers, source IDs, timings and output hashes,
not raw sensitive room content. See the runtime guide for the complete schemas.

## Run structure and resumption

Every run contains `manifest.json` and the directories `checkpoints`, `logs`,
`source_register`, `extracts`, `intake`, `evidence`, `workstreams`, `tax`,
`citations`, `red_team` and `outputs`. Stage states are `not_started`, `running`, `awaiting_input`,
`completed`, `failed` and `invalidated`.

State writes are atomic. Required artifacts must exist, be nonempty, contain the
run ID and pass format-level validation before completion. Failure diagnostics
and error history are retained for safe reruns. A changed stage input/output
checksum invalidates affected downstream results.

Source rooms are read-only and must remain outside the run directory. All
derived extraction assets stay under that run's `extracts/` tree. Arbitrary runs,
real rooms, secrets, caches, renders, OCR caches and local logs are ignored by
Git. Only the specifically allowlisted synthetic/example locations may
be committed later.

## Evaluation paths

### 1. Quick evaluation using the completed synthetic example

Open [`example_outputs/README.md`](example_outputs/README.md) and review the
completed synthetic demonstration package for run
`20260901T081036940718Z-ea9100a654cb`. It includes the full due-diligence
report, exactly two-page IC brief PDF, source register, extraction summary,
two intake rounds, structured ledgers, all workstreams and validation results.

Gavin does **not** need to answer anything before receiving this repository.
The included answers are prominently named **TEST-ONLY SYNTHETIC ANSWERS** and
are fictional test fixtures, not Gavin's responses or live deal-lead input. The
full example output comes only from this completed test-only run. It remains a
candidate bundle: its validation records `release_ready: false` because no
independent red-team isolation proof is present.

### 2. Interactive run with evaluator answers at both intake rounds

For a new room, use the primary runtime flow above with a separate run directory.
The engine intentionally pauses after Round 1 and again after Round 2. At each
pause, provide a JSON answer file through `intake --answers` before continuing;
the engine never manufactures a response from silence.

The canonical unanswered synthetic run
`runs/20260831T225933370390Z-a3b4274aee33` is deliberately left in
`awaiting_input`. It is not a completed report run and is not the source of the
shipped example outputs.

## Finding the outputs

Use `python -m dd_engine status --run runs/<run_id> --json` to inspect stage
state. The final report bundle is under `runs/<run_id>/outputs/`; the source
register is under `source_register/`; both intake rounds are under `intake/`;
task and public-research ledgers are under `logs/`; and independent red-team
artifacts belong under `red_team/`.

The checked-in evaluator example is [`example_outputs/`](example_outputs/README.md).
It is derived only from completed demonstration run
`20260901T081036940718Z-ea9100a654cb`; its two answer artifacts are explicitly
labelled test-only synthetic fixtures. The example excludes raw extracted text,
caches and rendered assets, while retaining source IDs and citation relationships.

## Troubleshooting

- `No module named dd_engine` or a missing package usually means the virtual
  environment is inactive or the editable install was run with a different
  Python. Activate `.venv`, then rerun `python -m pip install -e ".[dev]"` and
  `python -m dd_engine doctor --json`.
- `Python 3.11+ required` means the launcher selected an older interpreter.
  Recreate `.venv` with a Python 3.11 or newer executable.
- A bare run ID is rejected. Pass the absolute path printed by `init-run`, or
  `runs/<run_id>` from the repository root.
- A room path is rejected when it is missing, is the repository/run root, is a
  symlink or reparse point, overlaps the output path, or points at sealed planted
  truth. Choose the actual data-room directory and a separate output root.
- `awaiting_input` is expected. Open the generated Markdown packet, collect the
  deal lead's answers in JSON, ingest it with `--answers`, and only then continue.
- Corrupt, encrypted, unsupported or image-only sources remain explicit. Review
  `source_register/unreadable_sources.json`,
  `extracts/extraction_failures.json` and `extracts/needs_vision.json`; do not
  delete or invent around those limitations.
- Tesseract/document-conversion warnings are optional-capability warnings. Native
  PDF rendering is required; rerun the editable install if doctor marks it failed.
- `validate` can pass while `release_ready` remains false. Complete and prove the
  brand-new-context red-team flow from `prompts/runtime/red_team.md`; do not
  reinterpret candidate validation as final release approval.

## Development verification

```text
python -m pytest
python -m pytest tests/test_phase14.py
python -m ruff check .
python -m mypy
python scripts/validate_delivery_manifest.py --manifest DELIVERY_MANIFEST.md
```

Missing optional OCR or document conversion tools are doctor warnings with
stated fallbacks, not installation failures. Local PDF rendering is a required
pinned Python capability. See `AGENTS.md` and `CLAUDE.md` for the full evidence,
privacy and honesty contract.
