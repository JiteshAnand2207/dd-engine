# Phase 14 acceptance report

Date: 1 September 2026  
Implementation checkout: uncommitted by operator instruction  
Baseline revision: `bc3b6825290ec61ea034fe12a27be6a49f5f1f47`

## Overall decision

Phase 14's generalisation, 150-source scale, clean-clone, hostile-input and manual
audit gates pass. The project is suitable for a controlled candidate handover,
but it is **not release-ready** and the complete release handover gate does not
pass. A verified independent red-team context/reconciliation packet is absent,
sealed planted-issue scoring is consequently not complete, and no final
hash-complete delivery manifest has been produced.

Across AC-001 through AC-107: **103 PASS, 1 FAIL, 3 BLOCKED**. The FAIL is the
absent final delivery manifest (AC-054). The BLOCKED gates are sealed issue
scoring (AC-014) and independent red-team execution/coverage (AC-022/AC-023).

## Phase 14 requirement verification

| Requirement | Status | Evidence |
|---|---|---|
| P14-001 | PASS | `AGENTS.md` and all four authoritative documents were read completely; final run `20260901T040928457675Z-dede88eb959c` and initial clean Git state were inspected first. |
| P14-002 | FAIL | Primary planted truth was never opened, and the qualifying shadow context stayed sealed. However, the first shadow agent enumerated the truth filename and the implementation context later opened shadow truth; neither context is accepted as analytical evidence. |
| P14-003-P14-008 | PASS | `scripts/generate_phase14_rooms.py`, public shadow manifest and `tests/test_phase14.py` cover every requested variation/trap. |
| P14-009 | PASS | Semantic selectors, dynamic periods/labels and absence of primary identifiers in 16 shadow artifacts. |
| P14-010 | PASS | Post-fix fresh run `20260901T081036940718Z-ea9100a654cb`; context audit reports no truth listing/read/hash/search. |
| P14-011-P14-014 | PASS | Exactly 150 logical sources; 150 terminal states; 10 ZIP members; one isolated failure; 3.273 MiB traced peak. |
| P14-015-P14-020 | PASS | Explicit temp clone at committed HEAD; setup 206.388s; qualifying analysis 26.643s; tracked diff empty. |
| P14-021-P14-024 | PASS | Hostile-input integration matrix and prompt-injection/cache regressions pass. |
| P14-025 | PASS | 20-row manual audit covers all six analytical areas; 19 pass and one explicitly partial. |
| P14-026 | PASS | Five headline calculations independently recomputed. |
| P14-027 | PASS | Three contract families and three tax reconciliations checked with limitations. |
| P14-028 | PASS | Both saved-answer rounds audited; the IC brief contains the same 11 critical issues as the full report. |
| P14-029 | PASS | All four required Markdown reports exist. |
| P14-030 | PASS | Every AC below has PASS, FAIL or BLOCKED status and evidence; defects are retained. |
| P14-031 | PASS | This report and final handover cover the requested items; no commit or push was performed. |

P14-002 is deliberately not rewritten as a pass. P14-010 passes because the
qualifying post-fix run was performed in a different, strictly sealed context;
the contaminated attempts are excluded from its evidence.

## Complete acceptance-criterion matrix

