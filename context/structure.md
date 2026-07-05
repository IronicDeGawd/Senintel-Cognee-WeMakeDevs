# SentinelAI — Structure

> Tree of key dirs, entry points, config, touched files. Check BEFORE Grep/Glob. Update on file changes.

## Current (actual on disk)

```
SentinelAI/
  .gitignore                              # ignores .env, venv, node_modules, .playwright-mcp/, keys
  LICENSE                                 # Apache-2.0
  README.md                               # pitch + run steps + layout
  pyproject.toml                          # ruff (excl context/experiment) + pytest (asyncio auto)
  requirements.txt                        # Python deps (append-only; pillars add storage/partner libs)
  .env.example                            # env template (append-only; GEMINI_* + SENTINEL_<X>_MODE + creds)
  Google Cloud Rapid Agent Hackathon.docx # source merged-idea doc
  SentinelAI-Implementation-Plan.docx     # team approval doc (generated)
  agents/
    __init__.py
    sentinel/
      __init__.py                         # re-exports root_agent
      agent.py                            # ADK root orchestrator stub [entry: root_agent]
      pillars/
        __init__.py
        code_guardian/                    # P1 (GitLab) — branch feature/code-guardian
          __init__.py
          prompt.py                       # REVIEW + CI_RCA + GUARDIAN sub-agent instructions
          review.py                       # P1-2: run_review(commit)->MRReview via generate_json
          ci.py                           # P1-3: diagnose_ci(mr_id)->str|None via generate
          note.py                         # P1-4: render_mr_note(MRReview)->markdown (severity-grouped)
          cycle.py                        # P1-4: run_code_guardian_cycle(commit)->Signal [D1: +save_signal hook]
          agent.py                        # ADK sub-agent; sim FunctionTools | real GitLab McpToolset (dormant)
        production_sentinel/              # P2 (Dynatrace)
          __init__.py
          prompt.py                       # BRIEFING + RCA + CORRELATION instructions (promoted spike)
          rca.py                          # run_rca(problems)->Incident via shared.llm.generate_json
          correlation.py                  # P2-4 money shot: suspect_commit_for/get_mr_diff/correlate_incident
          cycle.py                        # P2-6: run_production_cycle()->Signal (RCA->correlate->KB->deliver) [D1: +save_signal hook]
          agent.py                        # ADK sub-agent; sim FunctionTools (incl get_mr_diff) | real McpToolset
        ai_quality_gate/                  # P3 (Arize/Phoenix) — branch feature/ai-quality-gate
          __init__.py
          gate.py                         # P3-1: evaluate(rule) + decide(EvalResult)->Signal + run_gate(suite)
          prompt.py                       # P3-2: EVALGEN (adversarial red-team) + GATE sub-agent instructions
          evalgen.py                      # P3-2: generate_eval_suite via generate_json; EvalCase/EvalSuite (pillar-local)
          agent.py                        # P3-2: ADK sub-agent; sim FunctionTools | real Phoenix McpToolset (dormant)
        demo_director/                      # D8 (Demo Director) — seeder agents
          __init__.py
          seeders.py                        # event/incident/signal seeders for demo scenarios
          scenario.py                       # Scenario: event list + expected outcomes
          agent.py                          # ADK agent orchestrating seeders, running scenario end-to-end
  integrations/
    __init__.py
    base.py                               # Integration ABC + build_integration(mode,sim,real) — ADAPTER CONTRACT
    arize/                                # P3 adapter (Arize/Phoenix) — branch feature/ai-quality-gate
      __init__.py
      interface.py                        # ArizeIntegration: run_eval(suite,dataset)->EvalResult, get_baseline
      simulator.py                        # canned eval runs (pass v1 / fail v2); passed via gate.evaluate; no creds
      factory.py                          # get(mode)->sim|real (real lazy, not yet created)
      fixtures/eval_runs.json             # baseline + canned runs + threshold (0.10)
    dynatrace/                            # P2 adapter (Prime A)
      __init__.py
      interface.py                        # DynatraceIntegration: list_problems, execute_dql, recent_deployments
      simulator.py                        # canned problems + DQL + deploy events (commit abc1234); no creds
      factory.py                          # get(mode)->sim|real (real imported lazily)
      fixtures/problems.json              # promoted spike fixture (Davis problem payload)
    gitlab/                               # P1 adapter (Code Guardian) — branch feature/code-guardian
      __init__.py
      interface.py                        # GitLabIntegration: get_mr_diff + get_pipeline_logs + post_mr_note
      simulator.py                        # canned MR diff + failing CI logs; post_mr_note->out/mr_note_<id>.md
      real.py                             # P1-7.1: GitLabReal via npx mcp-remote {URL}/api/v4/mcp (OAuth DCR)
      factory.py                          # get(mode)->sim|real
      fixtures/mr_diff.json               # promoted spike fixture (MR diff for commit abc1234)
      fixtures/pipeline_logs.json         # P1-1 canned failing pytest output (N+1 query regression)
  storage/                                # P2-3 incident memory + P3-4 eval trends + D1 signal persistence
    __init__.py
    embeddings.py                         # embed/cosine/most_similar; sim feature-hash | real Vertex
    incident_kb.py                        # IncidentKB: JsonFileKB (sim) | FirestoreKB (real); save/recent/similar
    eval_trends.py                        # P3-4 EvalTrends: JsonFileTrends (sim out/eval_trends.json) | BigQueryTrends (real); append/recent
    signal_store.py                       # D1: SignalStore: JsonFileSignalStore (sim out/signals.json) | FirestoreSignalStore (real); save/recent/latest_per_pillar
  delivery/                               # P2-5 briefing delivery
    __init__.py
    briefing.py                           # render_briefing + deliver_briefing (sim out/ | real Slack webhook)
  services/                               # FastAPI entry points (Cloud Run)
    __init__.py
    dashboard_api/                        # D2 (Dashboard backend) — 4th service
      __init__.py
      main.py                             # [entry: uvicorn services.dashboard_api.main:app] /signals, /history, /correlation, /trends/quality, /trigger/{pillar}, /health
    dashboard/                            # D2/D8 (Next.js frontend) — 5th service
      app/
        layout.tsx                        # root layout (type pairing, globals.css)
        globals.css                       # Tailwind v4 token system
        page.tsx                          # Landing page
        dashboard/
          page.tsx                        # Dashboard page (signal components, live SWR hooks)
      components/
        landing/                          # Hero, Pillars, Story, Architecture, CTAStrip
        dashboard/                        # StatusCards, CorrelationPanel, ActivityTimeline, DriftChart, TriggerPanel, DemoScenarioCard
        site/                             # Nav, Footer
      lib/
        api.ts                            # HTTP client (dashboard_api URLs)
        hooks.ts                          # useSWR hooks: useSignals, useHistory, useCorrelation, useQualityTrends, usePostTrigger
        types.ts                          # Signal, EvalPoint, CorrelationView (TypeScript mirrors of Python models)
        mock.ts                           # fallback mock data
        utils.ts                          # cn helper
      package.json, next.config.ts, tsconfig.json, postcss.config.mjs, eslint.config.mjs
      Dockerfile                          # Node 22, NEXT_PUBLIC_API_BASE arg, standalone
    demo_director/                        # D8 (Demo Director) — 6th service
      __init__.py
      main.py                             # [entry: uvicorn services.demo_director.main:app] POST /demo/run, /demo/{partner}, GET /debug/dql, POST /debug/send-event
    eval_runner/                          # P3-3 (AI Quality Gate) — 3rd service
      __init__.py
      main.py                             # P3-3 [entry: uvicorn services.eval_runner.main:app] POST /eval {suite} -> Signal, GET /health [D1: +save_signal hook]
    poller/                               # P2-6 (Production Sentinel) — 2nd service
      __init__.py
      main.py                             # P2-6 [entry: uvicorn services.poller.main:app] POST /run -> Signal, GET /health
    webhook_gateway/                      # P1-6 (Code Guardian) — 1st service
      __init__.py
      main.py                             # P1-6 [entry: uvicorn services.webhook_gateway.main:app] POST /gitlab/webhook -> Signal, GET /health
  shared/
    __init__.py
    config.py                             # pydantic-settings; settings singleton; load_dotenv
    models.py                             # THE CONTRACT: Severity/Problem/Finding/MRReview/EvalResult/Incident/Signal
    mcp.py                                # stdio_mcp() McpToolset helper + tenacity connect retry
    llm.py                                # generate() text + generate_json(schema) structured; retry on 429/5xx
    logging.py                            # get_logger()
  scripts/
    run_agent.py                          # InMemoryRunner harness [entry: python scripts/run_agent.py "msg"]
    run_briefing.py                       # run_rca() -> out/briefing.md (one live Gemini call)
    run_eval_gate.py                      # P3-2: generate_eval_suite (live Gemini) -> run_gate -> Signal
    run_code_review.py                    # P1-7.5: run_code_guardian_cycle(commit) -> Signal (live Gemini)
    probe_gitlab.py                       # P1-7.2: list MCP tools + smoke 3 calls against live GitLab MCP
  out/
    briefing.md                           # committed demo artifact (RCA output)
  tests/
    __init__.py
    conftest.py                           # forces SENTINEL_*_MODE=sim + dummy key
    test_ai_quality_gate.py               # P3-2: 4 tests: evalgen (mocked LLM) name-forcing, gate tool block/pass, sub-agent builds
    test_arize_simulator.py               # P3-1: 10 tests: factory sim, baseline/clean/regressed runs, evaluate rule, decide/run_gate
    test_correlation.py                   # 5 tests: suspect commit, link, no-deploy/unknown-commit/raise skips
    test_dashboard_api.py                 # D2: 8 tests: /health, /signals, /history with cap, /correlation (happy + empty), /trends, /trigger (503 + httpx mock)
    test_demo_director.py                 # D8: tests for demo scenario runner
    test_delivery.py                      # 4 tests: render with/without match, sim file write, real-needs-webhook
    test_dynatrace_simulator.py           # 6 tests: factory sim, normalized problems, root cause, DQL
    test_eval_runner.py                   # P3-3: 3 tests: /health, /eval block regressed + pass clean (trends stubbed)
    test_eval_trends.py                   # P3-4: 5 tests: factory sim, append/recent roundtrip, suite filter, empty
    test_foundation.py                    # 5 tests: config/models/abc/mode-switch/agent-builds
    test_gitlab_simulator.py              # 4 tests: get_mr_diff known/short/unknown commit
    test_incident_kb.py                   # 6 tests: embed determinism, cosine, KB save/recent, similar
    test_poller.py                        # 6 tests: severity->status, Signal assembly, /run + /health
    test_production_sentinel.py           # 4 tests: RCA (mocked LLM), sub-agent builds sim (3 tools)
    test_signal_store.py                  # D1: 5 tests: factory sim/real lazy, roundtrip, pillar filter, latest-per-pillar, save_signal resilience
  dashboard/                              # Next.js 16 app (App Router, TypeScript strict, Tailwind v4)
    app/
      layout.tsx                          # root layout (type pairing, globals.css)
      globals.css                         # Tailwind v4 token system (slate + lime + status colors + spacing)
      page.tsx                            # Landing page (5 hero components)
      dashboard/
        page.tsx                          # Dashboard page (6 signal-display components, mocked data)
    components/
      landing/                            # Hero, Pillars, Story, Architecture (SVG), CTAStrip
      dashboard/                          # DashboardHeader, StatusCards, CorrelationPanel, ActivityTimeline, DriftChart, TriggerPanel
      site/                               # Nav, Footer (shared chrome)
    lib/
      utils.ts                            # cn helper (clsx + tailwind-merge)
      types.ts                            # Signal, EvalPoint, CorrelationView interfaces (mirror Python models)
      mock.ts                             # mocked Signals, drift series, correlation view (Dynatrace first)
    package.json                          # deps: recharts, swr, lucide-react, clsx, tailwind-merge, cva
    tsconfig.json                         # strict mode
    next.config.ts                        # Turbopack
    postcss.config.mjs                    # Tailwind v4
    eslint.config.mjs                     # linting
      Dockerfile                          # Node 22, NEXT_PUBLIC_API_BASE arg, standalone
  experiment/                             # spike (reference appendix, untracked)
  context/                                # tracked (team-shared plan/research/progress)
    plan/sentinelai.md                    # approved implementation plan
    plan/build-steps.md                   # reprioritized step-by-step
    plan/features/                        # per-pillar parallel plans (00-foundation … 04-dashboard)
    progress.md                           # status / lessons / handoff
    structure.md                          # this file
    research/
      README.md                           # research index
      gitlab.md                           # GitLab MCP + REST API research
      arize.md                            # Arize Phoenix + Vertex embedding research
      dynatrace.md                        # Dynatrace MCP + Grail + OTLP research
      design-extract-saucelabs.md         # D2: palette, type, spacing, radii, hierarchy, component patterns
      saucelabs-desktop.png               # D2: reference screenshot (1280px)
      saucelabs-tablet.png                # D2: reference screenshot (768px)
      saucelabs-mobile.png                # D2: reference screenshot (375px)
```

