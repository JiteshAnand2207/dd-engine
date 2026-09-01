# Independent red-team challenge log

Run ID: `20260901T040928457675Z-dede88eb959c`  
Review date: 2026-09-01  
Purpose: attempt to refute the candidate due-diligence report without editing upstream artifacts.

## Review boundary

Reviewed inputs were limited to the explicit synthetic data room and the completed run's source register, structured extracts, intake questions and answers, evidence/calculation/contradiction/gap ledgers, workstreams, draft report, draft IC brief, and runtime/research logs. No planted-issue directory, synthetic generator source, expected-finding file, anomaly configuration, prior implementation conversation, or planted-answer artifact was opened or searched.

All 100 registered source hashes independently matched the read-only data room. All 15 headline calculation records reproduced arithmetically; that arithmetic agreement does not validate analytical conclusions whose period, population, classification or evidence is incomplete.

## Challenge summary

| Severity | Upheld | Rejected | Unresolved | Total |
|---|---:|---:|---:|---:|
| Critical | 7 | 3 | 0 | 10 |
| High | 11 | 2 | 2 | 15 |
| Medium | 2 | 0 | 1 | 3 |
| **Total** | **20** | **5** | **3** | **28** |

## Challenges

### RT-001

- **Challenge ID:** RT-001
- **Target claim or omission:** FIN-002 describes EUR 1.23m YTD EBITDA as an evidence-backed or supportable baseline.
- **Challenge hypothesis:** The baseline is a management assertion in the same unsupported schedule as the challenged EUR 0.18m add-back, not an independently evidenced ledger result.
- **Independent evidence/calculation:** SRC-0012 reports EUR 1.23m + EUR 0.18m = EUR 1.41m, but also says invoices, ledger detail and the restructuring plan were not supplied. The arithmetic reproduces; the evidential label does not.
- **Severity:** critical
- **Citation:** SRC-0012 page 1; SRC-0004 Request C5; report FIN-002.
- **Required correction:** Recast EUR 1.23m as management-reported unadjusted EBITDA pending a ledger reconciliation.
- **Status:** upheld

### RT-002

- **Challenge ID:** RT-002
- **Target claim or omission:** FIN-003 treats EUR 0.83m as the correct normalized net-working-capital basis.
- **Challenge hypothesis:** Correct point-in-time arithmetic is not a normalized peg, and included categories remain untested.
- **Independent evidence/calculation:** SRC-0027 gives EUR 1.48m + EUR 0.095m - EUR 0.93m + EUR 0.185m = EUR 0.83m. No monthly series, seasonality analysis, recoverability test or agreed SPA definition is provided.
- **Severity:** critical
- **Citation:** SRC-0027 Working_Capital!B4:B10; report FIN-003.
- **Required correction:** Separate the snapshot arithmetic from a normalized peg and require a monthly category bridge with agreed inclusions/exclusions.
- **Status:** upheld

### RT-003

- **Challenge ID:** RT-003
- **Target claim or omission:** The report omits a EUR 45,000 snagging retention in the property-sale document.
- **Challenge hypothesis:** The retention may be an omitted receivable, working-capital item or collectability exposure.
- **Independent evidence/calculation:** Visual review of SRC-0058 page 3 states that EUR 45,000 remains after the 15 October 2024 sale; the report leaves the property visual unresolved.
- **Severity:** medium
- **Citation:** SRC-0058 native PDF page 3; extracts/needs_vision.json; draft report.
- **Required correction:** Establish whether the retention remained receivable, its ageing/recoverability, and its completion-account treatment.
- **Status:** unresolved

### RT-004

- **Challenge ID:** RT-004
- **Target claim or omission:** FIN-005 presents EUR 1.26m arithmetic net debt using mismatched dates.
- **Challenge hypothesis:** December 2025 cash netted against June/August 2026 debt can misstate completion-date net debt.
- **Independent evidence/calculation:** Gross debt/debt-like items total EUR 2.22m; cited cash is EUR 0.96m at 31 December 2025, while debt is dated 30 June or 31 August 2026. EUR 1.26m is arithmetic only and unrestricted status is unproven.
- **Severity:** critical
- **Citation:** SRC-0010, SRC-0006, SRC-0017 paragraph 10, SRC-0026 Cash!C4.
- **Required correction:** Require a same-date lender-confirmed debt and unrestricted-cash statement; label EUR 1.26m non-contemporaneous.
- **Status:** upheld

