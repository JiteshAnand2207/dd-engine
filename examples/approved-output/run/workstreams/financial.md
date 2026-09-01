# Financial analysis

Run ID: `20260901T040928457675Z-dede88eb959c`

This is decision-oriented commercial due diligence, not a document summary. Source facts are separated from analytical conclusions. No independent valuation is provided.

## Material findings

### FIN-001 — HIGH

**Conclusion:** Statutory revenue increased 111.3% from 2020 to 2025, and EBITDA margin expanded from 11.6% to 15.9%; the six-year direction is positive, but annual filings alone do not establish current run-rate quality.

**Source fact:** The statutory series reports revenue of EUR 6,200,000 in 2020 and EUR 13,100,000 in 2025, with EBITDA of EUR 720,000 and EUR 2,080,000 respectively.

**Analysis:** The calculation is a trend analysis, not a valuation. Statutory EBITDA is a management measure in the filings and must be bridged to the ledger and YTD pack.

**Why it matters:** Historic growth supports the earnings narrative but does not validate adjustments or conversion.

**Transaction implication:** Use the statutory trajectory as a reference case only; condition price mechanics and any earn-out on a reconciled monthly earnings bridge rather than the headline trend.

**Confidence:** 85%

**Uncertainty/limitation:** Monthly phasing and the statutory-to-management reconciliation were not supplied.

**Recomputations:** `CALC-FIN-001`, `CALC-FIN-002`

**Supporting citations:**

- `EVD-FIN-001-01` — `SRC-0020` / page 1
- `EVD-FIN-001-02` — `SRC-0025` / page 1

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain the general-ledger-to-statutory bridge for each year and monthly 2025/2026 management accounts, then rerun margin and cash-conversion analysis.

### FIN-002 — CRITICAL

**Conclusion:** The EUR 180,000 transformation add-back is unsupported in the room; the management-reported unadjusted YTD EBITDA is EUR 1,230,000, 12.8% below reported adjusted EBITDA.

**Source fact:** The YTD pack reports adjusted EBITDA of EUR 1,410,000 and baseline ledger EBITDA of EUR 1,230,000; it states that invoices and an approved plan were absent.

**Analysis:** Without invoices, approvals or evidence that the cost is non-recurring, the add-back does not meet a supportable quality-of-earnings standard. The unadjusted figure is still a management-pack number and is not a ledger-reconciled QoE baseline.

**Why it matters:** An unsupported add-back directly inflates the earnings base used in price discussions.

**Transaction implication:** Exclude the adjustment from price assumptions. If the seller seeks value for the benefit, defer it into an earn-out tied to realized savings and require a warranty covering the completeness of adjustment support.

**Confidence:** 85%

**Uncertainty/limitation:** No adjustment support or ledger-to-management reconciliation has been supplied; neither the add-back nor the unadjusted management figure is independently verified.

**Recomputations:** `CALC-FIN-003`

**Supporting citations:**

- `EVD-FIN-002-01` — `SRC-0012` / page 1
- `EVD-FIN-002-02` — `SRC-0004` / Request List!C5

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain the approved restructuring plan, invoice/payroll detail, implementation dates and evidence of cessation; classify each cost as recurring or exceptional and rebuild the bridge.

### FIN-003 — CRITICAL

**Conclusion:** The submitted working-capital formula is wrong: it reports EUR -835,000 instead of a recomputed point-in-time net working-capital snapshot of EUR 830,000, a EUR 1,665,000 variance. The corrected snapshot is not a normalized completion-accounts peg.

**Source fact:** The workbook formula sums rows 5-7 and explicitly notes that trade debtors and a hidden prepayment row are omitted; the control row reports the correct baseline.

**Analysis:** The error reverses the direction and scale of the submitted snapshot. Correcting that formula does not establish seasonality, normalizations or the SPA definition.

**Why it matters:** An incorrect baseline can transfer value mechanically through the completion accounts.

**Transaction implication:** Do not use the vendor formula in the SPA. Define the working-capital schedule at account level, attach the corrected baseline, and require a specific completion-accounts warranty.

**Confidence:** 85%

**Uncertainty/limitation:** A monthly bridge, seasonality analysis, account-level SPA definition and agreed normalizations are still required before setting a peg.

**Recomputations:** `CALC-FIN-004`

**Supporting citations:**

