# 05 — Real Partner Integrations (Dynatrace + Arize) — Jun 10

> Before the dashboard ships, both partner pillars need to read real partner
> data, not fixtures. Sim mode stays as the fallback. Track is **Dynatrace**
> (highest weight); Arize is the strongest secondary integration.

## Current state of each partner

### Dynatrace — wiring done, data missing
- `integrations/dynatrace/real.py` (`DynatraceReal`) talks to the live MCP
  server via `npx mcp-remote {DT_ENVIRONMENT}/api/v4/mcp` over stdio.
  Live-verified during the Jun 9 spike: healthcheck OK, MCP tools callable,
  Grail budget tracking live (0/50 GB).
- `scripts/probe_dynatrace.py` exists.
- `agents/sentinel/pillars/production_sentinel/agent.py` real branch mounts
  the MCP server in `_build_tools()`.
- `shared/observability.py` ships ADK traces to Dynatrace OTLP.
- **GAP**: the connected tenant has zero Davis Problems. There's nothing
  for `list_problems` to return, so the cycle has nothing real to RCA.

### Arize / Phoenix — no real adapter at all
- `integrations/arize/` contains `interface.py`, `simulator.py`, `factory.py`
  and `fixtures/eval_runs.json` only.
- `factory.py::_real()` imports `from .real import ArizeReal` — this
  ImportError trips the moment anyone flips `SENTINEL_ARIZE_MODE=real`.
- `agents/sentinel/pillars/ai_quality_gate/agent.py` real branch mounts
  `npx @arizeai/phoenix-mcp` (dormant; the FunctionTools wrappers never
  get exercised against a real Phoenix instance).
- **GAP**: no `ArizeReal` adapter, no Phoenix instance to talk to, no real
  evaluations on file, no datasets.

---

## Path A — Dynatrace: get real Davis Problems flowing

Three options, pick one.

### A1 — Real OneAgent monitoring a sample app (most credible, heaviest)
1. Spin up the smallest possible monitored target:
   - Option (a): one Cloud Run service or a $5/mo Compute Engine f1-micro
     running a 30-line FastAPI app with two endpoints `/fast` and `/slow`.
     `/slow` calls `time.sleep(2)` to spike p95.
   - Option (b): a Docker container running locally for the demo only —
     fastest but not part of the always-on hosted submission.
2. Install Dynatrace OneAgent (Linux one-liner from the tenant UI), restart
   the container/host.
3. Wait ~5 min for OneAgent to register and start instrumenting.
4. Drive load: 1 minute of `hey -z 60s -c 20 https://target/slow` from
   anywhere. p95 will jump 50ms → 2000ms+. Davis raises a Problem
   automatically (latency degradation, monitored entity ID, evidence).
5. **Our adapter's `list_problems()` now returns a real `Problem` object**.
   Production Sentinel runs full RCA + Gemini correlation against it.
6. (Bonus) After Davis closes the Problem, leave the spike script running
   on a Cloud Scheduler cron every 4 hours so the demo always has fresh
   data within the trial window.

**Effort:** ~3 hours.
**Cost:** trial tenant ($0 for 15 days) + Compute Engine f1-micro free tier OR
local Docker.
**Quality:** highest. Real Davis-detected anomaly; real entity IDs; real
evidence numbers; OneAgent visible in the tenant UI for screenshots.

### A2 — Ingest synthetic Problems via Dynatrace Events API (medium)
1. Use the Davis Events API: POST a custom `EVENT_TYPE=PERFORMANCE` event
   tagged to a synthetic monitored entity. Davis ingests it and surfaces it
   in `list_problems` after a short correlation window.
2. Script: `scripts/seed_dynatrace_problem.py` that POSTs one synthetic event
   with realistic evidence (service name, latency numbers, deployment SHA in
   custom properties).
3. Re-run before each demo recording.

**Effort:** ~1.5 hours.
**Cost:** trial tenant only.
**Quality:** decent — real Davis ingestion path, but the source is synthetic
which a careful judge can spot in the Problem's `source` field. Honest if we
label it "synthetic event for demo".

