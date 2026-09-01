# Acceptance criteria

## Use of this document

These criteria define observable acceptance tests for the planned implementation. “Run” means one immutable run ID and its local artifact directory. “Material claim” means a claim marked material by a workstream or promoted into the executive report/IC brief. Requirement IDs refer to [requirements-traceability.md](requirements-traceability.md).

The engine is not accepted merely because it produces prose. It must pass the deterministic checks, preserve evidence and failure state, and survive a timed cold run on an unseen room.

## A. Scope, bootstrap and runtime

### AC-001 - Documentation-only planning change

Given the present planning task, when its Git diff is inspected, then only the four requested Markdown planning files are newly created; no engine, fixture, dependency or runtime file has been implemented. (USR-002-USR-006)

### AC-002 - Codex is the declared harness

Given a clean clone, when the README and runtime contract are inspected, then Codex is the primary supported harness and the operator can start the workflow from within Codex. Claude Code and Cursor are not required. (TB-048-TB-051, USR-008)

### AC-003 - Native Python version gate

Given Python 3.10, bootstrap exits before processing with a clear `Python 3.11+ required` diagnostic. Given Python 3.11 or later, the version gate passes. (TB-069, USR-009)

### AC-004 - Docker independence

Given a clean machine on which Docker is absent, when the documented primary setup path is followed, then setup and the smoke run succeed. Any future container path is labeled optional. (USR-010)

### AC-005 - No provider API key

Given no provider API-key environment variables and an already authenticated Codex subscription, when the engine runs, then Python makes no direct model API call and all reasoning occurs through Codex. Setup never asks for an API key. (TB-052)

### AC-006 - Clean clone and 20-minute gate

Given a fresh clone with no repo-local caches or pre-created virtual environment, when a first-time operator follows only README, then the engine reaches its first runnable/smoke-test state in under 20:00 wall-clock minutes without undocumented steps. (TB-059-TB-061, TB-071, TB-085)

### AC-007 - One-path operator journey

Given a local room path and separate output path, when the operator follows README in Codex, then configuration validates, processing starts, both intake pauses are explained, and final artifacts are discoverable without knowing repository internals. (TB-049, TB-060)

## B. Synthetic room

### AC-008 - Fictional provenance

Given the generated synthetic room, when its manifest and content are scanned and human-reviewed, then company names, people and figures are declared synthetic and no real entity/person/value has been copied. (TB-008, TB-100)

### AC-009 - Size, top-level structure and mix

Given the generated room, then it contains exactly 100 logical artifacts: exactly 90 visible files under legal, financial and tax top-level folders, with one of those files being a ZIP containing exactly 10 registered members. It covers every document-family row RS-002 through RS-020 and every required quirk. (RS-001)

### AC-010 - Financial fixture coverage

The room contains six annual abridged statutory-account PDFs, one YTD management-accounts PDF and no monthly packs, all listed financial spreadsheets, the sparse information-request XLSX, two loan-letter JPGs, an image-only loan/HP PDF and a related-party DOCX. (RS-002-RS-007)

### AC-011 - Legal fixture coverage

The room contains the legal questionnaire, corporate records, employment/contractor set, customer agreement/amendment families and correspondence, scanned property contracts, lease, insurance/licensing/provider agreements, board/CRO/work-permit/registration materials and one updated-responses ZIP with exactly 10 members. (RS-008-RS-015)

### AC-012 - Tax fixture coverage

The room contains the VAT series with an amended item, ROS-style VAT/PAYE/CT screens, three annual tax computations, registration and clearance evidence, trial-balance and invoice subfolders, and two tax-response summaries with changed Rev2 answers. (RS-016-RS-020)

### AC-013 - Required messiness

The room contains and the ground-truth manifest identifies at least one duplicate, superseded/versioned item, wrong-folder item, same-name/different-path pair, empty folder, renamed CSV, hidden sheet, photographed letter, image-only scan, non-tying spreadsheet, contradiction, `N/A`/`None` answer and broken folder reference. (TB-010, TB-046, RS-021)

### AC-014 - Planted-issue scoring

Given a sealed ground-truth manifest unavailable to drafting/red-team contexts, when the synthetic run finishes, then a scoring tool reports each planted issue as found, missed or false positive and does not silently change ground truth. (TB-047, TB-072, TB-091)

## C. Six required stages

### AC-015 - Stage manifests

For each of the six required stages, a manifest records input/output hashes, configuration, start/end time, status and validation results. Final success is impossible if any manifest is absent or non-successful. (TB-003, TB-086)

### AC-016 - Complete source register