### RT-005

- **Challenge ID:** RT-005
- **Target claim or omission:** The report omits the term-loan change-of-control review event and fixed/floating charge.
- **Challenge hypothesis:** Lender review, payoff and security release are explicit transaction conditions.
- **Independent evidence/calculation:** SRC-0008 states change of control is a review event under the EUR 1.45m facility. SRC-0009 page 1 shows a fixed and floating charge; pages 2-3 show HP title retention.
- **Severity:** critical
- **Citation:** SRC-0008 native image; SRC-0009 native PDF pages 1-3; report FIN-005; IC brief.
- **Required correction:** Add lender review/consent, payoff and security/HP-title releases as pre-completion conditions.
- **Status:** upheld

### RT-006

- **Challenge ID:** RT-006
- **Target claim or omission:** COMM-001 omits aggregate top-two and top-three customer-group concentration.
- **Challenge hypothesis:** Portfolio concentration is substantially higher than the largest-group headline conveys.
- **Independent evidence/calculation:** Mosaic plus Harbourlight is 51.91% FY2025 and 55.56% YTD; adding Glencree gives 71.76% and 75.82%. Harbourlight plus Mosaic is 72.07% of weighted pipeline.
- **Severity:** high
- **Citation:** SRC-0018 Customer_Revenue; SRC-0019 Pipeline; report COMM-001.
- **Required correction:** Add top-two/top-three group and pipeline concentration with downside implications.
- **Status:** upheld

### RT-007

- **Challenge ID:** RT-007
- **Target claim or omission:** Challenge to consolidation of Mosaic North and Mosaic South into one group.
- **Challenge hypothesis:** The grouping could be an unsupported name-based merge.
- **Independent evidence/calculation:** SRC-0018 assigns both entities the same group reference; SRC-0038 and SRC-0039 independently identify the common Mosaic group.
- **Severity:** high
- **Citation:** SRC-0018!D6:D7; SRC-0038 page 1; SRC-0039 page 1.
- **Required correction:** None; retain the identity citations.
- **Status:** rejected

### RT-008

- **Challenge ID:** RT-008
- **Target claim or omission:** Challenge that the report applied the superseded three-month Mosaic North liability cap.
- **Challenge hypothesis:** A later amendment may replace the base term.
- **Independent evidence/calculation:** SRC-0036 dated 18 February 2026 expressly replaces clause 11 with a twelve-month fee cap and uncapped service credits; the report applies it.
- **Severity:** high
- **Citation:** SRC-0035 page 1; SRC-0036 page 1; report LEGAL-002.
- **Required correction:** None; preserve the amendment analysis.
- **Status:** rejected

### RT-009

- **Challenge ID:** RT-009
- **Target claim or omission:** Challenge to Harbourlight change-of-control consent conclusion.
- **Challenge hypothesis:** A later amendment or response might remove or satisfy consent.
- **Independent evidence/calculation:** SRC-0037 requires prior written consent; SRC-0034 preserves clause 14.2; SRC-0093 says consent was not requested.
- **Severity:** critical
- **Citation:** SRC-0037 clause 14.2; SRC-0034 page 1; SRC-0093 page 1.
- **Required correction:** None; keep consent as a closing dependency.
- **Status:** rejected

### RT-010

- **Challenge ID:** RT-010
- **Target claim or omission:** Coverage says termination/renewal/pricing/service was analysed, but no customer termination schedule or gap appears.
- **Challenge hypothesis:** Material termination or renewal rights may remain unreviewed despite a completed coverage label.
- **Independent evidence/calculation:** Reviewed frameworks support group, liability and change-of-control points but do not provide a complete customer-by-customer termination/renewal schedule; no legal gap preserves that limitation.
- **Severity:** high
- **Citation:** Report coverage table; workstreams/legal_contractual.md; SRC-0035 to SRC-0039.
- **Required correction:** Mark coverage limited and add a full material-contract term schedule/gap.
- **Status:** upheld

### RT-011

- **Challenge ID:** RT-011
- **Target claim or omission:** The report omits shareholder pre-emption and approval mechanics.
- **Challenge hypothesis:** Pre-emption or 75% approvals may require waivers or affect sequencing.
- **Independent evidence/calculation:** SRC-0054 records share-transfer pre-emption and 75% approval for acquisitions, material borrowing and the business plan; the report does not map them to the transaction.
- **Severity:** high
- **Citation:** SRC-0054 page 1; legal workstream; draft report.
- **Required correction:** Obtain executed governing documents and a transaction-specific waiver/approval analysis.
- **Status:** unresolved

