# Phase 14 manual citation and calculation audit

Audit date: 1 September 2026  
Audited run: `20260901T040928457675Z-dede88eb959c`

This is a manual spot-check of the final primary synthetic run. It did not open
sealed planted-issue material. All 20 evidence rows below were resolved through
the run's structured evidence store and native locator. The complete registered
SHA-256, rather than only the displayed prefix, was compared with the current
source register. All 18 physical sources matched; the ZIP-member workbook also
matched its registered direct-member checksum. Phase 10 independently reports
176 structured citations, zero failures and 100% material-finding coverage.

## Material citation spot-check

| # | Workstream | Evidence / source / SHA-256 | Native locator | Cited fact | Result |
|---:|---|---|---|---|---|
| 1 | Financial | `EVD-FIN-001-01`, `SRC-0020`, `32094b5de2b73c88dc478a3a12a49694490f150d069315125a9f3c2d8db4344e` | PDF page 1 | Revenue EUR 6.2m; EBITDA EUR 0.72m | PASS |
| 2 | Financial | `EVD-FIN-002-01`, `SRC-0012`, `97cff696c06a9aee3aa83e3e446b1eaa08a53ec6d93734ba08ff9a3661b4d0e8` | PDF page 1 | Adjusted EBITDA EUR 1.41m and baseline EUR 1.23m | PASS |
| 3 | Financial | `EVD-FIN-003-01`, `SRC-0027`, `8c13cb3f3053c228e88fbc25f11de835765a8f79c4d51bb5e0eef68de9143f8f` | `Calculation!B9` | Reported working capital EUR -835k | PASS |
| 4 | Financial | `EVD-FIN-005-01`, `SRC-0010`, `7c9fbdaa21a7bfec7e7c154dc55d6b9d677220c0c655542e7dd3a63899f453bd` | `Loans!C6` | Loan total EUR 1.81m | PASS |
| 5 | Commercial | `EVD-COMM-001-01`, `SRC-0018`, `6d92e73e115381a22226044b45fd00b4eb5051f0ce92fdbe353df8da57535324` | `Revenue!D6` | First alias carries identity key `GRP-MOSAIC` | PASS |
| 6 | Commercial | `EVD-COMM-001-02`, `SRC-0018`, same registered checksum | `Revenue!D7` | Second alias carries the same identity key | PASS |
| 7 | Commercial | `EVD-COMM-004-01`, `SRC-0015`, `673eb808737e9e03f2dee34e482eb16a05ef04eebb108351831db74db668b379` | `PAYE!B4` | Cited customer allocation is 18 employees | PASS |
| 8 | Legal/contractual | `EVD-LEGAL-001-01`, `SRC-0037`, `6026df9b7b6489bdfab82b0f9f8ba2c2e29003176a6f8d3257d6cdbb5ef5dc73` | PDF page 1 | Prior written consent follows change of control | PASS |
| 9 | Legal/contractual | `EVD-LEGAL-001-02`, `SRC-0034`, `8a6ca9bf4e34833f494ce3329202ccc4ae6c6f775c2ccd4401be0a3900138d22` | PDF page 1 | Later amendment expressly leaves that clause in force | PASS |
| 10 | Legal/contractual | `EVD-LEGAL-002-01`, `SRC-0038`, `1cd9f5b1ca8c3b3b7141c3caef05f99c7ae60771238f130bc1435e13195e8292` | PDF page 1 | Base liability cap is three months of fees | PASS |
| 11 | Legal/contractual | `EVD-LEGAL-002-02`, `SRC-0035`, `192c6ef3402a570fa1620cdb8c58bd1029f5f852562ef5e327a87aa035ecd132` | PDF page 1 | Amendment replaces the clause with 12 months and uncapped credits | PASS |
| 12 | Operational/management | `EVD-OPS-001-01`, `SRC-0047`, `d73f4d352f7920dc27d189e374b6a5c637fa30da37e76efbd37628a20aef32eb` | DOCX paragraph 14 under heading 4 | Restore test was proposed but no date approved | PASS |
| 13 | Operational/management | `EVD-OPS-002-01`, `SRC-0055`, `c8ebc96835d0194089d0b6c5a0d7f60e12a2c484f864248fe56ebc252a1df23c` | PDF page 1 | Annual hosting fee is EUR 420k | PARTIAL — proves the amount, not by itself the report's broader dependency/default-risk inference |
| 14 | IT | `EVD-IT-001-01`, `SRC-0055`, same registered checksum | PDF page 1 | No contractual RTO, annual witnessed restore test, penetration report or independent assurance commitment | PASS |
| 15 | IT | `EVD-IT-002-01`, `SRC-0040`, `016a429103b401c37609ac2f86e585eaf963b8ac6bd459ca9f68ecc64ef65135` | PDF page 1 | Three P1 incidents exceeded the four-hour target | PASS |
| 16 | IT | `EVD-IT-003-01`, `SRC-0095`, `c70893e361bd9e60c9c36fab2db5e2f552968488401b1ab0e5e2880ffe2166ea` | ZIP-member XLSX `Employees!B2` | Workbook labels its contents synthetic personal data for privacy testing | PASS |
| 17 | Tax | `EVD-TAX-001-01`, `SRC-0083`, `1d4dd237ab06a214e89f8f6e54fa2d4f1f7e09d3abdca66708c8a79986327b41` | PDF page 1 | Original VAT payable EUR 174k | PASS |
| 18 | Tax | `EVD-TAX-001-02`, `SRC-0084`, `11e276d603c4bf426a8eb6ca6c05dcc11121d5c9559c48540a4b1b4f8b8b5e5c` | PDF page 1 | Amended VAT EUR 182k; increase EUR 8k | PASS |
| 19 | Tax | `EVD-TAX-002-01`, `SRC-0074`, `a6026e86b9b65ec1dcea046eb97adb9aedec8f8f33235d3b65509a5746e907c2` | PDF page 1 | Corporation-tax liability EUR 389.2k | PASS |
| 20 | Tax | `EVD-TAX-003-01`, `SRC-0076`, `f34d4beb58d17da8b3cc11ee4adb74e6062148aa31c2f221087b4f7575c33486` | PDF page 1 | Registered PAYE headcount 64; annual liability EUR 1.584m | PASS |

