"""The quality gate: turn an eval outcome into a deploy decision.

Picture a bouncer at a door with one rule: a release only gets in if it both
makes few things up (low hallucination) AND still answers like the trusted
baseline (low drift). Fail either and the deploy is blocked.

`evaluate` is that single rule — the simulator and the real path both use it, so
the pass/fail verdict can never disagree with itself. `decide` wraps a result in
the dashboard `Signal` envelope; `run_gate` is the one-call orchestration the
eval-runner service uses (run the suite, then gate it).
"""

from __future__ import annotations

from datetime import datetime, timezone

from shared.config import Mode
from shared.models import EvalResult, Signal


def evaluate(hallucination_rate: float, drift: float, threshold: float) -> bool:
    """Quality gate rule: pass only if BOTH metrics sit under the threshold."""
    return hallucination_rate < threshold and drift < threshold


def decide(result: EvalResult) -> Signal:
    """Map one eval outcome to the dashboard Signal. A failed gate blocks the
    deploy and surfaces as a critical signal."""
    if result.passed:
        status: str = "ok"
        headline = f"Quality gate passed: {result.suite} within thresholds"
    else:
        status = "critical"
        headline = (
            f"Deploy blocked: {result.suite} regressed "
            f"(hallucination {result.hallucination_rate:.0%}, "
            f"drift {result.drift:.0%}, threshold {result.threshold:.0%})"
        )
    return Signal(
        pillar="ai_quality",
        status=status,  # type: ignore[arg-type]
        headline=headline,
        detail=result.model_dump(),
        ts=datetime.now(timezone.utc),
    )


def run_gate(suite: str, dataset: list[dict] | None = None, mode: Mode | None = None) -> Signal:
    """Run the eval suite through the Arize adapter, then gate the result."""
    from integrations.arize.factory import get

    arize = get(mode)
    result = arize.run_eval(suite, dataset or [])
    return decide(result)