### RT-012

- **Challenge ID:** RT-012
- **Target claim or omission:** The EUR 182,000 VAT-control debit is not reconciled to the ROS screen showing listed charges paid.
- **Challenge hypothesis:** The debit may be a different period, receivable, posting error or incomplete tax evidence.
- **Independent evidence/calculation:** SRC-0079 has a EUR 182,000 VAT-control debit. The amended P2 return is EUR 182,000 and the VAT screen shows listed charges paid, but no ledger/period bridge explains the debit.
- **Severity:** high
- **Citation:** SRC-0079!B5; SRC-0083; SRC-0084; tax/tax-analysis.md.
- **Required correction:** Add a contradiction and require return-to-ROS-to-ledger reconciliation.
- **Status:** upheld

### RT-013

- **Challenge ID:** RT-013
- **Target claim or omission:** Challenge that TAX-001 falsely inferred an amended VAT filing.
- **Challenge hypothesis:** The revision might exist only in an intake answer.
- **Independent evidence/calculation:** SRC-0083 shows EUR 174,000 and SRC-0084 shows an amended EUR 182,000 return. The EUR 8,000 change is source-supported despite the inconsistent updated answer.
- **Severity:** critical
- **Citation:** SRC-0083 page 1; SRC-0084 page 1; intake/round_1_answers.json.
- **Required correction:** None to the amendment conclusion; preserve the answer contradiction.
- **Status:** rejected

### RT-014

- **Challenge ID:** RT-014
- **Target claim or omission:** TAX-002 treats equal EUR 401,700 totals as a corporation-tax settlement reconciliation.
- **Challenge hypothesis:** Equal totals across isolated screens do not prove assessment linkage, timing or final settlement.
- **Independent evidence/calculation:** EUR 420,000 - EUR 18,300 = EUR 401,700 and EUR 389,200 + EUR 12,500 = EUR 401,700, but dates/assessment references are absent; SRC-0070 separately shows a EUR 210,000 payment that may be a component.
- **Severity:** high
- **Citation:** SRC-0074; SRC-0063; SRC-0070; report TAX-002.
- **Required correction:** Treat the match as a hypothesis pending assessment-level ROS and bank allocation evidence.
- **Status:** unresolved

### RT-015

- **Challenge ID:** RT-015
- **Target claim or omission:** TAX-003 carries high confidence despite an unexplained EUR 132,000 PAYE-control credit.
- **Challenge hypothesis:** Annual return/payment agreement can coexist with a current liability, timing item or posting error.
- **Independent evidence/calculation:** SRC-0075 and SRC-0076 each total EUR 1.584m, but SRC-0079 records a EUR 132,000 PAYE-control credit; no monthly or post-year-end bridge resolves it.
- **Severity:** high
- **Citation:** SRC-0075; SRC-0076; SRC-0079!B6; report TAX-003.
- **Required correction:** Reduce confidence and require monthly PAYE return/payment/control reconciliation through the latest period.
- **Status:** upheld

### RT-016

- **Challenge ID:** RT-016
- **Target claim or omission:** Workforce analysis treats the contractor list as current at the report date.
- **Challenge hypothesis:** It is only a 30 June snapshot and contains contracts ending before 1 September.
- **Independent evidence/calculation:** SRC-0044 lists 12 contractors active at 30 June 2026, but six end dates fall from 15 July to 21 August 2026; renewals/current roster are absent.
- **Severity:** high
- **Citation:** SRC-0044 contractor rows; legal workstream; report LEGAL-003.
- **Required correction:** Use the dated snapshot or obtain current renewals, cessation records and roster.
- **Status:** upheld

### RT-017

- **Challenge ID:** RT-017
- **Target claim or omission:** The report omits a 61-versus-64 employee population/version inconsistency.
- **Challenge hypothesis:** Headcount, remuneration, allocation and PII analyses use different universes.
- **Independent evidence/calculation:** The redacted employee master has 61 rows with client/salary/start fields; the updated unredacted archive member has 64 rows with different fields; allocation and PAYE use 64. No bridge explains EMP062-EMP064 or timing.
- **Severity:** high
- **Citation:** SRC-0045; SRC-0090 archive member; SRC-0091; legal workstream.
- **Required correction:** Add a population contradiction and require a dated HR/payroll/allocation bridge.
- **Status:** upheld

