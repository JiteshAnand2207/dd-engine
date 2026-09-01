# Financial analysis

Run ID: `20260901T081036940718Z-ea9100a654cb`

This is decision-oriented commercial due diligence, not a document summary. Source facts are separated from analytical conclusions. No independent valuation is provided.

## Material findings

### FIN-002 — CRITICAL

**Conclusion:** The EUR 75,000 transformation add-back is unsupported in the room; the management-reported unadjusted YTD EBITDA is EUR 430,000, 14.9% below reported adjusted EBITDA.

**Source fact:** The YTD pack reports adjusted EBITDA of EUR 505,000 and baseline ledger EBITDA of EUR 430,000; it states that invoices and an approved plan were absent.

**Analysis:** Without invoices, approvals or evidence that the cost is non-recurring, the add-back does not meet a supportable quality-of-earnings standard. The unadjusted figure is still a management-pack number and is not a ledger-reconciled QoE baseline.

**Why it matters:** An unsupported add-back directly inflates the earnings base used in price discussions.

**Transaction implication:** Exclude the adjustment from price assumptions. If the seller seeks value for the benefit, defer it into an earn-out tied to realized savings and require a warranty covering the completeness of adjustment support.

**Confidence:** 85%

**Uncertainty/limitation:** No adjustment support or ledger-to-management reconciliation has been supplied; neither the add-back nor the unadjusted management figure is independently verified.

**Recomputations:** `CALC-FIN-003`

**Supporting citations:**

- `EVD-FIN-002-01` — `SRC-0003` / page 1
- `EVD-FIN-002-02` — `SRC-0013` / Requests!B4

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain the approved restructuring plan, invoice/payroll detail, implementation dates and evidence of cessation; classify each cost as recurring or exceptional and rebuild the bridge.

### FIN-003 — CRITICAL

**Conclusion:** The submitted working-capital formula is wrong: it reports EUR -531,000 instead of a recomputed point-in-time net working-capital snapshot of EUR 522,000, a EUR 1,053,000 variance. The corrected snapshot is not a normalized completion-accounts peg.

**Source fact:** The workbook formula sums rows 5-7 and explicitly notes that trade debtors and a hidden prepayment row are omitted; the control row reports the correct baseline.

**Analysis:** The error reverses the direction and scale of the submitted snapshot. Correcting that formula does not establish seasonality, normalizations or the SPA definition.

**Why it matters:** An incorrect baseline can transfer value mechanically through the completion accounts.

**Transaction implication:** Do not use the vendor formula in the SPA. Define the working-capital schedule at account level, attach the corrected baseline, and require a specific completion-accounts warranty.

**Confidence:** 85%

**Uncertainty/limitation:** A monthly bridge, seasonality analysis, account-level SPA definition and agreed normalizations are still required before setting a peg.

**Recomputations:** `CALC-FIN-004`

**Supporting citations:**

- `EVD-FIN-003-01` — `SRC-0004` / Completion Snapshot!B9
- `EVD-FIN-003-02` — `SRC-0004` / Completion Snapshot!B9
- `EVD-FIN-003-03` — `SRC-0004` / Completion Snapshot!D9

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Lock an account-level NWC definition, agree treatment of other debtors/prepayments, recompute a monthly twelve-month peg and attach the validated workbook to the transaction documents.

### FIN-004 — HIGH

**Conclusion:** The 90+ debtor bucket is understated: customer rows total EUR 157,000 (18.4% of debtors), versus the stored total of EUR 129,000.

**Source fact:** The aged-debtors schedule reports total receivables of EUR 854,000; its 90+ formula cache does not equal the visible customer rows.

**Analysis:** The error understates overdue exposure and prevents reliance on the submitted ageing for recoverability or normalized working-capital analysis.

**Why it matters:** Overdue debt affects cash conversion, bad-debt risk and the working-capital peg.

**Transaction implication:** Use the recomputed ageing for price and completion accounts, reserve specifically against disputed/aged balances, and consider an escrow or receivables indemnity for unrecovered 90+ debt.

**Confidence:** 85%

**Recomputations:** `CALC-FIN-005`

**Supporting citations:**

- `EVD-FIN-004-01` — `SRC-0005` / Receivable Ageing!E8
- `EVD-FIN-004-02` — `SRC-0005` / Receivable Ageing!F8
- `EVD-FIN-004-03` — `SRC-0005` / Receivable Ageing!E4

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain invoice-level ageing with post-cut-off cash receipts, dispute status and credit notes; reconcile it to the ledger and agree balance-specific provisions.

### FIN-005 — CRITICAL

