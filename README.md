# SentinelAI — the PR reviewer that remembers

> **An AI code reviewer with long-term memory. It learns your team's real conventions and past bugs, and applies them to every new pull request — powered by [Cognee](https://www.cognee.ai/).**

Built for the **WeMakeDevs "Where's My Context?"** hackathon.

---

## The problem: AI reviewers have amnesia

Every AI code reviewer starts from zero on every pull request. It re-reads the same static style guide and reviews in a vacuum. It doesn't know that *your* team already shipped an N+1 query that caused an outage last month. It doesn't remember the conventions you agreed on in review threads. The knowledge is there — in your merge history — but the reviewer can't reach it.

**SentinelAI gives the reviewer a memory.**

- When a PR **merges**, it *remembers* every review finding and post-merge bug.
- When the next PR **arrives**, it *recalls* the relevant history and reviews in context — like a senior engineer who's been on the team for years.

The memory is a **knowledge graph plus vector store**, built and queried by Cognee.

---

## How Cognee powers the memory

SentinelAI's code reviewer (the `code_guardian` pillar) wraps Cognee behind a small, swappable interface:

```
remember(item)   →  store a review finding / post-merge bug in the team's graph
recall(query)    →  pull the relevant conventions + past bugs for a new diff
improve()        →  re-index / strengthen the graph (cognify)
forget(dataset)  →  surgical delete of a memory namespace
```

**The lifecycle, end to end:**

```
1. Merge PR  →  remember_review(review)   →  Cognee builds graph nodes + edges
2. New PR    →  recall_context(diff)       →  relevant memory injected into the prompt
3. Review    →  Gemini flags the recurring bug, cites "seen before"
4. Store     →  the new finding is remembered  →  the graph grows
5. Repeat    →  every merge makes the next review smarter
```

**One detail that mattered:** Cognee's semantic retrieval matches on *intent-language*, not raw code. Handing it a unified diff returned nothing — the diff embeds too far from a stored rule like "avoid N+1 queries in loops." So before recall, the diff is summarized to one natural-language sentence (via Gemini) and *that* is the query. This is the difference between memory reaching the review or not. See [`agents/sentinel/pillars/code_guardian/memory.py`](agents/sentinel/pillars/code_guardian/memory.py).

---

## See the memory

Cognee stores the team's memory as a real knowledge graph on disk. Render it:

```python
import cognee
await cognee.visualize_graph("out/cognee_graph.html", dataset="sentinel_team_memory")
```

The result is an interactive graph — nodes for each rule, finding, and concept, with typed edges between them, e.g.:

```
avoid n+1 queries in loops  --[describes_problem]-->  n+1 query looping over orders
n+1 query problem           --[caused_by_action]-->  fetching notifications per subscriber
```

That is the team's accumulated review knowledge, queryable and growing.

---

## What's real, what's mocked

This is an MVP that **spotlights the Cognee memory pillar**. SentinelAI has three pillars (code review, production observability, AI-quality); the other two run in sim mode for this submission.

