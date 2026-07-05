"""Production Sentinel poller service.

One endpoint: POST /run executes a single sentinel cycle (RCA -> correlation ->
KB -> deliver) and returns the emitted Signal. Cloud Scheduler hits this every
few minutes in prod; locally you just curl it:

    uvicorn services.poller.main:app --reload
    curl -X POST localhost:8000/run
"""

from __future__ import annotations

import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agents.sentinel.pillars.production_sentinel.cycle import run_production_cycle
from shared.logging import get_logger
from shared.models import Signal
from shared.observability import init_tracing

log = get_logger(__name__)

# Self-observability: stream the poller's ADK traces to Dynatrace when creds are
# set; no-op otherwise. Called at import so every /run is instrumented.
init_tracing()

app = FastAPI(title="SentinelAI — Production Sentinel poller")


@app.exception_handler(Exception)
async def _surface(_request: Request, exc: Exception) -> JSONResponse:
    """Surface exception details in the response body. Cycle failures hide
    behind 500s otherwise — Cloud Logging truncates the ASGI trace below the
    actionable frames. Demo backend, no PII concern."""
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    log.error("poller /run error: %s", "".join(tb))
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "trace": "".join(tb)[-3000:],
        },
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "pillar": "production"}


@app.post("/run", response_model=Signal)
def run() -> Signal:
    """Run one production-sentinel cycle and return the Signal for the dashboard."""
    log.info("poller /run triggered")
    return run_production_cycle()
