# Cognee-powered PR Reviewer (Memorium-style code memory)

**Deadline:** July 5, 2026 — TODAY. Scope is MVP-first, stretch only if time.

## Why
Static style guides don't capture how a team *actually* reviews. Sentinel's
`code_guardian` already reviews a diff, but statelessly — it forgets every past
review. We give it **long-term memory via Cognee**: it learns the team's real
conventions, recurring bug patterns, and prior review comments from history, and
applies them to new PRs. Text-in, text-out — no engine, no rendering.

## Goal
On a new PR, the reviewer `recall()`s relevant team history and folds it into the
review. On merge, it `remember()`s the review comments and any post-merge bug.
Over time it `improve()`s (reinforces recurring patterns) and can `forget()` a
retracted rule. Full Cognee lifecycle → targets "Best Use of Cognee".

Sim/real switch so the demo never needs live creds:
`SENTINEL_MEMORY_MODE=sim` (local fake, deterministic, no network) | `real`
(Cognee — local self-hosted OR Cognee Cloud via code COGNEE-35).

## Architecture (extends existing code_guardian pillar)
Follow the existing adapter contract (`integrations/base.py`, sim/real factory).

```
integrations/cognee/                 # NEW adapter, mirrors integrations/gitlab/
  __init__.py
  interface.py     # CogneeMemory ABC: remember(item), recall(query)->list, improve(), forget(dataset)
  simulator.py     # in-memory/JSON fake: keyword+embedding match, no network (tests + demo backup)
  real.py          # wraps cognee SDK: add/cognify/search or remember/recall; Gemini-backed
  factory.py       # get(mode)->sim|real
  fixtures/team_history.json  # seeded past reviews + post-merge bugs for the demo

agents/sentinel/pillars/code_guardian/
  memory.py        # NEW: remember_review(pr, review, bugs) / recall_context(diff)->str
                   #      reinforce(pattern) / forget_rule(id) — thin glue over CogneeMemory
  review.py        # MODIFY: run_review() first calls recall_context(diff),
                   #         injects "Team memory" block into the REVIEW prompt
  prompt.py        # MODIFY: REVIEW prompt gains a {team_memory} section
  cycle.py         # MODIFY: after merge signal, remember_review(...)

shared/config.py   # MODIFY: add SENTINEL_MEMORY_MODE + COGNEE_* settings
.env.example       # MODIFY: append memory-mode + Cognee vars (append-only)

services/webhook_gateway/main.py  # STRETCH: on merge webhook -> remember_review
services/dashboard_api/main.py    # STRETCH: GET /memory/recall?pr=... (what was recalled)
dashboard/.../MemoryPanel.tsx     # STRETCH: show recalled conventions for current PR
```

## Cognee lifecycle mapping (the scoring money shot)
- `remember()` → `memory.remember_review()`: store each merged PR's review comments
  + post-merge bugs as memory items (tagged by repo/file/rule).
- `recall()` → `memory.recall_context()`: on new diff, pull top-k relevant past
  comments/bugs, inject into the review prompt.
- `improve()`/memify → `memory.reinforce()`: when a recalled pattern matches a new
  finding, reinforce it (raise weight / re-cognify).
- `forget()` → `memory.forget_rule()`: drop a retracted convention.

## Build sequence (small, committable units — MVP first)
Branch: `feature/cognee-memory`.

1. **Adapter skeleton + sim** — `integrations/cognee/{interface,simulator,factory}.py`
   + `fixtures/team_history.json`. Sim = deterministic keyword/embedding match
   (reuse `storage/embeddings.py`). Unit test roundtrip. ✅ remember/recall/forget work offline.
2. **memory.py glue** — `recall_context(diff)->str` and `remember_review(...)`.
   Test with sim. ✅
3. **Wire into review** — `review.py` recalls before reviewing; `prompt.py` gains
   `{team_memory}`. Test: recalled convention appears in the prompt/output. ✅
4. **remember on merge** — `cycle.py` (or a script) calls `remember_review` after a
   merged PR. Test roundtrip: review PR#2 surfaces a lesson learned from PR#1. ✅
   ← **This is the MVP demo: memory learned in one PR changes the next review.**
5. **real Cognee adapter** — `real.py` over the cognee SDK, Gemini-backed. Smoke
   test one remember→recall against local Cognee. Flip `SENTINEL_MEMORY_MODE=real`.
6. **improve() + forget()** — `reinforce()` and `forget_rule()` paths + tests.
   Rounds out the full lifecycle for the "Best Use of Cognee" score.

### Stretch (only if time before cutoff)
- Merge webhook auto-remember (`webhook_gateway`).
- Dashboard MemoryPanel: show "what the reviewer remembered" for the current PR.
- README section + 60-sec demo script (presentation score).

## Verification
- `tests/test_code_memory.py`: sim remember/recall/forget roundtrip; review injects
  recalled context; reinforce raises relevance; forget removes.
- Reproduce the demo: seed `team_history.json` with a PR#1 bug ("N+1 query"), review
  PR#2 with the same pattern → reviewer flags it citing the remembered history.
- `real` smoke: one remember→recall against a live Cognee instance.

## Demo story (60 sec)
1. Review PR#1 cold — reviewer gives generic feedback, a bug slips through.
2. Merge; post-merge the bug is found → `remember()` it.
3. Review PR#2 with the same pattern → reviewer **recalls** PR#1's lesson and flags
   it *before* merge, citing the team's own history. "It learned. It didn't forget."

## Open questions for user
- Target track: Open Source (self-hosted Cognee) or Cognee Cloud (iPhone)? Or both via mode?
- MVP cutoff: how far down the sequence must we get before you submit today?
- Real GitLab/GitHub PRs for the demo, or the seeded sim scenario (safer)?
