# Requirements traceability

## Purpose and counting rule

This matrix is the implementation-planning baseline for the due-diligence engine. A requirement is counted when a source sentence or list item creates an independently verifiable imperative, constraint, deliverable, evaluation expectation, or project condition. Compound sentences are split only where their clauses require different components, outputs, or checks. Descriptive background is not counted. Illustrative analyst examples and non-engine commercial terms are retained because they constrain evaluation or delivery.

The matrix contains **163 requirements**: 103 from the trial brief, 21 from the room specification, 14 from the planning directive, and 25 from the Phase 7 directive. Component and path names are contracts; some are now implemented as described in the architecture status.

## Source register

| Code | Source | Integrity reference |
|---|---|---|
| TB | [Founding Engineer Trial Project](../dd-engine-trial-brief.md.pdf), pages 1-4 | SHA-256 `ABF999C273012166AA9FD99CDA2AB9AB01EE968DC68D06FF78511F06C0358A0A` |
| RS | [Real-room document specification](../specs_req_room.pdf), pages 1-2 | SHA-256 `F99A520DE1505412926341A4A51F2992A9BC96A0D98E1218526445BEDFC510B8` |
| USR | Current task directive, 31 August 2026 | Conversation record |
| P7 | Phase 7 evidence/calculation directive, 1 September 2026 | Conversation record |

## Trial brief requirements

