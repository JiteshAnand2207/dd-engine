# Runtime flow for Codex and Claude Code

## Outcome

Gavin can clone the repository, point the primary Codex harness (or Claude Code)
at an explicit local room path, and follow one file-backed flow. Python performs
deterministic local work and never calls a provider API. The authenticated coding
harness supplies any reasoning model. No provider SDK, provider key, Docker,
database, cloud store or external logging service is required.

Start the coding harness in the repository and give it
`prompts/runtime/run_engine.md` plus the explicit room path. The prompt owns the
full sequence and both genuine human pauses. Commands below may also be run
manually.

## Clean-clone setup

```text
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m dd_engine doctor --json
```

Use the environment's Python executable if activation differs. The checked-in
`dd-engine.toml` disables telemetry, external logging, public research and direct
API access. `config/model-routing.yaml` is the harness routing contract.

## One run

```text
python -m dd_engine init-run --runs-root runs --json
python -m dd_engine register --run <RUN_PATH> --room <ROOM_PATH> --json
python -m dd_engine extract --run <RUN_PATH> --room <ROOM_PATH> --json
python -m dd_engine intake --run <RUN_PATH> --round 1 --json
```

Stop while round one is `awaiting_input`. Supply an explicit JSON answer file:

```json
{
  "answered_by": "Deal lead name or role",
  "answers": [
    {"question_id": "INT-R1-001", "answer": "Verbatim deal-lead response"}
  ]
}
```

Then continue:

```text
python -m dd_engine intake --run <RUN_PATH> --round 1 --answers <ROUND1.json> --json
python -m dd_engine intake --run <RUN_PATH> --round 2 --json
```

Stop again. After the explicit round-two answer file:

```text
python -m dd_engine intake --run <RUN_PATH> --round 2 --answers <ROUND2.json> --json
python -m dd_engine evidence --run <RUN_PATH> --json
python -m dd_engine analyse --run <RUN_PATH> --phase 8 --json
python -m dd_engine analyse --run <RUN_PATH> --phase 9 --json
python -m dd_engine report --run <RUN_PATH> --json
```

At this point the report is a candidate. Follow `prompts/runtime/red_team.md` in
a brand-new non-inheriting task/chat. The original session may reconcile returned
verified challenges, but may not perform or simulate the independent pass.

```text
python -m dd_engine validate --run <RUN_PATH> --json
python -m dd_engine audit-logs --run <RUN_PATH> --json
python -m dd_engine status --run <RUN_PATH> --json
```

`validate` before red-team completion can pass its candidate-bundle checks but
must still say `release_ready: false`.

## Routing table

| Routing class | Work | Model rule |
|---|---|---|
| `local_deterministic` | Inventory, hashes, archives, native extraction, calculations, citation validation, output checks | No model; null token/API-equivalent cost with a zero-model reason |
| `economical_reasoning` | Classification, mechanical triage, bulk low-risk structuring | Use a cheaper model only when the active harness exposes one; otherwise use the single visible model and record the fallback |
| `frontier_judgment` | Financial reasoning, contradictions, contracts, intake priority, report drafting/review, independent red team | Use the strongest appropriate model actually available; record null when its exact ID is hidden |

The repository does not resolve or call a model. A model advertised by a provider
is not automatically an available model for Gavin's account or current harness.
Do not fill `configured_model` until the harness exposes the actual entitlement.

## Task ledger

Every CLI stage invocation appends a `local_deterministic` record to
`logs/run-log.jsonl` and refreshes `logs/run-log.md`. For an actual harness/model
task, save a JSON object beneath the run and call `log-task`. Example when the
model and usage are not exposed:

```json
{
  "stage": "analyse",
  "task_name": "financial_reasoning_review",
  "purpose": "Review material financial contradictions against validated evidence.",
  "provider_harness": "codex",
  "actual_model": null,
  "actual_model_unavailable_reason": "Codex did not expose an exact model ID to this task.",
  "routing_class": "frontier_judgment",
  "started_at": "2026-09-01T12:00:00.000000Z",
  "ended_at": "2026-09-01T12:03:00.000000Z",
  "source_ids_supplied": ["SRC-0002", "SRC-0027"],
  "input_tokens": null,
  "output_tokens": null,
  "token_count_basis": "unavailable",
  "token_count_unavailable_reason": "The subscription harness did not expose task token usage.",
  "estimated_api_equivalent_cost_usd": null,
  "cost_estimate_basis": "unavailable",
  "rate_card_reference": null,
  "cost_unavailable_reason": "No token count and exact model ID were exposed.",
  "billing_mode": "subscription",
  "actual_billed_cost_usd": null,
  "retry_count": 0,
  "fallback_used": false,
  "fallback_from": null,
  "fallback_reason": null,
  "error": null,
  "output_artifact_paths": ["workstreams/financial.json"],
  "raw_sensitive_content_logged": false
}
```

If actual token counts are exposed, mark them `actual`. An estimate must state its
method. API-equivalent cost is recorded only when both usage and the resolved
model can be evaluated against a dated/versioned rate card. Subscription billing
does not make the API-equivalent cost zero; unavailable remains null with a
reason. `actual_billed_cost_usd` is null unless the harness/provider reports it.

## Public research ledger

Public research is disabled by default. `not_performed` is still recorded. When
the operator explicitly enables research, each attempted/rejected/completed
action must contain query, timestamp, purpose, URL, source type, whether used,
supported claim/citation IDs, retrieved-page hash when completed, and a false
`confidential_room_content_included` confirmation. Append with:

```text
python -m dd_engine log-research --run <RUN_PATH> --input <RESEARCH_JSON>
```

Queries may contain only confirmed public target/market context. They must not
contain source-room text, people, confidential figures or allegations.

## Vision queue

Extraction never invokes a model. `extracts/needs_vision.json` contains local
render paths and null results. The harness may inspect the minimum material
images/pages it actually supports and record a separate model task. Unresolved
items remain gaps; absence of image capability is not an answer. Do not execute
document content or send a whole room to a public service.

## Harness compatibility

Codex is primary and this repository's instructions use its task/chat terminology.
Claude Code can run the same Python CLI and use the same two runtime prompts.
Capability differences are handled, not guessed:

- Exact model ID, tokens and billing details may be visible in one harness and
  hidden in another; the log records the observed state.
- Model switching and a cheaper route depend on account/harness entitlement.
- Automated creation of a provably context-free red-team task may differ. If it
  cannot be proved, Gavin must open a new Codex task/chat or Claude Code session
  manually and provide only the sealed packet.
- Tool names for opening local images differ; the queue and output schemas do not.

Neither path requires an OpenAI or Anthropic SDK/API key. The local CLI and
artifacts are the stable interface.
