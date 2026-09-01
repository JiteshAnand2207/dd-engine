# Phase 14 generalisation and resilience report

Date: 1 September 2026

## Conclusion

The engine completed a qualifying, truth-isolated shadow-room rehearsal and a
150-logical-source stress run after generalisation fixes. This is positive
evidence that the deterministic engine is not tied to the primary synthetic
room's filenames, fixed years, exact cell addresses, customer names or values.
It is not a claim that all future rooms will be issue-complete, and it is not a
release-ready result: the final candidate still lacks a verified independent
red-team context and reconciliation manifest.

## Shadow-room construction

`scripts/generate_phase14_rooms.py` deterministically creates the public room at
`synthetic/shadow/data_room/`. Its public manifest records 48 physical files and
four direct ZIP members, for 52 logical sources. The fictional target is Orchard
Lantern Systems Limited, with different periods (including 2019, 2023 and 2024),
different customers, employees, providers, figures, folders and document names.

The room deliberately includes:

| Requirement | Shadow implementation | Observed engine result |
|---|---|---|
| Missing expected document | Monthly bank statements absent | Intake/gap state retained the absence |
| Irrelevant document | Cafeteria menu | Registered/extracted without becoming a material finding |
| Renamed duplicate | `CX-17` and `ArchiveAlias-991` | One exact-duplicate group; one analysis representative |
| Hidden sheet | Workbook control sheet | Hidden-sheet metric recorded |
| Misleading extension | CSV bytes named `.xlsx` | Detected as CSV; extension mismatch recorded |
| Corrupted source | `Damaged-Source.pdf` | One isolated extraction failure |
| Image-only scan | Fictional facility letter | One vision task reviewed explicitly; zero remained pending |
| ZIP members | Four direct members | Registered and extracted in memory without disk expansion |
| Prompt injection | Untrusted source text | `prompt_injection_like_text_untrusted`; no instruction executed |

The separate `synthetic/shadow_ground_truth/` directory is rejected as a room by
the source-path guard. The public manifest contains structure and hashes, not the
truth answer.

## Qualifying fresh-context rehearsal

Qualifying run: `20260901T081036940718Z-ea9100a654cb`  
Run directory: `runs/20260901T081036940718Z-ea9100a654cb`

The rehearsal was performed by a newly started analytical agent with no inherited
conversation. It was expressly prohibited from listing, opening, hashing,
searching or globbing either truth directory. Its command audit reports that the
boundary remained intact and that no repository-wide untracked-file inspection
was performed.

| Measure | Result |
|---|---:|
| Logical / physical / ZIP-member sources | 52 / 48 / 4 |
| Exact duplicates / version families | 1 / 3 |
| Extraction units | 379 |
| Successfully extracted / failed / archive-container unsupported | 50 / 1 / 1 |
| Pending vision tasks after review | 0 |
| Financial / Commercial findings | 6 / 4 |
| Legal / Operational / IT / Tax findings | 7 / 2 / 2 / 3 |
| Total findings; critical/high | 24; 22 |
| Calculations | 15 |
| Structured / displayed citations | 140 / 387 |
| Failed citations / material citation coverage | 0 / 100% |
| Report / IC brief | passed; exactly two A4 pages |
| Run/log state | all six stages completed; audit and privacy passed |

The two saved-answer rounds contained six and four questions. Four answers
remained open or narrowed, and those limitations remained in the analysis. The
final run used topic-key answer mapping, so its transaction perimeter, price,
thesis and scope answers were not shifted when the question sequence differed
from the primary room.

A scan of 16 analytical/final artifacts found zero occurrences of primary-room
identifiers `Larkspur`, `Harbourlight`, `Mosaic`, `Juniper` or
`Statutory_Accounts`. It also found neither `revenue revenue` nor the stale phrase
`remains pending visual review`. Findings instead referenced shadow evidence,
including Firbank concentration, a EUR 75k unsupported add-back, EUR 1.053m
working-capital variance, EUR 970k debt/debt-like items and a EUR 60k pipeline
understatement.

Core CLI processing took 36.263 seconds. Doctor-through-final-audit wall time was
12 minutes 9.852 seconds including manual saved-answer authoring and visual QA.
The brief's two rendered pages were inspected without clipping, overlap, broken
glyphs/tables, unreadable citations or filler.

Candidate validation passed but recorded `release_ready: false`, because
independent red team and reconciliation were deliberately not performed in this
fresh drafting context.

## Contaminated attempt and defects found

The first fresh agent completed mechanical validation for run
`20260901T075504358764Z-be57a0fde095`, but its final Git audit enumerated the
filename of the shadow truth file. It did not open or use the contents; nonetheless
the no-list boundary was breached, so that attempt is FAIL for AC-095 and supplies
no acceptance evidence.

That invalid attempt was still valuable as a quality review. It found four defects
that the passing validator had missed:

1. report transaction answers were mapped by question number and shifted into the
   wrong fields;
2. a negative variance produced the phrase `overstated by EUR -60,000`;
3. a generated heading produced `revenue revenue`; and
4. workstream limitations retained stale pending-vision text after review.

