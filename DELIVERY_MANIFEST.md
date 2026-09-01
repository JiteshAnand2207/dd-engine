# Delivery manifest

Handover prepared at: `2026-09-01T08:48:47.414574Z`  
Final synthetic run ID: `20260901T040928457675Z-dede88eb959c`  
Overall release status: **BLOCKED**

The repository contains every requested handover artifact. Candidate report,
citation, calculation and PDF validation pass, and all 28 recorded red-team
challenges have a resolution. Final release remains blocked because the run has
no red-team packet allowlist, sealed-packet manifest or brand-new-context
isolation manifest. The run's own validation therefore correctly records
`independent_red_team_performed: false` and `release_ready: false`.

| Deliverable | Exact path | Run ID | Checksum | Validation status | Generating stage | Any limitation |
|---|---|---|---|---|---|---|
| Repository README | `README.md` | repository | `78ed407fbf9300ae002814f030421cf93b5e6638b3598eb19c44f644d4eee7e2` | PASS - complete evaluator runbook | Phase 15 handover | macOS/Linux commands documented but not locally executed |
| Synthetic data room | `synthetic/data_room/` | synthetic-fixture | n/a - directory | PASS - 90 visible and 100 logical sources | Synthetic-room generation | entirely fictional; use only as a test room |
| Synthetic room manifest | `synthetic/room_manifest.json` | synthetic-fixture | `624050adfeeef5a5e4d85dc67c7b7e32cea787419075d4bd1bb0732df5f1abee` | PASS - public-only validation evidence | Synthetic-room generation | no planted truth required |
| Planted-issue note | `synthetic/planted_issues/README.md` | sealed-ground-truth | `14017f90fa1ceb4d5f1fd2d60c51fdfe371ee95d79522bb2e117b0b1c2483f32` | PRESENT - sealed | Synthetic-room generation | contents excluded from analytical and release-audit reasoning |
| Due-diligence report | `examples/approved-output/run/outputs/due_diligence_report.md` | 20260901T040928457675Z-dede88eb959c | `32aadc537e239db4f14a9050372dd232e767b3f384e7574cd384fcabf1c332af` | PASS - candidate report validation | Report and Phase 13 reconciliation | not release-ready without red-team isolation proof |
| IC brief Markdown | `examples/approved-output/run/outputs/ic_brief.md` | 20260901T040928457675Z-dede88eb959c | `c50855439b288e5ebf706d99ffde47257e920b6eaf185bba5beb9226db638a4a` | PASS - content and citation checks | Report and Phase 13 reconciliation | paired with the PDF below |
| IC brief PDF | `examples/approved-output/run/outputs/ic_brief.pdf` | 20260901T040928457675Z-dede88eb959c | `0bfa9824092c588ed2a293f68d01520ae6e6c2433fe3de46ca9b9bf41d79a787` | PASS - exactly two ISO A4 pages | Deterministic report renderer | 7.5-point minimum font; visual QA recorded in prior audit |
| Source register CSV | `examples/approved-output/run/source_register/source_register.csv` | 20260901T040928457675Z-dede88eb959c | `01b138c636f48250b2ec669341a7bbb3de9ddb0eaafed976df02055612adbff3` | PASS - 100 logical source rows | Register | synthetic source paths only |
| Source register JSON | `examples/approved-output/run/source_register/source_register.json` | 20260901T040928457675Z-dede88eb959c | `1281fbdc39b456039f2e068e8cb91454ba39999b7612d3768aceb57a57e3940e` | PASS - hashes and terminal rows | Register | ZIP members use virtual paths |
| Intake round one questions | `examples/approved-output/run/intake/round_1_questions.json` | 20260901T040928457675Z-dede88eb959c | `a44912927e1b4bcc83392c9064d6731f6e758ed1543d309d071986740f7f8047` | PASS - evidence-linked packet | Intake round one | synthetic test run |
| Intake round one answers | `examples/approved-output/run/intake/round_1_answers.json` | 20260901T040928457675Z-dede88eb959c | `7aaed74ee800e51c68a20fba3d0c77de354076ab931f290504545d778f114934` | PASS - verbatim provenance retained | Intake round one ingestion | test operator, not management; nine open answers |
| Intake round two questions | `examples/approved-output/run/intake/round_2_questions.json` | 20260901T040928457675Z-dede88eb959c | `496a95b9ba69f0b013887af2dbe3f1d4b9d135aa4b77f1fc6fe82cee3274ffc9` | PASS - evidence-linked packet | Intake round two | synthetic test run |
| Intake round two answers | `examples/approved-output/run/intake/round_2_answers.json` | 20260901T040928457675Z-dede88eb959c | `613ace23b62d938ccde2c8e833526ccb7d16a46f0c3fb1e1f2f96f57da1443e3` | PASS - verbatim provenance retained | Intake round two ingestion | test operator, not management; four open answers |
| Red-team challenge log | `examples/approved-output/run/red_team/red_team_challenge_log.md` | 20260901T040928457675Z-dede88eb959c | `8c1f91daa73fbd168f842826dd7a12169b88c8daba8b83925b7282c0cb97264c` | PRESENT - 28 challenges | Historical red-team review | BLOCKED as independent evidence; no isolation manifest |
| Red-team resolution log | `examples/approved-output/run/red_team/red_team_resolution.md` | 20260901T040928457675Z-dede88eb959c | `a0e54a1a2e0b53c70a2c66e392ede533fcc19840bb9f4f6ae6e6fc5b19b89bc8` | PASS - 23 accepted, 5 rejected, 0 unresolved | Phase 13 reconciliation | does not prove the original review context was independent |
| Run log JSONL | `examples/approved-output/run/logs/run-log.jsonl` | 20260901T040928457675Z-dede88eb959c | `1af57ca41193b4878379db710dee10ee6592e3055905d716c2a3718c1e49a34d` | PASS - 33 task records and honest null usage | Runtime ledger | 32 succeeded, 1 retained failed attempt; no red-team challenge task record |
| Run log summary | `examples/approved-output/run/logs/run-log.md` | 20260901T040928457675Z-dede88eb959c | `c20d9ccc6b661b8dba2a2843ad39466dca64413e5bb65e04798d708c1e7ccfc7` | PASS - routing/task summary | Runtime ledger | model IDs, tokens and model costs unavailable rather than fabricated |
| Public-research log | `examples/approved-output/run/logs/public-research-log.jsonl` | 20260901T040928457675Z-dede88eb959c | `2ccc0b5d078fa11173e5bec7bb36d64417de293d92d497f0eb126388900b96e0` | PASS - not_performed recorded | Phase 9 and runtime ledger | public research remained disabled |
| Delivery notes | `NOTES.md` | repository | `dd95b42a89fb1bf73d7f0fc03ee43f19be469f0e1ac3a2f06a937cf9a2f868dd` | PASS - six requested topics | Phase 15 handover | approximately one page |
| Acceptance evidence | `docs/acceptance-report.md` | acceptance-evidence | `de15c6e7c07f5461f0b3990ec7edf384551cacaaf95629fd295de15f7eb986da` | PASS as Phase 14 historical evidence | Phase 14 acceptance | records the then-missing manifest and red-team blocker |
| Clean-clone evidence | `docs/clean-clone-report.md` | acceptance-evidence | `cf222081cdabcd3332ef896bb664a4a8871b4896f5a05419fad89dfe9c040942` | PASS - Windows setup 206.388 seconds | Phase 14 clean-clone | committed revision predates this Phase 15 package |
| Generalisation evidence | `docs/generalisation-report.md` | acceptance-evidence | `5884f86af4d678f5c81c3e8afd0a7c3f8337248a14cd80b58bbfc8bb6dfa6f84` | PASS - sealed shadow and 150-source stress | Phase 14 generalisation | bounded synthetic evidence, not universal recall proof |
| Manual citation evidence | `docs/manual-citation-audit.md` | acceptance-evidence | `a02b2e38fcf3b1183ec3704d8a36e053d2c338f42d39a5403162c38168466d59` | PASS - 19 pass, 1 explicit partial, 0 fail | Phase 14 manual audit | one citation supports an amount but not the full inference alone |
| Final release audit | `docs/final-release-audit.md` | acceptance-evidence | `138935f7481e905cbc1638498b9e693e903975533d13ba25153c91165b82509e` | PASS - deterministic gates complete; release blocked | Phase 15 handover | not final-release approval until independent red team is proved |
| Report validation ledger | `examples/approved-output/run/outputs/report_validation.json` | 20260901T040928457675Z-dede88eb959c | `c3f892567691388c1ca6d41d7e3c67aa4dde73f152e3e68de9b8f98bf174333d` | PASS - candidate bundle | Validate | correctly records release_ready false |
| Run-log validation ledger | `examples/approved-output/run/logs/run-log-validation.json` | 20260901T040928457675Z-dede88eb959c | `a03f9567d8753ea5241213a39594bc4ebd77016d6bdde214ec7c6a814452171b` | PASS - privacy and completed-stage coverage | Audit logs | historical audit predates Phase 15 packaging |

## Package boundary

The approved output contains 71 run artifacts plus its local README. It excludes
run caches, rendered-page QA intermediates, virtual environments, test caches,
temporary files and arbitrary ignored runs. The source room remains the tracked
fictional room at `synthetic/data_room/`; no real or confidential room data is
part of this manifest.