### A3 — Public Dynatrace Playground / sample tenant (cheapest, fragile)
1. Some Dynatrace partner evangelists publish playground tenants with
   continuously-generated synthetic anomalies. Hunt down a working one
   (Discord, Dynatrace University labs).
2. Switch `DT_ENVIRONMENT` + `DT_PLATFORM_TOKEN` to point there.

**Effort:** ~1 hour (search + verify).
**Cost:** $0.
**Quality:** lower — playground tenants have rotating credentials; the demo
breaks if the URL gets recycled. Not recommended for submission.

**Recommendation: A1.** A2 is acceptable if time is tight; A3 is too fragile.

---

## Path B — Arize / Phoenix: build the real adapter + host Phoenix

Three options for the Phoenix instance, then one adapter build either way.

### B-host-1 — Self-host Phoenix (Docker on Cloud Run)
1. Add a fourth Cloud Run service: `sentinelai-phoenix`, image
   `arizephoenix/phoenix:latest`, port 6006. Persist with a small Cloud
   Storage bucket or skip persistence for the demo.
2. Use Phoenix's OSS endpoints (`/v1/datasets`, `/v1/experiments`, etc.).
3. No Arize SaaS account needed.

**Effort:** ~1 hour for the service + 30 min for auth/CORS.
**Cost:** Cloud Run free tier; bucket cents/mo.
**Quality:** real Phoenix, our infra.

### B-host-2 — Arize SaaS free tier
1. Sign up at `app.phoenix.arize.com` (Phoenix Cloud — Arize's hosted
   Phoenix). Free tier exists; takes ~5 min to register.
2. Get API key + endpoint.
3. Phoenix MCP server connects via env vars.

**Effort:** ~30 min setup.
**Cost:** $0 within free tier.
**Quality:** real Arize hosted infra, judges see arize.com in screenshots.

### B-host-3 — Self-host Phoenix locally for the demo only
Same Docker image, on the dev box. Cheapest but the dashboard can't reach
it from Cloud Run. Not viable for the hosted submission.

**Recommendation: B-host-2.** Arize SaaS lands the partner name in the
demo most credibly and skips infra work.

### B-adapter — Build `integrations/arize/real.py`
Either hosting path needs this. Maps the same `ArizeIntegration` interface
the simulator implements:

```python
class ArizeReal(ArizeIntegration):
    def run_eval(self, suite: str, dataset: str | None) -> EvalResult: ...
    def get_baseline(self, suite: str) -> EvalResult: ...
    def healthcheck(self) -> bool: ...
```

Talks to the Phoenix REST API (with `phoenix-mcp` reserved for the agent's
conversational path). Same hybrid posture we landed on for GitLab:
- **REST** for the data path the cycle uses (deterministic, headless).
- **MCP** for the agent's tool-call path (proves the partner-MCP claim).

Implementation steps:
1. Pull `phoenix-client` Python SDK or call REST directly with `httpx`.
2. `run_eval(suite, dataset)`:
   - Create an experiment in the suite's project (idempotent: re-use if
     name exists).
   - Run the experiment on the dataset using a pre-registered LLM task and
     three evaluators: `hallucination`, `qa_relevance` (drift proxy),
     `not_unsafe`.
   - Pull the experiment summary; compute `hallucination_rate` (% rows
     where hallucination evaluator returned `incorrect`) and `drift` (mean
     drift score vs baseline experiment).
   - Return `EvalResult(suite, hallucination_rate, drift, passed,
     threshold)` — `passed` computed via `gate.evaluate` like sim mode.
3. `get_baseline(suite)`:
   - Fetch the most recent past experiment tagged `baseline` in that suite.
4. Seed data: ship a one-time script
   `scripts/seed_phoenix.py` that creates `checkout-llm-v1` (baseline,
   passes) and `checkout-llm-v2` (regression, fails) projects + datasets
   + tasks in Phoenix on first run. Idempotent.

