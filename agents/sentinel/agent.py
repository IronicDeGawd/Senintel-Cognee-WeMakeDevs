"""Root ADK orchestrator (Foundation stub).

Carries the spike's mode-switch pattern (`_build_tools()`): tools are assembled
from the *active* pillars by their mode. No pillar is wired yet, so the tool
list starts empty and grows as pillars register their adapters here. The agent
still answers a plain hello-world turn so the loop is provable today.
"""

from __future__ import annotations

from google.adk.agents import Agent

from shared.config import settings
from shared.logging import get_logger

log = get_logger(__name__)

INSTRUCTION = """\
You are SentinelAI, an autonomous engineer watching an entire software delivery
pipeline across three pillars:
  - Production health (Dynatrace) — detect anomalies, do root-cause analysis.
  - Code (GitLab) — review merge requests, diagnose CI failures.
  - AI quality (Arize/Phoenix) — catch hallucination and drift before deploy.
When pillar tools are available, use them; otherwise answer from what you know.
Be concise and concrete.
"""


def _build_tools() -> list:
    """Assemble tools from active pillars by mode. Pillars append here as they
    land (e.g. Dynatrace adapter under settings.dt_mode). Empty for now."""
    tools: list = []
    log.info(
        "building root agent tools (dt=%s gl=%s arize=%s)",
        settings.dt_mode,
        settings.gl_mode,
        settings.arize_mode,
    )
    return tools


def build_root_agent() -> Agent:
    return Agent(
        model=settings.gemini_model,
        name="sentinel",
        instruction=INSTRUCTION,
        tools=_build_tools(),
    )


root_agent = build_root_agent()
