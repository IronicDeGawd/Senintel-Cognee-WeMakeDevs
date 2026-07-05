"""Root-cause analysis: open Dynatrace problems -> one draft Incident.

Programmatic path used by the poller to emit a Signal. Fetches problems from the
Dynatrace adapter (sim or real, by mode) and asks Gemini — via the shared
structured helper — for a validated Incident.
"""

from __future__ import annotations

import json

from agents.sentinel.pillars.production_sentinel.prompt import RCA_INSTRUCTION
from integrations.dynatrace.factory import get as get_dynatrace
from shared.llm import generate_json
from shared.logging import get_logger
from shared.models import Incident, Problem

log = get_logger(__name__)


def _problems_payload(problems: list[Problem]) -> str:
    return json.dumps([p.model_dump(mode="json") for p in problems], indent=2)


def run_rca(problems: list[Problem] | None = None) -> Incident:
    """Reason over open problems and return a draft Incident.

    Args:
        problems: pre-fetched problems; if None, fetch from the active Dynatrace
            adapter (mode-driven).
    """
    if problems is None:
        problems = get_dynatrace().list_problems()
    log.info("running RCA over %d problem(s)", len(problems))
    prompt = f"{RCA_INSTRUCTION}\n\nOPEN PROBLEMS (JSON):\n{_problems_payload(problems)}"
    return generate_json(prompt, Incident)