Given the synthetic room, then the complete source register has exactly 100 logical-artifact rows: 90 visible files, including the ZIP container, plus 10 ZIP-member rows. Every row has a stable ID, path, hash, type, classification and extraction status; duplicates, supersession candidates and unreadable items have explicit flags. (TB-016-TB-017, RS-001)

### AC-017 - Tiered extraction

Given native-text PDF/DOCX/XLSX/true-CSV/image fixtures, then deterministic content and metadata are extracted locally without a model event. Low-text and image-only PDF pages are selectively rendered, optional local OCR is recorded only when detected and used, and unresolved visual material receives a structured pending Codex/Claude vision task with a null result. Every extracted unit carries source ID/hash/path, a format-native locator, extraction method, confidence, warnings/limitations and extracted-content checksum. `extraction_manifest.json`, `extracted_units.jsonl`, `extraction_failures.json`, `needs_vision.json`, `rendered_pages/` and `cache/` are run-local. (TB-018-TB-019)

For XLSX, visible/hidden sheets, hidden rows/columns, formulas, source-cached values, merged cells, named ranges, date/currency formats, formula errors, totals and subtotals are inspected. No workbook is silently recalculated. Cache reuse requires an exact source checksum, extractor version and extraction configuration/capability fingerprint; a mismatch is a miss. Every register row has one terminal extraction status. (TB-018-TB-019, TB-043, TB-082)

### AC-018 - Unsupported and unreadable inputs

Given corrupt, encrypted, unsupported and unsafe archive fixtures, then the engine registers/quarantines them with reason codes, continues processing unaffected files, and propagates a limitation to impacted claims. (TB-017, TB-087)

### AC-019 - Stage 3 occurs twice

Given a normal run, intake round one selects no more than 12 questions from quick material register/extraction signals and pauses in `awaiting_input` without an answer artifact. Round two selects no more than 15 questions only after the complete source register, full extraction and explicit round-one answer ingestion, then pauses again. Each round has distinct question, answer and resume records. (TB-020-TB-022)

### AC-020 - Five workstreams

Given a completed analysis stage, then exactly five formal workstream outputs exist: financial, commercial, legal/contractual, operational/management and IT. Each passes the same analytical rubric. (TB-023-TB-024, TB-034-TB-035, TB-083)

### AC-021 - Mandatory standalone Tax module

Given tax-folder evidence, then a mandatory Tax module writes `tax/tax-findings.json`, `tax/tax-analysis.md` and a standalone Tax section in `report.md`. Each relevant tax finding cross-links into Financial, Legal/contractual, Operational/management and IT. Tax is neither a sixth formal workstream nor owned by Financial; missing structured output, report section or required cross-link fails validation. (RS-016-RS-020)

### AC-022 - Independent red team

Given a completed candidate report, then red team runs in a brand-new Codex task/chat with a new ID and receives only paths/hashes named in `red-team/packet-allowlist.json` and the sealed manifest. No inherited messages, drafting conversation, scratch notes, rejected drafts, private reasoning or planted ground truth are present. An ordinary subagent fails independence unless verifiable non-inheritance is recorded in the isolation manifest. (TB-025)

### AC-023 - Red-team challenge coverage

For every material issue, the red-team log records `upheld`, `modified`, `rejected` or `insufficient evidence`; headline numbers have independent recalculation references; newly identified gaps are logged; and appendix IDs exactly reconcile to the standalone challenge log. (TB-026-TB-029, TB-084)

### AC-024 - Final output stage

Given all prior gates pass, then stage 6 packages the full Markdown report with standalone Tax section, structured Tax outputs, A4 two-page IC brief, source register, red-team log, run log, research log and validation report under one run ID. (TB-030-TB-033)

## D. Human/deal-lead behavior

### AC-025 - Evidence-driven questions

Every intake question includes its ID/round, priority, exact wording, why it matters, supporting source IDs or an essential transaction-context gap, decision potentially affected, expected answer type, blocking status and evidence-change invalidation scope. Duplicate candidates and questions already answered are suppressed; every excluded candidate records a reason. A regression test proves the questions change when observed evidence changes. (TB-020, TB-090)

### AC-026 - Honest unanswered state

At a pause, the engine does not infer an answer from silence and creates no answer artifact. Explicit ingestion stores the verbatim answer, conservative normalised interpretation, provenance, ambiguity, open/narrowed/closed status and affected claims/gaps/stages. `N/A`, `None`, cross-references, partial and vague replies are evidence but do not automatically close a question. (TB-021-TB-022, TB-041-TB-042)

### AC-027 - Deal assumptions