## Completed (6 Cloud Run services live)

- sentinelai-gateway (webhook_gateway) — P1 GitLab webhook listener
- sentinelai-poller (poller) — P2 production incident watcher
- sentinelai-eval-runner (eval_runner) — P3 quality gate evaluator
- sentinelai-dashboard-api (dashboard_api) — D2 read API
- sentinelai-demo-director (demo_director) — D8 scenario runner
- sentinelai-dashboard (dashboard) — D2/D6 Next.js frontend

## Entry Points (Cloud Run live)

- Agent: `agents/sentinel/agent.py` (ADK root, demo harness)
- Services (all 6 Cloud Run): 
  - `services/webhook_gateway/main.py` (GitLab webhook, POST /gitlab/webhook)
  - `services/poller/main.py` (production sentiment, POST /run)
  - `services/eval_runner/main.py` (quality gate, POST /eval)
  - `services/dashboard_api/main.py` (read API, 6 endpoints + CORS)
  - `services/demo_director/main.py` (scenario runner, POST /demo/run)
  - `services/dashboard/app/` (Next.js App Router, live useSWR)
- Config: `shared/config.py` (env + mode switches), `.env.example`

## Config Files (Production Live)

- `requirements.txt` — Python deps (google-cloud-firestore, dynatrace-mcp, etc.)
- `.env.example` — env template (SENTINEL_*_MODE, creds, webhooks, Cloud Run URLs)
- `dashboard/package.json` — Node deps (recharts, swr, lucide-react, Tailwind v4)
- `.gitignore` — ignores .env, venv, node_modules, .playwright-mcp/, keys
- `pyproject.toml` — ruff config (excl context/experiment) + pytest (asyncio auto)
- Dockerfiles: backend (Python 3.12, uvicorn), dashboard (Node 22, next build)