**Effort:** ~3 hours adapter + ~1 hour data seeding.

---

## Cross-cutting work (shared by both partners)

### Config + secrets
- `.env`: `DT_PLATFORM_TOKEN`, `PHOENIX_ENDPOINT`, `PHOENIX_API_KEY` (already
  declared in `shared/config.py`; just need real values).
- Secret Manager: 3 new secrets — `dt-platform-token`, `phoenix-endpoint`,
  `phoenix-api-key`. Mount on poller (DT) + eval_runner (Phoenix) + dashboard_api
  (read-only).
- Update `infra/deploy.sh` per-service to set the right `SENTINEL_*_MODE`
  and inject the right secrets.

### Tests
- `tests/test_arize_real.py` — adapter tests with `httpx` mocked, ~6 cases.
- Live verification scripts kept out of pytest:
  - `scripts/probe_dynatrace.py` — already exists, re-run after Path A.
  - `scripts/probe_phoenix.py` — new, mirrors probe_gitlab.py.

### Demo arc end-to-end
With A1 + B-host-2:
1. Cron drives load on the sample app → Davis raises a Problem.
2. Poller runs (Cloud Scheduler every 5 min), calls real
   `list_problems()`, gets the real Davis Problem.
3. RCA → correlation → KB save → Signal saved to Firestore.
4. Independently, eval_runner runs the `checkout-llm-v2` suite against
   Phoenix → real `EvalResult` with hallucination_rate above threshold →
   `Signal(ai_quality, critical, "Deploy blocked: ...")` → Firestore.
5. Dashboard pulls both Signals + renders them with the production card
   leading and the AI-quality card showing the live `EvalResult`.

---

## Step-by-step (sequenced, no overlap with dashboard work)

### R1 — Dynatrace path (pick A1 / A2 / A3, recommend A1)
- Provision sample target (Cloud Run service or VM with OneAgent).
- Install OneAgent + verify host appears in tenant UI.
- Issue Platform Token (`dt0s16.`) with scopes:
  - `app-engine:apps:run`, `storage:problems:read`, `storage:events:read`,
    `storage:logs:read`, `storage:metrics:read`, `storage:buckets:read`,
    `storage:events:write` (for `send_event` if we use it).
- Add token to Secret Manager + `.env`.
- Drive synthetic load → confirm Davis raises Problem.
- Re-run `scripts/probe_dynatrace.py` → confirm `list_problems` returns the
  real Problem.
- Flip `SENTINEL_DT_MODE=real` on the poller Cloud Run service.
- Smoke: `curl -X POST {poller-url}/run` → real Signal in Firestore.

### R2 — Phoenix instance (pick B-host-1 / B-host-2, recommend B-host-2)
- Register at `app.phoenix.arize.com`, get API key + endpoint.
- Smoke from CLI: `curl -H "Authorization: Bearer $KEY" $ENDPOINT/v1/projects`.
- Add `PHOENIX_*` to Secret Manager + `.env`.

### R3 — Build `integrations/arize/real.py`
- Implement `ArizeReal` per Adapter spec above.
- Defensive normalizer for experiment summary JSON (we don't yet know the
  exact shape; probe finalises it).

### R4 — Probe + seed Phoenix
- `scripts/probe_phoenix.py`: list projects, run one experiment on
  `checkout-llm-v2`, print raw payload.
- `scripts/seed_phoenix.py`: idempotent seed of two suites (`v1` baseline,
  `v2` regression) so the gate has consistent data to evaluate.

### R5 — Tests + ruff
- `test_arize_real.py` (~6 cases, httpx mocked).
- Update `test_arize_simulator.py` if any contract field shifts.
- 103 → ~109 tests, all green.

### R6 — Flip pillar modes on Cloud Run
- `sentinelai-poller`: `SENTINEL_DT_MODE=real` + `DT_PLATFORM_TOKEN` secret.
- `sentinelai-eval-runner`: `SENTINEL_ARIZE_MODE=real` + `PHOENIX_*` secrets.
- Re-deploy via `infra/deploy.sh poller eval_runner`.

