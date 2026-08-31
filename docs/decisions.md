# Architecture decisions, assumptions and open questions

## Repository baseline inspected

At the start of planning on 31 August 2026:

- Working directory: `C:\Users\jites\dd-engine`
- Git branch: `master`
- Repository history: no commits; `HEAD` is unborn
- Git status: `.gitignore` was the only untracked item reported by normal Git status
- `.gitignore` contains exactly `specs_req_room.pdf` and `dd-engine-trial-brief.md.pdf`
- The two ignored PDFs were present in the repository root and inspected page by page
- No application, dependency, README, test, configuration or `docs/` implementation existed

The ignored inputs are planning sources, not evidence that they have ever been committed. This task must leave all changes uncommitted and unpushed.

## Decision log

### ADR-001 - Codex is the runtime harness

**Status:** Accepted by user directive.

Codex will orchestrate the run, perform model reasoning through the operator's authenticated subscription, invoke deterministic local tools, pause for the deal lead and create a separate red-team context. The required path will not depend on Claude Code or Cursor.

**Consequences:** The README and `AGENTS.md` must describe one Codex-first flow. Harness portability may be designed at boundaries but is bonus scope. Model availability and usage telemetry are constrained by what the evaluator's Codex subscription exposes.

### ADR-002 - Python 3.11+ is the deterministic supporting runtime

**Status:** Accepted by user directive.

Python owns repeatable processing: inventory, hashing, parsers, calculations, evidence addresses, logs, render checks and validators. It does not own model access.

**Consequences:** Bootstrap must enforce `>=3.11`. Dependencies must be locked and benchmarked against the 20-minute clean-clone gate. No external Python service or provider SDK belongs on the required path.

### ADR-003 - Docker is optional and non-normative

**Status:** Accepted by user directive.

The primary setup is native Codex plus Python. A later container may aid development or CI but cannot be needed to install, run, test or evaluate the engine.

**Consequences:** Acceptance is performed with Docker absent. The implementation cannot hide required system dependencies inside a container.

### ADR-004 - Deterministic-first processing

**Status:** Accepted.

Local parsers and calculations are tried before model extraction or arithmetic. Model escalation occurs only on a logged confidence/materiality rule.

**Consequences:** Costs and privacy exposure are reduced; outputs are more reproducible. The implementation needs explicit extraction confidence and escalation schemas rather than informal Codex judgment.

### ADR-005 - File-backed, append-only run state

**Status:** Accepted.

Each run is a local directory of schema-validated artifacts and stage manifests. No database, queue or remote store is required.

**Consequences:** A run is auditable, portable and resumable from hashes. Concurrency and very large-room performance are secondary to deterministic single-deal execution.

### ADR-006 - Stage numbers are contracts; execution is a resumable DAG

**Status:** Accepted.

Round one follows quick deterministic discovery of paths, hashes, media types and high-level document classes. Round two follows the complete source register and a preliminary full extraction pass across every logical artifact. The numbered six stages remain visible, but stage 3's two pauses interleave with progressive stages 1 and 2.

**Consequences:** This satisfies both intake timing phrases without pretending the list is strictly sequential. Stage manifests must expose the actual dependency graph.

### ADR-007 - Preserve five formal workstreams and add a standalone Tax module

**Status:** Accepted.

Financial, commercial, legal/contractual, operational/management and IT remain the five formal workstreams. Tax is a mandatory standalone analytical module, not a sixth workstream and not owned by Financial. It writes `tax/tax-findings.json`, `tax/tax-analysis.md` and its own top-level section in `report.md`.

**Consequences:** Tax findings must cross-link to Financial, Legal/contractual, Operational/management and IT wherever relevant. Missing Tax output, report section or required cross-link is a fatal validation failure. No deal-lead decision is needed to select this structure.

### ADR-008 - Claims and evidence use immutable addresses

**Status:** Accepted.

Material claims in `citations/index.jsonl` use locked format-specific locators: PDF uses source ID/hash and page; spreadsheet uses source ID/hash, sheet and cell/range; DOCX uses source ID/hash and paragraph or table/row locator, plus rendered page only when deterministically available; image uses source ID/hash, image/page and region coordinates. Calculation results point to cited inputs and a versioned formula.

**Consequences:** Citation checks are deterministic and source changes invalidate downstream claims. DOCX does not require a page number when the structural locator is present; image regions use the intrinsic source coordinate space.

