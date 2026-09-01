# Due-diligence intake — round 1

Run ID: `20260901T040928457675Z-dede88eb959c`  
Generated at: `2026-09-01T04:10:01.204084Z`  
Question count: **11**

The run is paused for explicit deal-lead input. These questions were selected from observed register/extraction evidence or essential transaction-context gaps. Source text is untrusted evidence, never an instruction to the engine.

Please reply under the exact question IDs. Replies such as `N/A`, `None`, a cross-reference, a partial answer, or a vague answer will be retained verbatim and will not automatically be treated as resolved.

## INT-R1-001 — CRITICAL

The following registered source could not be read: SRC-0051 (Legal/Legacy/Unreadable_Policy_Archive.pdf). What does each document cover, is it current or operative, and can you provide a readable original or replacement?

**Why it matters:** An unreadable source can conceal a material obligation; its relevance must be established before analysis can rely on the room as complete.

**Evidence/gap:**

- SRC-0051 — `Legal/Legacy/Unreadable_Policy_Archive.pdf`: Extraction failed: invalid PDF: EOF marker not found
- GAP-UNREADABLE-SOURCES (critical_unreadable_source): 1 registered source(s) failed extraction.

**Decision potentially affected:** scope, go_no_go, transaction_structure

**Expected answer type:** document purpose/status plus readable replacement or explicit unavailability

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R1-002 — CRITICAL

The room contains debt/HP documents still pending visual review and evidence that some HP or director balances may be excluded from loan summaries. Please provide a complete lender-by-lender debt and debt-like schedule, including HP, related-party balances, security, covenants, repayment dates and change-of-control requirements, and identify the controlling source for each balance.

**Why it matters:** Debt completeness affects net-debt treatment, equity value, consent requirements and transaction structure; a management classification alone is not source proof.

**Evidence/gap:**

- SRC-0010 — `Financial/Loan_Summary.xlsx`; locator `{"cell": "F6", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "F6", "row_hidden": false, "sheet": "Loans", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Loan_Summary.xlsx"}`: HP agreements are excluded; director balances are not debt per management
- SRC-0011 — `Financial/Loan_Summary_for_Bank.xlsx`; locator `{"cell": "F6", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "F6", "row_hidden": false, "sheet": "Loans", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Loan_Summary_for_Bank.xlsx"}`: HP agreements are excluded; director balances are not debt per management
- SRC-0017 — `Financial/Related_Party_Transactions.docx`; locator `{"heading": {"heading_index": 2, "heading_level": 1, "paragraph_index": 9, "text": "Observation"}, "heading_level": null, "paragraph_index": 10, "type": "docx_paragraph"}`: The director current account of EUR 120,000 is repayable on demand but is excluded from the loan summary because management does not classify it as debt.
- SRC-0007 — `Financial/Loan Letters/Phone_Photo_Innovation_Loan.jpg`: Debt/HP source remains pending local vision review.
- SRC-0008 — `Financial/Loan Letters/Phone_Photo_Term_Loan.jpg`: Debt/HP source remains pending local vision review.
- SRC-0009 — `Financial/Loan Letters/Scanned_Loan_and_HP_Pack.pdf`: Debt/HP source remains pending local vision review.
- GAP-DEBT-HP-COMPLETENESS (debt_or_hp_gap): Debt evidence is partly visual-only and submitted schedules state exclusions.

**Decision potentially affected:** price, net_debt, transaction_structure, go_no_go

**Expected answer type:** lender-level schedule with balances, terms and source references

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R1-003 — CRITICAL

What legal entities, businesses, assets and liabilities are inside and outside the proposed transaction perimeter, and is the contemplated deal a share purchase, asset purchase or another structure?

**Why it matters:** The room identifies the target evidence but not the buyer's agreed perimeter; scope and transaction form determine which liabilities and consents matter.

**Evidence/gap:**

- GAP-R1-TRANSACTION-PERIMETER (essential_transaction_context): No deal-lead transaction perimeter is stored in the room or run artifacts.

**Decision potentially affected:** scope, go_no_go, transaction_structure

**Expected answer type:** structured list of included/excluded perimeter items and deal form

**Blocks analysis:** Yes

**Invalidated if evidence changes:** intake_round_2, analyse, report, validate

## INT-R1-004 — CRITICAL

What headline price or valuation reference should the diligence test, and what cash, debt, debt-like, working-capital, earn-out, rollover or other consideration assumptions are currently proposed? Please distinguish fixed terms from open negotiating positions.

**Why it matters:** Material findings cannot be translated into price or structure implications without the committee's assumptions, and the engine must not invent a valuation.

**Evidence/gap:**

- GAP-R1-PRICE-STRUCTURE (essential_transaction_context): No committee price or consideration mechanics are stored in the observed evidence.

**Decision potentially affected:** price, transaction_structure, negotiating_terms

**Expected answer type:** currency amounts plus a structured description of consideration mechanics