| Criterion | Status | Evidence / disposition |
|---|---|---|
| AC-001 | PASS | Historical planning documents exist and remain authoritative. |
| AC-002 | PASS | README/runtime guide declare Codex primary. |
| AC-003 | PASS | Doctor passed Python 3.12.10 against the >=3.11 gate. |
| AC-004 | PASS | Native install/run used no Docker. |
| AC-005 | PASS | Doctor confirms no provider API key is read or required. |
| AC-006 | PASS | Clean setup completed in 206.388s, below 20 minutes. |
| AC-007 | PASS | README documents one doctor-through-delivery CLI path. |
| AC-008 | PASS | Public synthetic validator confirms fictional provenance. |
| AC-009 | PASS | Primary public validator: 90 physical, 100 logical, required mix. |
| AC-010 | PASS | Public manifest/validator confirms financial fixture coverage. |
| AC-011 | PASS | Public manifest/validator confirms legal fixture coverage. |
| AC-012 | PASS | Public manifest/validator confirms Tax fixture coverage. |
| AC-013 | PASS | Public validator passes duplicate/version/folder/name/hidden/corrupt/image quirks. |
| AC-014 | BLOCKED | Sealed found/missed/false-positive scoring was not run; final independent red team is incomplete and truth remained out of the qualifying context. |
| AC-015 | PASS | Run manifests/checkpoints record all stage states and fingerprints. |
| AC-016 | PASS | Primary and shadow registers are complete with terminal rows and hashes. |
| AC-017 | PASS | Native PDF/DOCX/XLSX/CSV/image/ZIP extraction and vision routing pass. |
| AC-018 | PASS | Unsupported/unreadable inputs remain explicit and isolated. |
| AC-019 | PASS | Both intake rounds generated separate packets and required explicit ingestion. |
| AC-020 | PASS | Five workstream artifacts are nonempty in the qualifying shadow run. |
| AC-021 | PASS | Standalone Tax JSON/Markdown is nonempty and cross-linked. |
| AC-022 | BLOCKED | No verified brand-new-context independent red-team isolation manifest exists for the final candidate. |
| AC-023 | BLOCKED | Prior challenge coverage cannot qualify until AC-022 independence and final reconciliation are proved. |
| AC-024 | PASS | Candidate report, outstanding-information output and two-page IC brief validate. |
| AC-025 | PASS | Intake derives observed questions plus explicit transaction-context topics. |
| AC-026 | PASS | Unanswered/vague replies stay open or narrowed; canonical run pauses. |
| AC-027 | PASS | Stable topic keys carry perimeter, price, thesis and materiality answers. |
| AC-028 | PASS | Run/report limitations expose priorities, deferrals and open evidence. |
| AC-029 | PASS | Findings separate fact, analysis, uncertainty, implication and next action. |
| AC-030 | PASS | EBITDA bridge is cited and independently recomputed. |
| AC-031 | PASS | Identity-key evidence supports customer grouping and concentration. |
| AC-032 | PASS | Base/amendment change-of-control decision is cited. |
| AC-033 | PASS | Headline calculations retain inputs, formula version and results. |
| AC-034 | PASS | Primary final run: 176 structured citations, zero failures, 100% material coverage. |
| AC-035 | PASS | 20-row manual audit resolved native locators and current hashes. |
| AC-036 | PASS | Confidence and high-materiality gaps remain explicit. |
| AC-037 | PASS | Irish commercial-diligence scope and non-opinion language retained. |
| AC-038 | PASS | Routing policy contains exactly the three required classes. |
| AC-039 | PASS | Shadow log audit passed with route/purpose/timing/output fields. |
| AC-040 | PASS | Hidden model/tokens/costs remain null with reasons; billing basis separate. |
| AC-041 | PASS | `notes.md` states larger-budget routing, telemetry and review changes. |
| AC-042 | PASS | Python path is local-only; telemetry/external logging disabled. |
| AC-043 | PASS | Shadow agent rehashed all 48 physical inputs with zero changes; outputs stayed under its run. |
| AC-044 | PASS | Public research default is disabled and allowlisted if enabled. |
| AC-045 | PASS | Run research ledger records `not_performed`; audit passes. |
| AC-046 | PASS | Public validator confirms synthetic PII-like fixture provenance. |
| AC-047 | PASS | Interrupted extraction resumes; unchanged stages reuse; answer/cache invalidation tests pass. |
| AC-048 | PASS | Fail-closed state/validation tests pass; release readiness stays false when final gates are absent. |
| AC-049 | PASS | README covers install, runtime, structure, privacy and troubleshooting/fallbacks. |
| AC-050 | PASS | Exactly 100-logical primary synthetic room plus separately sealed truth exists. |
| AC-051 | PASS | Primary run contains report Markdown, brief Markdown and exactly two-page A4 PDF. |
| AC-052 | PASS | Primary run contains matching source register, red-team challenge log and run log; independence is separately blocked at AC-022. |
| AC-053 | PASS | `notes.md` covers next build, surprises, least confidence and bigger-budget changes. |
| AC-054 | FAIL | `outputs/delivery_manifest.json` is absent; packaging cannot honestly pass before final independent reconciliation. |
| AC-055 | PASS | Qualifying unseen shadow flow completes without primary names/paths/values. |
| AC-056 | PASS | Six typed JSONL stores and validation tests pass. |
| AC-057 | PASS | Canonical Phase 14 check remains `awaiting_input`; evidence has 19 gaps and no claims/workstreams. |
| AC-058 | PASS | Native locator/version citation validation passes. |
| AC-059 | PASS | Material support and duplicate independence validation pass. |
| AC-060 | PASS | Calculation provenance/missing-input validation tests pass. |
| AC-061 | PASS | Evidence foundation and coverage ledger generated/validated. |
| AC-062 | PASS | PDF/XLSX/DOCX/CSV/image citation fixture matrix passes. |
| AC-063 | PASS | Public-only evidence-foundation integration passes without truth access. |
| AC-064 | PASS | Phase 8 refuses incomplete intake and enforces sequential answer gate. |
| AC-065 | PASS | Phase 8 financial/commercial JSON and Markdown contracts pass. |
| AC-066 | PASS | Finding-schema validation passes for all material shadow findings. |
| AC-067 | PASS | Financial/commercial recalculations pass, including shadow directionality. |
| AC-068 | PASS | Customer aliases require explicit identity evidence; grouping test passes. |
| AC-069 | PASS | Phase 9 writes Legal, Operational, IT and standalone Tax outputs. |
| AC-070 | PASS | Three manual base/amendment decisions agree with source precedence. |
| AC-071 | PASS | VAT, corporation-tax and PAYE arithmetic independently checks. |
| AC-072 | PASS | Irish scope retained; public research disabled and logged. |
| AC-073 | PASS | Phase 8/9 validation bundles pass with warnings kept explicit. |
| AC-074 | PASS | Analysis stages do not draft the final report or valuation. |
| AC-075 | PASS | Disposable saved-answer public synthetic analytical integration passes. |
| AC-076 | PASS | Report requires current Phase 8/9 outputs and emits all candidate artifacts. |
| AC-077 | PASS | Full report includes required workstream, transaction and limitation sections. |
| AC-078 | PASS | Material findings include evidence, confidence, implications and actions. |
| AC-079 | PASS | Material citation/source gate passes with zero failed citations. |
| AC-080 | PASS | Headline calculation trace gate passes with zero failed calculations. |
| AC-081 | PASS | Both primary and qualifying shadow IC PDFs are exactly two A4 pages. |
| AC-082 | PASS | Required headings and placeholder/text-completeness tests pass. |
| AC-083 | PASS | Primary and shadow bundle validation plus manual render inspection pass. |
| AC-084 | PASS | Phase 10 handover metrics are recorded; no commit/push occurred. |
| AC-085 | PASS | Exactly three routing classes are schema-validated. |
| AC-086 | PASS | Zero-model local tasks valid; unavailable model identity is not invented. |
| AC-087 | PASS | Qualifying shadow audit reconciles every completed stage to successful logs. |
| AC-088 | PASS | Usage/cost/privacy validation passes with explicit null reasons. |
| AC-089 | PASS | Default-disabled research action is recorded as `not_performed`. |
| AC-090 | PASS | Two prompts, runtime guide and routing YAML exist at required paths. |
| AC-091 | PASS | Both `awaiting_input` states require explicit answer files. |
| AC-092 | PASS | Codex-first, provider-SDK-free, Claude-compatible file contract documented. |
| AC-093 | PASS | Logged public synthetic integration passes without truth/red-team/commit. |
| AC-094 | PASS | Public shadow manifest/test proves all required identity/layout/file variations. |
| AC-095 | PASS | Only sealed post-fix run `20260901T081036940718Z-ea9100a654cb` qualifies; contaminated attempts are recorded as failures. |
| AC-096 | PASS | Scale register contains exactly 150 logical sources and valid SHA-256 values. |
| AC-097 | PASS | 150 terminal states; unchanged stage reused; one change yielded 147 hits/1 miss. |
| AC-098 | PASS | One failure isolated; peak traced Python allocation 3.273 MiB <512 MiB. |
| AC-099 | PASS | Clean-clone setup 206.388s; exact README-form rehearsal and audit pass. |
| AC-100 | PASS | Unsupported, corrupt, encrypted and empty classifications verified. |
| AC-101 | PASS | 40,000-cell sheet, traversal block, duplicate and basename conflict verified. |
| AC-102 | PASS | OCR-disabled image remains vision work; permission failure is explicit. |
| AC-103 | PASS | Interrupt/resume, changed cache and untrusted prompt warning verified. |
| AC-104 | PASS | 20 citations across Financial, Commercial, Legal, Operations, IT and Tax audited. |
| AC-105 | PASS | Five calculations, three version decisions and three tax checks audited. |
| AC-106 | PASS | Two intake rounds and exact 11-critical-issue IC/report correspondence audited. |
| AC-107 | PASS | Four requested reports exist, failures are explicit and no commit/push was made. |

