# Independent red-team resolution

Run ID: `20260901T040928457675Z-dede88eb959c`

Disposition: 23 accepted, 5 rejected, 0 unresolved (28 total).

The red-team labels were treated as hypotheses. Each decision below was checked against the registered original source or a hashed run artifact and its validated extraction. Accepted challenges were corrected in the pipeline and not only in final Markdown.

## RT-001 — ACCEPTED

The source labels the unadjusted YTD EBITDA and add-back as management figures and states that ledger-level support was not supplied. The baseline is now described as management-reported, not evidence-backed.

Verification evidence:

- SRC-0012 (page 1): The page presents management's EBITDA bridge and expressly records the missing supporting detail.

Root cause: reasoning, drafting.

Files changed: `src/dd_engine/analysis/phase8.py`, `src/dd_engine/analysis/records.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/financial.json`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`, `outputs/ic_brief.pdf`

## RT-002 — ACCEPTED

The arithmetic correction is valid, but the workbook is one point-in-time schedule and does not establish a normalized completion-accounts peg. The finding now makes that boundary explicit.

Verification evidence:

- SRC-0027 (Calculation!B10): The workbook contains a corrected working-capital result but no historical normalization evidence at this locator or elsewhere in the schedule.

Root cause: reasoning, drafting.

Files changed: `src/dd_engine/analysis/phase8.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/financial.json`, `evidence/calculations.jsonl`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-003 — ACCEPTED

Independent visual review confirmed a property-sale page stating that a retention remains for snagging. A validated harness-review extraction unit now feeds a dedicated property finding and transaction action.

Verification evidence:

- SRC-0058 (page 3): The visually reviewed page states the retained amount and its snagging basis.

Root cause: extraction, retrieval/evidence packaging, drafting.

Files changed: `src/dd_engine/extraction/vision.py`, `src/dd_engine/analysis/phase9.py`, `src/dd_engine/cli.py`

Regression test: `tests/test_extraction.py::test_harness_visual_review_becomes_citable_extraction_evidence`, `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `extracts/vision_review.json`, `extracts/extracted_units.jsonl`, `workstreams/legal_contractual.json`, `outputs/due_diligence_report.md`

## RT-004 — ACCEPTED

The identified gross debt and debt-like total is supportable, but offsetting it by cash from a different date is only non-contemporaneous arithmetic. The result is no longer presented as completion-date net debt or proof of unrestricted cash.

Verification evidence:

- SRC-0008 (image 1): The lender confirmation is dated later than the ledger cash source and says it is not a payoff statement.

Root cause: calculation, reasoning, drafting.

Files changed: `src/dd_engine/analysis/phase8.py`, `src/dd_engine/extraction/vision.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`, `tests/test_extraction.py::test_harness_visual_review_becomes_citable_extraction_evidence`

Regenerated artifacts: `workstreams/financial.json`, `evidence/calculations.jsonl`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-005 — ACCEPTED

The original lender materials identify a change-of-control review event and security over company assets. The debt finding now cites the reviewed lender pages and requires lender, payoff and release mechanics rather than generic balance confirmation alone.

Verification evidence:

- SRC-0008 (image 1): The visual lender confirmation states that change of control is a facility review event.
- SRC-0009 (page 1): The reviewed facility page identifies a fixed and floating charge over company assets.

Root cause: extraction, retrieval/evidence packaging, drafting.

Files changed: `src/dd_engine/extraction/vision.py`, `src/dd_engine/analysis/phase8.py`

Regression test: `tests/test_extraction.py::test_harness_visual_review_becomes_citable_extraction_evidence`, `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `extracts/vision_review.json`, `workstreams/financial.json`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-006 — ACCEPTED

Recomputation across the customer revenue schedule confirmed that top-two and top-three exposure is materially more decision-useful than the largest-group percentage alone. The commercial workstream now reports both aggregates for both periods.

Verification evidence:

- SRC-0018 (Revenue!B4): This is one of the customer revenue inputs used in the full-year concentration recomputation.
- SRC-0018 (Revenue!B5): This is another customer revenue input used to rank and aggregate portfolio concentration.

Root cause: calculation, drafting.

Files changed: `src/dd_engine/analysis/phase8.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/commercial.json`, `evidence/calculations.jsonl`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-007 — REJECTED

The grouping is not name-based. The two original frameworks identify common group identity evidence, so treating the separately named entities as one concentration exposure remains supported.

Verification evidence:

- SRC-0038 (page 1): The first framework contains the counterparty and group identity evidence used for normalization.
- SRC-0039 (page 1): The second framework independently provides the corresponding group identity evidence.

Root cause: reasoning.

Files changed: `src/dd_engine/red_team/resolution.py`, `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`, `tests/test_red_team_resolution.py::test_resolution_requires_complete_validated_challenge_coverage`

Regenerated artifacts: `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