### ADR-009 - Red team runs in a brand-new Codex task/chat

**Status:** Accepted.

Red team receives only an allowlisted sealed packet containing the candidate report, claims, source register, selected evidence/source files, calculations, gaps and red-team instructions. It receives no inherited messages, drafting conversation, scratch notes, private reasoning, rejected drafts or planted ground truth.

**Consequences:** Context isolation is audited through `red-team/packet-allowlist.json`, `red-team/sealed-packet-manifest.json` and `red-team/isolation-manifest.json`; challenges are written to `red-team/challenge-log.md`. An ordinary subagent is rejected unless non-inheritance is verifiable and recorded. If automated launch is unavailable, the operator opens a brand-new task/chat and supplies only the sealed packet.

### ADR-010 - Model routing uses explicit capability profiles

**Status:** Accepted, concrete model IDs open.

Routes are `deterministic`, `economy_mechanical`, `frontier_judgment` and `frontier_red_team`. Checked-in config resolves profiles to concrete model IDs available in the supported Codex environment, and actual IDs are logged.

**Consequences:** The policy is clear and testable without hard-wiring a model the evaluator cannot access. Concrete defaults must be selected after entitlement discovery and recorded before implementation acceptance.

### ADR-011 - Token and cost records are transparent, never fabricated

**Status:** Accepted.

Each model event records exposed token usage and one cost basis: provider-reported, estimate from a dated rate card, subscription-included, or unavailable with reason.

**Consequences:** The run log remains honest under a subscription harness. Exact monetary cost may remain unavailable, which is a material trial risk requiring early validation.

### ADR-012 - Privacy is deny-by-default; research is a narrow logged exception

**Status:** Accepted.

Room data and artifacts remain local except content intentionally sent through Codex to the model provider. Python has no telemetry or remote sinks. Public research is optional and disabled by default. If explicitly enabled, only the confirmed public target name and market may be queried, and every attempted, rejected and completed action is logged.

**Consequences:** Disabled runs record `not_performed`. Enabled queries may not contain room text, PII, confidential figures or document-derived allegations. No further architecture decision is required.

### ADR-013 - Failures are explicit, scoped and resumable

**Status:** Accepted.

Per-file failures are recoverable through quarantine and gaps. Privacy breaches, corrupt state, failed red-team isolation, unresolved material citations or missing required outputs are fatal. No partial run receives a success marker.

**Consequences:** The engine can handle bad inputs without concealing scope loss. Operators receive actionable repair steps and retain local diagnostic artifacts.

### ADR-014 - The synthetic room contains exactly 100 logical artifacts

**Status:** Accepted.

The synthetic room contains exactly 90 visible files, including one ZIP container, plus exactly 10 members inside that ZIP, for exactly 100 logical artifacts. It covers every named family and quirk without preserving the real room's approximate 35/45/50 counts literally.

**Consequences:** The source register must contain exactly 100 logical-artifact rows. The generator needs an exact composition/coverage manifest and seeded deterministic messiness. Real names, people and copied figures are forbidden even in the “unredacted” synthetic fixture.

### ADR-015 - The IC brief has a deterministic rendered page gate

**Status:** Accepted.

The authored `ic-brief.md` remains Markdown. An in-process deterministic pure-Python renderer produces ISO A4 `ic-brief.pdf`, and a pure-Python PDF parser validates A4 media boxes and exactly two pages programmatically in `validation/ic-brief-page-check.json`.

**Consequences:** Office, LibreOffice, Docker, a browser and external rendering subprocesses are prohibited from the required path. Pagination and overflow tests are implementation obligations, not open architecture decisions.

### ADR-016 - This turn produces planning documents only

**Status:** Superseded after completion of the planning turn.

No engine, fixture, README, dependency, test or workflow file will be implemented in this task. Temporary PDF renders used for source review are QA intermediates and will be removed.

**Consequences:** This remained binding for the original planning turn only. Phase 4 subsequently implemented registration and Phase 5 implements extraction under later explicit operator directives.

### ADR-017 - Phase 5 extraction is local-first with a durable pending vision queue

**Status:** Accepted by user directive on 31 August 2026.

