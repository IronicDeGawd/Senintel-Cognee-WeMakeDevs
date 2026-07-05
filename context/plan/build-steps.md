# SentinelAI — Step-by-Step Build Plan (reprioritized)

> Execution companion to [sentinelai.md](sentinelai.md) (the approved high-level plan).
> Re-prioritized for the real ~3-day clock (today Jun 8 → deadline **Jun 11 2PM PT**).
> Read [../research/RECONCILIATION.md](../research/RECONCILIATION.md) before building.

## Priority Lock (decided Jun 8)

| Rank | Pillar | Partner | Role | Build commitment |
|---|---|---|---|---|
| **Prime A** | P2 Production Sentinel | **Dynatrace** | Prize track + mandatory MCP | Full real + simulator. Non-negotiable. |
| **Prime B** | P1 Code Guardian | **GitLab** | Cross-pillar correlation story | Full real + simulator. |
| **Third** | P3 AI Quality Gate | **Arize/Phoenix** | Self-observability / eval | Sim stub + dashboard card first; **full real MCP only after both primes are demo-ready**. |

Demo arc (the thing every step serves):
`Dynatrace problem fires → Gemini RCA → "which MR shipped this?" → GitLab MCP diff+commit → one correlated incident card on the dashboard.`

---

## STEP 0 — Experiment Spike (`experiment/`, throwaway) — DO FIRST

**Purpose:** prove the vision is real before paying for the full repo structure. One throwaway folder, no production polish, copy liberally from `context/research/examples/`. Output is a **GO / NO-GO** decision, not shippable code.

**Validates (the vision checklist):**
1. ADK + Gemini runs locally on the AI Studio key (`adk run` / `InMemoryRunner`).
2. `McpToolset` actually mounts an external MCP server and Gemini calls its tools.
3. Adapter + mode switch works: `SENTINEL_DT_MODE=real|sim` returns the **same payload shape**.
4. Gemini reasons over a `list_problems` payload and produces a useful **morning-briefing + draft incident** (core P2 value).
5. Cross-pillar seed: feed one incident → ask "which commit?" → GitLab **simulator** returns a diff → Gemini correlates (core P1↔P2 value).
6. (Optional) OTel trace emits from the ADK run.

**Sub-steps:**

- **0.1 Scaffold spike** — `experiment/` with venv, minimal `requirements.txt` (`google-adk`, `google-genai`, `python-dotenv`, `mcp`), `.env` (Gemini key, `SENTINEL_DT_MODE=sim`). Copy `examples/gemini-hackathon/agent/main.py` + `instrumentation.py` as the runner/tracing base.
- **0.2 Gemini hello-world** — one ADK `Agent` with a trivial `FunctionTool`; `adk run` confirms the key + model work. (Mirrors `examples/gemini-hackathon/.../agent.py`.)
- **0.3 Dynatrace simulator tool** — a `FunctionTool` `list_problems()` returning a canned Davis-problem payload (shape copied from `dynatrace-mcp.md`). Prompt Gemini: "summarize open problems → morning briefing + draft incident." Confirms checklist #4 with zero external creds.
- **0.4 Real MCP mount (mechanism test)** — wire `McpToolset` to `npx @dynatrace-oss/dynatrace-mcp-server` per `adk.md` MCP-tools section. If DT creds exist, hit real `list_problems`; if not, mount a tiny local stdio MCP echo server to prove the mount path. Confirms checklist #2 + #3.
- **0.5 Cross-pillar correlation seed** — add a GitLab `simulator` tool `get_mr_diff(commit)` returning a canned diff. Feed Gemini one incident → it asks for the suspect commit → correlates diff to anomaly. Confirms checklist #5 (the headline demo arc, in miniature).
- **0.6 (optional) Trace export** — point OTLP at Phoenix or Dynatrace; confirm one span lands. Skip if clock is tight.

**Exit gate:** write `experiment/FINDINGS.md` — for each checklist item: ✅ works / ⚠️ works-with-caveat / ❌ blocked, plus any API/shape surprises. Decision:
- **GO** → lock the patterns (MCP mount snippet, sim payload shapes, prompt that produced a good briefing) and promote them into the real repo per `sentinelai.md` layout.
- **NO-GO / caveat** → adjust the real plan *before* writing it (e.g. if real DT MCP auth is too slow, commit to sim-first for the demo).