## RT-008 — REJECTED

The report already selected the later amendment and concluded that it replaced the earlier liability cap. The hypothesized superseded-version use did not occur.

Verification evidence:

- SRC-0035 (page 1): The later amendment states the operative replacement liability mechanics used in the regenerated legal finding.

Root cause: version selection.

Files changed: `src/dd_engine/red_team/resolution.py`, `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`, `tests/test_red_team_resolution.py::test_resolution_requires_complete_validated_challenge_coverage`

Regenerated artifacts: `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

## RT-009 — REJECTED

The later amendment preserves the original change-of-control consent clause, and no original-source waiver or consent was found. The consent conclusion therefore remains valid despite the challenge.

Verification evidence:

- SRC-0034 (page 1): The later amendment expressly keeps the original consent clause in force.

Root cause: version selection, reasoning.

Files changed: `src/dd_engine/red_team/resolution.py`, `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`, `tests/test_red_team_resolution.py::test_resolution_requires_complete_validated_challenge_coverage`

Regenerated artifacts: `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

## RT-010 — ACCEPTED

The supplied customer documents do not support a portfolio-wide conclusion on termination, renewal, pricing, service levels and statements of work. Coverage now remains a limitation and a contract-term matrix is an explicit action.

Verification evidence:

- SRC-0037 (page 1): The individual framework demonstrates that contract terms must be mapped by agreement and cannot establish portfolio-wide completeness.

Root cause: retrieval/evidence packaging, drafting.

Files changed: `src/dd_engine/analysis/phase9.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/legal_contractual.json`, `evidence/gaps.jsonl`, `outputs/due_diligence_report.md`

## RT-011 — ACCEPTED

The executed shareholders' agreement contains a supermajority reserved-matter threshold and transfer pre-emption mechanics. The legal finding and closing action now include those sequencing and waiver requirements.

Verification evidence:

- SRC-0031 (page 1): The agreement page contains the reserved-matter approval and transfer pre-emption terms.

Root cause: retrieval/evidence packaging, drafting.

Files changed: `src/dd_engine/analysis/phase9.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/legal_contractual.json`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-012 — ACCEPTED

The VAT-control balance is independently present in the tax trial balance and is not reconciled by the payment-status screen. The tax workstream now separates the filing contradiction from this additional control-account exposure.

Verification evidence:

- SRC-0081 (Tax TB!B6): The trial-balance cell contains the VAT-control debit used in the finding.

Root cause: calculation, reasoning.

Files changed: `src/dd_engine/analysis/phase9.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `tax/tax-findings.json`, `evidence/calculations.jsonl`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-013 — REJECTED

The VAT amendment is not inferred only from intake. The original ROS evidence records the amended charge, so the source-backed filing contradiction remains.

Verification evidence:

- SRC-0077 (page 1): The original tax screen identifies the VAT amendment and its charge independently of intake answers.

Root cause: reasoning.

Files changed: `src/dd_engine/red_team/resolution.py`, `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

Regression test: `tests/test_red_team_resolution.py::test_resolution_requires_complete_validated_challenge_coverage`, `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

## RT-014 — ACCEPTED

Matching totals across isolated return, charge and cash screens do not prove assessment-period allocation or settlement. The corporation-tax conclusion now treats equality as arithmetic only and requires a period-by-period ROS reconciliation.

Verification evidence:

- SRC-0074 (page 1): The return screen supplies one side of the arithmetic comparison.
- SRC-0072 (page 1): The payment screen supplies cash entries without proving their allocation to the cited assessment.

Root cause: calculation, reasoning.

Files changed: `src/dd_engine/analysis/phase9.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `tax/tax-findings.json`, `evidence/calculations.jsonl`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-015 — ACCEPTED

Annual PAYE return/payment equality is a positive control, but it does not resolve the separate PAYE-control credit in the trial balance. The finding now records both facts and reduces confidence through the common unresolved-intake cap.

Verification evidence:

- SRC-0081 (Tax TB!C7): The trial-balance cell contains the PAYE-control credit omitted from the prior conclusion.

Root cause: calculation, reasoning.

