# 02b — Real Dynatrace + Demo App + Self-Observability (P2-7, P2-8)

> Owner: Dev A. Builds on [02-production-sentinel.md](02-production-sentinel.md)
> (P2-1..P2-6 done in sim). Branch `feature/production-sentinel`.
> Approved Jun 9 2026. Implement Stage 1 first (probe-first, incremental).

## Context

Production Sentinel is demo-complete **in sim** (canned problems → RCA →
correlate to commit `abc1234` → KB → briefing → `Signal`). All data is fixtures.

The Dynatrace track **mandates real partner-MCP integration**, and a convincing
demo needs the briefing over *real* Dynatrace data. The tenant is empty —
Dynatrace only reports problems if it monitors a live app. So we (a) wire the
real Dynatrace MCP, and (b) stand up a small monitored "checkout-service" demo
app producing a real latency anomaly mirroring the canned story. P2-8 rides the
same OTel→Dynatrace pipeline (SentinelAI watches itself).

**Sim stays the guaranteed fallback; all real behavior is mode-flagged and must
never regress sim.**

## Decisions (confirmed)
- Demo app → **Cloud Run** ($300 GCP credits).
- Programmatic (poller/briefing) real path → **Dynatrace MCP over stdio** (one
  integration; agent already mounts the MCP toolset).
- **Probe-first, incremental** sequencing.

---

## Stage 1 — Real MCP wiring + tenant probe (low risk, no app)

**New `shared/mcp_client.py`** — programmatic (non-ADK) stdio MCP client via the
`mcp` lib (already a dep): `stdio_client` + `ClientSession`. Helper
`call_tool(command, args, env, tool, arguments) -> dict` wrapped in
`asyncio.run`, with tenacity connect-retry (Windows stdio was flaky in the
spike). Per-call session is fine for a 5-min poller (note spawn cost as future
optimization).

**New `integrations/dynatrace/real.py`** — `DynatraceReal(DynatraceIntegration)`
(the lazy `_real()` import in `factory.py` already expects this class):
- `healthcheck()` → trivial tool call → bool.
- `list_problems() -> list[Problem]` → MCP `list_problems`, normalize to
  `Problem`. **Normalizer finalized after the probe** (start from the simulator's
  `_to_problem`).
- `execute_dql(query) -> dict` → MCP `execute_dql` (Grail budget).
- `recent_deployments(service) -> list[dict]` → DQL deploy events →
  `{version, commit, timestamp}`; `[]` if absent (P2-4 degrades gracefully).

MCP env from `settings`: `DT_ENVIRONMENT`, `DT_PLATFORM_TOKEN`,
`DT_GRAIL_QUERY_BUDGET_GB` (small cap, e.g. 50), `DT_MCP_DISABLE_TELEMETRY=true`.

**New `scripts/probe_dynatrace.py`** — forces real mode, calls `list_problems` +
a tiny `execute_dql` + `recent_deployments`, prints raw JSON. User runs it once
(token in `.env`); we read output to confirm token/scopes and lock normalizers.

**Config/env:** `config.py` add `dt_grail_query_budget_gb: int = 50`.
`.env.example` add it + required Platform-Token scopes (`app-engine:apps:run`,
`storage:*:read` for DQL, `storage:events:write` + `document:documents:write` +
`app-settings:objects:read`) + reminder to use the `apps.dynatrace.com` URL.

**Tests:** after the probe reveals the real shape, save one scrubbed sample as a
fixture and unit-test the normalizer offline.

**Verify:** set `SENTINEL_DT_MODE=real` + token in `.env`; run
`python scripts/probe_dynatrace.py`; then poller `POST /run` returns a `Signal`
from the real path.

---

## Stage 2 — Demo "checkout-service" on Cloud Run, OTel → Dynatrace

**New `demo/checkout_service/`**
- `app.py` — FastAPI, `service.name = checkout-service`. `GET /health`,
  `POST /checkout` (fast), degrade toggle (`/admin/degrade` or env
  `CHECKOUT_DEGRADED`) simulating the N+1 from commit `abc1234` (per-item lookups
  with sleeps) → p95 climbs.
- OTel: `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`,
  `opentelemetry-instrumentation-fastapi`. Export traces (+metrics) to
  `${DT_ENVIRONMENT}/api/v2/otlp/v1/traces`, header `Authorization: Api-Token
  <ingest-token>`.
- `Dockerfile` + `demo/checkout_service/requirements.txt`.
- Deploy `gcloud run deploy checkout-service ...`; ingest token via **Secret
  Manager**, not plaintext.

**New `scripts/generate_load.py`** — drive traffic at the Cloud Run URL, flip
degrade partway → real latency spike Dynatrace ingests.

**Token note:** ingest needs a classic **Api-Token** with `openTelemetryTrace.
ingest` (+ `metrics.ingest`, `logs.ingest`) — distinct from the Platform Token
the MCP reads with. Both documented in `.env.example`.

**Reality check:** Davis raising a formal *problem* needs baseline + time, not
guaranteed in a short window. The reliable real signal is the **latency
timeseries via `execute_dql`** through the MCP — proves real MCP usage + feeds a
real briefing. If Davis raises a problem, `list_problems` lights up too — bonus.

**Verify:** load script → checkout-service spans/metrics in Dynatrace →
`execute_dql` via MCP returns the real latency rise → poller real briefing
reflects real numbers.

---

## Stage 3 — Self-observability (P2-8)

**New `shared/otel.py`** — OTel tracer provider exporting to the Dynatrace OTLP
endpoint (Api-Token) + `openinference-instrumentation-google-adk` to capture ADK
runs. Behind `SENTINEL_OTEL_ENABLED` (default false). Init at poller startup
(`services/poller/main.py`).

**Verify:** trigger a cycle → find a SentinelAI span in Dynatrace
(`fetch spans | filter ... sentinel ...`).

---

## Cross-cutting
- **Secrets:** tokens only in `.env` (gitignored) + Cloud Run Secret Manager.
  `.env.example` gets placeholders + scope docs. Never commit a token; run
  `secret-scanner` before any env/config commit.
- **Sim stays default & pristine** — real is mode-flagged.
- **Cost:** small `DT_GRAIL_QUERY_BUDGET_GB`, short DQL windows (12–24h), sim for
  tests (few live Gemini calls).

## Files at a glance
- New: `shared/mcp_client.py`, `integrations/dynatrace/real.py`,
  `scripts/probe_dynatrace.py`,
  `demo/checkout_service/{app.py,Dockerfile,requirements.txt}`,
  `scripts/generate_load.py`, `shared/otel.py`, normalizer test + fixture.
- Edit: `shared/config.py`, `.env.example`, `requirements.txt` (otel/openinference
  for Stage 3), `services/poller/main.py` (otel init).
- Reuse: `integrations/dynatrace/factory.py` (`_real()` hook present),
  `integrations/dynatrace/simulator.py` `_to_problem` (normalizer template),
  `shared/mcp.py` (retry pattern), `agents/.../agent.py` (agent mounts MCP).