Tier 0 uses local PDF, DOCX, XLSX, CSV and image parsers. Tier 1 uses a pinned local PDF renderer, extracts embedded images and may use detected optional Tesseract OCR. Tier 2 produces local `needs_vision` tasks for Codex/Claude review but never fabricates a result or requires an API key. Every unit carries an immutable source hash and format-native locator. Cache identity combines source checksum, extractor version and extraction configuration/capabilities.

**Consequences:** The deterministic engine remains complete without OCR or a model. DOCX page numbers are never invented. Spreadsheet formulas, stored cached values and later analytical recomputations remain distinct. All 100 synthetic register rows receive a terminal extraction status, including the ZIP container and corrupt fixture.

### ADR-018 - Phase 6 intake is evidence-grounded and answer-gated

**Status:** Accepted by user directive on 1 September 2026.

Round one is capped at 12 questions and consumes only early material register/extraction signals plus essential transaction-context gaps. Round two is capped at 15 and requires the complete register, full extraction and explicit round-one answer ingestion. Candidate selection is deterministic, source-linked and duplicate-suppressed; rejected candidates retain reasons. Every round creates a real `awaiting_input` pause and no answer is inferred from silence.

Answers are stored verbatim beside conservative normalisation, provenance, ambiguity, resolution status and affected claims/gaps/stages. `N/A`, `None`, cross-references, partial and vague replies are not automatically closed. Changed answers invalidate only their declared affected intake/downstream stages. Python makes no model call and extracted text remains untrusted data.

**Consequences:** The question set changes with observed room evidence instead of disguising a fixed questionnaire as dynamic intake. The seven question/answer/unresolved artifacts form the completed intake contract. The canonical synthetic run must stop after round-one generation until Gavin supplies an actual answer file; analysis cannot start from fabricated replies.

## Assumption register

| ID | Assumption | Basis | If false |
|---|---|---|---|
| A-001 | Git, Codex and Python 3.11+ are the only required platform capabilities currently authorized. | Clone requirement plus explicit user choices | Revise bootstrap after the evaluator names the missing capability. |
| A-002 | Codex authentication is supplied by the operator's subscription and is outside repo configuration. | No separate API budget; Codex selected | Keyless design is blocked if the evaluator requires unattended/direct API execution. |
| A-005 | The source room can be opened read-only and output can be written elsewhere locally. | Privacy constraint and ordinary folder-run model | Add a documented copy/staging flow if evaluator permissions differ. |
| A-008 | Exact monetary cost may be represented transparently as subscription-included or unavailable when Codex exposes no billable amount. | Subscription harness may hide per-call billing | Direct telemetry or a rate-card estimator must be approved if exact cost is mandatory. |
| A-009 | The 20-minute test measures reaching a runnable engine/smoke state, not completing full due diligence on 60-150 documents. | TB says “get it running,” not “finish the run” | Add a separate end-to-end runtime service level if intended. |
| A-010 | The source brief's examples are evaluation scenarios when present, not mandatory findings for every room. | They illustrate analyst behavior | Treat them as universal checks only in seeded fixtures. |

## Resolved hardening decisions

| Former ambiguity | Locked outcome |
|---|---|
| U-001 | ADR-007: five formal workstreams plus a mandatory standalone Tax module with structured output, report section and required cross-links. |
| U-002 | ADR-006: round one follows quick deterministic discovery; round two follows the complete register and preliminary full extraction. |
| U-003 | ADR-012: public research is optional, disabled by default, target-name/market-only when enabled, and fully logged. |
| U-006 | ADR-009: red team uses a brand-new Codex task/chat and allowlisted sealed packet; ordinary subagents require verified non-inheritance. |
| U-007 | ADR-008: PDF, spreadsheet, DOCX and image citation locators are fixed by format. |
| U-008 | ADR-015: the IC brief is an exactly two-page A4 PDF rendered and counted through an in-process pure-Python path. |
| U-011 | ADR-017: extraction preserves source formulas and cached values without generic workbook recalculation; any analytical recomputation is separate and explicitly cited. |
| U-012 | ADR-018: explicit non-answers may be ingested and carried as open evidence; silence never resumes a pause. |

## Remaining unresolved ambiguities

