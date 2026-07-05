# SentinelAI

> **The autonomous engineer that watches your entire delivery pipeline so your team can ship faster and sleep better.**

Every team builds the same broken loop: Dynatrace pages, Slack panics, someone greps `git log`, someone else opens the MR, someone else digs the eval dashboard. Three tools, three contexts, three humans, fifteen minutes of guessing, then a roll-back nobody trusts.

**SentinelAI runs that loop for you, in 70 seconds, with the receipts.**

One Google ADK agent, three pillars — production observability, code review, AI quality — wired into **real** partner MCP servers. Production spikes, finds the suspect commit, reviews the diff, gates a regressed model, and stamps a single verdict on a live dashboard:

> *Roll back MR !1 / commit `91d2dd2c`*

Live demo: **https://sentinel.parakramlabs.com** *(falls back to [sentinelai-dashboard.run.app](https://sentinelai-dashboard-552996008511.us-central1.run.app/) while DNS cert provisions)*

---

## The 70-second arc

```
1. Dynatrace                                    →  p95 spike, real Davis Problem
2. Production Sentinel (Gemini + DT MCP)        →  RCA → "N+1 in checkout/views.py"
3. Cross-pillar correlation                     →  pins to deploy commit 91d2dd2c
4. Code Guardian (Gemini + GitLab MCP/REST)     →  posts review note on real MR !1
5. AI Quality Gate (Arize-shaped Signal)        →  blocks deploy on 22% hallucination
6. Dashboard                                    →  one envelope, one verdict
```

Every step is **real**: real Davis problem in a real Dynatrace tenant, real Gemini calls on Vertex AI, real GitLab note on a real merge request, real Firestore writes, real Cloud Run cold-starts. The "Run scenario" button on the dashboard fires this end to end on demand.

---

## What makes it interesting

- **Real MCP, not toy MCP.** Headless `npx @dynatrace-oss/dynatrace-mcp-server` over stdio, GitLab Duo `mcp-remote` for the conversational tools, REST fallback for the project-ACL hole in the Duo Beta. We solved the elicit-input-gate problem with a generic auto-approve callback that reads the server's elicit schema and fills required fields — works for any MCP server, not just Dynatrace's.
- **Cross-pillar correlation is the money shot.** The dashboard's correlation panel joins the latest production Signal to the matching code Signal by the *exact* commit SHA. Gemini gets the suspect deploy diff in the same prompt as the draft incident — it names the file and the regression class, not just "investigate."
- **Team Memory via Cognee.** SentinelAI remembers past mistakes and lessons learned using Cognee. When reviewing a new MR, the Code Guardian recalls relevant context from past incidents or reviews, catching repeating patterns (like N+1 queries) that a stateless model would miss.
- **Sim/real switch on every adapter.** `SENTINEL_<PILLAR>_MODE=sim` runs the whole stack on fixtures with deterministic embeddings — no creds, no network, no cost — for tests and demo backup. Flip to `real` for live.
- **One envelope, many pillars.** Every pillar emits the same `Signal {pillar, status, headline, detail, ts}` model. The dashboard speaks Signal. New pillars plug in without dashboard changes.
- **Demo Director seeds the live tenant.** Live demos want repeatability. The Demo Director POSTs scenario data into the real Dynatrace tenant via MCP `send_event` (needs scope `storage:events:write`), Davis promotes those events into real Problems within 30s, the cycle picks them up — actual partner data, scripted story.

---

## Project structure

```
agents/sentinel/
  agent.py                            root ADK orchestrator (assembles pillar tools by mode)
  pillars/
    production_sentinel/              P2 — Dynatrace pillar (RCA, correlation, cycle)
    code_guardian/                    P1 — GitLab pillar (review, CI RCA, note posting)
    ai_quality_gate/                  P3 — Arize-shaped gate
  demo_director/                      D8 — scenario seeder for the demo arc
integrations/
  base.py                             Integration ABC + build_integration mode switch
  dynatrace/                          interface + simulator + real (MCP) + factory
  gitlab/                             interface + simulator + real (REST + MCP) + factory
  arize/                              interface + simulator + factory (real path stretch)
shared/
  models.py                           THE CONTRACT (Signal, Problem, MRReview, EvalResult, Incident)
  config.py                           typed settings + .env load
  mcp_client.py                       one-shot stdio MCP client + auto-approve elicit handler
  llm.py                              Gemini wrapper (Vertex AI + ADC, structured JSON)
  observability.py                    ADK → OTel → Dynatrace OTLP self-tracing
storage/
  signal_store.py                     JsonFileSignalStore (sim) + FirestoreSignalStore (real)
  incident_kb.py                      embedding-similarity incident memory
  eval_trends.py                      eval drift time series
services/
  webhook_gateway/                    GitLab webhook → Code Guardian cycle
  poller/                             Cloud Scheduler → Production Sentinel cycle
  eval_runner/                        Eval suite trigger → AI Quality Gate Signal
  dashboard_api/                      6-endpoint read API the frontend polls (5s)
  demo_director/                      POST /demo/run drives the scenario across pillars
dashboard/                            Next.js 16 + Tailwind v4 + SWR (live + mocked fallback)
infra/deploy.sh                       deploys all 6 Cloud Run services
```

