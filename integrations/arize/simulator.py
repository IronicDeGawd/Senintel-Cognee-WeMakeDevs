"""Arize/Phoenix simulator (mode = sim). Deterministic, no creds. Returns canned
EvalResult runs so the AI Quality Gate works end to end — and the dashboard card
renders real-looking numbers — without a live Phoenix space.

The pass/fail verdict is NOT hardcoded in the fixture: it is computed with the
gate's own `evaluate` rule, so the simulator can never disagree with the gate.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.sentinel.pillars.ai_quality_gate.gate import evaluate
from shared.models import EvalResult

from .interface import ArizeIntegration

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "eval_runs.json"


def _load() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _result(suite: str, hallucination_rate: float, drift: float, threshold: float) -> EvalResult:
    return EvalResult(
        suite=suite,
        hallucination_rate=hallucination_rate,
        drift=drift,
        threshold=threshold,
        passed=evaluate(hallucination_rate, drift, threshold),
    )


class ArizeSimulator(ArizeIntegration):
    def healthcheck(self) -> bool:
        return True

    def get_baseline(self, suite: str) -> EvalResult:
        data = _load()
        base = data["baseline"]
        return _result(base["suite"], base["hallucination_rate"], base["drift"], data["threshold"])

    def run_eval(self, suite: str, dataset: list[dict]) -> EvalResult:
        """Canned outcome keyed by suite name. `checkout-llm-v2` is the regressed
        release (the deploy-block demo); unknown suites fall back to a clean run."""
        data = _load()
        metrics = data["runs"].get(suite, data["default"])
        return _result(
            suite, metrics["hallucination_rate"], metrics["drift"], data["threshold"]
        )
