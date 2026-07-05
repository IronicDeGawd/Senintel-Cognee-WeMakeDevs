# 02 — Production Sentinel (Pillar 2, Dynatrace) — PRIME A / prize track

> Owner: Dev A. The centerpiece. Go deep on the Dynatrace MCP — this is the
> bucket the submission is judged in. Build first, after Foundation.
> Prereq: [00-foundation.md](00-foundation.md) contracts frozen.
> Reuse: spike `dt_sim.py`, `dt_real.py`, fixtures, briefing prompt.

## What it does (demo arc, prime half)
Cloud Scheduler fires every 5 min → agent calls Dynatrace `list_problems` →
Gemini does root-cause reasoning over the problem chain → checks the incident KB
("seen this before?") → asks Code Guardian "which commit?" → delivers a **morning
briefing + draft incident** to Slack + a Dynatrace notebook. Plus: the agent is
OTel-instrumented and watches **itself** in Dynatrace.

## File map
```
integrations/dynatrace/
  interface.py     # DynatraceIntegration(Integration): list_problems(), execute_dql(), send_briefing()
  simulator.py     # canned list_problems/execute_dql (promote experiment/fixtures/problems.json)
  real.py          # shared.mcp.stdio_mcp("npx", ["-y","@dynatrace-oss/dynatrace-mcp-server@latest"], env=DT_*)
  factory.py       # get(mode) -> sim|real
agents/sentinel/pillars/production_sentinel/
  agent.py         # sub-agent: tools = DT (by mode) + correlate(commit) + kb tools
  prompt.py        # promote experiment/sentinel/prompt.py briefing+correlation instruction
  rca.py           # Gemini RCA over problem chain (uses shared.llm)
services/poller/
  main.py          # FastAPI endpoint /run -> runs the agent one turn; Cloud Scheduler hits it
storage/
  incident_kb.py   # Firestore: store/lookup incidents (NOT MongoDB — competing-partner rule)
  embeddings.py    # Vertex AI embeddings: similarity "have we seen this?"
delivery/
  slack.py         # MCP send_slack_message OR slack_sdk fallback
```

## Step-by-step

### P2-1 — Simulator first (no creds)
- Promote `experiment/fixtures/problems.json` → `integrations/dynatrace/simulator.py`
  returning `list[Problem]` (the F3 model). Add a canned `execute_dql` response.
- `factory.get("sim")` returns it. Unit test: returns 2 problems, shared root cause.

### P2-2 — RCA + briefing agent (sim)
- `production_sentinel/agent.py`: ADK sub-agent, tools = sim `list_problems` +
  `execute_dql`. Prompt = promoted spike instruction.
- `rca.py`: Gemini (via `shared.llm`, retry-wrapped) turns problems → `Incident`.
- Run locally → confirm briefing matches spike quality. **Artifact:** saved briefing.

### P2-3 — Incident KB + similarity
- `storage/incident_kb.py`: Firestore collection `incidents`; `save(Incident)`,
  `recent(service)`. (Local: Firestore emulator or a JSON-file shim behind the same
  interface so Dev A isn't blocked on GCP.)
- `embeddings.py`: Vertex AI text-embedding; cosine vs. stored incidents → "similar
  past incident" line in the briefing. Sim fallback: precomputed vectors.

### P2-4 — Cross-pillar correlation hook (the money shot)
- Agent gets a `correlate(commit)` tool that calls **Code Guardian's**
  `get_mr_diff` via its interface (P1 owns the impl; here mock with P1's simulator
  so Dev A is unblocked). Gemini links anomaly → commit → diff.
- This is the demo climax — prioritize over breadth of DQL queries.

### P2-5 — Delivery
- `delivery/slack.py`: prefer DT MCP `send_slack_message`; fallback `slack_sdk`
  with `SLACK_WEBHOOK_URL`. Also `create_dynatrace_notebook` for the incident.
- Sim mode: write the briefing to `out/briefing.md` instead of posting.

### P2-6 — Poller service + Scheduler
- `services/poller/main.py`: FastAPI `POST /run` → one agent turn → emits a
  `Signal(pillar="production", ...)`. Local: `curl` it. Prod: Cloud Scheduler 5-min.

### P2-7 — Real Dynatrace wiring (flip `SENTINEL_DT_MODE=real`)
- `real.py` mounts `@dynatrace-oss/dynatrace-mcp-server` via `shared.mcp.stdio_mcp`,
  env `DT_ENVIRONMENT` (+ `DT_PLATFORM_TOKEN` or browser OAuth), `tool_filter=
  ["list_problems","execute_dql","send_slack_message","create_dynatrace_notebook"]`.
- Mind Grail query budget (`DT_GRAIL_QUERY_BUDGET_GB`). Re-run poller → parity.

### P2-8 — Self-observability (strong track story)
- `pip install openinference-instrumentation-google-adk`; export ADK OTel traces to
  Dynatrace `…/api/v2/otlp` with an Api-Token. SentinelAI appears in Dynatrace.

## Verification
- Sim: pytest (simulator + RCA shape) + local poller `POST /run` → `briefing.md` + `Signal`.
- Correlation: feed the canned incident → confirm it names the suspect commit + diff.
- Real: flip mode, hit a real `list_problems`, confirm briefing parity (or log stretch).
- Self-obs: confirm one span lands in Dynatrace.

## Definition of done
- Briefing + draft incident generated from `list_problems` (sim ✓, real ✓-or-logged).
- Correlation hook fires. Slack/notebook delivery (or `out/` in sim).
- `Signal(pillar="production")` emitted for the dashboard.
- Committed artifact: a real briefing output + a Dynatrace screenshot.

## Risks
- Real DT MCP auth (OAuth/Platform token, Grail budget) = top time-sink → sim is the
  guaranteed demo. Keep sim path pristine.
- Gemini 503 under load → already retry-wrapped via `shared.llm`.
