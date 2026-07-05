# Cognee PR Reviewer — Two-Dev Build Plan (WeMakeDevs, same-day)

## Context
WeMakeDevs "Where's My Context?" hackathon (deadline **July 5, 2026 — today**).
One hard rule: **Cognee powers the memory.** We extend SentinelAI's `code_guardian`
pillar into an **AI PR reviewer with long-term memory** — it `remember()`s each
merged PR's review comments + post-merge bugs, and `recall()`s relevant team history
when reviewing a new PR, learning a team's real conventions instead of a static guide.

**Decisions locked:**
- **Memory backend = Cognee Cloud** (coupon `COGNEE-35`). Mandatory — makes the
  submission valid + targets the iPhone/Cognee-Cloud track.
- **JSON sim backend** = offline tests/CI only, not the demo.
- **PR inputs = scripted fixtures** (deterministic, safe). Real Cognee memory + fake
  PR diffs = genuine Cognee usage, repeatable for judges.
- **Scope = MVP**: "memory changes the review." improve()/forget() + dashboard = stretch.

**Key constraint:** codebase is synchronous; Cognee SDK is async → real adapter wraps
async in `asyncio.run(...)` behind a sync interface. `storage/incident_kb.py`
(sim `JsonFileKB` / real `FirestoreKB`) is the template to clone.

## Team split
- **Vasu (Python + AI) — owns the ENTIRE Cognee integration + memory brain.**
  Phase 0 contract, both adapters (sim + Cognee Cloud), memory glue, review/cycle
  wiring, tests, Cognee Cloud account + creds + seed, deployment of the memory layer.
- **Jatin (fullstack + genai)** — demo scenario fixtures, seed *content*, prompt
  tuning (advisory), README + demo script + submission, stretch dashboard MemoryPanel.

---

## Phase 0 — Contract (Vasu lands first, ~20 min → unblocks Jatin)
1. **`shared/models.py`** — append `MemoryItem` (append-only): `repo`, `file|None`,
   `rule`, `comment`, `severity: Severity`, `source: Literal["review","post_merge_bug"]`,
   `commit`, `ts`, `id`.
2. **`shared/config.py`** — append (mirror `kb_mode` L54): `memory_mode` (alias
   `SENTINEL_MEMORY_MODE`), `cognee_api_key=""`, `cognee_dataset="sentinel_team_memory"`.
3. **`integrations/cognee/interface.py`** — `CogneeIntegration(Integration)`
   (`name="cognee"`): abstract `remember(item)->str`, `recall(query,limit=5)->list`,
   `improve()->None`, `forget(dataset=None)->None`, `healthcheck()->bool`.
Commit + push. Jatin pulls before starting.

## Vasu — memory brain (Cognee)
1. `integrations/cognee/simulator.py` — `CogneeSimulator`: clone `JsonFileKB`; embed via
   `storage/embeddings.py` (`embed`/`cosine`/`most_similar`). Offline → tests.
2. `integrations/cognee/real.py` — `CogneeReal`: wrap `cognee` SDK, `asyncio.run` around
   async remember/recall (or add+cognify+search). Gemini-backed. **Demo backend.**
3. `integrations/cognee/factory.py` — `get(mode=None)` via `build_integration`.
4. `agents/sentinel/pillars/code_guardian/memory.py` — `recall_context(diff)->str`,
   `remember_review(review)->None`.
5. `review.py` (L52) — inject `recall_context(diff)` into the prompt.
6. `cycle.py` (~L85) — call `remember_review(review)` after Signal built (remember-on-merge).
7. `tests/test_code_memory.py` — remember→recall roundtrip, review injects recalled rule, forget clears.
8. Cognee Cloud: claim `COGNEE-35`, `.env` (`SENTINEL_MEMORY_MODE=real`, `COGNEE_API_KEY`),
   append vars to `.env.example`, one-off seed script for `team_history.json`.

## Jatin — scenario, prompt, presentation
1. `integrations/cognee/fixtures/team_history.json` — realistic past reviews + a
   post-merge bug (content; Vasu writes the loader).
2. `integrations/gitlab/fixtures/mr_diff.json` — PR#1 (introduces bug) + PR#2 (same pattern).
3. Prompt tuning (advisory) on the TEAM-MEMORY section wording.
4. README section + 60-sec demo script + Google-Form submission.
5. STRETCH: dashboard MemoryPanel (`GET /memory/recall` + `useMemory` + `MemoryPanel.tsx`).

---

## Deployment Plan
Base app already runs **6 Cloud Run services**. This feature adds a Cognee Cloud
dependency and rides inside existing services — **no new service for MVP**.

**Owner: Vasu** (memory layer). Jatin owns dashboard redeploy only if the stretch ships.

### A. Same-day demo path (recommended — lowest risk)
1. `pip install cognee` into the venv; append `cognee` to `requirements.txt`.
2. Claim `COGNEE-35`; create Cognee Cloud account → API key + dataset.
3. Local `.env`: `SENTINEL_MEMORY_MODE=real`, `COGNEE_API_KEY=...`,
   `COGNEE_DATASET=sentinel_team_memory`. Point Cognee's LLM at the existing Gemini key.
4. Seed once: run the seed script → `remember()` every `team_history.json` item into Cognee.
5. Run locally: `scripts/run_code_review.py <PR#2 commit>` (or the gateway service) →
   confirm the review flags the remembered bug, citing team history.
   **This is the demo — no Cloud Run redeploy needed.**

### B. Cloud Run path (stretch — if time and judges want a live URL)
1. Rebuild the backend image with `cognee` in `requirements.txt`.
2. Store the Cognee key in **Secret Manager** (never bake into the image):
   `gcloud secrets create COGNEE_API_KEY --data-file=-`.
3. Update the affected service(s) — at minimum `sentinelai-gateway` (runs the
   code_guardian cycle + remember hook):
   `gcloud run services update sentinelai-gateway \
      --update-env-vars SENTINEL_MEMORY_MODE=real,COGNEE_DATASET=sentinel_team_memory \
      --update-secrets COGNEE_API_KEY=COGNEE_API_KEY:latest`
4. `gcloud run deploy sentinelai-gateway` (+ `sentinelai-dashboard-api` /
   `sentinelai-dashboard` only if MemoryPanel stretch shipped).
5. Seed the Cognee Cloud dataset once (same seed script, run against prod creds).
6. Verify: POST the PR#2 scenario to the deployed gateway → emitted Signal / MR note
   shows recalled memory. Cognee smoke against the cloud dataset.

### Rollback / demo safety
- `SENTINEL_MEMORY_MODE=sim` instantly falls back to the offline JSON memory (no
  Cognee, no network). Keep it as the escape hatch if Cognee Cloud is flaky mid-demo —
  the review still runs, just without live-cloud memory.

---

## Verification
- **Unit (offline):** `pytest tests/test_code_memory.py` on `memory_mode=sim`.
- **MVP end-to-end (demo):** `memory_mode=real` (Cognee Cloud). Seed history, review
  PR#2 → flags the remembered pattern citing history; PR#1 cold did NOT → proves
  memory, not the model, caught it.
- **Cognee smoke:** one `remember`→`recall` against Cognee Cloud returns the item.
- Full `pytest` → no regression in existing pillars.

## Coordination
- Single branch `feature/cognee-memory`, clean file ownership. Phase-0 shared files
  (models/config/interface) all Vasu, first. Commit small + push often.
- Seams: `MemoryItem` shape (Phase 0), `team_history.json` content, prompt wording.
- Commit identity locked to personal (pandeyVasu); Jatin commits from his own machine/identity.