Outcome: 19 PASS, 1 PARTIAL, 0 FAIL. The partial result remains explicit and
does not invalidate the locator; it limits what that one citation can prove.

## Five headline calculations

| Calculation | Independent recomputation | Result | Limitation |
|---|---|---|---|
| `CALC-FIN-001` revenue growth | `(13.1m - 6.2m) / 6.2m x 100` | `111.29%` — PASS | Period endpoints are those in the cited accounts; this is not a forecast. |
| `CALC-FIN-003` adjusted EBITDA | `1.23m + 0.18m` | `1.41m`; variance to reported `0` — PASS | Arithmetic does not establish that the adjustment is maintainable. |
| `CALC-FIN-004` working capital | `1.48m + 0.095m - 0.93m + 0.185m` | `0.83m`; variance to reported `-0.835m` is `1.665m` — PASS | The hidden/prepayment treatment still needs deal-lead confirmation. |
| `CALC-FIN-005` ageing total | `123 + 16 + 11.5 + 10.5 + 8 + 4.5 + 3` (EUR k) | `176.5k`; variance to `74k` is `102.5k` — PASS | Collection and credit-note status are not proved by the schedule. |
| `CALC-FIN-006` debt reconciliation | `1.81m + 0.29m + 0.12m - 0.96m` | `1.26m` — PASS | Inputs are not all contemporaneous and unrestricted cash was not established. |

## Three contract/version decisions

| Family | Decision | Result |
|---|---|---|
| Harbourlight | Base `SRC-0037` requires change-of-control consent; later amendment `SRC-0034` expressly preserves the clause. | PASS — both versions and precedence text reviewed. |
| Mosaic North | Base `SRC-0038` has a three-month cap; amendment `SRC-0035` supersedes the clause with 12 months and uncapped service credits. | PASS — effective amended term used. |
| Mosaic South | Amendment `SRC-0036` adds depots and an 18-month term while leaving all other terms unchanged; the base six-month cap in `SRC-0039` therefore continues. | PASS — continued base term is an explicit version inference, not a fabricated amendment. |

## Three tax reconciliations

| Reconciliation | Independent recomputation | Result | Limitation |
|---|---|---|---|
| VAT | `182k - 174k` | `8k` increase — PASS | Filing/payment status still requires confirmation. |
| Corporation tax | `420k - 18.3k - 389.2k - 12.5k` | `0` — PASS arithmetic | The arithmetic alone does not prove that all four records relate to one settled liability. |
| PAYE | `1.584m - 1.584m` | `0` annual variance — PASS arithmetic | Annual tie-out does not explain the separate EUR 132k control-period variance. |

These are commercial diligence checks, not Irish legal or tax opinions.

## Intake and IC/full-report consistency

Round one retained 11 verbatim saved answers under input SHA-256
`f34a74576a8eb94a14d2e88b2d0448bf0ba5b89e45a31e96efd31117f7120e58`:
2 closed and 9 open. Round two retained 4 answers under
`a79d5724b833090e8b0579ff37f1606f2a5ff0168fd86c06679e68124f40ef78`:
all 4 remain open. Both identify the responder as a synthetic test operator, not
management; no silence or vague reply was converted into fact.

The IC brief and full report contain the same 11 critical issue IDs:
`FIN-002`, `FIN-003`, `FIN-005`, `COMM-001`, `COMM-005`, `LEGAL-001`,
`LEGAL-007`, `IT-001`, `IT-003`, `TAX-001` and `TAX-002`. Their conclusions,
headline amounts and required protections/next actions agree. All IC citations
resolved, the PDF is exactly two A4 pages, and no critical full-report issue was
omitted from the brief.

## Audit disposition

AC-104: PASS. AC-105: PASS. AC-106: PASS. The single partial citation is a
calibration finding, not a dangling or inaccurate locator; the report must retain
the broader statement as an inference supported by the rest of its evidence set.
