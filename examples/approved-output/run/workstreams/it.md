# IT analysis

Run ID: `20260901T040928457675Z-dede88eb959c`

This is decision-oriented commercial due diligence, not a document summary. Source facts are separated from analytical conclusions. No independent valuation is provided.

## Scope

Commercial due diligence in an Irish transaction context; this is not a formal Irish legal or tax opinion and specialist advisers must confirm conclusions used in transaction documents.

## Material findings

### IT-001 — CRITICAL

**Conclusion:** IT resilience is not evidenced to an acquisition standard: there is no contractual RTO, witnessed disaster-recovery test, penetration-test report or independent assurance report.

**Source fact:** The hosting agreement and current vendor responses consistently identify the missing controls.

**Analysis:** Administrator MFA is a positive control but does not compensate for untested recovery and absent assurance.

**Why it matters:** Control failure can interrupt service, trigger customer credits and exceed cyber-insurance assumptions.

**Transaction implication:** Make remediation and evidence a closing condition, retain escrow for unresolved critical defects, and require cybersecurity/incident warranties.

**Confidence:** 85%

**Supporting citations:**

- `EVD-IT-001-01` — `SRC-0055` / page 1
- `EVD-IT-001-02` — `SRC-0097` / paragraph 7
- `EVD-IT-001-03` — `SRC-0099` / paragraph 7

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Commission an independent penetration test and witnessed restore/DR test; agree contractual RTO/RPO, remediate critical findings and deliver the final reports before completion.

### IT-002 — HIGH

**Conclusion:** Incident history is not clean: a customer alleges three priority-one SLA failures, management accepts two misses, and a full recovery exercise remains unscheduled.

**Source fact:** The complaint and company response document incident frequency, accepted misses and incomplete recovery testing.

**Analysis:** The evidence links technical-control gaps to a real customer service dispute.

**Why it matters:** Repeat incidents can drive credits, churn, liability and insurance notification obligations.

**Transaction implication:** Seek a specific pre-close incident indemnity/escrow, validate insurance notice compliance and condition closing on remediation of repeat root causes.

**Confidence:** 85%

**Uncertainty/limitation:** The room does not contain a complete incident history or insurer correspondence.

**Supporting citations:**

- `EVD-IT-002-01` — `SRC-0040` / page 1
- `EVD-IT-002-02` — `SRC-0041` / page 1

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Obtain the complete incident register, root-cause analyses, SLA calculations, insurer notifications, remediation evidence and post-incident trend metrics.

### IT-003 — CRITICAL

**Conclusion:** An unredacted employee workbook in the room contains work-email, personal-email and government-identifier-like fields; access, purpose, retention and secure-transfer controls are not evidenced.

**Source fact:** The workbook itself labels the personal-data content and exposes the three sensitive field categories. No personal values are reproduced in this finding.

**Analysis:** The presence of employee PII in an unrestricted diligence artifact creates a concrete data-handling issue independent of the broader policy-document gap.

**Why it matters:** Unnecessary or uncontrolled disclosure can create privacy, security and employee-trust exposure.

**Transaction implication:** Restrict the artifact immediately, preserve an access audit and make data-room remediation plus privacy warranties a transaction requirement.

**Confidence:** 85%

**Uncertainty/limitation:** The room does not provide an access log, lawful-basis assessment, retention record or confirmation of deletion from prior recipients.

**Supporting citations:**

- `EVD-IT-003-01` — `SRC-0095` / Employees!B2
- `EVD-IT-003-02` — `SRC-0095` / Employees!D3
- `EVD-IT-003-03` — `SRC-0095` / Employees!E3
- `EVD-IT-003-04` — `SRC-0095` / Employees!F3

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Move the workbook to least-privilege access, identify recipients, assess lawful purpose and necessity, replace it with a minimized/redacted version, document retention/deletion, and notify privacy counsel if required.

## Coverage and explicit limitations

| Topic | Status | Linked issues |
|---|---|---|
| hosting_provider_agreements | analysed | IT-001 |
| access_management | limitation | None |
| cybersecurity_controls | analysed | IT-001 |
| backup_restore_disaster_recovery | analysed | IT-001, IT-002 |
| vendor_dependence | analysed | OPS-002 |
| software_ip_licensing | analysed | LEGAL-007 |
| data_processing_gdpr | analysed | IT-003 |
| incident_history | analysed | IT-002 |
| missing_technical_evidence | limitation | None |

## General limitations

- No formal Irish legal or tax opinion is provided.
- Visual property/CRO evidence and the unreadable legacy policy remain unresolved.
- Topics marked limitation had insufficient source evidence for an adverse conclusion.