---

## Stack

| Layer | Tech |
|---|---|
| Agent runtime | Google ADK 2.x, Gemini 2.5 Flash on Vertex AI (ADC, no API key) |
| Partner MCP | Dynatrace MCP server v1.8.7 (stdio via `npx`) + GitLab Duo MCP (mcp-remote, OAuth DCR) |
| Backend | FastAPI · uvicorn · httpx · pydantic v2 · tenacity (retry) |
| Frontend | Next.js 16 standalone · Tailwind v4 · SWR · recharts · Instrument Serif + Geist + JetBrains Mono |
| Storage | Firestore (`signals` + `incidents` collections, composite indexes) · Vertex AI text-embedding-005 |
| Self-observability | ADK OpenInference → OTel → Dynatrace OTLP ingest (no-op unless creds set) |
| Infra | 6 Cloud Run services, one shared backend image (Python 3.12 + Node 22), one frontend image, Cloud Build, Secret Manager |
| Tests | pytest 138 green · ruff clean |

---

## Running it

```bash
# One-time
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
gcloud auth application-default login          # Gemini via Vertex AI + ADC
gcloud config set project <your-gcp-project>
cp .env.example .env                            # set GOOGLE_CLOUD_PROJECT + LOCATION

# Sim demo (no creds, no network)
python scripts/run_agent.py "say hi in one sentence"
python scripts/run_briefing.py                  # full P2 cycle on fixtures
python scripts/run_code_review.py abc1234       # full P1 cycle on fixtures
python scripts/run_eval_gate.py                 # full P3 cycle on fixtures

# Dashboard (frontend)
cd dashboard
npm install
npm run dev                                     # http://localhost:3000

# Quality gates
pytest -q                                       # 138 green
ruff check                                      # clean
```

To run **real** — set `SENTINEL_<PILLAR>_MODE=real` plus the credentials in `.env.example` for that pillar. The contracts are identical between sim and real, so agent code never changes.

To deploy to Cloud Run end to end:

```bash
./infra/deploy.sh all                           # builds + deploys all 6 services
```

---

## About the project

This started as a complaint, not an idea. Every place we've shipped software had the same 2am ritual: an observability alert fires, someone opens the problem card and stares at it, someone else greps `git log` for whatever deployed that afternoon, a third person opens the merge request and scrolls the diff hoping something looks guilty. Three tabs, three people — and the answer was usually sitting in plain sight the whole time. The alert and the commit just lived in tools that never talk to each other.

When we picked the Dynatrace track, the pitch wrote itself: stop building another dashboard that *shows* you the incident — build the engineer that *works* it. The agent should do exactly what the senior on-call does: read the Davis problem, find what deployed in the same window, read that diff, and say "roll back MR !1" with the evidence attached. Except in seconds, and without waking anyone up.

Building it on real partner backends — not mocks — was where the actual work went, and the scars are in the code:

- The Dynatrace MCP server gates `send_event` behind a human-approval prompt that silently auto-declines in a headless service. We lost an evening to "Operation cancelled" before writing a schema-aware auto-approve callback (`shared/mcp_client.py`) that reads the server's elicit schema and fills the required fields — it works against any MCP server, not just this one.
- Davis takes 20–60 seconds to promote a custom alert into a real problem. Our first runs raced it and lost, so the cycle falls back to querying the raw events until Davis catches up.
- DQL results came back as markdown with a JSON code-fence buried inside, not as records. There's a parser for that now in `integrations/dynatrace/real.py`, and we're not proud of how long it took to notice.
- Gemini would nail the root-cause analysis and then occasionally drop the suspect commit from its structured output — the one field the whole correlation story hangs on. The pipeline now pins it back deterministically after the model call.

The result is the loop we always wanted at 2am: a real Davis problem, a real Gemini RCA, a real review note on a real merge request, one verdict on one screen, about seventy seconds end to end. Click the button and watch it work.

---

## License

Apache-2.0 — see [LICENSE](LICENSE).
