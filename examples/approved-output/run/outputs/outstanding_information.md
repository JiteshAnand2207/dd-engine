# Outstanding information and transaction conditions

Run ID: `20260901T040928457675Z-dede88eb959c`

## Management response status

No management response was used for this synthetic report. Both rounds were answered by a Phase 10 synthetic test operator so that the analytical pipeline could be exercised; those answers are assumptions or explicit non-availability statements, not management evidence.

## Go/no-go and pre-completion conditions

1. Obtain the approved restructuring plan, invoice/payroll detail, implementation dates and evidence of cessation; classify each cost as recurring or exceptional and rebuild the bridge.
2. Lock an account-level NWC definition, agree treatment of other debtors/prepayments, recompute a monthly twelve-month peg and attach the validated workbook to the transaction documents.
3. Obtain dated lender statements, HP payoff schedules, security/covenant details, the director settlement agreement and bank evidence distinguishing unrestricted from restricted cash.
4. Confirm ultimate parent, billing entities, VAT numbers, cross-defaults and renewal dates for every group member, then rerun concentration on collected revenue and gross profit.
5. Confirm renewal, termination, pricing, consent and service status for each top exposure and refresh concentration on collected revenue and gross profit.
6. Counsel should confirm the contemplated transaction triggers the clause, prepare a contract-by-contract consent matrix and obtain unconditional written consent before completion.
7. Map every contractor to deliverables and signed terms, obtain confirmatory assignments and verify moral-rights, confidentiality and third-party-code terms.
8. Commission an independent penetration test and witnessed restore/DR test; agree contractual RTO/RPO, remediate critical findings and deliver the final reports before completion.
9. Move the workbook to least-privilege access, identify recipients, assess lawful purpose and necessity, replace it with a minimized/redacted version, document retention/deletion, and notify privacy counsel if required.
10. Tax advisers should obtain ROS filing receipts and account statements for every period, reconcile original/amended returns to the ledger and document amendment causes and settlement.
11. Obtain the filed Form CT1/supporting computation, assessment, general-ledger tax accounts and adviser bridge explaining every difference between computation, TB, return, charge, payment and refund.

## Open evidence gaps

### GAP-CONTRACT-AMENDMENT-CONTROL - CRITICAL

- Information required: The register links original agreements and amendments in candidate version families VER-0001, VER-0002. For each family, which documents are executed and operative, are any side letters or later amendments missing, and which provisions control consent, liability, termination and pricing?
- Why absent: Agreement supersession is candidate-only and not established as source truth.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: go_no_go, transaction_structure, price
- Follow-up: The register links original agreements and amendments in candidate version families VER-0001, VER-0002. For each family, which documents are executed and operative, are any side letters or later amendments missing, and which provisions control consent, liability, termination and pricing?

### GAP-CONTRACT-CONSENTS - CRITICAL

- Information required: The room states that at least one customer-consent review is outstanding or a consent has not been requested. Which contracts, amendments, leases, debt documents or licences require notice or consent for the contemplated transaction, what is the legal/commercial basis, and what is the owner and timetable for obtaining each consent?
- Why absent: Extracted vendor evidence says a material consent review is incomplete or not requested.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: go_no_go, transaction_structure, closing_conditions
- Follow-up: The room states that at least one customer-consent review is outstanding or a consent has not been requested. Which contracts, amendments, leases, debt documents or licences require notice or consent for the contemplated transaction, what is the legal/commercial basis, and what is the owner and timetable for obtaining each consent?

### GAP-CUSTOMER-GROUP-IDENTITIES - CRITICAL

- Information required: Observed customer names may represent related entities: Client Complaint Glencree Health Systems Limited, Client Complaint Larkspur Transit Analytics Limited, Harbourlight Between Larkspur Transit Analytics Limited, Harbourlight Stores Limited, Mosaic North Retail Limited, Mosaic South Trading Limited, Synthetic Holder Larkspur Transit Analytics Limited, Synthetic Insured Larkspur Transit Analytics Limited. Which names share a parent or common control, what is the ultimate group, and should exposure and revenue concentration be aggregated?
- Why absent: Multiple observed customer names share a distinctive root but ownership is not evidenced.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: go_no_go, price, customer_concentration
- Follow-up: Observed customer names may represent related entities: Client Complaint Glencree Health Systems Limited, Client Complaint Larkspur Transit Analytics Limited, Harbourlight Between Larkspur Transit Analytics Limited, Harbourlight Stores Limited, Mosaic North Retail Limited, Mosaic South Trading Limited, Synthetic Holder Larkspur Transit Analytics Limited, Synthetic Insured Larkspur Transit Analytics Limited. Which names share a parent or common control, what is the ultimate group, and should exposure and revenue concentration be aggregated?