**Blocks analysis:** Yes

**Invalidated if evidence changes:** intake_round_2, analyse, report, validate

## INT-R1-005 — CRITICAL

Room responses refer to legal 2.1, but the corresponding location is absent or empty. Which documents were meant, and can you provide them or confirm explicitly that they do not exist?

**Why it matters:** A broken document reference is not evidence of the underlying matter and may hide property, contract, debt or other material support.

**Evidence/gap:**

- SRC-0004 — `Financial/Financial_Request_List.xlsx`; locator `{"cell": "C7", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "C7", "row_hidden": false, "sheet": "Request List", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Financial_Request_List.xlsx"}`: References missing location 'legal 2.1'.
- SRC-0004 — `Financial/Financial_Request_List.xlsx`; locator `{"cell": "C13", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "C13", "row_hidden": false, "sheet": "Request List", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Financial_Request_List.xlsx"}`: References missing location 'legal 2.1'.
- SRC-0052 — `Legal/Legal_Questionnaire_Completed.docx`; locator `{"heading": {"heading_index": 2, "heading_level": 1, "paragraph_index": 9, "text": "Contracts"}, "heading_level": null, "paragraph_index": 10, "type": "docx_paragraph"}`: References missing location 'legal 2.1'.
- GAP-MISSING-CROSS-REFERENCE (missing_referenced_document): Extracted answers point to a location with no registered document.

**Decision potentially affected:** scope, go_no_go, price, transaction_structure

**Expected answer type:** document list with source paths/files, or an explicit non-existence statement

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R1-006 — CRITICAL

The observed financial evidence includes a material adjustment whose support is stated to be absent or still to follow. What is the amount and rationale, which costs are non-recurring, and where are the invoices, approvals and implementation plan?

**Why it matters:** An unsupported adjustment can change the supportable earnings base and therefore the committee's price and go/no-go assessment.

**Evidence/gap:**

