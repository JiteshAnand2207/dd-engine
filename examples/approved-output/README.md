# Approved synthetic candidate output

Run ID: `20260901T040928457675Z-dede88eb959c`

This directory is the deliberately selected, checked-in handover subset of the
final primary synthetic run. It contains the run manifest and stage checkpoints,
source register, extraction/evidence records needed for audit, both intake rounds,
all five workstreams plus Tax, report/IC bundle, task and public-research ledgers,
and red-team challenge/reconciliation records. Local caches, rendered-page QA
intermediates, temporary task inputs and arbitrary run artifacts are excluded.

Start with:

- `outputs/due_diligence_report.md`
- `outputs/ic_brief.md`
- `outputs/ic_brief.pdf`
- `source_register/source_register.csv`
- `intake/round_1_questions.md` and `intake/round_2_questions.md`
- `red_team/red_team_challenge_log.md`
- `red_team/red_team_resolution.md`
- `logs/run-log.md` and `logs/public-research-log.jsonl`
- `outputs/report_validation.json`

Candidate validation passed with 176 structured citations, zero failed
citations, 21 traced calculations and an exactly two-page ISO A4 brief. The
red-team reconciliation resolved all 28 challenges.

Release limitation: this is not an independently release-ready artifact. The
run has no packet allowlist, sealed-packet manifest or brand-new-context isolation
manifest, and `outputs/report_validation.json` records
`independent_red_team_performed: false` and `release_ready: false`. The challenge
and resolution records are retained as required evidence, but they do not cure
that missing proof.