| Component | Mode | Notes |
|---|---|---|
| **Cognee memory** | **Real** | Local self-hosted knowledge graph + LanceDB vector store |
| **Gemini (review + diff summary)** | **Real** | Gemini 2.5 Flash on Vertex AI via ADC |
| **Embeddings** | **Real** | Vertex AI text embeddings (Cognee's embedder) |
| Code diffs (PR inputs) | Fixtures | Deterministic, repeatable demo — `integrations/gitlab/fixtures/mr_diff.json` |
| Production Sentinel (Dynatrace) | Sim/mock | Partner free tier expired; dashboard shows mock data |
| AI Quality Gate (Arize) | Sim/mock | Same |

Every adapter has a `sim` and `real` path behind one interface, so the whole stack also runs **fully offline** (deterministic local embeddings) for tests — no creds, no network, no cost.

---

## Tech stack

| Layer | Tech |
|---|---|
| **Memory** | **Cognee 1.x** — knowledge graph + vector store, `remember/recall/improve/forget` |
| Vector store | LanceDB (Cognee's local backend) |
| Agent runtime | Google ADK, Gemini 2.5 Flash on Vertex AI (ADC, no API key) |
| Embeddings | Vertex AI text embeddings |
| Backend | Python 3.10+ · FastAPI · uvicorn · pydantic v2 · tenacity (retry) |
| Dashboard | Next.js 16 · Tailwind v4 · SWR (live + mocked fallback) |
| Contract | one `Signal` envelope + append-only pydantic models across pillars |
| Tests | pytest — 149 passing (memory suite runs offline in sim) |

---

## Project structure (memory path)

```
agents/sentinel/pillars/code_guardian/
  memory.py            recall_context(diff)  +  remember_review(review)   ← the glue
  review.py            injects the recalled TEAM MEMORY block into the prompt
  cycle.py             remembers each review's findings after the Signal is built
integrations/cognee/
  interface.py         CogneeIntegration ABC (remember/recall/improve/forget)
  simulator.py         offline JSON + local embeddings (tests, no creds)
  real.py              Cognee adapter — async SDK wrapped for the sync codebase
  factory.py           mode switch (sim | real) by SENTINEL_MEMORY_MODE
  fixtures/team_history.json   seed content (past reviews + a post-merge bug)
shared/
  models.py            MemoryItem (repo, file, rule, comment, severity, source, commit, ts)
  config.py            typed settings + .env load
  llm.py               Gemini wrapper (Vertex AI + ADC)
scripts/
  seed_team_memory.py  seed the graph + recall smoke  (--reset to forget first)
  run_code_review.py   run one review cycle from the CLI
tests/test_code_memory.py   remember→recall roundtrip, prompt injection, forget (offline)
```

The other two pillars (`production_sentinel`, `ai_quality_gate`) and the dashboard live alongside; they run in sim mode here.

---

## Running it

```bash
# One-time setup
python -m venv .venv
.venv/Scripts/activate            # Windows   (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
gcloud auth application-default login    # Vertex ADC — powers Gemini + Cognee embeddings
gcloud config set project <your-gcp-project>
cp .env.example .env                     # set GOOGLE_CLOUD_PROJECT
```

**Real Cognee memory** (the demo) — in `.env`:

```
SENTINEL_MEMORY_MODE=real
COGNEE_SERVICE_URL=            # blank = local self-hosted graph
```

```bash
python scripts/seed_team_memory.py --reset   # build the team-memory graph, run a recall smoke
python scripts/run_code_review.py cafe123     # review a new PR → recall fires → flags the N+1
```

- `cafe123` — a notifications PR with an N+1 hidden in a loop (recall catches it from history).
- `def5678` / `abc1234` — the original demo PRs (`mr_diff.json`).

**Offline / sim mode** (no creds, deterministic) — set `SENTINEL_MEMORY_MODE=sim`, or just:

```bash
pytest -q                                     # 149 passing, fully offline
```

> **Windows note:** Cognee's local store is relocated to `C:/cognee` automatically — the default path buries files past the 260-char `MAX_PATH` limit. Handled in `integrations/cognee/real.py`.

**Dashboard** (optional, shows the MemoryPanel + mocked pillars):

```bash
# backend
uvicorn services.dashboard_api.main:app --port 8000
# frontend
cd dashboard && npm install
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000 npm run dev   # http://localhost:3000
```

---

## About the project

This started from a real frustration: AI code review that never learns. You tell the reviewer the same thing every sprint — "we don't do N+1 queries here," "use the shared client," "this endpoint has a subtle auth check" — and next PR it's forgotten all of it. The team's hard-won lessons live in merged review threads and post-mortems, but the reviewer can't see them.

The WeMakeDevs "Where's My Context?" theme named the problem exactly: context that doesn't survive across sessions. Cognee is the fix — a memory layer that turns each review into a queryable knowledge graph instead of a discarded transcript. The interesting engineering wasn't calling `remember()`; it was making `recall()` actually surface the right memory for a raw code diff, which took a natural-language-summary step to bridge code and Cognee's semantic retrieval. Once that clicked, the loop closed: the reviewer flags a recurring bug in a service it had never seen, purely because the team remembered the pattern.

The base — SentinelAI, a three-pillar delivery guardian — gave us the agent, the sim/real adapter contract, and the dashboard to plug the memory into. This submission spotlights the memory pillar.

---

## License

Apache-2.0 — see [LICENSE](LICENSE).
