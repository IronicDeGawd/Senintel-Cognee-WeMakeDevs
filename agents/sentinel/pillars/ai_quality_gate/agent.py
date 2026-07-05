"""AI Quality Gate ADK sub-agent. Conversational path used by the orchestrator.

Tools follow the same mode switch as the other pillars:
  sim  -> FunctionTools wrapping the eval generator + the gate (no creds)
  real -> the Phoenix MCP server mounted over stdio (P3-5; dormant until
          SENTINEL_ARIZE_MODE=real with Phoenix creds)
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from shared.config import settings
from shared.logging import get_logger

from .evalgen import generate_eval_suite as _generate_eval_suite
from .gate import run_gate
from .prompt import GATE_INSTRUCTION

log = get_logger(__name__)


def generate_eval_suite(change_description: str, suite: str) -> dict:
    """Generate an adversarial eval suite for a change to an LLM service.

    Args:
        change_description: the service and what changed about it.
        suite: a name to tag the suite with (e.g. "checkout-llm-v2").
    """
    return _generate_eval_suite(change_description, suite).model_dump(mode="json")


def run_quality_gate(suite: str) -> dict:
    """Run the named eval suite through the gate and return the decision Signal.

    Args:
        suite: the eval suite to run (e.g. "checkout-llm-v2").
    """
    return run_gate(suite).model_dump(mode="json")


def _build_tools() -> list:
    if settings.arize_mode == "real":
        from shared.mcp import stdio_mcp

        log.info("ai_quality_gate: mounting real Phoenix MCP")
        return [
            stdio_mcp(
                command="npx",
                args=[
                    "-y",
                    "@arizeai/phoenix-mcp@latest",
                    "--baseUrl",
                    settings.phoenix_endpoint,
                    "--apiKey",
                    settings.phoenix_api_key,
                ],
            )
        ]
    return [
        FunctionTool(func=generate_eval_suite),
        FunctionTool(func=run_quality_gate),
    ]


def build_ai_quality_gate() -> Agent:
    return Agent(
        model=settings.gemini_model,
        name="ai_quality_gate",
        instruction=GATE_INSTRUCTION,
        tools=_build_tools(),
    )