- `EVD-FIN-003-01` — `SRC-0027` / Calculation!B9
- `EVD-FIN-003-02` — `SRC-0027` / Calculation!B10
- `EVD-FIN-003-03` — `SRC-0027` / Calculation!D9

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Lock an account-level NWC definition, agree treatment of other debtors/prepayments, recompute a monthly twelve-month peg and attach the validated workbook to the transaction documents.

### FIN-004 — HIGH

**Conclusion:** The 90+ debtor bucket is understated: customer rows total EUR 176,500 (11.9% of debtors), versus the stored total of EUR 74,000.

**Source fact:** The aged-debtors schedule reports total receivables of EUR 1,480,000; its 90+ formula cache does not equal the visible customer rows.

**Analysis:** The error understates overdue exposure and prevents reliance on the submitted ageing for recoverability or normalized working-capital analysis.

**Why it matters:** Overdue debt affects cash conversion, bad-debt risk and the working-capital peg.

**Transaction implication:** Use the recomputed ageing for price and completion accounts, reserve specifically against disputed/aged balances, and consider an escrow or receivables indemnity for unrecovered 90+ debt.

**Confidence:** 85%

**Recomputations:** `CALC-FIN-005`

**Supporting citations:**

- `EVD-FIN-004-01` — `SRC-0002` / Aged Debtors!E11
- `EVD-FIN-004-02` — `SRC-0002` / Aged Debtors!F11
- `EVD-FIN-004-03` — `SRC-0002` / Aged Debtors!E4

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain invoice-level ageing with post-cut-off cash receipts, dispute status and credit notes; reconcile it to the ledger and agree balance-specific provisions.

### FIN-005 — CRITICAL

**Conclusion:** Identified debt and debt-like items total EUR 2,220,000 before cash, including EUR 290,000 HP and a EUR 120,000 on-demand director balance excluded from management's loan summary. A non-contemporaneous arithmetic offset against the latest ledger cash identified is EUR 1,260,000; this is not completion-date net debt or proof that cash is unrestricted.

**Source fact:** Loan, HP and related-party sources report EUR 1,810,000, EUR 290,000 and EUR 120,000 respectively; the trial balance reports cash of EUR 960,000.

**Analysis:** HP and an on-demand related-party balance are debt-like regardless of management's classification. The cash date mismatch prevents a defensible completion-date net debt conclusion. Reviewed lender pages also identify security, title-retention and change-of-control review mechanics where present.

**Why it matters:** Debt-like classification changes equity proceeds, consent analysis and funds flow.

**Transaction implication:** Include HP and the director account in the debt-free/cash-free mechanism, require payoff letters and releases, and retain escrow until lender balances and unrestricted cash are confirmed.

**Confidence:** 85%

**Uncertainty/limitation:** No completion-date lender statements, payoff evidence or restricted-cash analysis is available, and the cash period differs from the debt schedules.

**Recomputations:** `CALC-FIN-006`

**Supporting citations:**

- `EVD-FIN-005-01` — `SRC-0010` / Loans!C6
- `EVD-FIN-005-02` — `SRC-0006` / HP!C6
- `EVD-FIN-005-03` — `SRC-0017` / paragraph 10
- `EVD-FIN-005-04` — `SRC-0026` / Trial Balance!C4
- `EVD-FIN-005-05` — `SRC-0009` / page 1
- `EVD-FIN-005-06` — `SRC-0009` / page 2

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain dated lender statements, HP payoff schedules, security/covenant details, the director settlement agreement and bank evidence distinguishing unrestricted from restricted cash.

### FIN-006 — HIGH

**Conclusion:** Workforce schedules do not reconcile: PAYE headcount is 64, but the client allocation lists 10 contractors while the legal list states 12, leaving 2 contractors unallocated. The redacted schedule states '61 records supplied; three payroll records omitted pending HR review', while a later unredacted employee workbook is also present; population selection must therefore be explicit.

**Source fact:** The PAYE, client-allocation and legal contractor schedules disagree. A redacted employee scope note and a later unredacted employee workbook are also present, so the population version must be selected explicitly.

**Analysis:** The mismatch prevents a complete payroll/contractor cost bridge and obscures client dependency and worker-status exposure.

**Why it matters:** Unreconciled workforce data affects cost normalization, client delivery and tax/employment risk.

**Transaction implication:** Do not accept the submitted headcount bridge for price assumptions. Require a warranty on workforce completeness and address status-related liabilities through targeted indemnity if unresolved.