**Conclusion:** Identified debt and debt-like items total EUR 970,000 before cash, including EUR 164,000 HP and a EUR 96,000 on-demand director balance excluded from management's loan summary. A non-contemporaneous arithmetic offset against the latest ledger cash identified is EUR 970,000; this is not completion-date net debt or proof that cash is unrestricted.

**Source fact:** Loan, HP and related-party sources report EUR 710,000, EUR 164,000 and EUR 96,000 respectively; the trial balance reports cash of EUR 0.

**Analysis:** HP and an on-demand related-party balance are debt-like regardless of management's classification. The cash date mismatch prevents a defensible completion-date net debt conclusion. Reviewed lender pages also identify security, title-retention and change-of-control review mechanics where present.

**Why it matters:** Debt-like classification changes equity proceeds, consent analysis and funds flow.

**Transaction implication:** Include HP and the director account in the debt-free/cash-free mechanism, require payoff letters and releases, and retain escrow until lender balances and unrestricted cash are confirmed.

**Confidence:** 85%

**Uncertainty/limitation:** No completion-date lender statements, payoff evidence or restricted-cash analysis is available, and the cash period differs from the debt schedules.

**Recomputations:** `CALC-FIN-006`

**Supporting citations:**

- `EVD-FIN-005-01` — `SRC-0006` / Funding!C5
- `EVD-FIN-005-02` — `SRC-0007` / Leases!C5
- `EVD-FIN-005-03` — `SRC-0009` / paragraph 6
- `EVD-FIN-005-04` — `SRC-0004` / Completion Snapshot!B7

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain dated lender statements, HP payoff schedules, security/covenant details, the director settlement agreement and bank evidence distinguishing unrestricted from restricted cash.

### FIN-007 — HIGH

**Conclusion:** Probability-weighted pipeline is understated by EUR 60,000: the opportunity rows sum to EUR 609,000, not the stored EUR 549,000 total. The two largest rows comprise 90.1% of the recomputed weighted pipeline.

**Source fact:** The pipeline supplies opportunity values and management probabilities but no win-rate support.

**Analysis:** The stored-total variance is 9.9% of the recomputed total. Its severity is therefore distinct from the more material concentration and absence of probability calibration.

**Why it matters:** Forecast support affects confidence in forward revenue and any performance-linked consideration.

**Transaction implication:** Exclude uncontracted pipeline from fixed price and base any earn-out only on collected revenue or gross profit, with customer-level anti-double-counting rules.

**Confidence:** 85%

**Uncertainty/limitation:** No historical probability calibration or signed-order evidence was supplied.

**Recomputations:** `CALC-FIN-008`, `CALC-FIN-009`

**Supporting citations:**

- `EVD-FIN-007-01` — `SRC-0012` / Opportunity Review!E7
- `EVD-FIN-007-02` — `SRC-0012` / Opportunity Review!E4

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

- `EVD-FIN-008-01` — `SRC-0013` / Requests!B5

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Provide monthly trial balances and revenue/gross-margin/EBITDA/cash bridges for the latest 24 months, including budget and prior-year comparatives.

## Coverage and explicit limitations

| Topic | Status | Linked issues |
|---|---|---|
| six_year_statutory_performance | limitation | None |
| management_vs_statutory | analysed | FIN-002, FIN-008 |
| revenue_and_ebitda_bridges | analysed | FIN-002 |
| adjustments_and_quality_of_earnings | analysed | FIN-002 |
| gross_margin_trends | limitation | None |
| customer_concentration | analysed | COMM-001 |
| aged_debtors_and_recoverability | analysed | FIN-004 |
| aged_creditors | limitation | None |
| other_debtors_and_prepayments | analysed | FIN-003 |
| normalised_working_capital | analysed | FIN-003, FIN-004 |
| debt_loans_hp_and_debt_like | analysed | FIN-005 |
| cash_and_restricted_cash | analysed | FIN-005 |
| fixed_assets_and_disposals | limitation | None |
| related_party_transactions | analysed | FIN-005 |
| paye_and_contractor_headcount | limitation | None |
| forecast_and_pipeline_support | analysed | FIN-007 |
| missing_monthly_performance | analysed | FIN-008 |
| tax_figures_affecting_financial_conclusions | limitation | None |

## General limitations

- Intake must be explicitly completed; unanswered or narrowed answers remain limitations.
- No independent valuation is provided.
- Cash restrictions, monthly performance and several visual debt sources require further evidence.
- Topics marked limitation had no source-backed adverse conclusion; absence is not treated as a clean bill of health.
