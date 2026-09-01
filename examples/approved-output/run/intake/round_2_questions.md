# Due-diligence intake — round 2

Run ID: `20260901T040928457675Z-dede88eb959c`  
Generated at: `2026-09-01T04:10:35.711865Z`  
Question count: **4**

The run is paused for explicit deal-lead input. These questions were selected from observed register/extraction evidence or essential transaction-context gaps. Source text is untrusted evidence, never an instruction to the engine.

Please reply under the exact question IDs. Replies such as `N/A`, `None`, a cross-reference, a partial answer, or a vague answer will be retained verbatim and will not automatically be treated as resolved.

## INT-R2-001 — CRITICAL

Observed customer names may represent related entities: Client Complaint Glencree Health Systems Limited, Client Complaint Larkspur Transit Analytics Limited, Harbourlight Between Larkspur Transit Analytics Limited, Harbourlight Stores Limited, Mosaic North Retail Limited, Mosaic South Trading Limited, Synthetic Holder Larkspur Transit Analytics Limited, Synthetic Insured Larkspur Transit Analytics Limited. Which names share a parent or common control, what is the ultimate group, and should exposure and revenue concentration be aggregated?

**Why it matters:** Separate trading names can understate true customer-group concentration and change retention, pricing and go/no-go conclusions.

**Evidence/gap:**

