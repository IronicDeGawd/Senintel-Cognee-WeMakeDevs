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
- **Left for Vasu (needs creds):** claim `COGNEE-35`, `pip install cognee`, set
  `.env` (`SENTINEL_MEMORY_MODE=real`, `COGNEE_API_KEY`), seed `team_history.json`
  into Cognee Cloud, run the live remember→recall smoke.
- **Jatin's track (parallel):** scenario fixtures, seed content, README + demo,
  stretch dashboard MemoryPanel.

## Team split
- **Vasu (Python/AI):** entire Cognee integration + memory brain (Phase 0, sim + real
  adapters, memory glue, review/cycle wiring, tests, Cognee Cloud creds + seed, deploy).
- **Jatin (fullstack/genai):** demo scenario fixtures, seed content, prompt tuning,
  README + demo + submission, stretch dashboard MemoryPanel.

## Completed
- 2026-07-05 — Fresh git repo (new history), pushed to `IronicDeGawd/Senintel-Cognee-WeMakeDevs`.
- 2026-07-05 — Zone-1 scrub: source links + old-hackathon framing updated.
- 2026-07-05 — Scaffolded `context-wemakedevs/`.

## Known Issues
- (none yet)

## TODO / Backlog
- [ ] Confirm WeMakeDevs hackathon: track, theme, rules, deadline, judging.
- [ ] Confirm the extension direction (Cognee? something else?).
- [ ] Decide which of the 3 pillars the new feature touches.
- [ ] Write `plan/<feature>.md` before any multi-file change.

## Lessons
- (append patterns from user corrections here)

## Resume From Here
- **Completed:** repo reset + context scaffold.
- **Next:** gather WeMakeDevs hackathon details + extension direction from user,
  then draft `plan/<feature>.md`.
- **Blockers:** hackathon scope + feature direction unknown — need user input.