Files changed: `src/dd_engine/analysis/phase9.py`, `src/dd_engine/analysis/records.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `tax/tax-findings.json`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-016 — ACCEPTED

The contractor list is explicitly a snapshot and multiple listed end dates precede the review date. It cannot establish the current roster; the legal workstream now computes and reports that limitation without assuming expiry means actual termination.

Verification evidence:

- SRC-0043 (Contractors!E4): This listed contract end date precedes the run date, illustrating why the snapshot is not a current-roster proof.

Root cause: version selection, reasoning.

Files changed: `src/dd_engine/analysis/phase9.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/legal_contractual.json`, `outputs/due_diligence_report.md`

## RT-017 — ACCEPTED

The redacted employee schedule discloses a reduced population and omitted payroll records, while a later unredacted employee workbook is present. The financial workstream now states the version inconsistency and requires explicit population selection.

Verification evidence:

- SRC-0044 (Employees!B2): The redacted workbook's scope note states the supplied and omitted record populations.
- SRC-0095 (Employees!A1): The later workbook identifies itself as the unredacted employee master.

Root cause: version selection, retrieval/evidence packaging, drafting.

Files changed: `src/dd_engine/analysis/phase8.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/financial.json`, `outputs/due_diligence_report.md`

## RT-018 — ACCEPTED

The later employee workbook contains explicit personal-data field categories. The IT workstream now records the concrete room-handling exposure without reproducing personal values and requires immediate access, minimization and retention remediation.

Verification evidence:

- SRC-0095 (Employees!D3): The header identifies one of the sensitive employee-data field categories; no row-level personal value is reproduced.

Root cause: inventory, retrieval/evidence packaging, drafting.

Files changed: `src/dd_engine/analysis/phase9.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/it.json`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-019 — REJECTED

Administrator MFA is a useful access control but does not evidence recovery objectives, restore performance, penetration testing or independent assurance. It therefore does not resolve the report's recovery-assurance conclusion.

Verification evidence:

- SRC-0097 (paragraph 7): The same source that records administrator MFA also says no independent penetration test or witnessed disaster-recovery exercise was supplied.

Root cause: reasoning.

Files changed: `src/dd_engine/red_team/resolution.py`, `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`, `tests/test_red_team_resolution.py::test_resolution_requires_complete_validated_challenge_coverage`

Regenerated artifacts: `red_team/red_team_resolution.json`, `red_team/red_team_resolution.md`

## RT-020 — ACCEPTED

The prior outputs elevated the same restore weakness twice. The operational finding is now a high-severity governance/action-ownership issue, while the distinct evidence-standard deficiency remains the critical IT finding.

Verification evidence:

- SRC-0047 (paragraph 14): The board record shows an unscheduled restore-test action with no approved date, supporting a governance finding distinct from technical assurance.

Root cause: reasoning, drafting.

Files changed: `src/dd_engine/analysis/phase9.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/operational_management.json`, `workstreams/it.json`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-021 — ACCEPTED

The creditor schedule supports aggregate and overdue amounts, but no default notice, suspension threat or contractual due-date conclusion. The operational finding now quantifies only the amount aged beyond current and expressly rejects an unsupported default inference.

Verification evidence:

- SRC-0001 (Aged Creditors!E4): The row contains the aggregate provider creditor balance.
- SRC-0001 (Aged Creditors!C4): This aged bucket is one input to the separately computed overdue amount.

Root cause: calculation, reasoning.

Files changed: `src/dd_engine/analysis/phase9.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/operational_management.json`, `evidence/calculations.jsonl`, `outputs/due_diligence_report.md`

## RT-022 — ACCEPTED

The complete sample contractor form contains no express IP assignment. Silence in one form is not proof that ownership failed, but across the stated contractor population it is a material chain-of-title limitation requiring signed-term mapping and confirmatory assignments.

Verification evidence:

- SRC-0042 (page 1): The reviewed sample form covers services, status and termination but contains no express IP ownership or assignment clause.

Root cause: retrieval/evidence packaging, reasoning, drafting.

Files changed: `src/dd_engine/analysis/phase9.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/legal_contractual.json`, `outputs/due_diligence_report.md`, `outputs/ic_brief.md`

## RT-023 — ACCEPTED

The prior normalizer treated long replies as substantive even when they explicitly said evidence was absent or the matter remained open. The policy now conservatively recognizes those replies, preserves every verbatim answer and migrates existing artifacts; thirteen questions are open after rerun.

Verification evidence:

- `intake/round_1_answers.json` (answer records and status_counts): The migrated artifact preserves the original verbatim replies and now classifies explicit non-evidence language as open.

Root cause: intake.

Files changed: `src/dd_engine/intake/answers.py`, `src/dd_engine/intake/pipeline.py`, `src/dd_engine/intake/__init__.py`

Regression test: `tests/test_intake.py::test_long_answer_that_explicitly_withholds_support_remains_open`, `tests/test_intake.py::test_answer_policy_migration_preserves_verbatim_and_reopens_long_non_answer`

Regenerated artifacts: `intake/round_1_answers.json`, `intake/round_2_answers.json`, `intake/unresolved_questions.md`, `workstreams/financial.json`, `workstreams/commercial.json`, `workstreams/legal_contractual.json`, `workstreams/operational_management.json`, `workstreams/it.json`, `tax/tax-findings.json`

## RT-024 — ACCEPTED

The short-form brief omitted critical execution levers that appeared in the full findings. Brief generation now includes every critical issue in the condition list and maps every transaction lever to the affected findings while retaining the deterministic two-page guardrail.

Verification evidence:

- `red_team/red_team_challenge_log.json` (RT-024): The sealed challenge log records the previously observed mismatch between the full report and short-form decision document.

Root cause: drafting, output formatting.

Files changed: `src/dd_engine/reporting/rendering.py`, `src/dd_engine/reporting/pdf.py`, `src/dd_engine/reporting/pipeline.py`

Regression test: `tests/test_analysis.py::test_phase10_generates_complete_validated_bundle`

Regenerated artifacts: `outputs/ic_brief.md`, `outputs/ic_brief.pdf`, `outputs/due_diligence_report.md`, `outputs/report_validation.json`

## RT-025 — ACCEPTED

The invoice sample and tax-clearance certificate provide real but bounded positive evidence. A new tax finding records invoice arithmetic/register reconciliation and clearance currency while explicitly avoiding a full-period completeness inference.

Verification evidence:

- SRC-0068 (Register!E4): The invoice-register gross amount is an input to the sample reconciliation.
- SRC-0070 (page 1): The certificate records current tax-clearance evidence for the stated period.

Root cause: retrieval/evidence packaging, reasoning.

Files changed: `src/dd_engine/analysis/phase9.py`, `src/dd_engine/analysis/pipeline.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `tax/tax-findings.json`, `outputs/due_diligence_report.md`