### GAP-DEBT-HP-COMPLETENESS - CRITICAL

- Information required: The room contains debt/HP documents still pending visual review and evidence that some HP or director balances may be excluded from loan summaries. Please provide a complete lender-by-lender debt and debt-like schedule, including HP, related-party balances, security, covenants, repayment dates and change-of-control requirements, and identify the controlling source for each balance.
- Why absent: Debt evidence is partly visual-only and submitted schedules state exclusions.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: price, net_debt, transaction_structure, go_no_go
- Follow-up: The room contains debt/HP documents still pending visual review and evidence that some HP or director balances may be excluded from loan summaries. Please provide a complete lender-by-lender debt and debt-like schedule, including HP, related-party balances, security, covenants, repayment dates and change-of-control requirements, and identify the controlling source for each balance.

### GAP-EXPLICIT-CALCULATION-CONTRADICTION - CRITICAL

- Information required: A source explicitly flags an incorrect, non-tying or unreconciled calculation. What is the correct treatment and amount, who approved it, and can you provide the controlled replacement schedule without overwriting the submitted source?
- Why absent: Extracted evidence explicitly describes a submitted calculation as incorrect or non-tying.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: price, working_capital_mechanism, go_no_go
- Follow-up: A source explicitly flags an incorrect, non-tying or unreconciled calculation. What is the correct treatment and amount, who approved it, and can you provide the controlled replacement schedule without overwriting the submitted source?

### GAP-EXTRACTION-SRC-0051 - HIGH

- Information required: Readable, source-verifiable content from Legal/Legacy/Unreadable_Policy_Archive.pdf
- Why absent: Extraction status is failed.; Failure: invalid PDF: EOF marker not found; Limitation: source could not safely reach a document parser
- Decision affected: scope, diligence_priority, go_no_go
- Follow-up: Provide a readable replacement or document explicitly that the source cannot be obtained.

### GAP-MISSING-CROSS-REFERENCE - CRITICAL

- Information required: Room responses refer to legal 2.1, but the corresponding location is absent or empty. Which documents were meant, and can you provide them or confirm explicitly that they do not exist?
- Why absent: Extracted answers point to a location with no registered document.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: scope, go_no_go, price, transaction_structure
- Follow-up: Room responses refer to legal 2.1, but the corresponding location is absent or empty. Which documents were meant, and can you provide them or confirm explicitly that they do not exist?

### GAP-PROPERTY-DOCUMENT-COVERAGE - HIGH

- Information required: Material property documents remain image-only pending vision review: SRC-0057 (Legal/Property/Property_Purchase_Contract_Scanned.pdf); SRC-0058 (Legal/Property/Property_Sale_Contract_Scanned.pdf). Which properties are owned, sold or leased, which are in the transaction perimeter, and can you provide searchable executed copies plus any lender/landlord consents?
- Why absent: Property source content is not yet deterministically readable.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: scope, transaction_structure, closing_conditions
- Follow-up: Material property documents remain image-only pending vision review: SRC-0057 (Legal/Property/Property_Purchase_Contract_Scanned.pdf); SRC-0058 (Legal/Property/Property_Sale_Contract_Scanned.pdf). Which properties are owned, sold or leased, which are in the transaction perimeter, and can you provide searchable executed copies plus any lender/landlord consents?

### GAP-R1-PRICE-STRUCTURE - CRITICAL

- Information required: What headline price or valuation reference should the diligence test, and what cash, debt, debt-like, working-capital, earn-out, rollover or other consideration assumptions are currently proposed? Please distinguish fixed terms from open negotiating positions.
- Why absent: No committee price or consideration mechanics are stored in the observed evidence.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: price, transaction_structure, negotiating_terms
- Follow-up: What headline price or valuation reference should the diligence test, and what cash, debt, debt-like, working-capital, earn-out, rollover or other consideration assumptions are currently proposed? Please distinguish fixed terms from open negotiating positions.

### GAP-R1-SCOPE-MATERIALITY - HIGH

- Information required: What diligence cut-off date, materiality thresholds, forecast horizon and scope exclusions should apply, including any topics already covered by another adviser?
- Why absent: No deal-specific cut-off, materiality threshold or scope exclusion is stored.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: scope, diligence_priority, go_no_go
- Follow-up: What diligence cut-off date, materiality thresholds, forecast horizon and scope exclusions should apply, including any topics already covered by another adviser?