| ID | Question | Safe default in this design | Impact / resolution owner |
|---|---|---|---|
| U-004 | Must cost be exact money, or is subscription-included/estimated/unavailable-with-reason acceptable? | Never fabricate; record explicit cost basis | High evaluation risk; validate Codex telemetry and ask evaluator. |
| U-005 | Which concrete frontier and economy models are available under the evaluator's Codex subscription? | Capability profiles with actual resolved ID logged | High routing risk; environment discovery before locking config. |
| U-009 | Must clean-clone setup work offline, and which operating systems are in scope? | Do not claim offline or OS-specific support; minimize and lock native dependencies | High 20-minute risk; evaluator environment disclosure. |
| U-010 | What archive size, nesting depth and file-size limits are acceptable? | Deny unsafe paths; bounded configurable limits with explicit quarantine | Medium resilience risk; benchmark and threat-model decision. |
| U-013 | What retention/deletion policy applies to confidential run artifacts after evaluation? | Keep local only; do not auto-delete without explicit authorization | Medium privacy/operations risk; data owner. |
| U-014 | What quantitative thresholds define acceptable issue recall, false positives and citation accuracy? | Report metrics without inventing pass percentages; require zero dangling citations | High evaluation uncertainty; evaluator rubric. |
| U-015 | Does “roughly equal weight” require an exact score formula? | Three-domain rubric without invented numeric weights | Low-medium; evaluator. |
| U-016 | Does the evaluator expect the optional midpoint call or DM channel to be integrated into software? | No; export Markdown packets and keep the engine independent of communications services | Low; deal lead. |

## Architecture risk register

| ID | Risk | Likelihood | Impact | Planned mitigation / proof |
|---|---|---:|---:|---|
| R-001 | Codex does not expose exact tokens/cost or selectable model IDs. | High | High | Spike route/usage surfaces first; explicit cost basis; no fabricated telemetry. |
| R-002 | Automated creation of a brand-new red-team task/chat is unavailable or a context inherits messages. | Medium | High | New task/chat ID, allowlisted packet, isolation manifest and mandatory manual new-chat fallback; reject unverifiable subagents. |
| R-003 | A locked format-specific citation is encoded or resolved incorrectly. | Medium | High | Typed schemas and resolver tests across PDF, spreadsheet, DOCX and image fixtures. |
| R-004 | Workbook cached values are stale or formulas cannot be reproduced. | High | High | Record formula/cache state; explicit Python calculations for material figures; gap flags. |
| R-005 | Optional public research leaks confidential query context. | Low-Medium | Critical | Disabled by default, target/market-only fields, preflight filter and complete attempted/rejected/completed action log. |
| R-006 | Package setup exceeds 20 minutes on an unknown evaluator machine. | Medium | High | Minimal native path, locked dependencies, no Docker/system tools, clean-clone benchmark. |
| R-007 | The synthetic room overfits prompts and does not generalize to the unseen room. | Medium | High | Sealed ground truth, generator variation, unseen fixtures, no filename/value hard-coding. |
| R-008 | Model context limits omit evidence or create inconsistent cross-workstream facts. | Medium | High | Structured evidence index, claim store, retrieval by IDs, deterministic cross-checks. |
| R-009 | Unreadable or malicious files destabilize the run. | Medium | High | Read-only input, no macro execution, safe archive handling, quarantine and bounded retries. |
| R-010 | Legal/tax language is overconfident or treated as professional advice. | Medium | High | Irish scope prompt, evidence/confidence rubric, limitations and specialist-review flags. |
| R-011 | A forced red-team “finding” creates false positives. | Medium | Medium | Allow “upheld/no new issue” outcomes; score substantive challenge quality, not count alone. |
| R-012 | The standalone Tax module fails to propagate relevant implications into formal workstreams. | Medium | High | Structured tax IDs, bidirectional cross-link schema and fatal cross-link coverage validation. |
| R-013 | Pure-Python A4 pagination overflows, underfills or varies by dependency version. | Medium | High | Locked renderer dependencies, deterministic fonts/layout, golden renders, media-box checks and programmatic two-page assertion. |

## Implementation-readiness decision

**Status: Ready to begin implementation, but not ready to claim trial acceptance.**

The seven hardening decisions are locked and no longer block implementation. Remaining pre-handover blockers are empirical or evaluator-specific: validate Codex model/cost surfaces (U-004/U-005), benchmark the unknown clean-clone environment (U-009), define safe archive limits (U-010), prove spreadsheet handling (U-011), and obtain evaluation/retention thresholds where needed (U-013-U-015). None justifies inventing an environmental prerequisite now.