### RT-018

- **Challenge ID:** RT-018
- **Target claim or omission:** The report does not flag the actual unredacted employee PII-like dataset in the room.
- **Challenge hypothesis:** The room contains a concrete privacy/security exposure beyond a generic privacy gap.
- **Independent evidence/calculation:** The updated archive member contains 64 work emails, 64 personal emails and 64 PPS-like identifiers.
- **Severity:** critical
- **Citation:** SRC-0090 archive/member extract; source register; draft report.
- **Required correction:** Add a specific PII exposure; restrict/audit access, establish purpose/retention, and require controlled removal or secure transfer.
- **Status:** upheld

### RT-019

- **Challenge ID:** RT-019
- **Target claim or omission:** Challenge to the conclusion that IT recovery assurance is inadequate.
- **Challenge hypothesis:** Admin MFA and backup statements might sufficiently mitigate recovery risk.
- **Independent evidence/calculation:** SRC-0055 and SRC-0097 confirm MFA but no formal RTO, witnessed end-to-end restore, recent penetration test or independent assurance. MFA does not evidence recoverability.
- **Severity:** critical
- **Citation:** SRC-0055 page 1; SRC-0097 paragraph 7; report IT-001.
- **Required correction:** None to the core conclusion; maintain recovery evidence and remediation requirements.
- **Status:** rejected

### RT-020

- **Challenge ID:** RT-020
- **Target claim or omission:** OPS-001 and IT-001 count the same RTO/restore weakness as two critical issues.
- **Challenge hypothesis:** One control failure is double-counted, inflating the critical count.
- **Independent evidence/calculation:** Both findings rely on substantially the same evidence and prescribe overlapping witnessed recovery testing and governance actions.
- **Severity:** high
- **Citation:** workstreams/operational_management.md OPS-001; workstreams/it.md IT-001; draft report.
- **Required correction:** Consolidate them or explicitly distinguish non-overlapping transaction implications.
- **Status:** upheld

### RT-021

- **Challenge ID:** RT-021
- **Target claim or omission:** OPS-002 treats all EUR 265,000 of hosting creditor balance as acute continuity risk with 95% confidence.
- **Challenge hypothesis:** Only EUR 92,750 is beyond current and no default, suspension or termination evidence is cited.
- **Independent evidence/calculation:** SRC-0001 shows EUR 172,250 current, EUR 66,250 at 31-60 days and EUR 26,500 at 61+ days; it proves exposure, not threatened interruption.
- **Severity:** high
- **Citation:** SRC-0001 Hosting_Creditor!B4:E4; report OPS-002.
- **Required correction:** Base arrears language on EUR 92,750, lower confidence, and obtain status/default/termination evidence.
- **Status:** upheld

### RT-022

- **Challenge ID:** RT-022
- **Target claim or omission:** The report does not elevate missing contractor IP-assignment wording.
- **Challenge hypothesis:** Deliverables from a 12-contractor population may not be cleanly owned by the target.
- **Independent evidence/calculation:** The reviewed contractor agreement has no express IP assignment, while the contractor list contains 12 people; only a generic privacy/IP gap remains.
- **Severity:** high
- **Citation:** SRC-0042 contractor agreement; SRC-0044 contractor list; legal workstream.
- **Required correction:** Add an IP chain-of-title issue and require assignments/confirmatory deeds for material contractor-created IP.
- **Status:** upheld

### RT-023

- **Challenge ID:** RT-023
- **Target claim or omission:** All 15 intake answers are closed and related gaps resolved despite unresolved text and non-management provenance.
- **Challenge hypothesis:** Test-operator answers were overinterpreted, prematurely closing questions.
- **Independent evidence/calculation:** Both answer files identify “Phase 11 synthetic test operator (not management).” Multiple answers say keep open, evidence not supplied, or unresolved; nevertheless all are closed and unresolved count is zero.
- **Severity:** critical
- **Citation:** intake/round_1_answers.json; intake/round_2_answers.json; intake/unresolved_questions.md; evidence/gaps.jsonl.
- **Required correction:** Reopen substantively unresolved questions, preserve provenance, and invalidate downstream confidence/completion that depended on false closure.
- **Status:** upheld

