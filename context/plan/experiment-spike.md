# Step 0 — Experiment Spike: Implementation Plan

> Throwaway proof-of-vision in `experiment/`. Goal: confirm the SentinelAI loop
> (ADK + Gemini + partner MCP + simulator + cross-pillar correlation) actually
> works before building the real repo. Output = `experiment/FINDINGS.md` GO/NO-GO.
> Companion to [build-steps.md](build-steps.md) §STEP 0. Timebox: ~half a day.
> Sources: [../research/adk.md](../research/adk.md) (MCP tools),
> [../research/dynatrace-mcp.md](../research/dynatrace-mcp.md),
> [../research/examples/gemini-hackathon/](../research/examples/gemini-hackathon/).

## What we are trying to prove (the only point of this spike)

| # | Claim under test | Pass = |
|---|---|---|
| C1 | ADK + Gemini runs locally on an AI Studio key | `adk run` answers a prompt |
| C2 | `McpToolset` mounts an external MCP server, Gemini calls its tools | one real MCP tool call returns |
| C3 | Adapter + mode switch (`real\|sim`) returns the **same payload shape** | both modes feed Gemini identically |
| C4 | Gemini turns `list_problems` into a useful **morning briefing + draft incident** | output is something an SRE would actually read |
| C5 | Cross-pillar: incident → "which commit?" → GitLab sim diff → correlation | Gemini links anomaly to the suspect diff |
| C6 | (optional) ADK OTel trace exports | one span lands in Phoenix/Dynatrace |

If C1–C5 pass → **GO** (promote patterns). Any ❌ → fix the real plan before writing it.

## Folder layout (throwaway, gitignored)

```
experiment/
  .env                  # GEMINI/GOOGLE key, SENTINEL_DT_MODE, SENTINEL_GL_MODE
  .env.example
  requirements.txt      # google-adk, google-genai, python-dotenv, mcp
  runner.py             # InMemoryRunner harness (copied from gemini-hackathon/main.py)
  sentinel/
    __init__.py
    agent.py            # root_agent: tools = sim tools OR McpToolset by mode
    prompt.py           # briefing + correlation instruction
    dt_sim.py           # FunctionTool list_problems() -> canned Davis payload
    gl_sim.py           # FunctionTool get_mr_diff(commit) -> canned diff
    dt_real.py          # McpToolset -> @dynatrace-oss/dynatrace-mcp-server
  fixtures/
    problems.json       # canned list_problems payload (shape from dynatrace-mcp.md)
    mr_diff.json        # canned MR diff + commit sha
  FINDINGS.md           # the exit-gate report
```

## Sub-steps (each is independently runnable + checks one claim)

### 0.1 Scaffold (no key needed)
- `python -m venv experiment/.venv`; activate; `pip install google-adk google-genai python-dotenv mcp`; freeze to `requirements.txt`.
- `.env.example` keys: `GOOGLE_API_KEY=`, `GOOGLE_GENAI_USE_VERTEXAI=FALSE`, `GEMINI_MODEL=gemini-2.5-flash`, `SENTINEL_DT_MODE=sim`, `SENTINEL_GL_MODE=sim`, (`DT_ENVIRONMENT=`, `DT_PLATFORM_TOKEN=` for C2).
- Copy `runner.py` from `examples/gemini-hackathon/agent/main.py` (InMemoryRunner harness, `load_dotenv`).

### 0.2 Gemini hello-world → **C1**
- `sentinel/agent.py`: one `Agent(model=GEMINI_MODEL, name=..., instruction=..., tools=[])`.
- Run: `python runner.py "say hi and name your model"` (or `adk run sentinel`).
- ✅ when Gemini answers. Confirms key + model wired. **Blocker if no key** — do 0.3/0.5 sim wiring first, run when key lands.