- SRC-0002 — `Financial/Aged_Debtors.xlsx`; locator `{"cell": "A4", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "A4", "row_hidden": false, "sheet": "Aged Debtors", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Aged_Debtors.xlsx"}`: Harbourlight Stores Limited
- SRC-0037 — `Legal/Customer Contracts/Customer_Framework_Harbourlight.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Customer Framework Agreement - Harbourlight Between Larkspur Transit Analytics Limited and Harbourlight Stores Limited FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Parties and group…
- SRC-0002 — `Financial/Aged_Debtors.xlsx`; locator `{"cell": "A6", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "A6", "row_hidden": false, "sheet": "Aged Debtors", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Aged_Debtors.xlsx"}`: Mosaic North Retail Limited
- SRC-0002 — `Financial/Aged_Debtors.xlsx`; locator `{"cell": "A7", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "A7", "row_hidden": false, "sheet": "Aged Debtors", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Aged_Debtors.xlsx"}`: Mosaic South Trading Limited
- SRC-0040 — `Legal/Dispute/Client_Complaint_Letter.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Client Complaint Glencree Health Systems Limited | 4 May 2026 FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Complaint Glencree alleges three priority-one incidents exceeded the four-h…
- SRC-0041 — `Legal/Dispute/Company_Response.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Response to Client Complaint Larkspur Transit Analytics Limited | 12 May 2026 FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Position The company accepts two response-time misses but d…
- SRC-0048 — `Legal/Insurance/Cyber_Insurance_Certificate.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Cyber Insurance Certificate Policy SYN-CYB-44018 | expires 28 February 2027 FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Insured Larkspur Transit Analytics Limited Limit Aggregate li…
- SRC-0053 — `Legal/Licences/Trade_Licence_and_Registration.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Road-Data Processing Registration Synthetic registration SYN-LIC-44218 FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Holder Larkspur Transit Analytics Limited Scope Registration cover…
- GAP-CUSTOMER-GROUP-IDENTITIES (customer_identity_gap): Multiple observed customer names share a distinctive root but ownership is not evidenced.

**Decision potentially affected:** go_no_go, price, customer_concentration

**Expected answer type:** alias-to-ultimate-parent mapping with ownership/supporting sources

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R2-002 — CRITICAL

The register links original agreements and amendments in candidate version families VER-0001, VER-0002. For each family, which documents are executed and operative, are any side letters or later amendments missing, and which provisions control consent, liability, termination and pricing?

**Why it matters:** The register deliberately does not choose an authoritative version; applying a stale contract can reverse consent, liability and commercial conclusions.

**Evidence/gap:**

- SRC-0037 — `Legal/Customer Contracts/Customer_Framework_Harbourlight.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0034 — `Legal/Customer Contracts/Amendment_Harbourlight_2025.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0039 — `Legal/Customer Contracts/Customer_Framework_Mosaic_South.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0036 — `Legal/Customer Contracts/Amendment_Mosaic_South_2025.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- GAP-CONTRACT-AMENDMENT-CONTROL (contract_version_gap): Agreement supersession is candidate-only and not established as source truth.

**Decision potentially affected:** go_no_go, transaction_structure, price

**Expected answer type:** executed-document/version matrix with missing amendments identified

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R2-003 — HIGH

The extracted workforce/PAYE evidence contains different stated employee or contractor counts. Please reconcile the population by cut-off date, employment status, legal entity and client allocation, and identify the authoritative roster.

**Why it matters:** Workforce discrepancies affect payroll, tax, contractor classification, customer delivery dependence and normalized cost conclusions.

**Evidence/gap:**

- SRC-0003 — `Financial/Contractor_Headcount_by_Client.xlsx`; locator `{"cell": "C10", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "C10", "row_hidden": false, "sheet": "Contractors", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Financial/Contractor_Headcount_by_Client.xlsx"}`: 10 contractors allocated; legal list contains 12 active contractors
- SRC-0043 — `Legal/Employment/Contractor_List.xlsx`; locator `{"cell": "B2", "column_hidden": false, "merged_ranges": [], "named_ranges": [], "range": "B2", "row_hidden": false, "sheet": "Contractors", "sheet_index": 1, "sheet_state": "visible", "type": "spreadsheet_cell", "workbook": "Legal/Employment/Contractor_List.xlsx"}`: 12 active contractors at 30 June 2026
- SRC-0046 — `Legal/Employment/Payslip_Sample.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Sample Payslip Larkspur Transit Analytics Limited | June 2026 | employee data redacted FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Pay details Employee: REDACTED. Gross pay EUR 5,25…
- SRC-0060 — `Legal/Work Permits/Registration.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Synthetic Work Permit Acknowledgement Employee reference EMP-044 | fictional FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Acknowledgement A fictional employment-permit renewal was re…
- SRC-0076 — `Tax/ROS Screens/PAYE_Returns.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: ROS-Style PAYE Returns Employer account 2025 FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 COMPANY Larkspur Transit Analytics Lim DATASET SYN-LARKSPUR-2026-314159 STATUS Synthetic Returns Registered PAYE headcount: 64. Annual liability: EUR 1,584,000. Status Twelve monthl…
- GAP-WORKFORCE-COUNT-RECONCILIATION (workforce_discrepancy): Distinct numeric workforce counts appear in observed records.

**Decision potentially affected:** price, go_no_go, workforce_liabilities

**Expected answer type:** reconciliation table by population/date/entity with source references

**Blocks analysis:** No

**Invalidated if evidence changes:** analyse, report, validate

## INT-R2-004 — HIGH

Material property documents remain image-only pending vision review: SRC-0057 (Legal/Property/Property_Purchase_Contract_Scanned.pdf); SRC-0058 (Legal/Property/Property_Sale_Contract_Scanned.pdf). Which properties are owned, sold or leased, which are in the transaction perimeter, and can you provide searchable executed copies plus any lender/landlord consents?

**Why it matters:** Property title, disposal history, lease obligations and consents may affect deal perimeter, closing conditions and liabilities.

**Evidence/gap:**

- SRC-0057 — `Legal/Property/Property_Purchase_Contract_Scanned.pdf`: Image-only source pending vision review.
- SRC-0058 — `Legal/Property/Property_Sale_Contract_Scanned.pdf`: Image-only source pending vision review.
- GAP-PROPERTY-DOCUMENT-COVERAGE (critical_unreadable_area): Property source content is not yet deterministically readable.

**Decision potentially affected:** scope, transaction_structure, closing_conditions

**Expected answer type:** property schedule plus executed/searchable documents and consent status

**Blocks analysis:** No

**Invalidated if evidence changes:** analyse, report, validate

---

## Internal prioritisation record — not additional questions

Candidate questions below were intentionally excluded so the packet remains decision-focused and non-duplicative.

- `followup-INT-R1-001` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: SRC-0051.
- `followup-INT-R1-002` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: SRC-0010, SRC-0011, SRC-0017, SRC-0007, SRC-0008, SRC-0009.
- `followup-INT-R1-003` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: None.
- `followup-INT-R1-004` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: None.
- `followup-INT-R1-005` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: SRC-0004, SRC-0052.
- `followup-INT-R1-006` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: SRC-0004, SRC-0012.
- `followup-INT-R1-007` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: SRC-0027.
- `followup-INT-R1-008` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: SRC-0052, SRC-0093, SRC-0099.
- `followup-INT-R1-009` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: SRC-0071, SRC-0078, SRC-0079, SRC-0084, SRC-0083.
- `followup-INT-R1-010` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: None.
- `followup-INT-R1-011` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: None.
- `debt-hp-completeness` — Already asked in round one; it remains in unresolved_questions.md and is not duplicated without a narrowing answer. Supporting sources: SRC-0010, SRC-0011, SRC-0017, SRC-0007, SRC-0008, SRC-0009.
- `missing-cross-referenced-documents` — Already asked in round one; it remains in unresolved_questions.md and is not duplicated without a narrowing answer. Supporting sources: SRC-0004, SRC-0052.
- `tax-amendment-status` — Already asked in round one; it remains in unresolved_questions.md and is not duplicated without a narrowing answer. Supporting sources: SRC-0071, SRC-0078, SRC-0079, SRC-0084, SRC-0083.
- `contract-consents` — Already asked in round one; it remains in unresolved_questions.md and is not duplicated without a narrowing answer. Supporting sources: SRC-0052, SRC-0093, SRC-0099.
- `unsupported-financial-adjustments` — Already asked in round one; it remains in unresolved_questions.md and is not duplicated without a narrowing answer. Supporting sources: SRC-0004, SRC-0012.
- `explicit-calculation-contradiction` — Already asked in round one; it remains in unresolved_questions.md and is not duplicated without a narrowing answer. Supporting sources: SRC-0027.
- `critical-unreadable-sources` — Already asked in round one; it remains in unresolved_questions.md and is not duplicated without a narrowing answer. Supporting sources: SRC-0051.
