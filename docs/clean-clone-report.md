# Phase 14 clean-clone report

Date: 1 September 2026  
Committed revision tested: `bc3b6825290ec61ea034fe12a27be6a49f5f1f47`

## Outcome

PASS, with an earlier command-line mistake retained below. A clean native-Windows
clone was installed and made runnable in 206.388 seconds (3 minutes 26.388
seconds), comfortably below the 20-minute ceiling. A later qualifying run used
the exact README command forms, an absolute room path and the run path printed by
`init-run`; it completed both saved-answer rounds, Phases 8-10, final validation
and the task-log audit in 26.643 seconds. Setup and analysis were timed separately.

## Safe clone boundary

The resolved explicit directory was:

`%LOCALAPPDATA%\Temp\dd-engine-phase14-clean-20260901T132046560`

Before creation, the absolute target was checked to be a descendant of
`%LOCALAPPDATA%\Temp`, not the workspace, home directory or a
computed broad path. The repository was cloned with `git clone --no-local` from
committed HEAD. Initial `git status --short` was empty.

The clone used Python 3.12.10 in a newly created `.venv`, upgraded pip and ran
the README editable install `python -m pip install -e ".[dev]"`. Doctor then
reported 7 passes, 2 optional-capability warnings and 0 failures. The warnings
were the documented optional OCR/document-conversion capabilities; required PDF
rendering and all pinned Python packages passed.

## Timing

| Measurement | Included work | Wall time | Result |
|---|---|---:|---|
| Setup | safe path check, no-local clone, new venv, pip upgrade, editable dev install, doctor | 206.388s | PASS, under 1,200s |
| First full rehearsal | run creation through log audit, including saved-answer authoring | 111.141s | Completed, but see the command mistake below |
| Qualifying README-form rehearsal | registration through log audit using existing explicit saved-answer fixtures | 26.643s | PASS |

The qualifying run ID was `20260901T082422670189Z-e68853f7aeb3`. Its explicit
room path was:

`%LOCALAPPDATA%\Temp\dd-engine-phase14-clean-20260901T132046560\synthetic\data_room`

## Qualifying run evidence

The successful sequence used `--run <printed absolute run path>` and the README's
`--room <absolute room path>` spelling throughout.

| Gate | Evidence | Result |
|---|---|---|
| Register | 100 registered and 100 terminal logical sources | PASS |
| Extract | 100/100 terminal; four optional-vision tasks remained explicit | PASS |
| Intake round 1 | 11 saved answers ingested; 9 matters stayed unresolved | PASS |
| Intake round 2 | 12 saved answers ingested; 16 total matters stayed unresolved | PASS |
| Evidence | Completed with explicit gaps and no fabricated pre-analysis claims | PASS |
| Phase 8 | 8 findings; validation passed | PASS |
| Phase 9 | 1 additional finding; validation passed | PASS |
| Report | 7,519 words; IC brief exactly two pages | PASS |
| Validate | Candidate validation passed | PASS |
| Log audit | 12 successful local-deterministic records; privacy passed; no missing stage log | PASS |

The saved answers deliberately remain test-only. Open matters were not converted
to management representations. The clone's required path used no Docker,
database, cloud storage, provider API key or mandatory system utility.

## Independence from the working checkout

After both rehearsals, `git rev-parse HEAD` still returned the committed revision
above and `git diff` for tracked files was empty. The only visible untracked files
were the two deliberately authored run-input files:

- `clean-clone-round1-answers.json`
- `clean-clone-round2-answers.json`

The clone did not copy or import any uncommitted source, documentation or fixture
from the working checkout. Therefore the committed baseline engine is reproducible
without a local uncommitted file. This does not pretend that the new Phase 14
changes are already committed; they remain only in the working checkout because
the operator prohibited committing.

## Failures and recovery

The first rehearsal initially passed a bare run ID to `--run`, which the CLI
correctly rejected because README requires the printed run path or
`runs/<run_id>`. The command was corrected and that run completed. It also used
the documented CLI alias `--data-room` after consulting command help, rather than
the README spelling `--room`. Neither error was hidden, but that attempt is not
used as the strict README-form qualification.

The second run began with a fresh `init-run` and used the exact README forms from
the outset. No command in that qualifying sequence failed.

## Disposition

AC-099: PASS. The reproducibility and time gate pass. This is candidate-build
evidence only; it does not satisfy the still-missing verified independent
red-team/reconciliation release gate.