### R7 — Verify both end-to-end
- `curl POST poller/run` → Signal posted, status warning/critical, real
  Dynatrace Problem id visible in `detail.incident.evidence`.
- `curl POST eval_runner/eval -d '{"suite":"checkout-llm-v2"}'` → Signal
  posted, critical, real Phoenix experiment id in detail.
- Both Signals visible in Firestore.

### R8 — Update setup-runbook.md
- Add Dynatrace OneAgent install steps + token scopes.
- Add Phoenix Cloud registration + secret values + API surface notes.

### R9 — Update progress.md + structure.md
- Mark P2 and P3 as "real-mode live in production".
- Lessons learned section per pillar.

---

## What changes after this lands

| Field | Before | After |
|---|---|---|
| `SENTINEL_DT_MODE` | sim | **real** on poller |
| `SENTINEL_ARIZE_MODE` | sim | **real** on eval_runner |
| Production Sentinel data source | fixtures/problems.json | Davis Problems via DT MCP |
| AI Quality Gate data source | fixtures/eval_runs.json | Phoenix experiments via REST |
| Submission claim | "sim demo, real path wired" | "real, live, partner-data end-to-end" |
| Files added | none | `integrations/arize/real.py`, `scripts/seed_phoenix.py`, `scripts/probe_phoenix.py`, `tests/test_arize_real.py` |
| Cloud Run revisions touched | 0 | poller (re-deploy), eval_runner (re-deploy) |
| Cost | $0 | Free tier + trial; ~$0/mo within trial windows |

---

## Risks

1. **Dynatrace trial expires in 15 days** — Jun 25-ish. Lock down credentials
   to a personal email so renewal isn't a team-blocker. Or move to a paid
   sandbox if the team has one.
2. **Phoenix Cloud free tier limits** — if the free tier has rate caps,
   experiments may fail under repeated demo runs. Mitigate by running each
   experiment idempotently (re-use if exists) instead of fresh-on-every-eval.
3. **OneAgent privacy on a sample VM** — OneAgent harvests system metrics
   including hostname. Use a throwaway hostname (`sentinelai-demo-target`).
4. **Phoenix evaluators are LLM-as-judge** — they hit Vertex Gemini.
   Adds quota pressure if the gate runs frequently. Cap eval_runner concurrency
   to 1 in Cloud Run config.
5. **Dynatrace MCP browser-OAuth gotcha** — the `dt0s16.` Platform Token
   is mandatory for headless Cloud Run. Browser OAuth caches only ~5 min;
   not viable for a long-running service. Verify token scopes before flip.

---

## Open questions (decide before starting)

1. **Dynatrace path**: A1 (real OneAgent on a sample app), A2 (synthetic event
   ingestion), or A3 (public playground)?
2. **Phoenix host**: B-host-1 (self-host on Cloud Run) or B-host-2 (Arize
   Phoenix Cloud free tier)?
3. **Sample target for A1** (if A1): Cloud Run service, GCE f1-micro VM, or
   local Docker?
4. **Order vs dashboard**: complete this fully (R1–R9) before starting
   dashboard D1, or interleave (R1+R2 to unblock backend; dashboard +
   R3–R9 in parallel)?
5. **Do we keep `sim` working as a fallback** after this lands, or drop the
   sim path entirely to reduce surface area? (Keep is cheaper; the modes
   are already mode-switched.)

---

## Recommendation in one paragraph

Do **A1 + B-host-2** in this order: register Arize Phoenix Cloud first
(unblocks Arize while Dynatrace setup is heavier), spin up an `f1-micro`
sample app with OneAgent, drive synthetic load to manufacture a Davis Problem,
build `ArizeReal` against Phoenix's REST API, run `scripts/seed_phoenix.py`
once, flip both Cloud Run services to real mode. Total effort ~7–8 hours.
After this lands, the dashboard plan (`04-dashboard.md`) runs against real
partner data end-to-end.
