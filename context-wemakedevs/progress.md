# Progress — WeMakeDevs Hackathon (SentinelAI extension)

> Single source of truth for the WeMakeDevs submission. Separate from the old
> `context/` (Google Cloud Rapid Agent Hackathon). Read at every session start.
> Update after EVERY change — no exceptions.

## Context
- **Base:** SentinelAI, built for the Google Cloud Rapid Agent Hackathon.
  Autonomous guardian across three pillars — code (pre-prod), production health,
  AI/LLM quality. Same-SHA cross-pillar correlation is the money shot.
- **New goal:** extend the project for the **WeMakeDevs "Where's My Context?"**
  hackathon (Cognee memory layer). **Deadline: July 5, 2026 — TODAY.**
- **Repo:** `IronicDeGawd/Senintel-Cognee-WeMakeDevs` (HTTPS, main).
- **Confirmed feature:** Cognee-powered **AI PR reviewer** — remembers a team's
  real coding conventions, past bug patterns, prior review comments across
  sessions; `recall()` on new PR, `remember()` on merge. Extends `code_guardian`.

## Current Status
- Research done (`research/wemakedevs.md`, `research/cognee.md`).
- Plan finalized: `plan/cognee-pr-reviewer.md` — two-dev split + deployment plan.
  Decisions locked: Cognee Cloud backend (COGNEE-35), seeded-sim PR scenario, MVP scope.
- Branch `feature/cognee-memory`.
- **Phase 0 contract DONE + pushed** (`1047f67`): `MemoryItem`, memory/cognee config,
  `CogneeIntegration` interface + package.
- **Track V (Vasu) DONE:** offline `CogneeSimulator` + factory; `memory.py` glue
  (`recall_context` / `remember_review`); recall wired into `review.py`; remember
  hook in `cycle.py`; Cognee Cloud adapter `real.py`; `.env.example`, `requirements.txt`
  (cognee), `.gitignore` fix. `tests/test_code_memory.py` (7 tests).
  **Verified: full suite 149 passed, no regression.** venv `.venv` created + installed.
- **Vasu real-backend wiring DONE:** COGNEE-35 claimed, `cognee` 1.2.2 installed,
  `.env` set, `scripts/seed_team_memory.py` built. Cognee LLM+embeddings pointed at
  Vertex AI (gcloud ADC). Windows MAX_PATH fix (relocate local store to `C:/cognee`).
  `cognee.serve()` wired for Cloud.
  **LOCAL Cognee VERIFIED WORKING:** seed builds a 33-node graph, recall returns the
  N+1 lesson, MVP demo (review PR#2 `def5678`) flags the N+1 citing memory. Running
  on `SENTINEL_MEMORY_MODE=real` with `COGNEE_SERVICE_URL` blank (local self-hosted).
- **Track J (Jatin) DONE:** scenario fixtures, seed content, README + demo script,
  stretch dashboard MemoryPanel (frontend built with rich aesthetics, timestamps, sources, `useMemory` hook implemented, backend `/memory/recall` endpoint wired).

## Team split
- **Vasu (Python/AI):** entire Cognee integration + memory brain (Phase 0, sim + real
  adapters, memory glue, review/cycle wiring, tests, Cognee Cloud creds + seed, deploy).
- **Jatin (fullstack/genai):** demo scenario fixtures, seed content, prompt tuning,
  README + demo + submission, stretch dashboard MemoryPanel (Completed).

## Completed
- 2026-07-05 — Fresh git repo (new history), pushed to `IronicDeGawd/Senintel-Cognee-WeMakeDevs`.
- 2026-07-05 — Zone-1 scrub: source links + old-hackathon framing updated.
- 2026-07-05 — Scaffolded `context-wemakedevs/`.
- 2026-07-05 — Build recheck: full suite green (149). Fixed offline code-memory
  suite timing out under a `real`-mode `.env` (autouse fixture pins sim); ignore
  `out/mr_note_*.md`. Committed + pushed (`6ffff22`).

## Known Issues
- **Cognee Cloud recall returns empty (local works).** With `COGNEE_SERVICE_URL` set,
  `cognee.serve()` connects and `remember()` succeeds, but `recall()` returns 0 hits
  (even ~30s later, so not just eventual consistency). `forget()` 422s and `cognify`
  needed an explicit `datasets=[...]` (fixed). Likely a Cloud dataset/query-shape
  mismatch needing the exact Cloud API. **Decision: ship on LOCAL** (Open Source
  track) — fully verified. Cloud path is wired; blank `COGNEE_SERVICE_URL` = local.
  Re-enable the URL in `.env` to retry Cloud (iPhone track) with more time.
- Cognee recall is slow (~40s local). For a live demo: pre-warm once, keep
  `SENTINEL_MEMORY_MODE=sim` as an instant offline fallback.
- One Vertex embedding call intermittently 422s then retries; graph recall unaffected.

## TODO / Backlog
- [ ] Confirm WeMakeDevs hackathon: track, theme, rules, deadline, judging.
- [ ] Confirm the extension direction (Cognee? something else?).
- [ ] Decide which of the 3 pillars the new feature touches.
- [ ] Write `plan/<feature>.md` before any multi-file change.

## Lessons
- Offline test suites that route through `get_cognee()` must pin `memory_mode=sim`
  via an autouse fixture. A local `.env` with `SENTINEL_MEMORY_MODE=real` otherwise
  leaks into tests, hitting the networked Cognee backend and timing out.
- (append patterns from user corrections here)

## Resume From Here
- **Completed:** repo reset + context scaffold.
- **Next:** gather WeMakeDevs hackathon details + extension direction from user,
  then draft `plan/<feature>.md`.
- **Blockers:** hackathon scope + feature direction unknown — need user input.
