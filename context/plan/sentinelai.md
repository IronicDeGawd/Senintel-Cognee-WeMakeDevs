# SentinelAI — Implementation Plan

> Approved plan (source of truth for implementation). Mirror of the plan accepted in plan mode.

## Context

**Why:** Building SentinelAI from scratch — one autonomous agent guarding the whole software delivery lifecycle across three layers: code (pre-prod), production health, and AI/LLM quality. Merged-idea doc (`Google Cloud Rapid Agent Hackathon.docx`) frames these as three "pillars" of one problem. Repo started empty except that doc.

**Goal:** All three pillars built for real, each behind a real/simulator switch so the demo never depends on live external events. Hackathon deadline **June 11** (planning started June 5 → ~6 days). Primary prize track: **Dynatrace** (Pillar 2 centerpiece).

**One-sentence pitch:** "SentinelAI is the autonomous engineer that watches your entire delivery pipeline so your team can ship faster and sleep better."

## Locked Decisions

| Decision | Choice |
|---|---|
| Scope | All 3 pillars real, each with a **simulator fallback** behind every external feed |
| Agent framework | **Google ADK** (Python, local-testable, deploys to Cloud Run) |
| LLM | Gemini via AI Studio key (user obtains first) |
| Python env | **venv + pip** + `requirements.txt` |
| Frontend | **Next.js** unified dashboard |
| Credentials user provides first | **GCP + Gemini key** only. GitLab / Dynatrace / Arize → simulated now, wired to real later |
| Storage | MongoDB (incident KB), BigQuery (eval trends), Vertex AI embeddings (similarity) |
| Infra | Cloud Run (services), Cloud Scheduler (5-min poll) |

## Core Architectural Principle — Adapter + Mode Switch

Every external integration sits behind a common interface with a factory returning **real MCP client** or **simulator** based on env (`SENTINEL_<X>_MODE=real|sim`). Build/test against simulators today, flip to real when credentials land, keep simulator as demo-day safety net.

```
integrations/<name>/
  interface.py     # abstract contract
  real.py          # MCP-backed implementation
  simulator.py     # deterministic fake events/data
  factory.py       # returns real|sim from env
```

## Repo Layout

```
SentinelAI/
  agents/sentinel/
    agent.py                 # ADK root orchestrator
    pillars/
      code_guardian/         # Pillar 1
      production_sentinel/   # Pillar 2
      ai_quality_gate/       # Pillar 3
    tools/                   # ADK tools wrapping integration adapters
  services/
    webhook_gateway/         # GitLab webhook listener (Pillar 1 trigger)
    poller/                  # Scheduler-driven Dynatrace poll (Pillar 2 trigger)
    eval_runner/             # Arize eval runner (Pillar 3 trigger)
    dashboard_api/           # aggregates the 3 signals
  integrations/{gitlab,dynatrace,arize}/
  storage/{mongo,bigquery,embeddings}/
  simulators/
  shared/                    # config, models, logging
  dashboard/                 # Next.js
  infra/                     # Dockerfiles, Cloud Run + Scheduler config
  tests/
  context/
  .env.example  requirements.txt  docker-compose.yml
```

## Key Dependencies

- Agent/LLM: `google-adk`, `google-genai`
- Services: `fastapi`, `uvicorn`, `httpx`, `pydantic`, `pydantic-settings`
- Storage: `motor`, `google-cloud-bigquery`, `google-cloud-aiplatform`
- Pillar 2 output: `slack_sdk`
- Pillar 3: `arize-phoenix` (local), `arize` (cloud, optional)
- Dashboard: Next.js (+ shadcn/ui TBC)
- Dev/test: `pytest`, `pytest-asyncio`, `ruff`

## Build Phases

- **Phase 0 — Foundation:** scaffold, venv, requirements, .env.example, docker-compose (Mongo), shared config/logging/models, integration interface+factory+simulator stubs, ADK hello-world on Gemini.
- **Phase 1 — Pillar 2 (Dynatrace):** adapter (sim+real), poller service, Gemini root-cause, Mongo incident KB + Vertex embeddings similarity, Slack briefing + incident ticket, Cloud Scheduler.
- **Phase 2 — Pillar 1 (GitLab):** adapter, webhook gateway, diff review + CI diagnosis, MR comment post, cross-link to Pillar 2 commit correlation.
- **Phase 3 — Pillar 3 (Arize/Phoenix):** adapter, eval suite gen, baseline compare, deploy block, BigQuery trends.
- **Phase 4 — Dashboard:** Next.js 3 signal cards + aggregation API, responsive.
- **Phase 5 — Deploy + Demo:** Dockerfiles, Cloud Run, Scheduler, end-to-end sim dry run, backup recording, submission.

## Verification

- Per phase, sim mode: pytest unit tests + run service locally + trigger (simulated POST / `adk run`) → confirm output artifact.
- Cross-pillar: simulate incident → confirm Code Guardian correlation fires.
- Dashboard: `npm run build` + Playwright screenshots at 375/768/1280.
- Real wiring: flip `SENTINEL_<X>_MODE=real`, re-run trigger, confirm parity.
- Demo dry run: full docker-compose stack, sim mode, recorded.

## Open Items / Risks

- Scope vs deadline (HIGH): simulator-first ordering protects demo; real wiring for Pillars 1/3 deferred first if short on time.
- GCP billing needed for Cloud Run/Scheduler/BigQuery/Vertex (free credit covers).
- GitLab webhooks need public URL (ngrok local / Cloud Run prod).
- Slack target (channel/webhook) — confirm at Phase 1.
- shadcn/ui — confirm at Phase 4.
- Dynatrace real anomalies need a monitored demo app; trial = credentials + authenticity, simulator = repeatable events.