The run captures the committee's price/structure assumptions without producing an independent valuation, and findings explain implications against those assumptions. (TB-011-TB-014)

### AC-028 - Priorities are disclosed

The run plan and notes identify what was prioritized, deferred and why, and the final report exposes material scope limitations. (TB-092-TB-094)

## E. Analysis, calculations and citations

### AC-029 - Analyst rather than clerk

Each material workstream finding states conclusion, evidence, contradiction/uncertainty, decision implication and recommended follow-up. A section containing only source summaries fails the workstream rubric. (TB-015, TB-034-TB-045)

### AC-030 - Financial reconciliation exemplar

Given the planted management/statutory EBITDA discrepancy, then the engine computes a cited bridge, identifies the supportable figure or explains why it cannot, and states price/structure impact. (TB-037)

### AC-031 - Customer concentration exemplar

Given planted customer aliases belonging to one group, then the engine links the aliases, recomputes concentration from cited rows/cells and explains the risk. (TB-038)

### AC-032 - Change-of-control exemplar

Given a planted agreement/amendment with a transaction-triggered change-of-control term, then the legal workstream identifies the operative text, amendment/version, transaction effect and renegotiation leverage with citations. (TB-039)

### AC-033 - Reproducible headline arithmetic

For every headline number, a deterministic calculation record identifies input source cells, formula/version, output and hash. Red team can recompute it without workstream scratch reasoning. (TB-027, TB-040)

### AC-034 - Citation completeness

Every material claim in the report and IC brief has at least one structured entry in `citations/index.jsonl` with the locked locator for its format: PDF uses source ID/hash and page; spreadsheet uses source ID/hash, sheet and cell/range; DOCX uses source ID/hash and paragraph or table/row locator, plus rendered page only when deterministically available; image uses source ID/hash, image/page and region coordinates. (TB-043, TB-082)

### AC-035 - Citation accuracy spot-check

A deterministic resolver opens each locked locator type, and a random human spot-check across PDF, spreadsheet, DOCX and image claims finds no mismatched source hash or locator. Any dangling, malformed or hash-mismatched citation is fatal. (TB-043, TB-082)

### AC-036 - Confidence calibration

High-confidence conclusions cannot rely solely on unreadable, contradicted or low-confidence extraction. Unresolved high-materiality gaps appear in the report; generic hedging does not replace a conclusion. (TB-041, TB-044-TB-045, TB-081)

### AC-037 - Irish legal scope

The legal/contractual output declares Irish jurisdiction, distinguishes sourced contract interpretation from legal advice, and cites controlling agreement/amendment text. (TB-024)

## F. Routing, token usage and cost

### AC-038 - Checked-in route policy

The repository contains a schema-valid route policy mapping deterministic, economy-mechanical, frontier-judgment and frontier-red-team profiles to concrete supported Codex model IDs or explicit availability resolution. (TB-053-TB-056)

### AC-039 - Route use is sensible and visible

Every model reasoning unit has one run-log event containing route profile, resolved model, purpose, input/output hashes, timing, result and escalation reason. Mechanical tasks do not use frontier routes without a documented exception. (TB-019, TB-054-TB-057, TB-088)

### AC-040 - Usage and cost honesty

Every model event has token-usage fields and one cost basis: exact provider-reported, estimate from a dated rate card, subscription-included, or unavailable with reason. Missing, silently zeroed or fabricated values fail validation. (TB-033, TB-088)

### AC-041 - Bigger-budget note

The final notes state which route/model/telemetry decisions would change with a larger budget and why. (TB-058, TB-075)

## G. Privacy and public research

### AC-042 - Local-only processing boundary

With public research disabled, observed network activity is limited to Codex/model-provider traffic initiated by the harness. Python sends no room or derived data to any remote endpoint, and no telemetry or third-party logging dependency is active. (TB-062-TB-065)

### AC-043 - Source room immutability

Before and after a run, the source-room tree hashes match. Derived files reside only under the separate output directory. (TB-062, architecture invariant)

### AC-044 - Public research allowlist

Public research is optional and disabled by default. Given the default configuration, no request occurs and the ledger says `not_performed`. If explicitly enabled, each query contains only the confirmed public target name and market and no room text, PII or confidential figure; every attempted, rejected and completed action is logged locally. (TB-066-TB-067)

### AC-045 - Public research ledger

Every attempted research action records query, purpose, timestamp and disposition; every completed action also records URL, retrieved-page hash, public fact used and downstream claim IDs. Public claims in the report resolve to that ledger. (TB-067)

### AC-046 - Synthetic unredacted-list fixture remains fictional

