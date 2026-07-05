"""Dashboard backend — one FastAPI service the Next.js frontend polls.

Six endpoints:
  GET  /signals               latest Signal per pillar
  GET  /history               recent Signals (newest first, optional pillar)
  GET  /correlation           latest prod incident joined to the matching MR
  GET  /trends/quality        eval trends time series (for the drift chart)
  POST /trigger/{pillar}      proxy fire-and-forget to the pillar's Cloud Run
  GET  /health                liveness

Reuses the existing stores so nothing fan-outs to GCP twice:
- signal_store    -> /signals, /history, /correlation
- incident_kb     -> not strictly needed (Signal.detail.incident has the body)
- eval_trends     -> /trends/quality

Deploys as the fourth Cloud Run service (same image, override command). The
three trigger URLs are set as env at deploy:
  DASHBOARD_TRIGGER_GATEWAY_URL, _POLLER_URL, _EVAL_RUNNER_URL.
"""

from __future__ import annotations

import traceback
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import settings
from shared.logging import get_logger
from shared.models import Signal
from storage.eval_trends import get_trends
from storage.signal_store import get_signal_store

log = get_logger(__name__)

app = FastAPI(title="SentinelAI — Dashboard API")

# Wide-open CORS for the demo: the Vercel frontend lives on a separate origin
# and the surface is public read-only. Trigger endpoints are rate-limited at
# Cloud Run, not at the app layer.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)

Pillar = Literal["production", "code", "ai_quality"]

_TRIGGER_TARGETS: dict[Pillar, tuple[str, str, dict]] = {
    # pillar -> (env-config field, suffix path, canned request body)
    "production": ("dashboard_trigger_poller_url", "/run", {}),
    # The gateway validates a real MR webhook payload + X-Gitlab-Token; the
    # Demo Director owns that logic (live MR head SHA + webhook secret), so
    # the code trigger proxies through its /demo/gitlab seeder instead of
    # POSTing an empty body straight at the gateway (which 401s).
    "code": ("dashboard_demo_director_url", "/demo/gitlab", {}),
    # /eval validates an EvalRequest body — an empty POST 422s.
    "ai_quality": (
        "dashboard_trigger_eval_runner_url",
        "/eval",
        {"suite": "checkout-llm-v2", "dataset": []},
    ),
}


@app.exception_handler(Exception)
async def _all_errors(_request: Request, exc: Exception) -> JSONResponse:
    """Surface the actual exception in the response body. The dashboard is the
    only consumer and lives behind public CORS; visibility beats discretion for
    a demo backend. Cloud Run access logs also pick this up as a structured row."""
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    log.error("dashboard_api error: %s", "".join(tb))
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "trace": "".join(tb)[-2000:],
        },
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "dashboard_api"}


@app.get("/signals")
def signals() -> dict[Pillar, Signal | None]:
    """Latest Signal for each pillar. Missing pillars come back as None so the
    dashboard can render an "awaiting first signal" placeholder card."""
    latest = get_signal_store().latest_per_pillar()
    return {
        "production": latest.get("production"),
        "code": latest.get("code"),
        "ai_quality": latest.get("ai_quality"),
    }


@app.get("/history")
def history(pillar: Pillar | None = None, limit: int = 20) -> list[Signal]:
    """Recent Signals (newest first). Cap `limit` at 100 to keep responses
    bounded if a frontend bug ever sends `limit=1e6`."""
    limit = max(1, min(limit, 100))
    return get_signal_store().recent(limit=limit, pillar=pillar)


@app.get("/correlation")
def correlation() -> dict:
    """Join the latest production Signal to the most recent code Signal that
    shares its suspect_commit / mr_id. Returns null fields when either side is
    missing so the frontend can render an empty-state card."""
    store = get_signal_store()
    prod = next(iter(store.recent(limit=1, pillar="production")), None)
    code = next(iter(store.recent(limit=1, pillar="code")), None)

    suspect_commit = None
    incident = None
    if prod is not None:
        incident = prod.detail.get("incident") or {}
        suspect_commit = incident.get("suspect_commit")

    # Best-effort join: prefer the code Signal whose review.commit matches the
    # incident's suspect_commit. Fall back to the most recent code Signal.
    review = None
    if code is not None:
        review_payload = code.detail.get("review") or {}
        if suspect_commit and review_payload.get("commit") == suspect_commit:
            review = review_payload
        elif suspect_commit is None:
            review = review_payload

    return {
        "production": incident,
        "code": review,
        "verdict": (
            f"Roll back MR !{review['mr_id']} / commit {suspect_commit}"
            if (review and suspect_commit)
            else None
        ),
    }


@app.get("/trends/quality")
def trends_quality(limit: int = 30) -> list[dict]:
    """Eval trend rows (latest N), newest first. Powers the drift chart."""
    limit = max(1, min(limit, 200))
    rows = get_trends().recent(limit=limit)
    if rows:
        return rows
    # On Cloud Run the sim trends store is a per-container JSON file, so the
    # eval-runner's appends are invisible to this service. The same numbers
    # ride in on every ai_quality Signal (detail == EvalResult dump) and the
    # signal store IS shared, so chart from those when the store is empty.
    signals = get_signal_store().recent(limit=limit, pillar="ai_quality")
    return [
        {**s.detail, "ts": s.ts.isoformat()}
        for s in signals
        if "hallucination_rate" in s.detail
    ]


@app.post("/demo/run")
async def demo_run() -> dict:
    """Proxy the dashboard 'Run Scenario' button to the Demo Director's
    /demo/run. Returns 503 when DASHBOARD_DEMO_DIRECTOR_URL is unset (dev
    mode). The full scenario can take 30+ seconds, so the timeout is generous;
    Cloud Run requests can run up to 60 minutes by default."""
    base = settings.dashboard_demo_director_url
    if not base:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DASHBOARD_DEMO_DIRECTOR_URL not configured",
        )
    url = base.rstrip("/") + "/demo/run"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json={})
    except httpx.HTTPError as exc:
        log.warning("demo proxy %s failed: %s", url, exc)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, detail=f"demo upstream error: {exc}"
        ) from exc
    ctype = resp.headers.get("content-type", "")
    body = resp.json() if ctype.startswith("application/json") else {}
    return {"upstream_status": resp.status_code, "result": body}


@app.post("/trigger/{pillar}")
async def trigger(pillar: Pillar) -> dict:
    """Fire-and-forget proxy to the pillar's Cloud Run service. Empty target URL
    means we're running in sim/dev: return 503 instead of silently no-op'ing so
    the frontend can show a clear "not wired" pill."""
    if pillar not in _TRIGGER_TARGETS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"unknown pillar {pillar}")

    field, suffix, payload = _TRIGGER_TARGETS[pillar]
    base = getattr(settings, field, "")
    if not base:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{field} not configured (set the env to enable this trigger)",
        )

    url = base.rstrip("/") + suffix
    # Don't hold the dashboard request open for the full pillar cycle — the
    # poller's /run does 30s+ of Gemini + MCP work synchronously. A read
    # timeout after the POST landed means "accepted, still running", not an
    # error; only connect-level failures are surfaced as 502.
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            resp = await client.post(url, json=payload)
    except httpx.ReadTimeout:
        log.info("trigger %s -> %s accepted (upstream still running)", pillar, url)
        return {"pillar": pillar, "target": url, "upstream_status": 202}
    except httpx.HTTPError as exc:
        log.warning("trigger %s -> %s failed: %s", pillar, url, exc)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, detail=f"trigger upstream error: {exc}"
        ) from exc

    return {
        "pillar": pillar,
        "target": url,
        "upstream_status": resp.status_code,
    }
