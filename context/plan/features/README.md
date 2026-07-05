# SentinelAI — Feature Plans (parallel-ready)

Standalone, step-by-step build plans so two+ devs work in parallel without colliding.
Companion to [../build-steps.md](../build-steps.md) (overall sequence) and
[../experiment-spike.md](../experiment-spike.md) (Step 0, already **GO**).

## Local dev setup (every dev — one-time, ~10 min)

Foundation is **already built and on `main`**. To run it locally:

```bash
# 1. Python env
python -m venv .venv
.venv\Scripts\activate                     # Windows  (source .venv/bin/activate elsewhere)
pip install -r requirements.txt

# 2. Google auth — Gemini runs for REAL via Vertex AI + ADC (no API keys in repo)
#    Install gcloud SDK first if missing:  winget install --id Google.CloudSDK
gcloud auth application-default login                       # browser consent → writes ADC file
gcloud auth application-default set-quota-project <PROJECT_ID>
gcloud config set project <PROJECT_ID>

# 3. Env file (gitignored; copy the template)
cp .env.example .env                       # set GOOGLE_CLOUD_PROJECT=<PROJECT_ID>; leave SENTINEL_*_MODE=sim

# 4. Verify
ruff check
pytest                                     # 5/5 green
python scripts/run_agent.py "say hi"       # live Gemini turn over Vertex
```

Notes:
- **ADC ≠ gcloud login.** `application-default login` authorizes *client libraries* (our code). `gcloud auth login` is a separate CLI-account login only needed for `gcloud` admin commands (e.g. `gcloud services enable`). Vertex AI API must be enabled on the project once.
- No `GEMINI_API_KEY` needed. The optional key path exists only as a fallback (`GOOGLE_GENAI_USE_VERTEXAI=false`).
- You need a **GCP project with billing/free-credits**. Whole-hackathon Gemini cost ≈ $5–10.

## Mock vs. real — the auth/data split (do not confuse)

> **Gemini = always REAL** (Google Vertex API via ADC). It is the product; never mock it.
> **Partner feeds (Dynatrace / GitLab / Arize) = MOCK by default** (`SENTINEL_<X>_MODE=sim`),
> flipped to real MCP with one env var once that partner's creds exist.

| Dependency | Default | Real path | Switch |
|---|---|---|---|
| Gemini (reasoning) | **real** Vertex+ADC | — | always on |
| Dynatrace (P2) | `sim` fixtures | `McpToolset` → dynatrace-mcp-server | `SENTINEL_DT_MODE=real` + DT creds |
| GitLab (P1) | `sim` fixtures | GitLab MCP (Duo) | `SENTINEL_GL_MODE=real` + GitLab token |
| Arize (P3) | `sim` fixtures | Phoenix MCP | `SENTINEL_ARIZE_MODE=real` + Phoenix creds |

Build + test against the simulator; Gemini reasons over it for real. No partner creds needed to develop any pillar.

## The rule that makes parallel work possible

> Every pillar builds against its **simulator** behind a shared **interface**.
> Nobody waits on anyone's real API/MCP creds. Real wiring is flipped in later
> with one env var. The only blocking prerequisite is **Foundation** — once the
> contracts in [00-foundation.md](00-foundation.md) land, all pillars are
> independent.

```
        [00 Foundation: contracts + scaffold]   <-- BLOCKING, ~half day, one owner
                          |
        +-----------------+-----------------+----------------+
        |                 |                 |                |
  [02 Production    [01 Code         [03 AI Quality    [04 Dashboard]
   Sentinel/DT]      Guardian/GL]     Gate/Arize]      (reads signals)
   PRIME A           PRIME B          THIRD             needs signal shape only
```

## Plans

| # | Feature | Pillar | Partner | Priority | Plan |
|---|---|---|---|---|---|
| 00 | Foundation + contracts | — | — | **BLOCKING first** | [00-foundation.md](00-foundation.md) |
| 02 | Production Sentinel | P2 | Dynatrace | **Prime A** (prize) | [02-production-sentinel.md](02-production-sentinel.md) |
| 01 | Code Guardian | P1 | GitLab | **Prime B** | [01-code-guardian.md](01-code-guardian.md) |
| 03 | AI Quality Gate | P3 | Arize/Phoenix | Third (stretch) | [03-ai-quality-gate.md](03-ai-quality-gate.md) |
| 04 | Dashboard | — | — | Needed for demo | [04-dashboard.md](04-dashboard.md) |

## Recommended split (2 devs, ~3 days)

| | Dev A | Dev B |
|---|---|---|
| **Day 1 AM** | **00 Foundation** (contracts, scaffold, models, factory) — both pair on the contracts for the first ~1h, then A owns it | Read research, set up local env, write **P1 + P2 simulator fixtures** against the agreed contract |
| **Day 1 PM → Day 2** | **02 Production Sentinel (Dynatrace)** — prime/prize, go deep | **01 Code Guardian (GitLab)** incl. the P2↔P1 correlation hook |
| **Day 2 PM** | Dynatrace real wiring + self-observability | **04 Dashboard** (3 cards + aggregation API) |
| **Day 3** | Deploy (Cloud Run + Scheduler), end-to-end sim dry run | Record ≤3-min video, **03 stretch** if time, polish |

> 3+ devs: third dev takes **04 Dashboard** from Day 1 (only needs the `Signal` shape) then **03 AI Quality Gate**. Plans are standalone — assign by file, not by person.

## Hard coordination points (the only places parallel work can collide)

1. **`shared/models.py` + `integrations/base.py`** — the contracts. Agree these in the Day-1 pairing hour. After that they are **append-only**; change them only via a quick sync so nobody's simulator breaks.
2. **`Signal` schema** (what the dashboard consumes) — frozen in Foundation so Dashboard can start immediately.
3. **The P2→P1 correlation call** — Code Guardian exposes `get_mr_diff(commit)`; Production Sentinel calls it. Defined as an interface method so each side mocks the other.
4. **`.env.example`** — append-only; each pillar adds its own `SENTINEL_<X>_MODE` + creds keys, never edits others'. Core Google auth block (`GOOGLE_GENAI_USE_VERTEXAI` / `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION`) is already there — don't change it.

## Definition of done (every feature)
- Simulator path works end to end (pytest + local run + trigger → artifact).
- Real path flips with `SENTINEL_<X>_MODE=real` and reaches parity (or is logged as stretch).
- Emits a `Signal` the dashboard renders.
- One committed demo artifact (screenshot / saved output / recording).
- Notes in `context/progress.md`.

## Carry-forward from the spike (already proven — reuse, don't re-derive)
- `McpToolset` stdio mount snippet → now `shared/mcp.py` `stdio_mcp()` (with connect retry).
- Simulator payload shapes for `list_problems` + `get_mr_diff` (in `experiment/fixtures/`).
- The briefing+correlation prompt (in `experiment/sentinel/prompt.py`).
- Gemini call wrapper with retry/backoff on 429/5xx → `shared/llm.py` `generate()`.
- Known gotchas: Gemini 503/429 under load → handled by `shared/llm.py` retry; Windows MCP stdio flaky → connect retry in `shared/mcp.py`, or deploy on Linux/Cloud Run.