The nested ZIP's “unredacted” employee list contains synthetic PII-like values only, is flagged as sensitive, and never causes real personal data to be embedded in tests or committed. (RS-015, TB-100)

## H. Failure, resumption and final deliverables

### AC-047 - Idempotent resume

Given an interruption at either intake pause or a recoverable extraction failure, when the run resumes with unchanged input/config/answer hashes, then previously valid stages are reused and outputs are not duplicated. A changed deal-lead answer invalidates only its declared affected intake/downstream stages and preserves unrelated completed upstream stages. (TB-002, TB-087)

### AC-048 - Fatal status is honest

Given a privacy breach, corrupt run state, non-new or inherited red-team context, packet allowlist violation, unresolved material citation, missing Tax output/cross-link, invalid A4/page-count check or missing required output, then terminal status is `FAILED`, no success marker is written, and diagnostics name the repair action. (TB-087)

### AC-049 - Deliverable 1

The Git repository contains a README with setup, runtime, structure, privacy and troubleshooting instructions that pass the clean-clone test. (TB-071)

### AC-050 - Deliverable 2

The release contains the exactly 100-logical-artifact fictional synthetic room - 90 visible files including one ZIP plus its 10 members - and planted-issues note with sealed ground truth inaccessible to reasoning runs. (TB-072, RS-001)

### AC-051 - Deliverable 3

The release contains `report.md`, `ic-brief.md` and an ISO A4 `ic-brief.pdf` generated in-process through pure-Python rendering. A Python PDF parser proves exactly two pages and valid A4 media boxes; Office, LibreOffice, Docker and browser rendering are absent from the path. All outputs are tied to the recorded synthetic run ID and evidence index. (TB-073)

### AC-052 - Deliverable 4

The release contains source register, standalone red-team log and run log from the same synthetic run; their run IDs and hashes reconcile. (TB-074)

### AC-053 - Deliverable 5

The release contains a concise notes file with sections for next build, surprises, least-confidence areas and bigger-budget changes. (TB-058, TB-075)

### AC-054 - Complete handover

A delivery manifest enumerates all five deliverables, hashes every artifact and records the handover timestamp. Missing or cross-run artifacts fail packaging. (TB-070-TB-075)

### AC-055 - Unseen-room evaluation readiness

The engine completes the same acceptance flow on an unseen mixed-input fixture with no filenames, paths, company values or planted-issue knowledge hard-coded from the synthetic room. (TB-076-TB-089)

## I. Phase 7 evidence and calculation foundation

### AC-056 - Six typed record contracts

The run-local evidence directory contains schema-valid claims, evidence,
calculations, contradictions, gaps and issues JSONL stores with all Phase 7 fields,
stable IDs and the run ID in every record. Empty analytical stores remain explicit
rather than containing placeholder claims. (P7-005-P7-010)

### AC-057 - Pre-analysis boundary and intake gaps

Given completed extraction and intake in `awaiting_input`, the `evidence` command
may complete its own validation artifacts but leaves intake paused and `analyse`
not started. Every available answer retains verbatim/provenance fields; unanswered,
vague and narrowed matters remain open/narrowed gaps. No workstream prose or report
is created. (P7-002, P7-004, P7-024)

### AC-058 - Native citation resolution and version safety

Each evidence and calculation-input citation resolves its source ID and checksum
against both register and extraction. PDF page, XLSX sheet/cell/range, DOCX
paragraph/table, CSV row/column and intrinsic image-region locators are validated.
A potentially superseded source fails unless explicitly acknowledged; acknowledgement
remains a warning visible in the result. (TB-043, TB-082, P7-011-P7-015)

### AC-059 - Material support and duplicate independence

An active high/critical claim with no valid supporting citation fails. Multiple
citations from the same exact-duplicate group/checksum count as one independent
source and appear in the duplicate-exclusion ledger. (TB-040, TB-045, TB-081,
P7-014, P7-016)

### AC-060 - Calculation provenance and missing inputs

Every calculation has source inputs/locators, explicit period/currency/sign/unit
normalization, a versioned formula, separate reported/recomputed results, rounding,
method and independent recomputation status. Deterministic formulas use only the
safe arithmetic expression subset. A missing input stays null, is named with a
reason and blocks recomputation rather than becoming zero. (TB-027, AC-033,
P7-007, P7-015, P7-017-P7-020)

### AC-061 - Phase 7 output and coverage ledger

