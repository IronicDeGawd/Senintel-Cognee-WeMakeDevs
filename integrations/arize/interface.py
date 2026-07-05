"""Arize/Phoenix adapter contract. Both the simulator and the real Phoenix MCP
client implement these, so the agent code is identical regardless of mode.

Methods mirror what the AI Quality Gate needs:
  - run_eval     -> run one eval suite over a dataset, normalized to EvalResult
  - get_baseline -> the reference run a new run's drift is measured against
"""

from __future__ import annotations

from abc import abstractmethod

from integrations.base import Integration
from shared.models import EvalResult


class ArizeIntegration(Integration):
    name = "arize"

    @abstractmethod
    def run_eval(self, suite: str, dataset: list[dict]) -> EvalResult:
        """Run the named eval suite over `dataset` (adversarial test cases) and
        return the outcome as a normalized EvalResult. `dataset` may be empty in
        sim mode, where the result is deterministic."""
        ...

    @abstractmethod
    def get_baseline(self, suite: str) -> EvalResult:
        """Return the baseline run for `suite` — the reference point a new run's
        semantic drift is measured against."""
        ...
