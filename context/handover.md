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

**Active task:** P4 dashboard (Next.js), branch `feature/dashboard` (just created
off main, no commits yet). User asked me NOT to start coding — plan only. Last
plan written to `context/plan/features/04-dashboard.md`.

**Where we are in dashboard plan:** plan locked, branch open, **not yet coding**.
Next step on user's go: D1 = `storage/signal_store.py` (mirror `incident_kb.py`
shape, JSON sim + Firestore real) + add `save_signal(signal)` call at end of
each pillar cycle (P2 cycle.py, P1 cycle.py, eval_runner main.py).

**Parallel work by other dev (do NOT touch on this branch):** real Dynatrace +
Arize integrations per `context/plan/features/05-real-partner-integrations.md`.
They own `integrations/arize/real.py` (new), `scripts/probe_phoenix.py`,
`scripts/seed_phoenix.py`, `tests/test_arize_real.py`, Dynatrace OneAgent setup,
and Cloud Run env flips on poller + eval_runner. Cycle.py edits are the only
overlap (~1 LOC); coordinate before pushing if both touch the same file.

**Dashboard scope locked (per user picks):**
- All 6 pieces: status cards, correlation panel, activity timeline, quality
  drift chart, trigger buttons, architecture SVG.
- TWO pages: Landing `/` + Dashboard `/dashboard`.
- Dynatrace pillar shown FIRST in every triad (chosen track).
- Partner names in plain text labels only (no decorative logos — rules §7B).
- Storage = Firestore. Host = Vercel. UI = Next.js 15 + Tailwind + shadcn/ui.
- Backend = new 4th Cloud Run service `services/dashboard_api/main.py` (same
  image, override command).

**Live infra in this session (don't redo):**
- 3 Cloud Run services live: `sentinelai-gateway` (P1 real), `sentinelai-poller`
  (P2 sim), `sentinelai-eval-runner` (P3 sim). URLs in `progress.md`.
- GitHub: `IronicDeGawd/Google-Rapid-Hackathon`, main pushed.
- GitLab webhook registered (id 80763611) → gateway URL. Async cycle returns
  202; background task posts MR notes.
- Custom domain `sentinel.parakramlabs.com` deferred (Search Console verify
  flake — Vercel subdomain is fine for submission).
- 103 tests green, ruff clean on main.

**Secrets / creds (locations only):**
- `/project/Google-Rapid-Hackathon/.env` (chmod 600, gitignored): GITLAB_TOKEN
  PAT, GITLAB_WEBHOOK_TOKEN (random), GITLAB_PROBE_COMMIT, GITLAB_PROJECT_ID=83079708,
  GITLAB_DEMO_MR_IID=1.
- Secret Manager: `gitlab-pat`, `gitlab-webhook-secret`.
- `~/.mcp-auth/mcp-remote-0.1.37/*` — GitLab MCP OAuth cache.
- gcloud account: `parakramlabs.tech@gmail.com`, project
  `project-8feccae3-bcae-4254-b60`, region `us-central1`.

**Reproducible commands (no changes this session):**
- Deploy: `./infra/deploy.sh {gateway|poller|eval_runner|all}` from repo root.
- Live sim review: `SENTINEL_GL_MODE=sim python scripts/run_code_review.py abc1234`.
- Live real review: `SENTINEL_GL_MODE=real python scripts/run_code_review.py <sha>`.
- Trigger live webhook: `cd /project/checkout-service-demo && git commit
  --allow-empty -m '...' && git push`.
- Tail gateway logs: `gcloud run services logs tail sentinelai-gateway
  --region=us-central1 --project=project-8feccae3-bcae-4254-b60`.
- Run tests: `source .venv/bin/activate && python -m pytest -q`.

**Important "don'ts":**
- Don't drop the Vertex AI default model `gemini-2.5-flash` — covered in
  `shared/config.py`.
- Don't proxy the Cloudflare CNAME (must be DNS-only / grey cloud for cert).
- Don't add partner logos in the dashboard (rules §7B).
- Don't touch `integrations/arize/real.py` or anything in R1–R9 of
  `05-real-partner-integrations.md` — owned by other dev.
- User asked NOT to start dashboard code yet. Wait for explicit go.