| ID | Source | Normalized sentence-level requirement | Planned component | Planned output | Verification method |
|---|---|---|---|---|---|
| TB-001 | TB p.1, header | Complete the paid trial in five working days, hand over by end of 4 September 2026, and support evaluation on 7 September 2026. | Delivery governance | Handover checklist and dated release manifest | Compare release timestamps and checklist to brief dates. |
| TB-002 | TB p.1, Context | The product must be reproducible, testable, usable on any deal, and runnable without the original author in the loop. | Codex workflow, deterministic core, test suite | Locked setup, run manifest, automated checks | Clean-clone acceptance run by a person other than the author. |
| TB-003 | TB p.1, The task | Build an end-to-end due-diligence engine. | Codex orchestrator and six-stage state machine | Completed run directory | End-to-end test reaches all terminal artifacts. |
| TB-004 | TB p.1, The task | Accept a folder of mixed documents as the data-room input. | Intake/path validator and source registrar | Validated input manifest | Fixture test with mixed supported and unsupported files. |
| TB-005 | TB p.1, The task | Provide access points for questions to a deal lead. | Human pause/resume controller | Question and answer files for both rounds | Resume test with supplied answers and immutable audit timestamps. |
| TB-006 | TB p.1, The task | Produce a due-diligence report and a two-page IC brief. | Report assembler and deterministic pure-Python brief renderer/validator | `report.md`, `ic-brief.md`, `ic-brief.pdf` | Schema/content checks plus programmatic assertion that the rendered PDF is A4 and exactly two pages. |
| TB-007 | TB p.1, The task | Build the synthetic data room before relying on a confidential real room. | Synthetic-room factory | `synthetic-room/` | Generation test precedes engine fixture run. |
| TB-008 | TB p.1, The task | Make the synthetic target an entirely fictional Irish company and follow the attached room specification. | Synthetic-room manifest and fiction guard | Room files and `planted-issues.md` | Manifest coverage check and forbidden-real-entity review. |
| TB-009 | TB p.1, The task | Develop and test the engine against the synthetic room. | Test harness | Golden run under `examples/` or `runs/` | Recreate expected planted-issue detections. |
| TB-010 | TB p.1, The task | Make the synthetic room realistically messy rather than a folder of clean PDFs. | Synthetic-room mutation layer | Duplicates, scans, photos, contradictions and malformed references | Fixture audit against the RS checklist. |
| TB-011 | TB p.1, The task | Address the report to an investment committee moving toward acquisition. | Report contract and drafting prompt | Audience-specific executive report | Rubric review for IC relevance and decision focus. |
| TB-012 | TB p.1, The task | Support go/no-go and price/structure decisions. | Issue prioritizer and impact framing | Decision-oriented findings and IC brief | Each material finding carries decision and price/structure implications. |
| TB-013 | TB p.1, The task | Do not give an independent valuation opinion. | Report validator | Scope statement and valuation guardrail | Lint report for prohibited valuation conclusion language. |
| TB-014 | TB p.1, The task | Test findings against the committee's stated price. | Deal-assumption intake and financial reasoning | Price-context assumptions and sensitivity commentary | Trace report conclusions to deal-lead price input. |
| TB-015 | TB p.1, The task | Write as an adviser who holds a view, not as a clerk summarizing documents. | Frontier-model workstream synthesis | Prioritized, supported conclusions | Analyst-quality rubric and red-team challenge. |
| TB-016 | TB p.1, Stage 1 | Inventory and classify every file in the source register. | Deterministic source registrar | `source-register.csv` and JSON equivalent | File-system walk count equals register count, including archive members. |
| TB-017 | TB p.1, Stage 1 | Flag duplicate, superseded and unreadable files. | Hash/version detector and extraction-status validator | Register flags and reason codes | Fixtures for byte duplicates, semantic/version candidates and unreadable files. |
| TB-018 | TB p.1, Stage 2 | Extract PDFs, Word, Excel, scanned images and other encountered formats. | Tiered extraction adapters | Evidence records and extraction ledger | Format fixtures; unsupported formats quarantine without stopping the run. |
| TB-019 | TB p.1, Stage 2 | Tier extraction so expensive models touch only documents that need them. | Router and deterministic extraction confidence gate | Routing decision per file/chunk | Assert deterministic success bypasses model routes; audit exceptions. |
| TB-020 | TB p.2, Stage 3 | Generate intake questions from evidence already read, not from a fixed script. | Question generator | Evidence-linked question set | Every question cites triggering evidence/gap; no static-only question list. |
| TB-021 | TB p.2, Stage 3 | Send questions to and ingest answers from the deal lead. | Human pause/resume controller | `questions.md`, `answers.md`, answer provenance | Pause, edit answer file, resume, and verify downstream use. |
| TB-022 | TB p.2, Stage 3 | Run two intake rounds: one early and one once the source register exists. | State machine checkpoints | Round 1 packet after quick deterministic discovery; round 2 packet after the complete register and preliminary full extraction | Run-state test proves both distinct gated checkpoints and their locked ordering. |
| TB-023 | TB p.2, Stage 4 | Cover exactly the five named workstreams: financial, commercial, legal/contractual, operational/management and IT. | Workstream coordinator | Five workstream finding files | Artifact count/name assertion and coverage rubric. |
| TB-024 | TB p.2, Stage 4 | Apply Irish jurisdiction context to legal/contractual analysis. | Legal workstream prompt and jurisdiction field | Jurisdiction-scoped legal findings | Prompt/config assertion plus expert-review rubric; no unsupported legal advice. |
| TB-025 | TB p.2, Stage 5 | Run red team independently without access to the drafting history. | Brand-new Codex task/chat and allowlisted sealed-packet builder | `red-team/packet-allowlist.json`, `red-team/sealed-packet-manifest.json` and `red-team/isolation-manifest.json` | Verify a new task/chat ID, verify no inherited context, and reject an ordinary subagent unless non-inheritance is demonstrably verified. |
| TB-026 | TB p.2, Stage 5 | Instruct red team to refute key issues. | Red-team prompt contract | Challenge entries per key issue | Coverage check from key-issue IDs to challenge outcomes. |
| TB-027 | TB p.2, Stage 5 | Recompute headline numbers from source. | Deterministic recomputation helpers plus red-team reasoning | Recalculation sheets and variances | Independent formula replay against cited source cells. |
| TB-028 | TB p.2, Stage 5 | Identify gaps during red team. | Red-team gap scanner | Gap entries with severity and remediation | Compare unresolved evidence/questions to challenge log. |
| TB-029 | TB p.2, Stage 5 | Put the red-team challenge log in a report appendix. | Report assembler | Red-team appendix and standalone log | Appendix-to-log ID reconciliation. |
| TB-030 | TB p.2, Stage 6 | Produce the full report in Markdown. | Report assembler | `report.md` | Markdown/schema lint and required-section check. |
| TB-031 | TB p.2, Stage 6 | Produce a two-page IC brief. | IC brief assembler and deterministic pure-Python A4 renderer | `ic-brief.md` and `ic-brief.pdf` | Generate without Office, LibreOffice, Docker or a browser; programmatically assert A4 media boxes and exactly two PDF pages. |
| TB-032 | TB p.2, Stage 6 | Produce the source register as a final output. | Output packager | Final source register | Compare packaged hash to validated stage-1 register. |
| TB-033 | TB p.2, Stage 6 | Produce a run log naming models, purposes, token usage and cost. | Append-only invocation ledger and cost adapter | `run-log.jsonl` and human summary | Schema check; every model call has route, resolved model, purpose, usage and cost status. |
| TB-034 | TB p.2, Standard | Meet the standard of a Big Four financial due-diligence report for an investment committee. | Workstream/report quality rubric | Quality scorecard | Structured human review and blinded comparison where available. |
| TB-035 | TB p.2, Standard | Hold every workstream to that standard. | Workstream validator | Per-workstream rubric results | Fail packaging if any workstream lacks rubric coverage. |
| TB-036 | TB p.2, Standard | Deliver within the deliberately tight five-day trial window. | Delivery governance | Time-boxed plan and handover | Handover timestamp; no runtime requirement invented from this schedule. |
| TB-037 | TB p.2, What good looks like | Reconcile management-account EBITDA against statutory filings, determine the supportable number and explain price impact when that pattern appears. | Financial workstream and reconciliation engine | Reconciliation finding | Synthetic exemplar with known discrepancy and expected conclusion. |
| TB-038 | TB p.2, What good looks like | Resolve customers belonging to the same group under different trading names and assess true concentration when evidence supports it. | Commercial entity-resolution analysis | Customer concentration bridge | Seeded alias fixture and recomputed concentration. |
| TB-039 | TB p.2, What good looks like | Detect transaction-triggered change-of-control clauses and explain renegotiation leverage when present. | Legal clause analysis | Contractual risk finding | Seeded contract/amendment test with source citation. |
| TB-040 | TB p.2, What good looks like | Make inferences and state conclusions with evidence behind them. | Evidence graph and drafting contract | Claim-evidence-impact records | Claim validator requires evidence and reasoning classification. |
| TB-041 | TB p.2, What good looks like | Clearly state what could not be established. | Uncertainty register | Limitations section and gap log | No unresolved high-severity gap omitted from report. |
| TB-042 | TB p.2, What good looks like | State what was asked or would be asked of management. | Question/evidence linker | Management-question appendix | Question IDs referenced from relevant findings/gaps. |
| TB-043 | TB p.2, What good looks like | Cite every material claim to source document and page, sheet or cell. | Canonical evidence-address service | Inline citations and `citations/index.jsonl` | Resolve PDF citations by source ID/hash and page; spreadsheets by source ID/hash, sheet and cell/range; DOCX by source ID/hash and paragraph/table/row plus optional deterministic page; images by source ID/hash, image/page and region coordinates. |
| TB-044 | TB p.2, What good looks like | Avoid hedging all conclusions into unhelpful language. | Drafting rubric and language lint | Decisive qualified conclusions | Human rubric plus detection of unsupported generic caveats. |
| TB-045 | TB p.2, What good looks like | Do not claim confidence the evidence does not support. | Confidence calibration validator | Confidence and evidence-strength fields | Challenge high-confidence claims with weak/missing evidence. |
| TB-046 | TB p.2, What good looks like | Model real-room mess: duplicates, superseded versions, photographed letters, image-only scans, non-tying spreadsheets, contradictions, `N/A`, and references to missing folders. | Synthetic-room mutation layer | Messiness manifest | Fixture-by-fixture existence and detection checks. |
| TB-047 | TB p.2, What good looks like | Plant a handful of known issues and verify that the engine finds them. | Ground-truth manifest kept from drafting agents | `planted-issues.md` and scored detection report | Precision/recall comparison after the synthetic run. |
| TB-048 | TB p.3, Constraints | Run inside Claude Code, Codex or Cursor. | Runtime harness | Codex workflow files | Clean-clone run in Codex; other harnesses are non-required. |
| TB-049 | TB p.3, Constraints | Let the evaluator open the repo in the harness, point at a room folder and run. | Codex entry workflow | Single documented start command/prompt | First-time-user test from clone with an arbitrary room path. |
| TB-050 | TB p.3, Constraints | Choose a harness and state it in the README. | Documentation | README runtime declaration | README lint/search and clean-clone usability test. |
| TB-051 | TB p.3, Constraints | Treat support for more than one harness as optional bonus scope. | Architecture boundary | Portability note | Confirm acceptance does not depend on Claude Code or Cursor. |
| TB-052 | TB p.3, Constraints | Use the builder's model subscription; do not require a separate API budget. | Codex-authenticated model execution | Keyless setup instructions | Run with no provider API-key environment variables. |
| TB-053 | TB p.3, Constraints | Use the models the implementer recommends. | Versioned routing policy | Model-profile configuration | Architecture review of route rationale and actual run ledger. |
| TB-054 | TB p.3, Constraints | Use frontier models for judgment such as drafting, financial reasoning and red team. | Judgment route profile | Route decisions in run log | Route-policy unit test and ledger audit. |
| TB-055 | TB p.3, Constraints | Use cheaper models for mechanical inventory, classification and bulk extraction when a model is needed. | Economy route profile after deterministic tools | Route decisions in run log | Confirm mechanical calls avoid frontier route absent documented escalation. |
| TB-056 | TB p.3, Constraints | Make model routing explicit in the repository. | Checked-in route policy | `model-routing.yml` or equivalent | Config schema test and documentation review. |
| TB-057 | TB p.3, Constraints | Make actual routing visible in the run log. | Invocation ledger | Per-call route and resolved model | Reconcile model-call count with run-log entries. |
| TB-058 | TB p.3, Constraints | Explain in the notes what would change with a bigger model budget. | Notes template | Budget trade-off section | Required-heading check. |
| TB-059 | TB p.3, Constraints | Run cold from a clean clone. | Bootstrap and dependency lock | Reproducible environment and smoke test | Test in a fresh directory with no caches relied upon. |
| TB-060 | TB p.3, Constraints | From a clone, support opening Codex, following README, choosing a room, running and answering intake questions. | README and resumable workflow | End-to-end operator instructions | Timed novice runbook test. |
| TB-061 | TB p.3, Constraints | Get the engine running within 20 minutes. | Minimal bootstrap | Setup timing record | Wall-clock clean-clone test; fail at 20:00. |
| TB-062 | TB p.3, Constraints | Keep room data on the machine except content intentionally sent to the model provider. | Local artifact store and egress guard | Privacy manifest and egress log | Network/connector audit and test with telemetry disabled. |
| TB-063 | TB p.3, Constraints | Emit no telemetry. | Logging configuration | Local-only logs | Static dependency/config audit and network observation. |
| TB-064 | TB p.3, Constraints | Use no third-party logging. | Local append-only logger | Local logs only | Dependency and endpoint audit. |
| TB-065 | TB p.3, Constraints | Use no external services beyond model calls, subject to the brief's narrow public-research permission. | Connector allowlist | Egress decision log | Deny-by-default integration test and allowlist review. |
| TB-066 | TB p.3, Constraints | Limit permitted public web research to the target's name and market. | Public research is optional and disabled by default; an enabled research broker enforces the query filter | Disabled-state record or allowlisted request records | Assert no default request; when explicitly enabled, reject queries beyond the confirmed public target name and market or containing room text, PII or confidential facts. |
| TB-067 | TB p.3, Constraints | Log public web research. | Research ledger | `public-research-log.jsonl` with `not_performed` or attempted/rejected/completed action records | Schema, action completeness and report-citation reconciliation. |
| TB-068 | TB p.3, Constraints | Make the repository auditable before it is used on real material. | Transparent config and privacy documentation | Data-flow, route and dependency inventory | Manual repo audit checklist. |
| TB-069 | TB p.3, Constraints | Supporting code may use any language, but extraction, spreadsheet and check setup must be documented in README. | Python 3.11 supporting package and docs | Locked dependencies and setup instructions | Clean environment install and smoke test. |
| TB-070 | TB p.3, Deliverables | Hand over all deliverables by end of Friday 4 September 2026. | Delivery governance | Release manifest | Timestamp and completeness check. |
| TB-071 | TB p.3, Deliverable 1 | Deliver a Git repository with README covering setup, run procedure and structure. | Repository/documentation | Git repo and README | Clean-clone run plus required-heading check. |
| TB-072 | TB p.3, Deliverable 2 | Deliver the synthetic data room and a note describing planted issues. | Synthetic-room factory | Room tree and `planted-issues.md` | Manifest/ground-truth reconciliation. |
| TB-073 | TB p.3, Deliverable 3 | Deliver the report and IC brief produced on the synthetic room. | Output packager | Synthetic-run `report.md`, `ic-brief.md` and two-page A4 `ic-brief.pdf` | Provenance links all outputs to the synthetic run ID; PDF geometry and page count pass programmatic validation. |
| TB-074 | TB p.3, Deliverable 4 | Deliver the source register, red-team log and run log from that run. | Output packager | Three named run artifacts | Run-ID and hash consistency checks. |
| TB-075 | TB p.3, Deliverable 5 | Deliver a short notes file covering next build, surprises and least-confidence areas. | Notes template | `notes.md` | Required-heading and concise-length review. |
| TB-076 | TB p.3, Evaluation | Support a cold run on a second, unseen, confidential real room. | Generalized pipeline and privacy controls | Confidential-run artifacts local to evaluator | Evaluator-run acceptance test; no synthetic ground truth dependency. |
| TB-077 | TB p.3, Evaluation | Permit output comparison with the existing pipeline's report for the same deal. | Stable output structure | Comparable report/brief | Blind evaluation procedure. |
| TB-078 | TB p.3, Evaluation | Permit blinded reading by the client's deal lead. | Neutral artifact packaging | Report without engine-identifying editorial noise | Blind-review checklist. |
| TB-079 | TB p.3, Evaluation | Treat report quality, engineering and judgment as roughly equally weighted. | Acceptance scorecard | Three-domain rubric | Scorecard weights review. |
| TB-080 | TB p.4, Report quality | Surface material issues found. | Workstream synthesis and prioritizer | Issue register/report | Compare to planted issues and evaluator reference. |
| TB-081 | TB p.4, Report quality | Control false positives. | Evidence and confidence validators | Suppressed/qualified unsupported claims | Precision review and red-team results. |
| TB-082 | TB p.4, Report quality | Produce accurate citations that survive source spot-checking. | Evidence-address service | Format-specific resolvable citations | Random claim-to-source spot-check across PDF, spreadsheet, DOCX and image locators. |
| TB-083 | TB p.4, Report quality | Make each workstream read like Big Four analysis rather than summary. | Workstream rubric | Analytical workstream sections | Blinded expert rubric. |
| TB-084 | TB p.4, Report quality | Ensure red team identifies meaningful challenges. | Independent red-team executor | Substantive challenge log | Minimum challenge coverage plus human quality review; no forced false finding. |
| TB-085 | TB p.4, Engineering | Run cold from README on an unseen room. | Bootstrap/runbook | Reproducible run | Clean-clone unseen-fixture test. |
| TB-086 | TB p.4, Engineering | Have every stage present and working. | State machine | Six completed stage manifests | Stage-contract integration test. |
| TB-087 | TB p.4, Engineering | Handle bad inputs without falling over. | Quarantine, retries and partial-run policy | Error ledger and continued artifacts | Corrupt, encrypted, malformed and unsupported fixtures. |
| TB-088 | TB p.4, Engineering | Keep model routing and cost visible and sensible. | Route policy and cost ledger | Human-readable run summary | Policy/ledger audit and exception rationale. |
| TB-089 | TB p.4, Engineering | Produce code that can be handed to another engineer. | Modular package, typing, tests and docs | Maintainable repository | Independent engineer review and change exercise. |
| TB-090 | TB p.4, Judgment | Generate high-quality intake questions. | Evidence-linked question generator | Prioritized questions | Deal-lead rubric for relevance, answerability and non-duplication. |
| TB-091 | TB p.4, Judgment | Make the synthetic room realistic. | Synthetic-room factory | Representative room | Coverage and realism review against RS. |
| TB-092 | TB p.4, Judgment | Prioritize work and tell the evaluator what was prioritized. | Priority ledger | Run plan and notes | Compare executed work to disclosed priorities. |
| TB-093 | TB p.4, Judgment | Produce a useful notes file. | Notes template | `notes.md` | Human rubric. |
| TB-094 | TB p.4, Judgment | Ask useful questions along the way. | Human pause/resume and issue escalation | Intake and clarification record | Deal-lead rubric and audit trail. |
| TB-095 | TB p.4, Evaluation | Allow an architecture different from the incumbent; judge the outcome rather than architectural similarity. | Decision framework | ADRs with outcome rationale | No acceptance criterion depends on incumbent internals. |
| TB-096 | TB p.4, Logistics | Allow project questions by direct message, with an expected response within a couple of EU working hours. | Project governance | Clarification log | Human process check; not an engine runtime dependency. |
| TB-097 | TB p.4, Logistics | Permit engine-generated intake questions to use that deal-lead channel. | Human interface | Exportable intake packet | Manual delivery/response test. |
| TB-098 | TB p.4, Logistics | Treat a 20-minute midpoint call as optional. | Project governance | Optional agenda | Confirm engine operation does not depend on the call. |
| TB-099 | TB p.4, Logistics | Record that the trial fee is payable on delivery regardless of outcome. | Commercial governance | Contract/handover record | Human contractual confirmation; no software behavior. |
| TB-100 | TB p.4, Logistics | Make the synthetic room entirely fictional with no real company names, people or copied figures. | Fiction guard and human review | Synthetic provenance declaration | Entity/value scan plus reviewer sign-off. |
| TB-101 | TB p.4, Logistics | Treat produced work as subject to the trial agreement's IP assignment. | Repository governance | License/ownership note if counsel directs | Human contractual confirmation; do not invent license terms. |
| TB-102 | TB p.4, Logistics | Preserve the stated fee/code ownership outcome if the parties do not proceed. | Commercial governance | Contract record | Human contractual confirmation; not enforced in code. |
| TB-103 | TB p.4, Logistics | Ask for clarification instead of guessing when the brief is unclear. | Assumption and decision log | `docs/decisions.md` open questions | Review unresolved ambiguities before implementation and at human pauses. |