**Confidence:** 85%

**Recomputations:** `CALC-FIN-007`

**Supporting citations:**

- `EVD-FIN-006-01` — `SRC-0003` / Contractors!B10
- `EVD-FIN-006-02` — `SRC-0043` / Contractors!B2
- `EVD-FIN-006-03` — `SRC-0015` / PAYE!B11
- `EVD-FIN-006-04` — `SRC-0044` / Employees!B2
- `EVD-FIN-006-05` — `SRC-0095` / Employees!A1

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Reconcile every PAYE employee and contractor by unique ID, cost centre, client, start/end date and tax status to payroll returns, contracts and the general ledger.

### FIN-007 — MEDIUM

**Conclusion:** Probability-weighted pipeline is overstated by EUR 37,500: the opportunity rows sum to EUR 2,542,500, not the stored EUR 2,580,000 total. The two largest rows comprise 72.1% of the recomputed weighted pipeline.

**Source fact:** The pipeline supplies opportunity values and management probabilities but no win-rate support.

**Analysis:** The stored-total variance is 1.5% of the recomputed total. Its severity is therefore distinct from the more material concentration and absence of probability calibration.

**Why it matters:** Forecast support affects confidence in forward revenue and any performance-linked consideration.

**Transaction implication:** Exclude uncontracted pipeline from fixed price and base any earn-out only on collected revenue or gross profit, with customer-level anti-double-counting rules.

**Confidence:** 85%

**Uncertainty/limitation:** No historical probability calibration or signed-order evidence was supplied.

**Recomputations:** `CALC-FIN-008`, `CALC-FIN-009`

**Supporting citations:**

- `EVD-FIN-007-01` — `SRC-0019` / Pipeline!E8
- `EVD-FIN-007-02` — `SRC-0019` / Pipeline!E4

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Correct the pipeline total and provide signed orders, stage history, historical conversion rates, expected close dates and margin by opportunity.

### FIN-008 — HIGH

**Conclusion:** No monthly management-account pack was prepared; current trading, seasonality, margin movement and cash conversion cannot be tested at an adviser-quality monthly cadence.

**Source fact:** The financial request response says only a YTD pack is prepared.

**Analysis:** A single six-month total cannot reveal monthly volatility or cut-off effects.

**Why it matters:** Missing monthly data weakens the reliability of run-rate and forecast conclusions.

**Transaction implication:** Do not annualize the YTD pack for fixed price. Use a completion condition or tightly defined earn-out measurement until monthly ledger extracts are validated.

**Confidence:** 85%

**Supporting citations:**

- `EVD-FIN-008-01` — `SRC-0004` / Request List!C4

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Provide monthly trial balances and revenue/gross-margin/EBITDA/cash bridges for January 2024 through the latest month, including budget and prior-year comparatives.

## Coverage and explicit limitations

| Topic | Status | Linked issues |
|---|---|---|
| six_year_statutory_performance | analysed | FIN-001 |
| management_vs_statutory | analysed | FIN-001, FIN-002, FIN-008 |
| revenue_and_ebitda_bridges | analysed | FIN-001, FIN-002 |
| adjustments_and_quality_of_earnings | analysed | FIN-002 |
| gross_margin_trends | analysed | FIN-001 |
| customer_concentration | analysed | COMM-001 |
| aged_debtors_and_recoverability | analysed | FIN-004 |
| aged_creditors | limitation | None |
| other_debtors_and_prepayments | analysed | FIN-003 |
| normalised_working_capital | analysed | FIN-003, FIN-004 |
| debt_loans_hp_and_debt_like | analysed | FIN-005 |
| cash_and_restricted_cash | analysed | FIN-005 |
| fixed_assets_and_disposals | limitation | None |
| related_party_transactions | analysed | FIN-005 |
| paye_and_contractor_headcount | analysed | FIN-006 |
| forecast_and_pipeline_support | analysed | FIN-007 |
| missing_monthly_performance | analysed | FIN-008 |
| tax_figures_affecting_financial_conclusions | limitation | None |

## General limitations

- Intake must be explicitly completed; unanswered or narrowed answers remain limitations.
- No independent valuation is provided.
- Cash restrictions, monthly performance and several visual debt sources require further evidence.
- Topics marked limitation had no source-backed adverse conclusion; absence is not treated as a clean bill of health.