### GAP-TAX-AMENDMENT-STATUS - HIGH

- Information required: The observed tax evidence includes amended/versioned returns or a late amendment entry. Which return is the filed controlling version, what caused each amendment, and have all resulting charges, interest and payments been fully settled?
- Why absent: Versioned/amended tax evidence does not itself establish filing and settlement status.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: price, tax_indemnity, escrow, go_no_go
- Follow-up: The observed tax evidence includes amended/versioned returns or a late amendment entry. Which return is the filed controlling version, what caused each amendment, and have all resulting charges, interest and payments been fully settled?

### GAP-UNREADABLE-SOURCES - CRITICAL

- Information required: The following registered source could not be read: SRC-0051 (Legal/Legacy/Unreadable_Policy_Archive.pdf). What does each document cover, is it current or operative, and can you provide a readable original or replacement?
- Why absent: 1 registered source(s) failed extraction.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: scope, go_no_go, transaction_structure
- Follow-up: The following registered source could not be read: SRC-0051 (Legal/Legacy/Unreadable_Policy_Archive.pdf). What does each document cover, is it current or operative, and can you provide a readable original or replacement?

### GAP-UNSUPPORTED-FINANCIAL-ADJUSTMENT - CRITICAL

- Information required: The observed financial evidence includes a material adjustment whose support is stated to be absent or still to follow. What is the amount and rationale, which costs are non-recurring, and where are the invoices, approvals and implementation plan?
- Why absent: A source asserts an adjustment but also says its supporting evidence is absent.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: price, go_no_go, earnings_quality
- Follow-up: The observed financial evidence includes a material adjustment whose support is stated to be absent or still to follow. What is the amount and rationale, which costs are non-recurring, and where are the invoices, approvals and implementation plan?

### GAP-VISION-SRC-0007 - HIGH

- Information required: Visual meaning of Financial/Loan Letters/Phone_Photo_Innovation_Loan.jpg
- Why absent: 1 local vision task(s) remain pending with null model_result.; Deterministic extraction captured metadata/rendering but did not interpret visual content.
- Decision affected: scope, diligence_priority
- Follow-up: Complete an authenticated local vision review and retain its result with the source checksum and locator.

### GAP-VISION-SRC-0008 - HIGH

- Information required: Visual meaning of Financial/Loan Letters/Phone_Photo_Term_Loan.jpg
- Why absent: 1 local vision task(s) remain pending with null model_result.; Deterministic extraction captured metadata/rendering but did not interpret visual content.
- Decision affected: scope, diligence_priority
- Follow-up: Complete an authenticated local vision review and retain its result with the source checksum and locator.

### GAP-VISION-SRC-0009 - HIGH

- Information required: Visual meaning of Financial/Loan Letters/Scanned_Loan_and_HP_Pack.pdf
- Why absent: 3 local vision task(s) remain pending with null model_result.; Deterministic extraction captured metadata/rendering but did not interpret visual content.
- Decision affected: scope, diligence_priority
- Follow-up: Complete an authenticated local vision review and retain its result with the source checksum and locator.

### GAP-VISION-SRC-0030 - HIGH

- Information required: Visual meaning of Legal/Corporate/CRO_Search_Screenshot.png
- Why absent: 1 local vision task(s) remain pending with null model_result.; Deterministic extraction captured metadata/rendering but did not interpret visual content.
- Decision affected: scope, diligence_priority
- Follow-up: Complete an authenticated local vision review and retain its result with the source checksum and locator.

### GAP-VISION-SRC-0057 - HIGH

- Information required: Visual meaning of Legal/Property/Property_Purchase_Contract_Scanned.pdf
- Why absent: 3 local vision task(s) remain pending with null model_result.; Deterministic extraction captured metadata/rendering but did not interpret visual content.
- Decision affected: scope, diligence_priority
- Follow-up: Complete an authenticated local vision review and retain its result with the source checksum and locator.

### GAP-VISION-SRC-0058 - HIGH

- Information required: Visual meaning of Legal/Property/Property_Sale_Contract_Scanned.pdf
- Why absent: 3 local vision task(s) remain pending with null model_result.; Deterministic extraction captured metadata/rendering but did not interpret visual content.
- Decision affected: scope, diligence_priority
- Follow-up: Complete an authenticated local vision review and retain its result with the source checksum and locator.

### GAP-VISION-SRC-0092 - HIGH

