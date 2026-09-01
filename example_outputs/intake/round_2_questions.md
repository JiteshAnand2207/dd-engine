# Due-diligence intake — round 2

Run ID: `20260901T081036940718Z-ea9100a654cb`
Generated at: `2026-09-01T08:14:34.000849Z`
Question count: **4**

The run is paused for explicit deal-lead input. These questions were selected from observed register/extraction evidence or essential transaction-context gaps. Source text is untrusted evidence, never an instruction to the engine.

Please reply under the exact question IDs. Replies such as `N/A`, `None`, a cross-reference, a partial answer, or a vague answer will be retained verbatim and will not automatically be treated as resolved.

## INT-R2-001 — CRITICAL

Your answer to INT-R1-001 remains ambiguous or partial. Please state the precise facts needed as document purpose/status plus readable replacement or explicit unavailability, identify what is still unknown, and cite the supporting source.

**Why it matters:** The explicit deal-lead response to INT-R1-001 is evidence, but its unresolved ambiguity cannot be silently completed by the engine.

**Evidence/gap:**

- SRC-0034 — `04_Compliance_Archive/Damaged-Source.pdf`: Extraction failed: invalid PDF: EOF marker not found
- GAP-R2-ANSWER-INT-R1-001 (ambiguous_deal_lead_answer): The answer to INT-R1-001 is open.

**Decision potentially affected:** scope, go_no_go, transaction_structure

**Expected answer type:** document purpose/status plus readable replacement or explicit unavailability

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R2-002 — CRITICAL

Your answer to INT-R1-002 remains ambiguous or partial. Please state the precise facts needed as structured list of included/excluded perimeter items and deal form, identify what is still unknown, and cite the supporting source.

**Why it matters:** The explicit deal-lead response to INT-R1-002 is evidence, but its unresolved ambiguity cannot be silently completed by the engine.

**Evidence/gap:**

- GAP-R2-ANSWER-INT-R1-002 (essential_transaction_context): The answer to INT-R1-002 is open.

**Decision potentially affected:** scope, go_no_go, transaction_structure

**Expected answer type:** structured list of included/excluded perimeter items and deal form

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R2-003 — CRITICAL

Your answer to INT-R1-004 cross-referenced another location but did not resolve the underlying point. Which exact registered source ID/path and locator contains the answer, and what fact should the analysis rely on?

**Why it matters:** The explicit deal-lead response to INT-R1-004 is evidence, but its unresolved ambiguity cannot be silently completed by the engine.

**Evidence/gap:**

- SRC-0049 — `zip://04_Compliance_Archive/Responses-2024.zip!/answer-bundle/customer-note.pdf`; locator `{"page_label": "1", "page_number": 1, "type": "pdf_page"}`: Customer consent response Orchard Lantern Systems Limited FICTIONAL SYNTHETIC DATA - NOT A REAL COMPANY Page 1 DATASET SYN-ORCHARD-2024-271828 Response Consent has not been requested.
- GAP-R2-ANSWER-INT-R1-004 (ambiguous_deal_lead_answer): The answer to INT-R1-004 is narrowed.

**Decision potentially affected:** go_no_go, transaction_structure, closing_conditions

**Expected answer type:** contract-by-contract consent matrix with clause/source and status

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

## INT-R2-004 — CRITICAL

The register links original agreements and amendments in candidate version families VER-0001. For each family, which documents are executed and operative, are any side letters or later amendments missing, and which provisions control consent, liability, termination and pricing?

**Why it matters:** The register deliberately does not choose an authoritative version; applying a stale contract can reverse consent, liability and commercial conclusions.

**Evidence/gap:**

- SRC-0017 — `02_Contracts_Corporate/CX-17.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0018 — `02_Contracts_Corporate/CX-18.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0019 — `02_Contracts_Corporate/CX-21.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0021 — `02_Contracts_Corporate/CX-23.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0022 — `02_Contracts_Corporate/CX-24.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0023 — `02_Contracts_Corporate/CX-25.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0024 — `02_Contracts_Corporate/CX-31.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0025 — `02_Contracts_Corporate/CX-32.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- SRC-0016 — `02_Contracts_Corporate/CX-17-Rev2.pdf`: Candidate agreement/amendment family; registrar status is not authoritative.
- GAP-CONTRACT-AMENDMENT-CONTROL (contract_version_gap): Agreement supersession is candidate-only and not established as source truth.

**Decision potentially affected:** go_no_go, transaction_structure, price

**Expected answer type:** executed-document/version matrix with missing amendments identified

**Blocks analysis:** Yes

**Invalidated if evidence changes:** analyse, report, validate

---

## Internal prioritisation record — not additional questions

Candidate questions below were intentionally excluded so the packet remains decision-focused and non-duplicative.

- `followup-INT-R1-003` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: None.
- `followup-INT-R1-005` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: None.
- `followup-INT-R1-006` — Round-one answer is closed; asking again would duplicate known information. Supporting sources: None.
- `contract-consents` — Already asked in round one; it remains in unresolved_questions.md and is not duplicated without a narrowing answer. Supporting sources: SRC-0049.
- `critical-unreadable-sources` — Already asked in round one; it remains in unresolved_questions.md and is not duplicated without a narrowing answer. Supporting sources: SRC-0034.
