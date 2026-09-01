# Tax analysis

Run ID: `20260901T040928457675Z-dede88eb959c`

This is decision-oriented commercial due diligence, not a document summary. Source facts are separated from analytical conclusions. No independent valuation is provided.

## Scope

Commercial due diligence in an Irish transaction context; this is not a formal Irish legal or tax opinion and specialist advisers must confirm conclusions used in transaction documents.

## Material findings

### TAX-001 — CRITICAL

**Conclusion:** The Rev2 tax response is demonstrably wrong: a 2025-P2 VAT amendment increased payable VAT by EUR 8,000, although Rev2 states that no VAT returns were amended. The tax trial balance also carries a EUR 182,000 VAT-control balance that the payment-status evidence does not reconcile.

**Source fact:** The original return reports EUR 174,000, the amended return reports EUR 182,000, and the ROS-style account says all listed charges were paid.

**Analysis:** Payment evidence for listed charges reduces one cash-exposure concern, but it does not clear or explain the ledger control balance. The current questionnaire answer is unreliable and requires a broader completeness check.

**Why it matters:** Incorrect tax responses undermine warranty disclosure and may conceal other amendments or process failures.

**Transaction implication:** Require corrected tax disclosures, a specific tax warranty covering amended filings and a tax covenant/indemnity for pre-close liabilities, interest and penalties.

**Confidence:** 85%

**Recomputations:** `CALC-TAX-001`

**Supporting citations:**

- `EVD-TAX-001-01` — `SRC-0083` / page 1
- `EVD-TAX-001-02` — `SRC-0084` / page 1
- `EVD-TAX-001-03` — `SRC-0079` / Responses!B5
- `EVD-TAX-001-04` — `SRC-0077` / page 1
- `EVD-TAX-001-05` — `SRC-0081` / Tax TB!B6

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Tax advisers should obtain ROS filing receipts and account statements for every period, reconcile original/amended returns to the ledger and document amendment causes and settlement.

### TAX-002 — CRITICAL

**Conclusion:** Net ROS cash of EUR 401,700 arithmetically equals the EUR 389,200 return plus EUR 12,500 late-amendment charge, but the return does not reconcile to the EUR 178,625 annual computation or EUR 348,200 trial-balance tax figure. This equality does not prove that the cited cash entries settled the cited assessment.

**Source fact:** Payments of EUR 420,000 less a EUR 18,300 refund equal the return plus charge; the computation and trial balance show different amounts.

**Analysis:** The equality is an arithmetic hypothesis only: the source set lacks assessment references, filing receipts and transaction-level linkage. A separate tax-payment confirmation elsewhere in the room also requires classification rather than being silently ignored.

**Why it matters:** An unexplained CT bridge affects tax warranties, normalized earnings and balance-sheet provisions.

**Transaction implication:** Do not adjust price for a presumed refund or liability without the bridge; require a tax covenant and retain escrow for unresolved pre-close CT exposures.

**Confidence:** 85%

**Uncertainty/limitation:** The source set does not establish why the computation, ledger and filed return differ or link the cash entries—including the separate payment confirmation—to a specific assessment. The additional unlinked payment is EUR 210,000.

**Recomputations:** `CALC-TAX-002`

**Supporting citations:**

- `EVD-TAX-002-01` — `SRC-0074` / page 1
- `EVD-TAX-002-02` — `SRC-0071` / page 1
- `EVD-TAX-002-03` — `SRC-0072` / page 1
- `EVD-TAX-002-04` — `SRC-0073` / page 1
- `EVD-TAX-002-05` — `SRC-0063` / page 1
- `EVD-TAX-002-06` — `SRC-0026` / Trial Balance!C16
- `EVD-TAX-002-07` — `SRC-0033` / page 1

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain the filed Form CT1/supporting computation, assessment, general-ledger tax accounts and adviser bridge explaining every difference between computation, TB, return, charge, payment and refund.

### TAX-003 — HIGH

**Conclusion:** PAYE returns and payments agree at EUR 1,584,000 and the 64-person count is corroborated by the updated reconciliation. The annual tie-out does not resolve the EUR 0 PAYE-control balance or contractor-status risk.

**Source fact:** The ROS-style return/payment pair and updated CSV carry matching liability/payment and headcount evidence.

**Analysis:** The annual PAYE cash tie-out is supported, but equality of annual totals is not a ledger reconciliation and does not explain the control balance.

**Why it matters:** A supported payroll tax tie-out narrows, but does not eliminate, workforce tax exposure.

**Transaction implication:** Use the tie-out as supporting disclosure; preserve tax indemnity for omitted workers, periods and classification matters.

**Confidence:** 85%

**Uncertainty/limitation:** The EUR 0 PAYE control balance and post-source periods require reconciliation.

**Recomputations:** `CALC-TAX-003`

**Supporting citations:**

- `EVD-TAX-003-01` — `SRC-0076` / page 1
- `EVD-TAX-003-02` — `SRC-0075` / page 1
- `EVD-TAX-003-03` — `SRC-0100` / row 2, column 2
- `EVD-TAX-003-04` — `SRC-0081` / Tax TB!B7

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Reconcile monthly payroll submissions, payslips, employee master, contractor payments and the PAYE control balance through the latest completion date.

### TAX-004 — MEDIUM

**Conclusion:** The supplied invoice sample is internally arithmetical and its gross total reconciles to the register at EUR 541,200; tax clearance is shown as current through 2027-04-30. These are positive controls, not proof of full-period tax completeness.

**Source fact:** Each sampled invoice's net plus VAT equals gross, the invoice gross values tie to the register, and a separate clearance certificate states its validity date.

**Analysis:** The checks support the sampled documents and clearance status only; they do not override unresolved VAT, PAYE or corporation-tax control balances.

**Why it matters:** Balanced reporting distinguishes verified positive controls from broader adverse reconciliation findings.

**Transaction implication:** Retain these items as supporting disclosure while preserving the tax covenant, warranties and completion-date reconciliations for open balances.

**Confidence:** 85%

**Uncertainty/limitation:** Sample coverage and completion-date clearance remain limited.

**Recomputations:** `CALC-TAX-004`

**Supporting citations:**

- `EVD-TAX-004-01` — `SRC-0064` / page 1
- `EVD-TAX-004-02` — `SRC-0065` / page 1
- `EVD-TAX-004-03` — `SRC-0066` / page 1
- `EVD-TAX-004-04` — `SRC-0067` / page 1
- `EVD-TAX-004-05` — `SRC-0068` / Register!E8
- `EVD-TAX-004-06` — `SRC-0070` / page 1

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Extend the invoice-to-ledger/return test across a representative period and obtain fresh tax-clearance confirmation immediately before completion.

## Coverage and explicit limitations

| Topic | Status | Linked issues |
|---|---|---|
| vat_returns_xero_original_amended | analysed | TAX-001 |
| vat_charges_payments | analysed | TAX-001 |
| paye_returns_payments | analysed | TAX-003 |
| corporation_tax_returns_payments_charges_refunds | analysed | TAX-002 |
| annual_computations_trial_balances | analysed | TAX-002 |
| invoice_samples | analysed | TAX-004 |
| tax_clearance | analysed | TAX-004 |
| original_vs_rev2_responses | analysed | TAX-001 |

## General limitations

- No formal Irish legal or tax opinion is provided.
- Visual property/CRO evidence and the unreadable legacy policy remain unresolved.
- Topics marked limitation had insufficient source evidence for an adverse conclusion.
