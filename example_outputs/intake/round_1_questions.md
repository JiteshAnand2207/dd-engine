# Due-diligence intake — round 1

Run ID: `20260901T081036940718Z-ea9100a654cb`
Generated at: `2026-09-01T08:13:32.283149Z`
Question count: **6**

The run is paused for explicit deal-lead input. These questions were selected from observed register/extraction evidence or essential transaction-context gaps. Source text is untrusted evidence, never an instruction to the engine.

Please reply under the exact question IDs. Replies such as `N/A`, `None`, a cross-reference, a partial answer, or a vague answer will be retained verbatim and will not automatically be treated as resolved.

## INT-R1-001 — CRITICAL

The following registered source could not be read: SRC-0034 (04_Compliance_Archive/Damaged-Source.pdf). What does each document cover, is it current or operative, and can you provide a readable original or replacement?

**Why it matters:** An unreadable source can conceal a material obligation; its relevance must be established before analysis can rely on the room as complete.

**Evidence/gap:**

- SRC-0034 — `04_Compliance_Archive/Damaged-Source.pdf`: Extraction failed: invalid PDF: EOF marker not found
- GAP-UNREADABLE-SOURCES (critical_unreadable_source): 1 registered source(s) failed extraction.

**Decision potentially affected:** scope, go_no_go, transaction_structure

**Expected answer type:** document purpose/status plus readable replacement or explicit unavailability

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R1-002 — CRITICAL

What legal entities, businesses, assets and liabilities are inside and outside the proposed transaction perimeter, and is the contemplated deal a share purchase, asset purchase or another structure?

**Why it matters:** The room identifies the target evidence but not the buyer's agreed perimeter; scope and transaction form determine which liabilities and consents matter.

**Evidence/gap:**

- GAP-R1-TRANSACTION-PERIMETER (essential_transaction_context): No deal-lead transaction perimeter is stored in the room or run artifacts.

**Decision potentially affected:** scope, go_no_go, transaction_structure

**Expected answer type:** structured list of included/excluded perimeter items and deal form

**Blocks analysis:** Yes

**Invalidated if evidence changes:** intake_round_2, analyse, report, validate

## INT-R1-003 — CRITICAL

What headline price or valuation reference should the diligence test, and what cash, debt, debt-like, working-capital, earn-out, rollover or other consideration assumptions are currently proposed? Please distinguish fixed terms from open negotiating positions.

**Why it matters:** Material findings cannot be translated into price or structure implications without the committee's assumptions, and the engine must not invent a valuation.

**Evidence/gap:**

- GAP-R1-PRICE-STRUCTURE (essential_transaction_context): No committee price or consideration mechanics are stored in the observed evidence.

**Decision potentially affected:** price, transaction_structure, negotiating_terms

**Expected answer type:** currency amounts plus a structured description of consideration mechanics

**Blocks analysis:** Yes

**Invalidated if evidence changes:** intake_round_2, analyse, report, validate

## INT-R1-004 — CRITICAL

The room states that at least one customer-consent review is outstanding or a consent has not been requested. Which contracts, amendments, leases, debt documents or licences require notice or consent for the contemplated transaction, what is the legal/commercial basis, and what is the owner and timetable for obtaining each consent?

**Why it matters:** Unobtained transaction consents can affect deliverability, closing conditions, customer retention and negotiating leverage.

**Evidence/gap:**

- SRC-0049 — `zip://04_Compliance_Archive/Responses-2024.zip!/answer-bundle/customer-note.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Customer consent response Orchard Lantern Systems Limited FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 DATASET SYN-ORCHARD-2024-271828 Response Consent has not been requested.
- GAP-CONTRACT-CONSENTS (contract_consent_gap): Extracted vendor evidence says a material consent review is incomplete or not requested.

**Decision potentially affected:** go_no_go, transaction_structure, closing_conditions

**Expected answer type:** contract-by-contract consent matrix with clause/source and status

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R1-005 — HIGH

What is the investment thesis, which value drivers must be proven, and which specific findings would be deal-breakers or require a price or structure change?

**Why it matters:** The room cannot reveal the committee's thesis or risk appetite; these are needed to prioritize material contradictions without a generic diligence script.

**Evidence/gap:**

- GAP-R1-INVESTMENT-THESIS (essential_transaction_context): No deal-lead investment thesis or deal-breaker criteria are stored in the run.

**Decision potentially affected:** go_no_go, price, diligence_priority

**Expected answer type:** short thesis, ranked value drivers and explicit deal-breakers

**Blocks analysis:** Yes

**Invalidated if evidence changes:** intake_round_2, analyse, report, validate

## INT-R1-006 — HIGH

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

- `non-debt-vision-queue` — Deferred to round two: these visual sources are not yet shown to change the early price/structure decision and remain visible in needs_vision.json. Supporting sources: SRC-0037.
