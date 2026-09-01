# Phase 15 final handover and release audit

Audit date: 1 September 2026  
Final synthetic run ID: `20260901T040928457675Z-dede88eb959c`  
Repository revision audited: `05fee85f5cc6bf6675893c73aa8c106ee07fd081` plus the uncommitted Phase 15 change set  
Release decision: **BLOCKED**

## Executive conclusion

The repository contains every requested handover artifact, including a complete
evaluator README, fictional synthetic room, separately sealed planted-issue note,
approved synthetic report/IC bundle, source register, both intake rounds,
red-team challenge and resolution logs, honest task/research ledgers, delivery
notes, delivery manifest and acceptance/clean-clone evidence.

All deterministic final checks pass. The approved report has 176 structured
citations with zero failures, 21 traced calculations with zero failures, 100%
material-finding citation coverage and a two-page ISO A4 IC brief. The run's 28
red-team challenges are fully reconciled.

The candidate is nevertheless not release-ready. No
`packet-allowlist.json`, `sealed-packet-manifest.json` or
`isolation-manifest.json` exists, no logged red-team challenge task proves a
brand-new non-inheriting context, and the run validation correctly records
`independent_red_team_performed: false` and `release_ready: false`. This blocks
AC-014, AC-022 and AC-023 and makes final sharing with Gavin unsafe as a completed
trial handover.

## Evidence and instruction boundary

This audit read the complete trial-brief requirement matrix in
`docs/requirements-traceability.md`, `AGENTS.md`, `CLAUDE.md`, all four
authoritative planning documents, the four Phase 14 acceptance reports and the
complete red-team challenge/resolution reports. It did not open or use the
contents of `synthetic/planted_issues/` or `synthetic/shadow_ground_truth/`.
The planted-issue README was checked only for path presence and SHA-256 for the
delivery manifest. Sealed scoring was not run because verified independent red
team remains incomplete.

## Deliverable audit

The checksum-complete path inventory is in `DELIVERY_MANIFEST.md`. Key paths are:

| Deliverable | Path | Status |
|---|---|---|
| Repository runbook | `README.md` | PASS |
| Synthetic room | `synthetic/data_room/` | PASS, public-only validator |
| Sealed planted-issue note | `synthetic/planted_issues/README.md` | PRESENT, not used analytically |
| Due-diligence report | `examples/approved-output/run/outputs/due_diligence_report.md` | PASS as candidate |
| Exactly two-page IC brief | `examples/approved-output/run/outputs/ic_brief.pdf` | PASS |
| Source register | `examples/approved-output/run/source_register/source_register.csv` | PASS, 100 rows |
| Intake rounds | `examples/approved-output/run/intake/` | PASS, questions/answers for both rounds |
| Red-team challenge log | `examples/approved-output/run/red_team/red_team_challenge_log.md` | PRESENT; independence BLOCKED |
| Red-team resolution log | `examples/approved-output/run/red_team/red_team_resolution.md` | PASS, all 28 resolved |
| Task/token/cost log | `examples/approved-output/run/logs/run-log.jsonl` | PASS, honest unavailable values |
| Public-research log | `examples/approved-output/run/logs/public-research-log.jsonl` | PASS, `not_performed` |
| Delivery notes | `NOTES.md` | PASS, six required topics |
| Acceptance evidence | `docs/acceptance-report.md` and related Phase 14 reports | PASS as historical evidence |

The approved output is an intentional 71-file run subset plus its README. It
excludes caches, render intermediates, arbitrary runs and temporary task inputs.
The full source evidence remains reproducible from the tracked fictional room.

## Requirement disposition

After Phase 15, the acceptance matrix is **104 PASS, 0 FAIL, 3 BLOCKED** across
AC-001 through AC-107. Phase 15 fixes the prior AC-054 failure by adding the
delivery manifest and checked-in output pack. The remaining blocked criteria are:

- AC-014: sealed found/missed/false-positive scoring must wait until verified
  independent red team is complete.
- AC-022: no brand-new-context/allowlist/isolation proof exists.
- AC-023: challenge coverage cannot qualify as independent until AC-022 passes,
  even though the historical 28-item challenge log is fully reconciled.

All Phase 15 deliverable, README, notes, manifest, hygiene and deterministic
verification requirements pass. Final release and final-recipient sharing remain
blocked by the three criteria above, not by a failing deterministic test.

## Verification results