## Real-room specification requirements

| ID | Source | Normalized sentence-level requirement | Planned component | Planned output | Verification method |
|---|---|---|---|---|---|
| RS-001 | RS p.1, opening | Model a real room of roughly 130-150 files across legal, financial and tax folders; the synthetic room may contain 60-100 if it preserves the mix and mess. | Synthetic-room manifest | Exactly 100 logical artifacts: 90 visible files, including one ZIP, plus exactly 10 members inside that ZIP | Assert 90 visible files, one ZIP, 10 ZIP members, 100 registerable logical artifacts, three top-level folders, full family coverage and all quirks. |
| RS-002 | RS p.1, Financial | Include six years of statutory accounts, one abridged CRO-style PDF per year. | Financial fixture generator | Six statutory-account PDFs | Manifest count/year/style checks. |
| RS-003 | RS p.1, Financial | Include one year-to-date management-accounts PDF and no monthly packs. | Financial fixture generator | One YTD PDF | Positive count and negative monthly-pack assertion. |
| RS-004 | RS p.1, Financial | Include the listed spreadsheets: trial balance, aged debtors/creditors, other debtors and prepayments, fixed assets, working capital, revenue by customer, PAYE and contractor headcount, loan, HP, profit on disposal and pipeline. | Spreadsheet fixture generator | Named XLSX/CSV files with cross-file relationships | Manifest checklist plus planted tie-out tests. |
| RS-005 | RS p.1, Financial | Include a financial information request XLSX whose vendor-answer column is about half `N/A`, `None` or `see legal 2.1`. | Questionnaire generator | Financial request list | Deterministic proportion and value assertions. |
| RS-006 | RS p.1, Financial | Include two JPG phone photos of bank-loan letters and one scanned image-only PDF of a loan/HP pack. | Image/scan fixture generator | Three image-dependent documents | Format/content-layer checks and extraction escalation test. |
| RS-007 | RS p.1, Financial | Include a short Word document on related-party transactions. | DOCX fixture generator | Related-party DOCX | Manifest and content-topic check. |
| RS-008 | RS p.1, Legal | Include the legal questionnaire as a Word document with answers pasted in. | Legal fixture generator | Legal questionnaire DOCX | Format and answer-presence check. |
| RS-009 | RS p.1, Legal | Include a statutory register/cap-table XLSX, shareholders' agreement and constitution. | Legal fixture generator | Corporate records | Manifest and cross-document ownership consistency tests. |
| RS-010 | RS p.1, Legal | Include a redacted employee master, contractor-list XLSX, sample employment/contractor agreements and a payslip. | HR/legal fixture generator | Employment records | Manifest, redaction and planted employee-count reconciliation checks. |
| RS-011 | RS p.1, Legal | Include two or three customer framework agreements with amendments as separate PDFs (about six files), plus a client letter and company response. | Contract fixture generator | Contract families and correspondence | Family/version linkage and count checks. |
| RS-012 | RS p.1, Legal | Include large scanned property purchase/sale contracts and a lease. | Scan fixture generator | Property scans and lease | Image-only/large-file behavior and manifest check. |
| RS-013 | RS p.1, Legal | Include two or three insurance certificates, fleet schedule, trade licence/registration, HR provider agreement and web-hosting agreement. | Legal/operations/IT fixture generator | Listed documents | Manifest coverage across relevant workstreams. |
| RS-014 | RS p.1, Legal | Include board minutes, a CRO screenshot instead of an extract, work-permit subfolder and business-registration subfolder. | Legal fixture generator | Listed files/folders | Structure, format and missing-proper-extract gap checks. |
| RS-015 | RS p.1, Legal | Include an in-room ZIP with about ten updated responses, including a synthetic unredacted employee list. | Archive fixture generator and privacy scanner | One visible ZIP containing exactly 10 updated-response members, including a synthetic PII-like record | Assert the ZIP is one of the 90 visible files; safely register all 10 members; test version detection and privacy flags. |
| RS-016 | RS pp.1-2, Tax | Include about 15 small VAT3-return and Xero-style bimonthly VAT-summary PDFs, with one amended. | Tax fixture generator and mandatory standalone Tax module | VAT document series; structured tax findings | Period/count/version checks, amended-return precedence and Tax-module consumption. |
| RS-017 | RS p.2, Tax | Include about 12 ROS-style screens covering VAT charges/payments, PAYE returns/payments and CT returns/payments/charges/refunds. | Tax screenshot generator and mandatory standalone Tax module | ROS-style PDF set; structured tax findings | Manifest/category coverage, image extraction and Tax-module coverage tests. |
| RS-018 | RS p.2, Tax | Include three annual tax computation/information PDFs, ROS registration details and tax clearance certificate. | Tax fixture generator and mandatory standalone Tax module | Tax compliance documents; structured tax findings | Year/count/topic and Tax-module coverage checks. |
| RS-019 | RS p.2, Tax | Include a trial-balance subfolder and an invoice-samples subfolder of about five files. | Tax fixture generator and mandatory standalone Tax module | Nested subfolders; tax tie-out records | Structure/count, Tax-module coverage and tax-to-financial tie-out tests. |
| RS-020 | RS p.2, Tax | Include two versions of the tax-response-summary XLSX, with Rev2 changing answers. | Tax questionnaire generator and mandatory standalone Tax module | Versioned XLSX pair; tax version-delta findings | Version ordering, changed-cell detection and Tax-module citation checks. |
| RS-021 | RS p.2, Quirks | Preserve duplicates, wrong folders, same filenames in different locations, an empty folder, renamed CSV and hidden sheet. | Synthetic-room mutation layer and registrar | Quirk manifest and flags | One deterministic fixture and expected detection per quirk. |

