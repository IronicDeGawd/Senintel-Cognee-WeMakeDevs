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
- **Phase 0 contract DONE:** `MemoryItem` (shared/models.py), memory/cognee config
  (shared/config.py), `CogneeIntegration` interface + package (integrations/cognee/).
  Syntax-checked. Pushing so Jatin can pull + start his track in parallel.

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