### 0.3 Dynatrace SIMULATOR tool → **C3 + C4** (no creds)
- `fixtures/problems.json`: canned Davis payload — list of `{problemId, title, severityLevel, status, impactedEntities, rootCauseEntity, startTime}` (shape per `dynatrace-mcp.md` `list_problems`).
- `dt_sim.py`: `def list_problems() -> dict:` returns the fixture (this IS the adapter `simulator` path).
- `prompt.py`: instruct agent — "call list_problems, then write a morning briefing (top problems, likely root cause, severity) + a draft incident ticket (title, summary, suspected cause, next action)."
- Wire as `FunctionTool(func=list_problems)` when `SENTINEL_DT_MODE=sim`.
- Run `python runner.py "give me the morning briefing"` → judge the output by eye. ✅ when it reads like a real SRE briefing.

### 0.4 Dynatrace REAL MCP mount → **C2** (mechanism proof)
- `dt_real.py`:
```python
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

dynatrace_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@dynatrace-oss/dynatrace-mcp-server@latest"],
            env={"DT_ENVIRONMENT": os.environ["DT_ENVIRONMENT"],
                 "DT_PLATFORM_TOKEN": os.environ.get("DT_PLATFORM_TOKEN", "")},
        )
    ),
    tool_filter=["list_problems", "execute_dql"],  # keep narrow for the spike
)
```
- `agent.py`: when `SENTINEL_DT_MODE=real`, put `dynatrace_mcp` in `tools` instead of the sim FunctionTool.
- **If DT creds exist:** run → confirm a real `list_problems` returns. ✅ = C2.
- **If no DT creds yet:** prove the mount path with a trivial public MCP instead — mount `npx -y @modelcontextprotocol/server-filesystem <abs path>` with `tool_filter=["list_directory"]` and confirm Gemini calls it. That still proves C2 (McpToolset → external stdio server → tool call works); swap the DT package in later. Note the substitution in FINDINGS.

### 0.5 Cross-pillar correlation seed → **C5** (the headline arc, miniature)
- `fixtures/mr_diff.json`: `{commit, mr_id, author, diff}` where the diff plausibly causes the canned anomaly (e.g. a query change → latency spike).
- `gl_sim.py`: `def get_mr_diff(commit: str) -> dict:` returns the fixture.
- Add `get_mr_diff` as a second tool; extend the prompt: "after the briefing, identify the suspect commit, call get_mr_diff, and explain in plain English whether that change likely caused the anomaly."
- Run → ✅ when Gemini chains problem → commit → diff → causal explanation. This is the demo climax proven in one process.

### 0.6 (optional) Trace export → **C6**
- Reuse `examples/gemini-hackathon/agent/instrumentation.py` `setup_tracing()`. Point OTLP at Phoenix (`http://localhost:6006`) or Dynatrace `…/api/v2/otlp`. ✅ when one span lands. Skip if clock tight.

## Run / verify commands
```bash
cd experiment && .venv\Scripts\activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python runner.py "say hi"                          # 0.2  C1
python runner.py "give me the morning briefing"    # 0.3  C4 (sim)
$env:SENTINEL_DT_MODE="real"; python runner.py "..."  # 0.4  C2
python runner.py "brief me, then find the commit"  # 0.5  C5
```

## Exit gate — `experiment/FINDINGS.md`
For each C1–C6: ✅ works / ⚠️ works-with-caveat / ❌ blocked + the surprise (API shape, auth friction, payload mismatch). Then the decision:
- **GO** — copy forward the winning artifacts: the `McpToolset` snippet, the fixture payload shapes, and the exact prompt that produced a good briefing. These seed Phase 0/1 of the real build.
- **NO-GO / caveat** — record what to change in `build-steps.md` *before* scaffolding the real repo (most likely: if real DT MCP auth is slow/flaky → commit to sim-first for the demo, real wiring as stretch).

## Guardrails
- This is a **spike**. No tests, no error handling polish, no clean architecture — just enough to answer C1–C6. Resist building the real thing here.
- `experiment/` is gitignored (or kept as a reference appendix). It is **never** the submission code.
- Hard timebox ~half a day. If C2 (real MCP auth) burns the box, mark ⚠️ and move on — sim path already proves the product loop.
```
