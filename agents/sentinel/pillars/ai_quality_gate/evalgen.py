"""Adversarial eval-suite generation. Gemini plays red-teamer: given a service
and the change shipping to it, it writes hard test cases designed to surface
hallucination, jailbreaks, and edge-case failures before users hit them.

The output (EvalSuite) is the dataset the gate runs. EvalCase/EvalSuite are
pillar-local shapes — they never leave P3, so they stay here, not in the shared
contract.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from shared.llm import generate_json
from shared.logging import get_logger

from .prompt import EVALGEN_INSTRUCTION

log = get_logger(__name__)


class EvalCase(BaseModel):
    prompt: str
    category: Literal["hallucination_bait", "jailbreak", "edge_case"]
    expected_behavior: str


class EvalSuite(BaseModel):
    suite: str
    cases: list[EvalCase]


def generate_eval_suite(change_description: str, suite: str) -> EvalSuite:
    """Ask Gemini for an adversarial eval suite targeting `change_description`.

    Args:
        change_description: short text describing the service and what changed
            (e.g. "checkout-llm: new prompt that summarizes order issues").
        suite: the name to tag this suite with (e.g. "checkout-llm-v2").
    """
    log.info("generating adversarial eval suite for %s", suite)
    prompt = (
        f"{EVALGEN_INSTRUCTION}\n\nSUITE NAME: {suite}\n"
        f"SERVICE / CHANGE:\n{change_description}"
    )
    result = generate_json(prompt, EvalSuite)
    # Gemini may echo its own suite name; force the caller's name for consistency.
    result.suite = suite
    return result
