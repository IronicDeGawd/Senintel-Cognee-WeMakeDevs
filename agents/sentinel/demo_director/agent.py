"""Demo Director ADK sub-agent. Thin wrapper that lets the root agent (or a
conversational caller) drive the same scenario the dashboard's /demo/run
endpoint runs. Each tool maps to one seeder; one tool kicks off the full arc.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from shared.config import settings

from . import scenario, seeders


def build_demo_director() -> LlmAgent:
    """Build the Demo Director ADK sub-agent.

    Tools wrap module-level seed functions directly. The agent is intentionally
    instruction-light: the dashboard speaks to the seeders via the FastAPI
    service, so the conversational path is for demo narration ("seed a fake
    spike") rather than autonomous decisions.
    """
    tools = [
        FunctionTool(seeders.seed_dynatrace_problem),
        FunctionTool(seeders.seed_gitlab_webhook),
        FunctionTool(seeders.seed_eval_regression),
        FunctionTool(scenario.run_checkout_scenario),
    ]
    return LlmAgent(
        name="demo_director",
        model=settings.gemini_model,
        description=(
            "Seeds reproducible demo scenarios into the real partner backends "
            "(Dynatrace, GitLab, Arize) so the rest of SentinelAI runs against "
            "actual partner data on demand."
        ),
        instruction=(
            "You are the Demo Director. When the user asks to run, seed, or "
            "stage a demo scenario, call run_checkout_scenario. When they ask "
            "for a single partner seeded, call the matching seed_* tool. Always "
            "report the receipt back as-is — do not editorialize."
        ),
        tools=tools,
    )
