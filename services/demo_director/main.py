"""Demo Director service. One endpoint to drive the full demo scenario, plus
per-partner endpoints for fine-grained seeding from the dashboard.

  POST /demo/run       full checkout scenario across DT + GitLab + Arize
  POST /demo/dynatrace just the DT seed (events into Grail)
  POST /demo/gitlab    just the GitLab MR webhook
  POST /demo/eval      just the AI Quality Gate
  GET  /health

The endpoints return the seeder receipt as-is so the dashboard can render the
exact outcome of each step. CORS is wide open — same model as dashboard_api.
"""

from __future__ import annotations

import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents.sentinel.demo_director import scenario, seeders
from shared.logging import get_logger

log = get_logger(__name__)

app = FastAPI(title="SentinelAI — Demo Director")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)


@app.exception_handler(Exception)
async def _surface(_request: Request, exc: Exception) -> JSONResponse:
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    log.error("demo-director error: %s", "".join(tb))
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "trace": "".join(tb)[-2500:],
        },
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "demo_director"}


@app.post("/demo/run")
def demo_run() -> dict[str, Any]:
    return scenario.run_checkout_scenario()


@app.post("/demo/dynatrace")
def demo_dynatrace() -> dict[str, Any]:
    return seeders.seed_dynatrace_problem()


@app.post("/demo/gitlab")
def demo_gitlab() -> dict[str, Any]:
    return seeders.seed_gitlab_webhook()


@app.post("/demo/eval")
def demo_eval() -> dict[str, Any]:
    return seeders.seed_eval_regression()


@app.get("/debug/dql")
def debug_dql(q: str = "fetch events | limit 5") -> dict[str, Any]:
    """Run an arbitrary DQL query against the real tenant. Used to probe
    what table the Demo Director's seeded events actually land in (the MCP
    docs are a bit thin). Demo backend only — drop once probes stop."""
    from integrations.dynatrace.factory import get as get_dynatrace
    return {"query": q, "result": get_dynatrace().execute_dql(q)}


@app.post("/debug/send-event")
def debug_send_event(arg_name: str = "approved") -> dict[str, Any]:
    """Push one canary event via the MCP send_event tool and return the raw
    MCP response. The Dynatrace MCP server gates send_event behind a human
    approval prompt; this endpoint tries different bypass argument names
    (`approved`, `confirm`, `bypassConfirmation`, etc.) so we can find the
    one the server actually honors headlessly."""
    from integrations.dynatrace.factory import get as get_dynatrace
    dt = get_dynatrace()
    args = {
        "eventType": "CUSTOM_INFO",
        "title": f"SentinelAI canary (try={arg_name})",
        "properties": {"source": "debug-send-event", "try": arg_name},
        arg_name: True,
    }
    raw = dt._call("send_event", args)  # type: ignore[attr-defined]
    return {"args": args, "raw": raw}
