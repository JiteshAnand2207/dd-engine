# Tax analysis

Run ID: `20260901T081036940718Z-ea9100a654cb`

This is decision-oriented commercial due diligence, not a document summary. Source facts are separated from analytical conclusions. No independent valuation is provided.

## Scope

Commercial due diligence in an Irish transaction context; this is not a formal Irish legal or tax opinion and specialist advisers must confirm conclusions used in transaction documents.

## Material findings

### TAX-001 — CRITICAL

**Conclusion:** The current tax response is demonstrably wrong: a 2024 VAT amendment increased payable VAT by EUR 6,500, although the current response states that no VAT returns were amended. The tax trial balance also carries a EUR -13,500 VAT-control balance that the payment-status evidence does not reconcile.

**Source fact:** The original return reports EUR 41,000, the amended return reports EUR 47,500, and the ROS-style account says all listed charges were paid.

**Analysis:** Payment evidence for listed charges reduces one cash-exposure concern, but it does not clear or explain the ledger control balance. The current questionnaire answer is unreliable and requires a broader completeness check.

**Why it matters:** Incorrect tax responses undermine warranty disclosure and may conceal other amendments or process failures.

**Transaction implication:** Require corrected tax disclosures, a specific tax warranty covering amended filings and a tax covenant/indemnity for pre-close liabilities, interest and penalties.

**Confidence:** 85%

**Recomputations:** `CALC-TAX-001`

**Supporting citations:**

- `EVD-TAX-001-01` — `SRC-0041` / page 1
- `EVD-TAX-001-02` — `SRC-0040` / page 1
- `EVD-TAX-001-03` — `SRC-0042` / Responses!B4
- `EVD-TAX-001-04` — `SRC-0043` / page 1
- `EVD-TAX-001-05` — `SRC-0044` / Tax Ledger!B4

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Tax advisers should obtain ROS filing receipts and account statements for every period, reconcile original/amended returns to the ledger and document amendment causes and settlement.

### TAX-003 — HIGH

**Conclusion:** PAYE returns and payments agree at EUR 612,000 and the 35-person count is corroborated by the updated reconciliation. The annual tie-out does not resolve the EUR 8,400 PAYE-control balance or contractor-status risk.

**Source fact:** The ROS-style return/payment pair and updated CSV carry matching liability/payment and headcount evidence.

**Analysis:** The annual PAYE cash tie-out is supported, but equality of annual totals is not a ledger reconciliation and does not explain the control balance.

**Why it matters:** A supported payroll tax tie-out narrows, but does not eliminate, workforce tax exposure.

**Transaction implication:** Use the tie-out as supporting disclosure; preserve tax indemnity for omitted workers, periods and classification matters.

**Confidence:** 85%

**Uncertainty/limitation:** The EUR 8,400 PAYE control balance and post-source periods require reconciliation.

**Recomputations:** `CALC-TAX-003`

**Supporting citations:**

- `EVD-TAX-003-01` — `SRC-0045` / page 1
- `EVD-TAX-003-02` — `SRC-0046` / page 1
- `EVD-TAX-003-03` — `SRC-0051` / row 2, column 2
- `EVD-TAX-003-04` — `SRC-0044` / Tax Ledger!B5

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Reconcile monthly payroll submissions, payslips, employee master, contractor payments and the PAYE control balance through the latest completion date.

### TAX-004 — MEDIUM

**Conclusion:** The supplied invoice sample is internally arithmetical and its gross total reconciles to the register at EUR 34,440; tax clearance is shown as current through 2024-09-30. These are positive controls, not proof of full-period tax completeness.

**Source fact:** Each sampled invoice's net plus VAT equals gross, the invoice gross values tie to the register, and a separate clearance certificate states its validity date.

**Analysis:** The checks support the sampled documents and clearance status only; they do not override unresolved VAT, PAYE or corporation-tax control balances.

**Why it matters:** Balanced reporting distinguishes verified positive controls from broader adverse reconciliation findings.

**Transaction implication:** Retain these items as supporting disclosure while preserving the tax covenant, warranties and completion-date reconciliations for open balances.

**Confidence:** 85%

**Uncertainty/limitation:** Sample coverage and completion-date clearance remain limited.

**Recomputations:** `CALC-TAX-004`

**Supporting citations:**

- `EVD-TAX-004-01` — `SRC-0038` / page 1
- `EVD-TAX-004-02` — `SRC-0039` / page 1
- `EVD-TAX-004-03` — `SRC-0047` / Invoice Control!E6
- `EVD-TAX-004-04` — `SRC-0048` / page 1

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Extend the invoice-to-ledger/return test across a representative period and obtain fresh tax-clearance confirmation immediately before completion.

## Coverage and explicit limitations

| Topic | Status | Linked issues |
|---|---|---|
| vat_returns_xero_original_amended | analysed | TAX-001 |
| vat_charges_payments | analysed | TAX-001 |
| paye_returns_payments | analysed | TAX-003 |
| corporation_tax_returns_payments_charges_refunds | limitation | None |
| annual_computations_trial_balances | limitation | None |
| invoice_samples | analysed | TAX-004 |
| tax_clearance | analysed | TAX-004 |
| original_vs_rev2_responses | analysed | TAX-001 |

## General limitations

- No formal Irish legal or tax opinion is provided.
- Unreadable sources remain unresolved; reviewed visual evidence is limited to its recorded transcription and citation.
- Topics marked limitation had insufficient source evidence for an adverse conclusion.
