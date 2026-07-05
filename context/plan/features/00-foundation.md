# 00 — Foundation + Contracts (BLOCKING prerequisite)

> ✅ **STATUS: BUILT + verified on `main` (Jun 9).** ruff clean, pytest 5/5, live
> Gemini turn over Vertex AI + ADC. This doc is now the onboarding reference for
> anyone picking up a pillar — read the **setup** in
> [README.md](README.md#local-dev-setup-every-dev--one-time-10-min) first.
>
> One owner (Dev A). ~half day. Everything else waits on the **contracts** here
> (interfaces + data models + factory). Pair with Dev B for the first hour to
> agree the contracts, then they are append-only.
> Carry forward the proven patterns from `experiment/` (spike = GO).

## Scope
Scaffold the real repo, define the shared contracts that let pillars build in
parallel, and stand up the ADK root orchestrator + mode-switch factory. No
pillar logic here — just the skeleton everyone plugs into.

## Prereqs
- Spike GO (done). Python 3.12, Node 22 (for npx MCP servers).
- **gcloud SDK + ADC**, not an API key. Install gcloud (`winget install --id Google.CloudSDK`),
  then `gcloud auth application-default login` + `set-quota-project <PROJECT_ID>`.
  Gemini runs for real on Vertex AI through ADC. Full steps in
  [README.md §Local dev setup](README.md#local-dev-setup-every-dev--one-time-10-min).
- A GCP project with billing/free-credits; Vertex AI API enabled once.

## Step-by-step

### F1 — Repo scaffold + LICENSE (rules require public OSS + LICENSE day 1)
- Create the tree from `context/plan/sentinelai.md` §Repo Layout.
- `python -m venv .venv`; `requirements.txt` (see §Deps); `pip install -r`.
- `LICENSE` (Apache-2.0 or MIT), `README.md` (one-paragraph pitch + run steps).
- `.env.example` (append-only; pillars add their own keys).

### F2 — `shared/config.py` (pydantic-settings) ✅ built
- Load env once. Fields: **Google auth** `google_genai_use_vertexai` (default `true`),
  `google_cloud_project`, `google_cloud_location` (default `us-central1`) — these are
  also the env vars ADK reads directly. `gemini_model` (default `gemini-2.5-flash`).
  `gemini_api_key` kept only as opt-out fallback. Per-pillar mode flags
  `dt_mode`/`gl_mode`/`arize_mode` (`sim|real`) via `SENTINEL_<X>_MODE`, plus the creds
  blocks (DT_ENVIRONMENT/DT_PLATFORM_TOKEN, GITLAB_*, PHOENIX_*).
- `load_dotenv` at import (spike pattern) so client libs + ADK see the same env.

### F3 — `shared/models.py` (THE CONTRACT — freeze early)
Pydantic models every pillar + dashboard import. Append-only after the pairing hour.
```python
class Severity(str, Enum): INFO="info"; LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"

class Problem(BaseModel):          # P2 in  — mirrors Dynatrace list_problems
    problem_id: str; title: str; severity: Severity; status: str
    service: str; root_cause_entity: str | None; start_time: datetime
    evidence: dict

class Finding(BaseModel):          # P1 in  — one code-review issue
    file: str; line: int | None; category: str; severity: Severity
    message: str; suggestion: str | None

class MRReview(BaseModel):         # P1 out
    mr_id: int; commit: str; findings: list[Finding]; ci_root_cause: str | None

class EvalResult(BaseModel):       # P3 out
    suite: str; hallucination_rate: float; drift: float
    passed: bool; threshold: float

class Incident(BaseModel):         # P2 out (the briefing artifact)
    title: str; severity: Severity; service: str; summary: str
    suspected_cause: str; suspect_commit: str | None; next_action: str

class Signal(BaseModel):           # THE DASHBOARD CONTRACT — every pillar emits this
    pillar: Literal["code","production","ai_quality"]
    status: Literal["ok","warning","critical"]
    headline: str
    detail: dict                   # pillar-specific payload (Incident / MRReview / EvalResult)
    ts: datetime
```

### F4 — `integrations/base.py` (THE ADAPTER CONTRACT)
```python
class Integration(ABC):
    name: str
    @abstractmethod
    def healthcheck(self) -> bool: ...
# Each pillar subclasses with its own methods, e.g. DynatraceIntegration.list_problems().
```
- Per-integration folder: `interface.py` (abstract methods) + `simulator.py` +
  `real.py` + `factory.py`. `factory.get(mode)` returns sim or real.

### F5 — `shared/mcp.py` (reusable MCP mount helper — proven in spike)
```python
def stdio_mcp(command, args, env=None, tool_filter=None) -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(command=command, args=args, env=env or {})),
        tool_filter=tool_filter)
```
- Add a **connect retry** wrapper (spike finding: Windows stdio flaky).

### F6 — `shared/llm.py` (Gemini call with retry/backoff) ✅ built
- `generate(prompt, model=None)`. Builds `genai.Client(vertexai=True, project=…,
  location=…)` from config (ADC auth); falls back to API key only if
  `GOOGLE_GENAI_USE_VERTEXAI=false`. Tenacity retry on 429/5xx overload (spike
  finding: Gemini 503/429 under load). All pillars use this, not raw calls.

### F7 — `agents/sentinel/agent.py` (root orchestrator stub)
- ADK root `Agent` on `gemini-2.5-flash`. Tools list assembled from the active
  pillars by mode (extend the spike `_build_tools()` pattern). Hello-world turn.

### F8 — `shared/logging.py` + `tests/conftest.py`
- Structured logging; pytest fixtures that force `*_MODE=sim` for deterministic tests.

## Deps (`requirements.txt`)
`google-adk>=1.32`, `google-genai`, `pydantic`, `pydantic-settings`, `python-dotenv`,
`mcp`, `fastapi`, `uvicorn`, `httpx`, `tenacity`, `pytest`, `pytest-asyncio`, `ruff`.
(Storage/partner libs added by their pillars: `google-cloud-firestore`/`bigquery`,
`google-cloud-aiplatform`, `slack_sdk`, `arize-phoenix`.)

## Verification
- `pytest tests/` green (config + models import + factory returns sim).
- Root agent hello-world answers (reuses spike key).
- `ruff check` clean.

## Definition of done
- Tree + LICENSE + `.env.example` committed; repo public.
- `shared/models.py` (incl. `Signal`) + `integrations/base.py` frozen and announced to the team.
- `shared/mcp.py` + `shared/llm.py` reusable helpers in place.
- Pillars can now start in parallel.

## Hand-off to teammates (post-F3/F4)
Announce in the team channel: "Contracts frozen — `Signal`, `Problem`, `MRReview`,
`EvalResult`, `Incident`, `Integration`. Build your pillar's `simulator.py` against
these. Add your `SENTINEL_<X>_MODE` to `.env.example`. Don't edit others' sections."