### RT-024

- **Challenge ID:** RT-024
- **Target claim or omission:** The IC brief lists FIN-005, FIN-003 and TAX-002 but omits matching conditions, questions or protections.
- **Challenge hypothesis:** The decision document understates debt/security, working-capital and corporation-tax execution risk.
- **Independent evidence/calculation:** IC conditions/actions do not expressly require lender review/payoff/releases, same-date net debt, full NWC peg mechanics, or assessment-level corporation-tax reconciliation/protection.
- **Severity:** critical
- **Citation:** outputs/ic_brief.md; report FIN-003, FIN-005 and TAX-002.
- **Required correction:** Add IC conditions/protections for lender releases, same-date debt, NWC peg/true-up and corporation-tax reconciliation/escrow or indemnity.
- **Status:** upheld

### RT-025

- **Challenge ID:** RT-025
- **Target claim or omission:** Tax clearance and invoice samples are labelled limitations without their positive evidence being recorded.
- **Challenge hypothesis:** The gap labels are likely false positives or materially overstated.
- **Independent evidence/calculation:** Tax clearance states current through 30 April 2027. Four invoices tie to the register at 23% VAT: EUR 440,000 net + EUR 101,200 VAT = EUR 541,200 gross.
- **Severity:** medium
- **Citation:** SRC-0068; SRC-0066; SRC-0061, SRC-0062, SRC-0064, SRC-0065; tax analysis.
- **Required correction:** Record the positive tests while retaining authenticity and population-completeness caveats.
- **Status:** upheld

### RT-026

- **Challenge ID:** RT-026
- **Target claim or omission:** FIN-007 assigns high severity to a EUR 37,500 pipeline cached-value discrepancy without a materiality basis.
- **Challenge hypothesis:** It is a stale cache equal to 1.45% of the displayed total, not necessarily a high-severity weakness.
- **Independent evidence/calculation:** Live inputs sum to EUR 2,542,500 versus cached EUR 2,580,000: EUR 37,500 or 1.4535%. The live formula itself is correct.
- **Severity:** medium
- **Citation:** SRC-0019 Pipeline!E4:E8; report FIN-007.
- **Required correction:** Characterize the stale-cache control issue and justify severity against deal materiality.
- **Status:** upheld

### RT-027

- **Challenge ID:** RT-027
- **Target claim or omission:** LEGAL-003 uses 64 employees plus 10 contractors despite a 12-contractor legal population.
- **Challenge hypothesis:** The 27.03% Harbourlight workforce point estimate has an incomplete denominator.
- **Independent evidence/calculation:** Allocation gives 20/74 = 27.027%. Using all 12 contractors, the share ranges from 20/76 = 26.316% to 22/76 = 28.947%, depending on two unallocated contractors.
- **Severity:** high
- **Citation:** SRC-0091 Resource_Allocation; SRC-0044 contractor list; report LEGAL-003.
- **Required correction:** Present a range or reconcile every contractor before reporting a precise concentration.
- **Status:** upheld

### RT-028

- **Challenge ID:** RT-028
- **Target claim or omission:** Findings carry 90-99% confidence although unresolved answers remain and most analytical/drafting stages are logged local deterministic.
- **Challenge hypothesis:** Granular judgment confidence and routing provenance are unsupported.
- **Independent evidence/calculation:** The run log has 14 local_deterministic records and one frontier_judgment candidate review after report creation. Phase 8, Phase 9 and report are local deterministic; candidate-review.md identifies the candidate review as the sole reasoning task.
- **Severity:** high
- **Citation:** logs/run-log.jsonl; logs/candidate-review.md; workstream JSON; draft report.
- **Required correction:** Recalibrate confidence to source sufficiency/unresolved status and record judgment-heavy task/model provenance accurately.
- **Status:** upheld

## Review conclusion

The most consequential upheld challenges concern unsupported EBITDA quality, non-normalized working capital, non-contemporaneous net debt and omitted lender security/consent mechanics, false intake closure, unredacted employee PII, and incomplete IC decision protections. Rejected challenges confirm that Mosaic grouping, Mosaic amendment supersession, Harbourlight consent, the VAT amendment, and the core IT recovery gap are source-supported. These challenge statuses do not resolve or edit the underlying report; they define the independent corrections and evidence still required.