## Current task directive requirements

| ID | Source | Normalized sentence-level requirement | Planned component | Planned output | Verification method |
|---|---|---|---|---|---|
| USR-001 | USR | Inspect both supplied documents, the repository and current Git status. | Planning/review process | Source registry and baseline in decisions | Hashes, page review record and Git-status snapshot. |
| USR-002 | USR | Do not implement the engine yet. | Scope control | Documentation-only change set | Git diff contains only the four requested Markdown files after QA cleanup. |
| USR-003 | USR | Create `docs/requirements-traceability.md`. | Documentation | This file | File existence and content checks. |
| USR-004 | USR | Create `docs/architecture.md`. | Documentation | Architecture document | File existence and required-section checks. |
| USR-005 | USR | Create `docs/acceptance-criteria.md`. | Documentation | Acceptance document | File existence and trace-link checks. |
| USR-006 | USR | Create `docs/decisions.md`. | Documentation | Decision record | File existence and ambiguity/risk sections. |
| USR-007 | USR | Map every sentence-level requirement to a planned component, output and verification method, explicitly covering all named topics and all five deliverables. | Traceability method | Complete matrix | Row schema check, ID counts, and named-topic coverage audit. |
| USR-008 | USR | Choose Codex as the runtime harness. | Architecture decision | ADR-001 and Codex execution design | Cross-document consistency check. |
| USR-009 | USR | Choose Python 3.11 or later for deterministic supporting code. | Architecture decision | ADR-002 and setup plan | Cross-document consistency and planned version gate. |
| USR-010 | USR | Docker may be optional but must not be required. | Packaging decision | Native setup path and optional container note | Clean-clone acceptance runs without Docker installed. |
| USR-011 | USR | Distinguish deterministic local processing, Codex reasoning, human/deal-lead pauses, independent red-team execution, and validation/failure handling. | Architecture presentation | Five-plane component/flow sections | Architecture heading and flow audit. |
| USR-012 | USR | State assumptions clearly and do not invent environment requirements absent from the brief. | Decision discipline | Assumption register and open questions | Review each prerequisite against a cited source or explicit user choice. |
| USR-013 | USR | Finish with files created, requirement count, unresolved ambiguities, architecture risks, keyless rationale and readiness. | Handover process | Final response and decisions summary | Six-item handover checklist. |
| USR-014 | USR | Do not commit or push. | Git scope control | Uncommitted working-tree changes only | Final `git status`; no commits/remotes altered. |