`experiment/` is gitignored or kept as a reference appendix — never the submission code.

---

## Then: real build (each step ends in a commit; sim-first, flip real later)

### Phase 0 — Foundation (promote Step-0 learnings)
Scaffold real repo per `sentinelai.md` layout: venv, `requirements.txt`, `.env.example`, `shared/` (config/models/logging), the `integrations/<name>/{interface,real,simulator,factory}.py` skeleton, public repo + **LICENSE** (rules require it day 1), ADK root orchestrator stub. Carry over the exact MCP-mount snippet and sim payloads that worked in Step 0.

### Phase 1 — Prime A: Production Sentinel (Dynatrace) ← centerpiece, build first
1. `integrations/dynatrace/` interface + simulator (canned `list_problems`/`execute_dql`) + real (`McpToolset` → dynatrace-mcp-server).
2. `services/poller/` — Cloud-Scheduler-driven 5-min trigger → agent runs `list_problems` → Gemini RCA over the chain.
3. Incident KB (Firestore/BigQuery per reconciliation — avoid MongoDB on DT track) + Vertex embeddings similarity ("seen this before?").
4. Delivery: `send_slack_message` morning briefing + draft incident/notebook.
5. Self-observability: ADK OTel traces → Dynatrace OTLP.
6. **Verify (sim):** pytest + local run + simulated trigger → briefing artifact. Flip `SENTINEL_DT_MODE=real`, re-run, confirm parity.

### Phase 2 — Prime B: Code Guardian (GitLab) ← build the correlation, not the world
1. `integrations/gitlab/` interface + simulator (canned MR diff + CI log) + real (GitLab MCP, Duo namespace per `gitlab.md`).
2. `services/webhook_gateway/` — MR-opened webhook → Gemini diff review (SQLi, secrets, perf, logic) → structured MR comment with severity.
3. CI-failure path: fetch pipeline logs → plain-English root cause in the MR comment.
4. **Cross-link (the money shot):** P2 incident → call P1 `get_mr_diff(commit)` → correlated incident card. This is the demo climax; prioritize it over breadth of review rules.
5. **Verify (sim):** simulated webhook POST → MR comment artifact; simulated incident → correlation fires.

### Phase 3 — Dashboard (Next.js) ← needed for "must run on web" + the 3-min demo
`dashboard_api/` aggregates the signals; Next.js cards: **Production (P2)**, **Code (P1)**, **AI-Quality (P3 placeholder)**. Render the correlated incident card prominently. `npm run build` + Playwright screenshots at 375/768/1280.

### Phase 4 — Third: AI Quality Gate (Arize/Phoenix) — gated on primes done
- **Default (clock tight):** `integrations/arize/` simulator only → feeds the P3 dashboard card with canned eval/drift numbers. No real MCP.
- **If both primes are recorded-demo-ready:** real Phoenix MCP (`@arizeai/phoenix-mcp`) — eval suite gen, baseline compare, deploy-block, BigQuery trends. Shares the OTel layer already built in Phase 1.

### Phase 5 — Deploy + Demo + Submit
Dockerfiles → Cloud Run; Cloud Scheduler; **full sim-mode dry run** end-to-end (demo never depends on a live external event); record ≤3-min video; public repo + LICENSE + hosted URL + Devpost form. Keep simulator as demo-day safety net.

---

## Verification matrix (per `sentinelai.md`)
- Per phase, sim mode: pytest + local service run + simulated trigger → confirm output artifact.
- Cross-pillar: simulate incident → confirm Code Guardian correlation fires.
- Dashboard: `npm run build` + Playwright at 3 widths.
- Real wiring: flip `SENTINEL_<X>_MODE=real`, re-run, confirm parity.
- Demo: full stack, sim mode, recorded backup.

## Risks specific to this ordering
- Step 0 must stay **timeboxed** (≈ half a day). It is a spike, not a product — resist polishing it.
- Real Dynatrace MCP auth (OAuth/Platform token, Grail budget) is the most likely time sink → sim path is the guaranteed demo.
- GitLab MCP is beta (Duo namespace requirement) → simulator-first protects Phase 2.
- P3 real wiring is explicitly the first thing cut if the clock runs out.