- Information required: Visual meaning of zip://Legal/Updated_Responses.zip!/Updated Responses/CRO_Search_Refresh.png
- Why absent: 1 local vision task(s) remain pending with null model_result.; Deterministic extraction captured metadata/rendering but did not interpret visual content.
- Decision affected: scope, diligence_priority
- Follow-up: Complete an authenticated local vision review and retain its result with the source checksum and locator.

### GAP-WORKFORCE-COUNT-RECONCILIATION - HIGH

- Information required: The extracted workforce/PAYE evidence contains different stated employee or contractor counts. Please reconcile the population by cut-off date, employment status, legal entity and client allocation, and identify the authoritative roster.
- Why absent: Distinct numeric workforce counts appear in observed records.; The reply explicitly says that requested evidence or confirmation is absent or that the matter remains open.
- Decision affected: price, go_no_go, workforce_liabilities
- Follow-up: The extracted workforce/PAYE evidence contains different stated employee or contractor counts. Please reconcile the population by cut-off date, employment status, legal entity and client allocation, and identify the authoritative roster.

### GAP-P9-IP-DATA - HIGH

- Information required: Complete IP chain-of-title, software licensing, privacy and data-processing evidence.
- Why absent: Only sample employment IP wording and provider-level data clauses were identified; no complete IP register, contractor assignment set or DPA inventory was supplied.
- Decision affected: go_no_go, warranty, indemnity
- Follow-up: Provide the IP/software register, employee and contractor assignments, open-source scan, privacy notices, Article 30-style records, DPAs, transfer assessments and incident log.

### GAP-P9-KEY-PERSON-CONTROLS - HIGH

- Information required: Management succession, delegation, capacity, KPI controls and key-person coverage.
- Why absent: Board minutes and provider contracts were supplied, but no organization chart, succession plan, capacity model or control matrix was identified.
- Decision affected: go_no_go, earn_out, retention
- Follow-up: Provide organization/capacity plans, decision rights, management KPI packs, succession and retention proposals, and evidence of control operation.

### GAP-P9-IT-CONTROLS - HIGH

- Information required: User access reviews, privileged-access inventory, vulnerability management, software/IP licensing, data maps, GDPR evidence and complete incident history.
- Why absent: The room provides administrator-MFA narrative and provider contracts but no complete technical-control evidence set.
- Decision affected: go_no_go, warranty, indemnity, closing_condition
- Follow-up: Provide IAM exports and reviews, security policies/evidence, asset/software inventories, licences, vulnerability and patch reports, DPAs/data maps and the incident register.

## What was asked of management