The command creates `claims.jsonl`, `evidence.jsonl`, `calculations.jsonl`,
`contradictions.jsonl`, `gaps.jsonl`, `issues.jsonl`,
`citation_validation.json` and `evidence_coverage.md`. The validation artifact
reports failed citations, material-claim coverage, structural/reference failures
and duplicate exclusions; zero material claims reports coverage as not applicable,
not a fabricated 100%. (P7-021)

### AC-062 - Citation fixture matrix

Automated tests include valid and invalid PDF, XLSX and DOCX locators; valid CSV
and image locators; exact-duplicate corroboration; superseded-version citation;
valid/invalid calculation citations; and missing-input behavior. (P7-022)

### AC-063 - Synthetic evidence-foundation run

The public-only synthetic validator and canonical register/extract/evidence commands
complete without reading the sealed issue key. The resulting foundation records
all unanswered round-one matters and pending extraction/vision limitations as gaps,
while intake stays `awaiting_input` and analysis/reporting remain unstarted.
(P7-003, P7-023-P7-024)

## J. Phase 8 and Phase 9 analysis

### AC-064 - Sequential answer gate

Phase 8 refuses to run until both intake rounds have explicit answer artifacts and
the intake stage is completed. Phase 9 refuses to run until current Phase 8
validation passes. A refusal creates no workstream success artifact. (P8-001,
P9-001)

### AC-065 - Phase 8 output contract

Phase 8 creates the Financial and Commercial JSON/Markdown pairs,
`financial_calculations.md` and `customer_grouping.md`; every artifact contains the
run ID and Phase 8 leaves analysis running rather than falsely complete. (P8-002,
P8-014)

### AC-066 - Adviser-quality finding schema

Every material Phase 8/9 finding separates source fact from inference and includes
a conclusion, valid evidence, contradiction or explicit limitation, recomputation
where relevant, materiality, confidence, transaction implication and exact next
action. Document-summary-only findings fail. (P8-003-P8-004, P9-003)

### AC-067 - Financial and commercial recomputation exemplars

The canonical public synthetic fixture recomputes the unsupported EBITDA
adjustment, working-capital formula, 90+ debtors, debt/debt-like position, pipeline
total, group concentration and client-linked headcount from native source
locators. Reported values remain separate. (P8-005-P8-009)

### AC-068 - Evidence-backed customer grouping

Customer similarity alone never confirms a group. A confirmed group identifies
the contract, address, VAT, answer or equivalent evidence used; other suggested
groups remain candidates. Exact duplicates do not add corroboration. (P8-010)

### AC-069 - Phase 9 output contract

Phase 9 creates Legal/contractual, Operational/management and IT JSON/Markdown
pairs plus `tax/tax-findings.json` and `tax/tax-analysis.md`, then completes the
analysis stage only after all required validations pass. (P9-002, P9-004-P9-007,
P9-014)

### AC-070 - Effective-version decisions

Legal amendments, revised questionnaire responses and updated ZIP documents are
resolved through registered version evidence. A potentially superseded clause is
not presented as current without acknowledgement. (P9-008)

### AC-071 - Tax reconciliation checks

VAT original/amended returns and summaries, payments/charges/refunds, PAYE,
corporation tax, trial balance, computation and response versions receive explicit
tie-outs or limitations. Headline tax calculations independently recompute. (P9-009)

### AC-072 - Irish scope and public-research boundary

Legal and tax findings state that they are commercial diligence, not formal Irish
legal or tax opinions. Public research is supplemental, contains no confidential
document text, and is logged with query, timestamp, purpose, URL and conclusion;
`not_performed` is logged when disabled. (P9-010-P9-011)

### AC-073 - Analysis validation bundle

Analysis validation checks citations, amendment/version choices, questionnaire
references, tax recomputation, PII handling, missing evidence, unsupported legal
conclusions and required finding fields. A failed check fails analysis. (P8-011,
P9-012-P9-013)

### AC-074 - No report or valuation

Phases 8 and 9 create no `report.md`, IC brief, independent valuation or
placeholder report success artifact. `report` and final `validate` continue to
report `stage not implemented`. (P8-012-P8-013, P9-015)

### AC-075 - Public synthetic analytical integration

A disposable public synthetic run with explicit test-only answers executes Phase
8 and then Phase 9, validates all material citations and headline calculations,
and never opens `synthetic/planted_issues/`. The canonical operator run remains
paused without fabricated answers. (P8-015, P9-016)

## Release gate

Implementation is eligible for trial handover only when AC-002 through AC-075 pass, every locked architecture decision in [decisions.md](decisions.md) is implemented, remaining open risks have recorded dispositions, and the final Git status contains no confidential room data, generated run data or credentials. AC-001 applies only to the original planning task.