The fixes now resolve answers by stable topic key, use direction-aware absolute
variance wording, normalise period headings and derive vision limitations from
current queue state. Focused regressions prove all four on the shadow room.

Separately, the primary implementation context accidentally opened the shadow
truth file after the invalid first rehearsal. It was therefore barred from
supplying shadow analytical evidence. It never opened the primary room's
`synthetic/planted_issues/`. The qualifying replacement context above remained
fully sealed and post-dated every fix.

The qualifying agent also recorded non-analytical setup mistakes: its first
doctor invocation used an MSYS Python without the package, one task-log timestamp
needed `Z` formatting, and two local review commands had quoting/syntax errors.
Each was retried successfully; no analytical stage failed.

## Semantic generalisation changes

- Source selection now matches extracted content first; path hints only rank an
  otherwise ambiguous match or serve as a fallback.
- Period labels, totals and material rows are derived from evidence labels rather
  than hard-coded years, customer names or primary cell positions.
- Contract/version prose derives party names and effective versions from the
  source register and document text.
- VAT, corporation-tax and PAYE descriptions use observed periods and values.
- Intake answers flow into both report and IC brief by stable `topic_key`.
- Report state fingerprints include the live vision queue, preventing stale
  limitations after a review.
- Prompt-like source content is deterministically flagged as untrusted evidence;
  it cannot alter routing or execute a command.

## 150-logical-source stress result

The scale generator creates 140 compact physical files plus ten direct ZIP
members. It avoids needlessly large binaries while exercising a count above 100.
A retained command result and `tests/test_phase14.py` produced:

| Measure | Observed result | Status |
|---|---:|---|
| Logical sources | 150 | PASS |
| Physical files / direct ZIP members | 140 / 10 | PASS |
| Valid SHA-256 fields | 150 | PASS |
| Terminal extraction states | 150 | PASS |
| Successful / failed / archive unsupported | 148 / 1 / 1 | PASS — failure isolated |
| Cold cache hits / misses | 0 / 148 | PASS |
| Immediate unchanged rerun | stage reused | PASS |
| Changed-source rerun hits / misses | 147 / 1 | PASS |
| Changed-source stage reused | false | PASS — invalidated correctly |
| Peak traced Python allocation | 3,431,633 bytes (3.273 MiB) | PASS, below 512 MiB |

The memory figure is `tracemalloc` peak Python allocation for cold register plus
extract; it is not a claim about total process RSS. Its value is well below the
explicit Phase 14 threshold and, together with 150 terminal records, establishes
that no 100-source logic ceiling was encountered.

## Bad-input matrix

| Case | Expected isolation | Verified outcome | Status |
|---|---|---|---|
| Unsupported binary | explicit unsupported terminal row | registered unsupported | PASS |
| Corrupted PDF | explicit unreadable/failure | registered unreadable; failed extraction isolated | PASS |
| Encrypted PDF | no password guessing | encrypted state retained | PASS |
| Empty file | explicit terminal state | registered unsupported, not omitted | PASS |
| Large spreadsheet in limits | parse without arbitrary small cap | at least 40,000 spreadsheet cells extracted | PASS |
| Archive traversal | never escape room/archive | `../escape.csv` blocked unsafe; safe member retained | PASS |
| Duplicate source | retain rows, one independence key | exact-duplicate group recorded | PASS |
| Same basename | do not merge by name | distinct rows plus one basename conflict | PASS |
| No native PDF text | vision workflow | image-only page queued | PASS |
| Optional OCR missing | no fabricated OCR text | test config disables OCR; queue remains explicit | PASS |
| Read-only output | explicit failure | simulated portable `PermissionError` becomes `RunError` | PASS |
| Interrupted extraction | resumable state | simulated interrupt leaves stage running; retry completes | PASS |
| Changed source | invalidate only affected cache identity | 147 hits and exactly one miss | PASS |
| Prompt injection | treat as evidence only | warning recorded; no source instruction executed | PASS |

The permission test is simulated because Windows ACL and administrator behavior
make chmod-only tests unreliable. It directly exercises the engine's permission
error path; it does not claim a physical ACL denial occurred on every platform.

## Verification and remaining limits

The full repository suite passed: 111 tests. Phase 14's focused suite passed 5
tests; Ruff and mypy both passed; doctor reported 7 required passes, 2 optional
warnings and no failures. The public-only primary-room validator passed all 32
checks without opening sealed truth. A canonical current-checkout run registered
and extracted 100 logical sources, generated round-one questions, completed the
evidence foundation and correctly remained `awaiting_input` with analysis not
started.

Remaining limits are explicit:

- no qualifying independent red-team/reconciliation isolation manifest exists;
- shadow ground-truth scoring was not used as analytical evidence;
- optional OCR and document conversion were absent, with documented fallbacks;
- the tests prove bounded synthetic behavior, not guaranteed recall on every
  confidential client room; and
- environment-specific offline/other-OS setup, production archive limits and
  retention policy still require operator decisions.

AC-094: PASS. AC-095: PASS using only the post-fix sealed retry; the earlier
attempt remains FAIL. AC-096 through AC-098 and AC-100 through AC-103: PASS.