## Verification evidence

| Check | Result |
|---|---|
| Full test suite | 111 passed in 55.56s |
| Phase 14 focused suite | 5 passed in 17.64s |
| Analysis/source-path focused suite | 20 passed in 31.12s |
| Ruff | all checks passed |
| mypy | no issues in 56 source files |
| Doctor | 7 pass, 2 optional warnings, 0 fail |
| Public-only primary validator | 32/32 pass; sealed metadata not accessed |
| Canonical current-checkout pause run | register/extract completed; round 1 awaiting input; 19 evidence gaps; analysis not started |
| Qualifying shadow run | all six stages completed; 140 citations; 15 calculations; 100% material coverage; two A4 pages |
| Scale run | 150 terminal; 3.273 MiB traced peak; isolated failure; changed cache 147/1 |

## Failures, fixes and blockers

The contaminated first shadow attempt, the later implementation-context shadow
truth read, report answer shift, signed-variance wording, duplicate word and stale
vision limitation are all recorded in `docs/generalisation-report.md`. Each code
defect has a focused regression and passes in the qualifying sealed run. The
clean-clone bare-ID/alias mistake and its qualifying exact rerun are recorded in
`docs/clean-clone-report.md`. The one partial citation remains explicit in
`docs/manual-citation-audit.md`.

The unresolved release sequence is:

1. prepare a hash-allowlisted final candidate packet;
2. run red team in a verified brand-new context with a recorded isolation
   manifest;
3. reconcile and revalidate all accepted challenges;
4. perform authorized sealed scoring; and
5. create the final hash-complete delivery manifest.

Until those steps are complete, `release_ready` must remain false.

## Handover and Git safety

The four required reports are:

- `docs/acceptance-report.md`
- `docs/clean-clone-report.md`
- `docs/generalisation-report.md`
- `docs/manual-citation-audit.md`

No commit or push was performed. The changes are suitable for review and a later
commit because generated run directories remain ignored and no real room data,
secret, credential or telemetry artifact was intentionally added. Commit safety
still requires a final diff/status inspection after all verification completes.