## RT-026 — ACCEPTED

The cached-total discrepancy is small relative to displayed weighted pipeline and did not justify high severity by itself. The finding is now medium severity and separately reports the materially concentrated top-two opportunity share.

Verification evidence:

- SRC-0019 (Pipeline!E4): This is one of the weighted opportunity inputs used in both the total and concentration calculations.
- SRC-0019 (Pipeline!E5): This second weighted opportunity input supports the top-two concentration recomputation.

Root cause: calculation, reasoning.

Files changed: `src/dd_engine/analysis/phase8.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/financial.json`, `evidence/calculations.jsonl`, `outputs/due_diligence_report.md`

## RT-027 — ACCEPTED

The prior workforce-share point estimate mixed the full employee population with only allocated contractors. The commercial finding now uses the full legal contractor population in the denominator and reports a lower/upper range because two contractors are unallocated.

Verification evidence:

- SRC-0043 (Contractors!B2): The legal list states the full contractor population at its snapshot date.
- SRC-0003 (Contractors!C10): The allocation schedule says fewer contractors are client-allocated, establishing the unknown-assignment range.

Root cause: calculation, version selection, reasoning.

Files changed: `src/dd_engine/analysis/phase8.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`

Regenerated artifacts: `workstreams/commercial.json`, `evidence/calculations.jsonl`, `outputs/due_diligence_report.md`

## RT-028 — ACCEPTED

The previous confidence values did not reflect unresolved intake and extraction limits. Finding confidence is now capped by the lowest supporting extraction confidence and at 85% whenever intake remains open; report release readiness also remains false without validated independent-run isolation evidence.

Verification evidence:

- `intake/round_2_answers.json` (answer records and status_counts): The migrated second-round artifact records open questions that now constrain analytical confidence.

Root cause: intake, reasoning, drafting.

Files changed: `src/dd_engine/analysis/records.py`, `src/dd_engine/reporting/pipeline.py`, `src/dd_engine/reporting/rendering.py`

Regression test: `tests/test_analysis.py::test_red_team_regressions_are_resolved_systemically`, `tests/test_analysis.py::test_phase10_generates_complete_validated_bundle`

Regenerated artifacts: `workstreams/financial.json`, `workstreams/commercial.json`, `workstreams/legal_contractual.json`, `workstreams/operational_management.json`, `workstreams/it.json`, `tax/tax-findings.json`, `outputs/due_diligence_report.md`, `outputs/report_validation.json`