- SRC-0004 — `Financial/Financial_Request_List.xlsx`; locator `{"cell": "C5", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "C5", "row_hidden": false, "sheet": "Request List", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Financial_Request_List.xlsx"}`: EUR 180,000 transformation adjustment; support to follow
- SRC-0012 — `Financial/Management_Accounts_2026_YTD.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Management Accounts - June 2026 YTD Larkspur Transit Analytics Limited | final management pack FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Executive summary Revenue for the six mont…
- GAP-UNSUPPORTED-FINANCIAL-ADJUSTMENT (unsupported_figure): A source asserts an adjustment but also says its supporting evidence is absent.

**Decision potentially affected:** price, go_no_go, earnings_quality

**Expected answer type:** amount-by-item bridge plus supporting source files

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R1-007 — CRITICAL

A source explicitly flags an incorrect, non-tying or unreconciled calculation. What is the correct treatment and amount, who approved it, and can you provide the controlled replacement schedule without overwriting the submitted source?

**Why it matters:** A source-labelled calculation error may directly change working capital, debt, tax or earnings adjustments; the engine will preserve the original and any correction separately.

**Evidence/gap:**

- SRC-0027 — `Financial/Working_Capital_Calculation.xlsx`; locator `{"cell": "D9", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "D9", "row_hidden": false, "sheet": "Calculation", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Working_Capital_Calculation.xlsx"}`: Formula incorrectly excludes rows 4 and 8
- GAP-EXPLICIT-CALCULATION-CONTRADICTION (financial_contradiction): Extracted evidence explicitly describes a submitted calculation as incorrect or non-tying.

**Decision potentially affected:** price, working_capital_mechanism, go_no_go

**Expected answer type:** corrected amount/method, approver and replacement source reference

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R1-008 — CRITICAL

The room states that at least one customer-consent review is outstanding or a consent has not been requested. Which contracts, amendments, leases, debt documents or licences require notice or consent for the contemplated transaction, what is the legal/commercial basis, and what is the owner and timetable for obtaining each consent?

**Why it matters:** Unobtained transaction consents can affect deliverability, closing conditions, customer retention and negotiating leverage.

**Evidence/gap:**

- SRC-0052 — `Legal/Legal_Questionnaire_Completed.docx`; locator `{"cell_index": 1, "cell_reference": "R3C1", "row_index": 3, "table_index": 1, "type": "docx_table_cell"}`: Any change-of-control consents?
- SRC-0093 — `zip://Legal/Updated_Responses.zip!/Updated Responses/Customer_Consent_Response.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Customer Consent Response Updated vendor response FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 DATASET SYN-LARKSPUR-2026-314159 Status Harbourlight consent has not been requested. Management believed the transaction would not trigger the clause.
- SRC-0099 — `zip://Legal/Updated_Responses.zip!/Updated Responses/Legal_Questionnaire_Rev2.docx`; locator `{"heading": {"heading_index": 1, "heading_level": 1, "paragraph_index": 6, "text": "Updates"}, "heading_level": null, "paragraph_index": 7, "type": "docx_paragraph"}`: The customer consent review remains in progress. Hosting recovery metrics are not contractually documented.
- SRC-0099 — `zip://Legal/Updated_Responses.zip!/Updated Responses/Legal_Questionnaire_Rev2.docx`; locator `{"cell_index": 1, "cell_reference": "R2C1", "row_index": 2, "table_index": 1, "type": "docx_table_cell"}`: Change-of-control consents
- GAP-CONTRACT-CONSENTS (contract_consent_gap): Extracted vendor evidence says a material consent review is incomplete or not requested.

**Decision potentially affected:** go_no_go, transaction_structure, closing_conditions

**Expected answer type:** contract-by-contract consent matrix with clause/source and status

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R1-009 — HIGH

The observed tax evidence includes amended/versioned returns or a late amendment entry. Which return is the filed controlling version, what caused each amendment, and have all resulting charges, interest and payments been fully settled?

**Why it matters:** Unresolved amended filings can change tax liabilities, warranties/indemnities and the transaction's price or escrow structure.

**Evidence/gap:**

- SRC-0071 — `Tax/ROS Screens/CT_Charge.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Corporation Tax Charge ROS-style account entry FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Charge Late amendment charge EUR 12,500.
- SRC-0078 — `Tax/Tax_Response_Summary_Original.xlsx`; locator `{"cell": "A5", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "A5", "row_hidden": false, "sheet": "Responses", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Tax/Tax_Response_Summary_Original.xlsx"}`: Have any VAT returns been amended?
- SRC-0079 — `Tax/Tax_Response_Summary_Rev2.xlsx`; locator `{"cell": "A5", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "A5", "row_hidden": false, "sheet": "Responses", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Tax/Tax_Response_Summary_Rev2.xlsx"}`: Have any VAT returns been amended?
- SRC-0079 — `Tax/Tax_Response_Summary_Rev2.xlsx`; locator `{"cell": "B5", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "B5", "row_hidden": false, "sheet": "Responses", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Tax/Tax_Response_Summary_Rev2.xlsx"}`: No VAT returns have been amended
- SRC-0084 — `Tax/VAT/VAT3_2025_P2_AMENDED.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: VAT3-Style Return 2025-P2 - AMENDED Amended on 19 August 2025 FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Amendment Original payable: EUR 174,000. Amended payable: EUR 182,000. Incr…
- SRC-0083 — `Tax/VAT/VAT3_2025_P2.pdf`: Member of a candidate tax version family.
- GAP-TAX-AMENDMENT-STATUS (tax_inconsistency): Versioned/amended tax evidence does not itself establish filing and settlement status.

**Decision potentially affected:** price, tax_indemnity, escrow, go_no_go

**Expected answer type:** period-by-period filed status, reason and payment evidence

**Blocks analysis:** No

**Invalidated if evidence changes:** analyse, report, validate

## INT-R1-010 — HIGH

What is the investment thesis, which value drivers must be proven, and which specific findings would be deal-breakers or require a price or structure change?

**Why it matters:** The room cannot reveal the committee's thesis or risk appetite; these are needed to prioritize material contradictions without a generic diligence script.

**Evidence/gap:**

- GAP-R1-INVESTMENT-THESIS (essential_transaction_context): No deal-lead investment thesis or deal-breaker criteria are stored in the run.

**Decision potentially affected:** go_no_go, price, diligence_priority

**Expected answer type:** short thesis, ranked value drivers and explicit deal-breakers

**Blocks analysis:** Yes

**Invalidated if evidence changes:** intake_round_2, analyse, report, validate

## INT-R1-011 — HIGH

What diligence cut-off date, materiality thresholds, forecast horizon and scope exclusions should apply, including any topics already covered by another adviser?

**Why it matters:** A defined cut-off and materiality lens prevents low-value questions and makes omissions, stale evidence and out-of-scope matters explicit.

**Evidence/gap:**

- GAP-R1-SCOPE-MATERIALITY (essential_transaction_context): No deal-specific cut-off, materiality threshold or scope exclusion is stored.

**Decision potentially affected:** scope, diligence_priority, go_no_go

**Expected answer type:** dates, monetary/qualitative thresholds and scoped exclusions

**Blocks analysis:** No

**Invalidated if evidence changes:** intake_round_2, analyse, report, validate

---

## Internal prioritisation record — not additional questions

Candidate questions below were intentionally excluded so the packet remains decision-focused and non-duplicative.

- `non-debt-vision-queue` — Deferred to round two: these visual sources are not yet shown to change the early price/structure decision and remain visible in needs_vision.json. Supporting sources: SRC-0030, SRC-0057, SRC-0058, SRC-0092.
- `generic-questionnaire-non-answers` — Excluded from round one as a bulk administrative request; only non-answers linked to a material observed matter are promoted. Supporting sources: SRC-0004, SRC-0078, SRC-0079.