## Phase 7 evidence/calculation requirements

| ID | Source | Normalized sentence-level requirement | Component | Output | Verification method |
|---|---|---|---|---|---|
| P7-001 | P7, before editing | Read authoritative planning/agent instructions, extraction outputs and intake schema; inspect Git status and preserve existing work. | Implementation process | Review/status record | Complete bounded reads and pre-edit `git status`. |
| P7-002 | P7, before editing | Use available intake answers and preserve unanswered matters as gaps. | Evidence foundation | `gaps.jsonl` with answer provenance/status | Answered, unanswered, vague and absent-answer fixtures. |
| P7-003 | P7, boundary | Do not read planted-issue files during implementation or the synthetic analytical run. | Operating boundary | No ground-truth dependency | Command/tool and code-path audit. |
| P7-004 | P7, objective | Create an auditable layer between extracted documents and analytical prose so unsupported material claims cannot pass. | Evidence foundation and coverage validator | Six record stores plus validation/coverage | Unsupported-material-claim fixture fails. |
| P7-005 | P7, records | Store claim ID, statement, type, workstream, materiality, confidence and status; limit claim type to fact, calculation, inference, recommendation or limitation. | Typed claim model | `evidence/claims.jsonl` | Schema/enumeration tests. |
| P7-006 | P7, records | Store evidence ID, claim ID, source ID, exact locator, extracted value/text, support/contradiction direction, extraction confidence and source/version status. | Typed evidence model | `evidence/evidence.jsonl` | Schema and source-content matching tests. |
| P7-007 | P7, records | Store calculation ID/description, source inputs/locators, units/currency, normalization, formula, result, rounding and independent recomputation status. | Typed calculation model | `evidence/calculations.jsonl` | Structural and recomputation tests. |
| P7-008 | P7, records | Store contradiction ID, conflicting claims/values, sources, likely explanations, resolution status and applicable intake question. | Typed contradiction model | `evidence/contradictions.jsonl` | Schema/reference tests. |
| P7-009 | P7, records | Store expected information, evidence of absence, importance, affected decision, requested follow-up and gap status. | Typed gap model | `evidence/gaps.jsonl` | Schema plus intake/extraction gap tests. |
| P7-010 | P7, records | Store issue ID/conclusion/workstream, supporting and counterevidence, calculations, materiality/confidence, transaction implication, recommended action and unresolved question. | Typed issue model | `evidence/issues.jsonl` | Schema/reference tests. |
| P7-011 | P7, citations | Validate that each cited source ID exists and its checksum matches the locked register/extraction source. | Citation validator | Citation result per evidence/input | Missing-source and checksum-mismatch tests. |
| P7-012 | P7, citations | Validate PDF pages, XLSX sheets/cells/ranges, DOCX paragraphs/tables, CSV rows/columns and intrinsic image locators. | Format-native resolvers | Locator validation results | Valid/invalid format fixture matrix. |
| P7-013 | P7, citations | Prevent silently superseded versions from being cited. | Version-aware validator | Failure or explicit acknowledgement warning | Superseded source tests. |
| P7-014 | P7, citations | Require material claims to contain valid supporting evidence. | Claim coverage gate | Per-claim support result | Unsupported claim test. |
| P7-015 | P7, citations | Require calculated values to identify source inputs and a formula. | Calculation validator | Input citations and recomputation result | Valid/invalid calculation citation tests. |
| P7-016 | P7, citations | Do not count duplicate documents as independent corroboration. | Independence-key resolver | Duplicate exclusion ledger | Exact-duplicate two-citation test. |
| P7-017 | P7, calculations | Preserve reported and recomputed numbers separately and never overwrite source values. | Calculation record/recomputer | Separate result fields; immutable inputs | Reported-versus-recomputed test. |
| P7-018 | P7, calculations | Normalize periods, currency, signs and units explicitly. | Calculation schema | `normalisation` object | Missing-normalization tests. |
| P7-019 | P7, calculations | Store formula/inputs and report missing inputs rather than assuming zero. | Safe deterministic recomputer | Formula/version and null missing inputs | Missing-input blocking test. |
| P7-020 | P7, calculations | Record whether a calculation is deterministic or model-assisted. | Calculation schema | `calculation_method` | Enumeration test. |
| P7-021 | P7, outputs | Create the six named JSONL record stores, `citation_validation.json` and `evidence_coverage.md`. | Evidence pipeline | Eight named artifacts | File-existence and run-ID checks. |
| P7-022 | P7, tests | Test valid and invalid PDF, spreadsheet, DOCX, duplicate, superseded-version and calculation citations. | Test suite | `tests/test_evidence.py` | Focused fixture suite. |
| P7-023 | P7, synthetic run | Run the evidence foundation against the synthetic room without consulting the answer key. | Canonical run procedure | Run-local evidence artifacts | Public-only validation plus evidence command. |
| P7-024 | P7, scope | Do not draft workstream prose or the report in Phase 7. | Stage boundary | `analyse`/`report` remain unimplemented | CLI/state and output-tree assertions. |
| P7-025 | P7, scope | Do not commit or push. | Git scope control | Uncommitted changes only | Final Git status/log inspection. |

