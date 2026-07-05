# 01 — Code Guardian (Pillar 1, GitLab) — PRIME B

> Owner: Dev B. Carries the cross-pillar correlation that makes the demo land.
> Build after Foundation contracts; fully parallel to Production Sentinel.
> Prereq: [00-foundation.md](00-foundation.md) frozen. Reuse spike `gl_sim.py` + `mr_diff.json`.

## What it does
On a GitLab Merge Request opened/updated → agent reads the diff via GitLab MCP →
Gemini semantic review (SQLi, hardcoded secrets, perf anti-patterns, logic
regressions) → posts a structured MR comment with severity-rated `Finding`s. If
CI failed → fetches pipeline logs → plain-English root cause in the same comment.
**Also exposes `get_mr_diff(commit)`** — the method Production Sentinel calls to
correlate a prod incident back to a commit.

## File map
```
integrations/gitlab/
  interface.py     # GitLabIntegration: get_mr_diff(commit), get_pipeline_logs(mr_id), post_mr_note(mr_id, body)
  simulator.py     # canned diff + CI log (promote experiment/fixtures/mr_diff.json)
  real.py          # shared.mcp.stdio_mcp for GitLab MCP (stdio) OR HTTP; Duo namespace set
  factory.py       # get(mode) -> sim|real
agents/sentinel/pillars/code_guardian/
  agent.py         # tools = GitLab (by mode); produces MRReview
  prompt.py        # review rubric: SQLi/secrets/perf/logic + CI RCA
  review.py        # Gemini diff review -> list[Finding] (shared.llm)
services/webhook_gateway/
  main.py          # FastAPI POST /gitlab/webhook -> verify token -> run review -> post note
```

## Step-by-step

### P1-1 — Simulator first (no creds)
- Promote `experiment/fixtures/mr_diff.json` → `integrations/gitlab/simulator.py`:
  `get_mr_diff(commit)` returns the canned diff; add a canned failing `get_pipeline_logs`.
- `post_mr_note` in sim writes to `out/mr_note.md`. Unit test the shapes.

### P1-2 — Diff review agent (sim)
- `review.py`: Gemini over the diff → `list[Finding]` (F3 model). Rubric in `prompt.py`:
  - **Security:** SQL injection, hardcoded secrets/keys, unsafe deserialization.
  - **Performance:** N+1 queries, unbounded loops, missing pagination.
  - **Logic:** off-by-one, swallowed exceptions, broken null checks.
  - Each `Finding`: file, line, category, severity, message, suggestion.
- `agent.py` assembles `MRReview(mr_id, commit, findings, ci_root_cause)`.
- Run on the canned N+1 diff → confirm it flags the N+1. **Artifact:** `mr_note.md`.

### P1-3 — CI failure diagnosis
- `get_pipeline_logs(mr_id)` (sim canned) → Gemini → plain-English root cause →
  fills `MRReview.ci_root_cause`. Appended to the MR note.

### P1-4 — MR comment formatting
- Render `MRReview` → markdown: severity-grouped findings + fix suggestions + CI RCA.
- Post via `post_mr_note` (sim → `out/`, real → MCP).

### P1-5 — Correlation contract (consumed by P2)
- `get_mr_diff(commit)` is the seam Production Sentinel calls. Keep its return
  shape identical sim↔real so P2 correlation works regardless of mode. Coordinate
  the shape with Dev A once (it already matches the spike fixture).

### P1-6 — Webhook gateway
- `services/webhook_gateway/main.py`: FastAPI `POST /gitlab/webhook` → verify
  `X-Gitlab-Token` → on `merge_request` open/update → run review → post note →
  emit `Signal(pillar="code", ...)`. Local: simulated POST with a sample payload.

### P1-7 — Real GitLab wiring (flip `SENTINEL_GL_MODE=real`)
- `real.py` mounts the GitLab MCP server (stdio or HTTP). Auth: OAuth 2.0 DCR;
  **set the default Duo namespace** (required for external MCP clients — see
  `research/gitlab.md` gitlab-05). 30-day Ultimate trial, Duo credits.
- Webhook needs a public URL: ngrok locally, Cloud Run in prod.
- Re-run review against a real MR → parity.

## Verification
- Sim: pytest (review finds the N+1; CI RCA non-empty) + simulated webhook POST → `mr_note.md` + `Signal`.
- Correlation: P2 calls `get_mr_diff("abc1234")` → returns the diff (cross-pillar smoke).
- Real: real MR opened → comment posted (or logged as stretch).

## Definition of done
- MR review with severity-rated findings + CI root cause (sim ✓, real ✓-or-logged).
- `get_mr_diff` stable for P2 correlation.
- `Signal(pillar="code")` emitted.
- Committed artifact: a rendered MR note + (real) a screenshot of the posted comment.

## Risks
- GitLab MCP is beta (Duo namespace requirement, credits) → simulator-first protects the demo.
- Webhook public URL → use Cloud Run URL in prod; ngrok only for local real test.
