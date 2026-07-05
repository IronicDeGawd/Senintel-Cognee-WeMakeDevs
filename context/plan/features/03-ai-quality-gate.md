# 03 — AI Quality Gate (Pillar 3, Arize/Phoenix) — THIRD (stretch)

> Owner: whoever finishes a prime first (or a 3rd dev). Build only after both
> primes are demo-ready. Default = simulator + dashboard card; full real MCP only
> if the clock allows. Prereq: [00-foundation.md](00-foundation.md) frozen.

## What it does
When an LLM-powered service ships (prompt/model change) → agent generates an
adversarial eval suite → runs it through Phoenix → measures hallucination rate +
semantic drift vs. a baseline → **blocks the deploy** if quality regresses past a
threshold → logs trend to BigQuery. Shares the OTel layer with Production Sentinel
(one instrumentation feeds both Phoenix and Dynatrace).

## File map
```
integrations/arize/
  interface.py     # ArizeIntegration: run_eval(suite, dataset) -> EvalResult, get_baseline()
  simulator.py     # canned EvalResult (pass + fail cases)
  real.py          # shared.mcp.stdio_mcp("npx", ["-y","@arizeai/phoenix-mcp@latest","--baseUrl",..,"--apiKey",..])
  factory.py       # get(mode) -> sim|real
agents/sentinel/pillars/ai_quality_gate/
  agent.py         # tools = Arize (by mode); produces EvalResult + gate decision
  prompt.py        # adversarial eval-suite generation + judge rubric
  evalgen.py       # Gemini generates adversarial test cases (shared.llm)
services/eval_runner/
  main.py          # FastAPI POST /eval -> run suite -> EvalResult -> gate -> Signal
storage/
  eval_trends.py   # BigQuery: append eval runs for trend charts
```

## Step-by-step

### P3-1 — Simulator first (no creds) — THIS is the default deliverable
- `integrations/arize/simulator.py`: canned `EvalResult` (a passing run and a
  failing run with high hallucination/drift). `factory.get("sim")`.
- Emit `Signal(pillar="ai_quality", status=...)` so the **dashboard card renders**
  with real-looking numbers. Unit test pass/fail gating.

### P3-2 — Eval generation + gate (sim)
- `evalgen.py`: Gemini generates adversarial prompts (hallucination bait, jailbreak,
  edge cases) → an eval dataset. `agent.py` runs the suite (sim) → `EvalResult`.
- Gate logic: `passed = hallucination_rate < threshold and drift < threshold`.
  On fail → `Signal(status="critical", headline="Deploy blocked: quality regressed")`.

### P3-3 — Eval runner service
- `services/eval_runner/main.py`: `POST /eval` (triggered by a deploy event) →
  run → gate → emit Signal + (real) write to BigQuery.

### P3-4 — BigQuery trends
- `storage/eval_trends.py`: append each run; dashboard reads for a drift-over-time
  chart. Sim fallback: canned trend rows.

### P3-5 — Real Phoenix wiring (flip `SENTINEL_ARIZE_MODE=real`) — only if time
- Mount `@arizeai/phoenix-mcp@latest` via `shared.mcp.stdio_mcp`, `--baseUrl`
  = Phoenix space (`https://app.phoenix.arize.com/s/<space>`), `--apiKey` `px_live_...`.
- Local Phoenix option: `pip install arize-phoenix`; `phoenix serve` at `:6006`.
- ADK auto-instrument via `openinference-instrumentation-google-adk` →
  `register(auto_instrument=True)` (reuse `experiment/.../instrumentation.py` pattern).
- Run real evals through Phoenix; pull metrics via the MCP tools.

## Verification
- Sim: pytest (gate blocks on the failing canned result) + `POST /eval` → Signal + (canned) trend.
- Real (if built): a real eval run lands in Phoenix; metrics flow back; gate decision matches.

## Definition of done
- **Minimum (stretch-default):** simulator emits `Signal(pillar="ai_quality")`; dashboard card renders pass/fail + numbers.
- **Full (if time):** real Phoenix MCP eval run + deploy-block + BigQuery trend.
- Committed artifact: a gate decision output (+ Phoenix screenshot if real).

## Risks
- This is the **first thing cut** if the clock runs out. Keep the sim path enough to
  tell the three-pillar story on the dashboard without real wiring.
- Arize is a different prize bucket — does NOT earn points in the Dynatrace bucket;
  it is narrative completeness only.