| Check | Command or method | Exact result |
|---|---|---|
| Complete test suite | `.venv/Scripts/python.exe -m pytest` | PASS: 112 passed in 50.22s |
| Lint | `.venv/Scripts/python.exe -m ruff check .` | PASS: all checks passed |
| Type checks | `.venv/Scripts/python.exe -m mypy` | PASS: no issues in 56 source files |
| Doctor | `.venv/Scripts/python.exe -m dd_engine doctor --json` | PASS: 7 pass, 2 optional warnings, 0 fail on Python 3.12.10 |
| Synthetic-room validator | `.venv/Scripts/python.exe scripts/validate_synthetic_room.py --room synthetic/data_room --manifest synthetic/room_manifest.json --canonical synthetic/canonical_dataset.json --public-only --json` | PASS: 32/32 checks; 90 visible, 10 ZIP members, 100 logical; sealed metadata not accessed |
| Source-register validator | fresh temporary `init-run` + `register`, then compare `(relative_path, sha256, size_bytes)` with approved register | PASS: 100 registered, 100 terminal, 100 approved rows, 0 mismatches |
| Citation validator | `dd_engine.evidence.validate_citations` on a temporary run-ID-named copy of approved output | PASS: 176 citations, 0 failed; 21 calculations, 0 failed; coverage 1.0 |
| Report validator | `.venv/Scripts/python.exe -m dd_engine validate --run <temporary-run-copy> --json` | PASS: 12,589 words; 27 material findings; 176 structured citations; 21 calculations; candidate validation true |
| IC page-count and visual validator | `pypdf.PdfReader` media-box assertion plus local PDFium PNG render of both pages | PASS: 2 pages; both 595.276 x 841.890 points (ISO A4); no clipping, overlap, broken glyphs/tables or missing footer/page number |
| Run-log validator | `.venv/Scripts/python.exe -m dd_engine audit-logs --run <temporary-run-copy> --json` | PASS: six completed stages covered; privacy passed; one `not_performed` research record |
| Delivery-manifest validator | `.venv/Scripts/python.exe scripts/validate_delivery_manifest.py --manifest DELIVERY_MANIFEST.md --json` | PASS: 26 rows after this audit is added; release status remains false |
| Markdown links | commit-candidate relative-link scan | PASS: no broken internal links; ignored source PDFs are named with hashes rather than linked |
| Placeholder/TODO review | repository text scan plus report validator | PASS: no delivery-output placeholder; remaining matches are validator/tests/requirements text only |
| Absolute local paths | repository/package path scan | PASS: operator paths redacted; only validator pattern definitions match `/Users/` or `/home/` |
| Secret scan | commit-candidate regex scan for private keys and common provider tokens | PASS: 318 candidate paths, 183 UTF-8 text files, 0 hits |
| Oversized-file review | commit-candidate size inventory | PASS: 7.012 MiB total; no file over 5 MiB; largest required file is 1.692 MiB extracted evidence |
| Git diff check | `git diff --check` plus status/diff review | PASS: no whitespace errors; no commit, tag or push performed |

The package run log itself contains 33 records: 31 `local_deterministic` and two
`frontier_judgment`; 32 succeeded and one failed attempt is retained. All 33
records honestly mark token usage unavailable. The two reasoning tasks have null
model IDs and costs with reasons. The run-log summary's USD 0.000000 recorded
estimate reflects zero-model local records, not a claimed price for hidden
subscription reasoning.

## Clean-clone result

PASS on Windows 11 using a new `%TEMP%` clone, a new Python 3.12.10 virtual
environment, the README editable development install, doctor and the delivery-
manifest validator. Clone-through-validation took 144.466 seconds, below the
20-minute setup gate. Because the operator prohibited committing, the Phase 15
diff and new files were explicitly overlaid onto a clone of committed HEAD; this
tests the final working tree but must be repeated from a plain clone after the
user creates the commit.

Two failed rehearsals are retained rather than hidden. The first exposed the
Windows case-only `notes.md` to `NOTES.md` rename and was fixed with a two-step
rename. The second exposed CRLF checkout invalidating text SHA-256 values; adding
`.gitattributes` to enforce LF fixed the problem. The qualifying third rehearsal
passed doctor (7/2/0) and manifest validation.

## Repository hygiene

| Check | Result |
|---|---|
| Real/confidential data | PASS: only declared fictional primary/shadow rooms and approved synthetic output are commit candidates |
| Secrets/tokens/credentials | PASS: no detected secret material; no environment files, keys or credentials selected |
| Absolute local paths | PASS after redacting historical operator paths; approved package contains none |
| Temporary files/venvs/caches | PASS: ignored only; none selected for commit |
| Broken links | PASS |
| Placeholder text | PASS in deliverables and outputs |
| TODOs affecting requirements | PASS: none found |
| Untracked required files | PASS once all files listed below are included together in the commit |
| Oversized unnecessary files | PASS |
| Hidden planted-issue dependency | PASS: runtime references are deny guards; generator/sealed-validator paths are explicit maintenance boundaries |

## Known limitations and release safety

- Red-team independence is not proved; this is the release blocker.
- Sealed planted-issue scoring was consequently not authorized or run.
- macOS/Linux setup commands are documented but only Windows was exercised.
- Offline installation is not proved.
- Optional OCR and document conversion were absent; explicit fallbacks passed.
- The 150-source memory result measures Python allocations, not total process RSS.
- Production archive limits, confidential-run retention and quantitative
  recall/false-positive thresholds remain operator/evaluator decisions.
- Irish legal/tax work is commercial diligence, not a formal opinion.

It is safe to create a commit containing the complete Phase 15 candidate change
set because tests, hygiene and commit-candidate scans pass. The commit message and
release metadata must not claim release readiness. It is **not safe to share with
Gavin as the final completed trial handover** until a verified new-context red
team, isolation manifest, challenge-task log, reconciliation revalidation and
authorized sealed scoring are complete.

## Git disposition

Commit together:

- `.gitattributes`
- `.gitignore`
- `README.md`
- case-only rename `notes.md` to `NOTES.md`
- `DELIVERY_MANIFEST.md`
- `docs/clean-clone-report.md`
- `docs/decisions.md`
- `docs/requirements-traceability.md`
- `docs/final-release-audit.md`
- `scripts/validate_delivery_manifest.py`
- `tests/test_delivery_manifest.py`
- the complete `examples/approved-output/` tree

Do not commit:

- `runs/`
- `.venv/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` or `__pycache__/`
- `.renders/` or OCR/render caches
- the ignored trial/source-room PDFs
- temporary clone/register directories under `%TEMP%`
- any real/confidential room, credentials, secrets or arbitrary local logs

No commit, tag, push or external send was performed during Phase 15.
