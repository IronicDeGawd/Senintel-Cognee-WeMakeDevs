# Demo Polish Plan — Cognee PR Reviewer (WeMakeDevs)

> Goal: a ~60-second clip that proves **memory** caught the bug, not the model.
> Cold PR slips it; warm PR flags it citing team history. Owner: Jatin (with Vasu
> for the backend warm-up).

## The narrative — three beats
1. **Cold** — review PR#1 `abc1234` with empty memory. The N+1 bug (query per
   item in a serializer) slips through. Show the near-clean review.
   Line: *"No memory yet — the model misses the team's known trap."*
2. **Remember** — merge fires `remember_review()`; the finding is stored. Show the
   memory item landing (seed = `integrations/cognee/fixtures/team_history.json`).
3. **Warm** — review PR#2 `def5678` (same N+1 pattern, different file
   `profile/views.py`). Recall fires; the review flags it and says **"seen
   before."** Line: *"Memory changed the verdict."*

## Pre-warm — run BEFORE recording (recall is ~40s cold)
```bash
# seed + reset, build the graph
python scripts/seed_team_memory.py --reset
# warm the recall path with a throwaway run so the graph is hot on camera
python scripts/run_code_review.py def5678
```

## Guards (the things that bite on camera)
- **Recall slow (~40s)** → pre-warm above. Never run the first recall live.
- **Cognee hiccup live** → instant fallback: set `SENTINEL_MEMORY_MODE=sim` in
  `.env`. Same output, deterministic, offline, zero spend. Rehearse both paths.
- **Vertex embedding 422 flake** → retry is automatic; if seeding errors once,
  rerun `--reset`.
- **Same reviewer both times** → cold vs warm must differ ONLY in memory state.
  Do not change the prompt between takes, or judges can't attribute the catch to
  memory.

## Record checklist
- [ ] Split screen: diff on left, review output on right.
- [ ] Show the memory item text so "seen before" is credible.
- [ ] Say "Cognee" out loud once (track requirement).
- [ ] ≤60s: cut the ~40s recall wait (pre-warmed); keep only the reveal.

## Deliverables (Jatin)
- The clip.
- README section: "How memory changes the review."
- Google Form submission.

## Commands reference (Windows venv)
- Tests: `./.venv/Scripts/python.exe -m pytest -q`
- Seed + recall smoke: `python scripts/seed_team_memory.py --reset`
- MVP demo: `python scripts/run_code_review.py def5678` (PR#2; PR#1 = `abc1234`)
