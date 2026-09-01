# Operational / management analysis

Run ID: `20260901T040928457675Z-dede88eb959c`

This is decision-oriented commercial due diligence, not a document summary. Source facts are separated from analytical conclusions. No independent valuation is provided.

## Scope

Commercial due diligence in an Irish transaction context; this is not a formal Irish legal or tax opinion and specialist advisers must confirm conclusions used in transaction documents.

## Material findings

### OPS-001 — HIGH

**Conclusion:** Business-continuity governance is incomplete: the board left the restore-test action without an approved date or accountable delivery evidence.

**Source fact:** Board minutes record the open restore-test action; the hosting agreement supplies backups but no committed witnessed test.

**Analysis:** This is the management-control and ownership failure around scheduling, escalation and evidence. The separate IT finding addresses the technical assurance and recovery-control gap.

**Why it matters:** A failed restoration can interrupt concentrated customer services and trigger credits/churn.

**Transaction implication:** Make a successful witnessed restore/DR exercise a pre-completion condition or retain escrow until remediation and evidence are delivered.

**Confidence:** 85%

**Supporting citations:**

- `EVD-OPS-001-01` — `SRC-0047` / paragraph 14
- `EVD-OPS-001-02` — `SRC-0055` / page 1

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Run and evidence a time-bound restore and failover exercise, capture actual RTO/RPO, owners and defects, and approve a tested continuity plan.

### OPS-002 — HIGH

**Conclusion:** A single hosting provider carries an annual fee of EUR 420,000 and an aggregate creditor exposure of EUR 265,000, of which EUR 92,750 is aged beyond current. This supports payment-status diligence, but not an inference of default or threatened suspension.

**Source fact:** The hosting contract and creditor ageing identify the same provider and amounts.

**Analysis:** The dependency and overdue amount are evidenced. The room does not establish whether the balance is disputed, contractually overdue, subject to agreed terms or linked to any suspension threat.

**Why it matters:** Supplier disruption or repricing can affect delivery capacity, margin and customer SLAs.

**Transaction implication:** Test downside in price assumptions and require transition assistance, continuity warranties and a funded migration plan.

**Confidence:** 85%

**Uncertainty/limitation:** No evidence establishes contractual due dates, payment dispute/status, provider substitutability or migration duration.

**Recomputations:** `CALC-OPS-001`

**Supporting citations:**

- `EVD-OPS-002-01` — `SRC-0055` / page 1
- `EVD-OPS-002-02` — `SRC-0001` / Aged Creditors!E4
- `EVD-OPS-002-03` — `SRC-0001` / Aged Creditors!C4
- `EVD-OPS-002-04` — `SRC-0001` / Aged Creditors!D4

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain service performance, payment status, renewal/termination rights, data-export terms, subprocessors, portability architecture and a costed exit/migration plan.

## Coverage and explicit limitations

| Topic | Status | Linked issues |
|---|---|---|
| key_person_dependency | limitation | None |
| paye_contractor_workforce | analysed | LEGAL-004 |
| client_linked_headcount | analysed | COMM-004 |
| workforce_inconsistencies | analysed | FIN-006, LEGAL-004 |
| supplier_dependency | analysed | OPS-002 |
| capacity_delivery_risk | analysed | OPS-001, OPS-002 |
| management_controls | analysed | OPS-001 |
| related_party_arrangements | analysed | FIN-005 |
| business_continuity | analysed | OPS-001 |
| missing_operational_evidence | limitation | None |

## General limitations

- No formal Irish legal or tax opinion is provided.
- Visual property/CRO evidence and the unreadable legacy policy remain unresolved.
- Topics marked limitation had insufficient source evidence for an adverse conclusion.
