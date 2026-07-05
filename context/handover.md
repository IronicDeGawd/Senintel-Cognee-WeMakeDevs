# Handover — SentinelAI

> Compact-survival essentials. Auto-generated git sections refreshed by the
> PreCompact hook; Session Notes preserved across compactions.

## Branch

_Refreshed by hook on `/compact`._

## Files In Flight

_Refreshed by hook on `/compact`._

## Recent Commits

_Refreshed by hook on `/compact`._

## Session Notes

**Active task:** WeMakeDevs "Where's My Context?" hackathon — Cognee-powered AI PR
reviewer extending the `code_guardian` pillar. **Feature COMPLETE + verified on LOCAL
Cognee.** Repo `IronicDeGawd/Senintel-Cognee-WeMakeDevs`, working on `main` (team
converged there). Full status: `context-wemakedevs/progress.md`; plan +
deployment: `context-wemakedevs/plan/cognee-pr-reviewer.md`.

**What it does:** on review, `recall_context(diff)` pulls team memory into the prompt;
at cycle end, `remember_review(review)` stores findings. Backend by
`SENTINEL_MEMORY_MODE`: sim (JSON+local embeddings, tests) | real (Cognee).

**Key files:** `integrations/cognee/{interface,simulator,real,factory}.py`;
`agents/sentinel/pillars/code_guardian/memory.py` + recall wired into `review.py`
(prompt concat) + remember hook in `cycle.py`; `MemoryItem` in `shared/models.py`;
`scripts/seed_team_memory.py`; `tests/test_code_memory.py` (7). 149 tests green.

**Exact commands (Windows venv):**
- Tests: `./.venv/Scripts/python.exe -m pytest -q`
- Seed + recall smoke: `python scripts/seed_team_memory.py --reset`
- MVP demo: `python scripts/run_code_review.py def5678` (PR#2 flags N+1 from memory;
  PR#1 = `abc1234`). Fixtures: `integrations/gitlab/fixtures/mr_diff.json`.

**Decisions this session:**
- Cognee LLM+embeddings via **Vertex AI + gcloud ADC** (not AI Studio); `GEMINI_API_KEY`
  left blank → `real.py _configure()` takes the Vertex branch.
- **Windows MAX_PATH fix:** relocate Cognee local store to `C:/cognee` (real.py).
- **Ship LOCAL** (Open Source track). Cloud parked.

**Gotchas / known issues (also in progress.md):**
- **Cognee Cloud recall returns 0** — `serve()`+`remember()` work, `recall()` empty even
  30s later; `forget` 422s; `cognify` needs `datasets=[...]` (fixed). `COGNEE_SERVICE_URL`
  BLANKED in `.env` (URL kept in a comment) → local active. Re-enable to retry Cloud.
- Recall slow (~40s local) → pre-warm before demo; `SENTINEL_MEMORY_MODE=sim` = instant fallback.
- One Vertex embedding call intermittently 422s then retries; graph recall unaffected.

**Creds (.env, gitignored/untracked — never commit):** `SENTINEL_MEMORY_MODE=real`,
`COGNEE_API_KEY` set (**ROTATE — appeared in session logs**), `GOOGLE_CLOUD_PROJECT=
project-8feccae3-bcae-4254-b60`, gcloud ADC at `AppData/Roaming/gcloud`.

**Jatin (other dev):** merged PR #1 (MemoryPanel + `GET /memory/recall` + fixtures +
`team_history.json`). Removed his `shared/llm.py` hardcoded mock fallback (broke
Incident model, killed retry). His Python-downgrade sweep (StrEnum→str,Enum, PEP-695→
TypeVar) kept — he runs older Python; verified harmless.

**Left (Jatin/submission):** 60s demo video, README section, Google Form.