## Coverage index for specifically named concerns

| Concern | Primary requirement IDs | Planned owner |
|---|---|---|
| Six stages | TB-016-TB-033, TB-086 | State machine and stage contracts |
| Five workstreams | TB-023-TB-024, TB-035, TB-083 | Workstream coordinator |
| Tax handling | RS-016-RS-020; ADR-007 in decisions | Mandatory standalone Tax analytical module producing `tax/tax-findings.json`, `tax/tax-analysis.md`, its own `report.md` section, and cross-links to Financial, Legal, Operational/management and IT |
| Two intake rounds | TB-020-TB-022 | Human pause/resume controller |
| Source-level citations | TB-040-TB-043, TB-082 | Evidence-address service |
| Phase 7 structured records | P7-005-P7-010 | Evidence foundation |
| Citation validation and duplicate independence | P7-011-P7-016 | Format-native citation validator |
| Calculation provenance | TB-027, P7-007, P7-015, P7-017-P7-020 | Safe deterministic recomputation ledger |
| Model routing | TB-019, TB-053-TB-057, TB-088 | Routing policy and invocation ledger |
| Token and cost logging | TB-033, TB-088 | Invocation/cost ledger |
| Privacy restrictions | TB-062-TB-065, RS-015 | Egress guard and local artifact store |
| Public-research logging | TB-066-TB-067 | Research broker and ledger |
| Clean-clone setup | TB-059-TB-060, TB-071, TB-085 | Bootstrap/runbook |
| 20-minute setup | TB-061 | Timed acceptance test |
| Five final deliverables | TB-071-TB-075 | Output packager and delivery manifest |
