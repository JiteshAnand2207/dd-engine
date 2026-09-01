# IT analysis

Run ID: `20260901T081036940718Z-ea9100a654cb`

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

- `EVD-IT-001-01` — `SRC-0027` / page 1
- `EVD-IT-001-02` — `SRC-0028` / paragraph 6
- `EVD-IT-001-03` — `SRC-0030` / paragraph 6

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Commission an independent penetration test and witnessed restore/DR test; agree contractual RTO/RPO, remediate critical findings and deliver the final reports before completion.

### IT-003 — CRITICAL

**Conclusion:** An unredacted employee workbook in the room contains work-email, personal-email and government-identifier-like fields; access, purpose, retention and secure-transfer controls are not evidenced.

**Source fact:** The workbook itself labels the personal-data content and exposes the three sensitive field categories. No personal values are reproduced in this finding.

**Analysis:** The presence of employee PII in an unrestricted diligence artifact creates a concrete data-handling issue independent of the broader policy-document gap.

**Why it matters:** Unnecessary or uncontrolled disclosure can create privacy, security and employee-trust exposure.

**Transaction implication:** Restrict the artifact immediately, preserve an access audit and make data-room remediation plus privacy warranties a transaction requirement.

**Confidence:** 85%

**Uncertainty/limitation:** The room does not provide an access log, lawful-basis assessment, retention record or confirmation of deletion from prior recipients.

**Supporting citations:**

- `EVD-IT-003-01` — `SRC-0052` / Restricted!B2
- `EVD-IT-003-02` — `SRC-0052` / Restricted!B3
- `EVD-IT-003-03` — `SRC-0052` / Restricted!C3
- `EVD-IT-003-04` — `SRC-0052` / Restricted!D3

**Contradictory or limiting citations:**

- None identified.

**Exact next action:** Move the workbook to least-privilege access, identify recipients, assess lawful purpose and necessity, replace it with a minimized/redacted version, document retention/deletion, and notify privacy counsel if required.

## Coverage and explicit limitations

| Topic | Status | Linked issues |
|---|---|---|
| hosting_provider_agreements | analysed | IT-001 |
| access_management | limitation | None |
| cybersecurity_controls | analysed | IT-001 |
| backup_restore_disaster_recovery | analysed | IT-001 |
| vendor_dependence | analysed | OPS-002 |
| software_ip_licensing | analysed | LEGAL-007 |
| data_processing_gdpr | analysed | IT-003 |
| incident_history | limitation | None |
| missing_technical_evidence | limitation | None |

## General limitations

- No formal Irish legal or tax opinion is provided.
- Unreadable sources remain unresolved; reviewed visual evidence is limited to its recorded transcription and citation.
- Topics marked limitation had insufficient source evidence for an adverse conclusion.
