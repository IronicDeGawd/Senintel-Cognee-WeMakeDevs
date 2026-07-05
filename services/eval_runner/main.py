"""AI Quality Gate eval-runner service.

A deploy event hits POST /eval with the suite to check; the service runs the
eval suite through the gate, records the run for trend charts, and returns the
Signal the dashboard renders. A blocked deploy comes back as a critical Signal.

    uvicorn services.eval_runner.main:app --reload
    curl -X POST localhost:8000/eval -H 'content-type: application/json' \\
         -d '{"suite": "checkout-llm-v2"}'
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from agents.sentinel.pillars.ai_quality_gate.gate import decide
from integrations.arize.factory import get as get_arize
from shared.logging import get_logger
from shared.models import Signal
from storage.eval_trends import get_trends
from storage.signal_store import save_signal

log = get_logger(__name__)

app = FastAPI(title="SentinelAI — AI Quality Gate eval runner")


class EvalRequest(BaseModel):
    suite: str
    dataset: list[dict] = []


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "pillar": "ai_quality"}


@app.post("/eval", response_model=Signal)
def run_eval(req: EvalRequest) -> Signal:
    """Run one eval suite, record the run for trends, and return the gate Signal."""
    log.info("eval-runner /eval triggered for suite=%s", req.suite)
    result = get_arize().run_eval(req.suite, req.dataset)
    get_trends().append(result)
    signal = decide(result)
    save_signal(signal)
    return signal