| ID | Priority | Question | Response provenance/status | Supporting source IDs |
|---|---|---|---|---|
| INT-R1-001 | critical | The following registered source could not be read: SRC-0051 (Legal/Legacy/Unreadable_Policy_Archive.pdf). What does each document cover, is it current or operative, and can you provide a readable original or replacement? | Phase 11 synthetic test operator (not management); engine status open | `SRC-0051` |
| INT-R1-002 | critical | The room contains debt/HP documents still pending visual review and evidence that some HP or director balances may be excluded from loan summaries. Please provide a complete lender-by-lender debt and debt-like schedule, including HP, related-party balances, security, covenants, repayment dates and change-of-control requirements, and identify the controlling source for each balance. | Phase 11 synthetic test operator (not management); engine status open | `SRC-0010`, `SRC-0011`, `SRC-0017`, `SRC-0007`, `SRC-0008`, `SRC-0009` |
| INT-R1-003 | critical | What legal entities, businesses, assets and liabilities are inside and outside the proposed transaction perimeter, and is the contemplated deal a share purchase, asset purchase or another structure? | Phase 11 synthetic test operator (not management); engine status closed | None |
| INT-R1-004 | critical | What headline price or valuation reference should the diligence test, and what cash, debt, debt-like, working-capital, earn-out, rollover or other consideration assumptions are currently proposed? Please distinguish fixed terms from open negotiating positions. | Phase 11 synthetic test operator (not management); engine status open | None |
| INT-R1-005 | critical | Room responses refer to legal 2.1, but the corresponding location is absent or empty. Which documents were meant, and can you provide them or confirm explicitly that they do not exist? | Phase 11 synthetic test operator (not management); engine status open | `SRC-0004`, `SRC-0052` |
| INT-R1-006 | critical | The observed financial evidence includes a material adjustment whose support is stated to be absent or still to follow. What is the amount and rationale, which costs are non-recurring, and where are the invoices, approvals and implementation plan? | Phase 11 synthetic test operator (not management); engine status open | `SRC-0004`, `SRC-0012` |
| INT-R1-007 | critical | A source explicitly flags an incorrect, non-tying or unreconciled calculation. What is the correct treatment and amount, who approved it, and can you provide the controlled replacement schedule without overwriting the submitted source? | Phase 11 synthetic test operator (not management); engine status open | `SRC-0027` |
| INT-R1-008 | critical | The room states that at least one customer-consent review is outstanding or a consent has not been requested. Which contracts, amendments, leases, debt documents or licences require notice or consent for the contemplated transaction, what is the legal/commercial basis, and what is the owner and timetable for obtaining each consent? | Phase 11 synthetic test operator (not management); engine status open | `SRC-0052`, `SRC-0093`, `SRC-0099` |
| INT-R1-009 | high | The observed tax evidence includes amended/versioned returns or a late amendment entry. Which return is the filed controlling version, what caused each amendment, and have all resulting charges, interest and payments been fully settled? | Phase 11 synthetic test operator (not management); engine status open | `SRC-0071`, `SRC-0078`, `SRC-0079`, `SRC-0084`, `SRC-0083` |
| INT-R1-010 | high | What is the investment thesis, which value drivers must be proven, and which specific findings would be deal-breakers or require a price or structure change? | Phase 11 synthetic test operator (not management); engine status closed | None |
| INT-R1-011 | high | What diligence cut-off date, materiality thresholds, forecast horizon and scope exclusions should apply, including any topics already covered by another adviser? | Phase 11 synthetic test operator (not management); engine status open | None |
| INT-R2-001 | critical | Observed customer names may represent related entities: Client Complaint Glencree Health Systems Limited, Client Complaint Larkspur Transit Analytics Limited, Harbourlight Between Larkspur Transit Analytics Limited, Harbourlight Stores Limited, Mosaic North Retail Limited, Mosaic South Trading Limited, Synthetic Holder Larkspur Transit Analytics Limited, Synthetic Insured Larkspur Transit Analytics Limited. Which names share a parent or common control, what is the ultimate group, and should exposure and revenue concentration be aggregated? | Phase 11 synthetic test operator (not management); engine status open | `SRC-0002`, `SRC-0037`, `SRC-0040`, `SRC-0041`, `SRC-0048`, `SRC-0053` |
| INT-R2-002 | critical | The register links original agreements and amendments in candidate version families VER-0001, VER-0002. For each family, which documents are executed and operative, are any side letters or later amendments missing, and which provisions control consent, liability, termination and pricing? | Phase 11 synthetic test operator (not management); engine status open | `SRC-0037`, `SRC-0034`, `SRC-0039`, `SRC-0036` |
| INT-R2-003 | high | The extracted workforce/PAYE evidence contains different stated employee or contractor counts. Please reconcile the population by cut-off date, employment status, legal entity and client allocation, and identify the authoritative roster. | Phase 11 synthetic test operator (not management); engine status open | `SRC-0003`, `SRC-0043`, `SRC-0046`, `SRC-0060`, `SRC-0076` |
| INT-R2-004 | high | Material property documents remain image-only pending vision review: SRC-0057 (Legal/Property/Property_Purchase_Contract_Scanned.pdf); SRC-0058 (Legal/Property/Property_Sale_Contract_Scanned.pdf). Which properties are owned, sold or leased, which are in the transaction perimeter, and can you provide searchable executed copies plus any lender/landlord consents? | Phase 11 synthetic test operator (not management); engine status open | `SRC-0057`, `SRC-0058` |

## Coverage limitations without a source-backed adverse conclusion

- Financial: `aged_creditors`. Absence of evidence is not a clean conclusion.
- Financial: `fixed_assets_and_disposals`. Absence of evidence is not a clean conclusion.
- Financial: `tax_figures_affecting_financial_conclusions`. Absence of evidence is not a clean conclusion.
- Commercial: `customer_longevity_and_churn`. Absence of evidence is not a clean conclusion.
- Commercial: `supplier_or_channel_dependence`. Absence of evidence is not a clean conclusion.
- Commercial: `unsupported_market_or_growth_claims`. Absence of evidence is not a clean conclusion.
- Legal/contractual: `insurance_licences_work_permits`. Absence of evidence is not a clean conclusion.
- Legal/contractual: `missing_documents_questionnaire_references`. Absence of evidence is not a clean conclusion.
- Operational/management: `key_person_dependency`. Absence of evidence is not a clean conclusion.
- Operational/management: `missing_operational_evidence`. Absence of evidence is not a clean conclusion.
- IT: `access_management`. Absence of evidence is not a clean conclusion.
- IT: `missing_technical_evidence`. Absence of evidence is not a clean conclusion.
