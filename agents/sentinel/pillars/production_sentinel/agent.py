"""Production Sentinel ADK sub-agent. Conversational/briefing path used by the
orchestrator + poller.

Tools follow the spike's mode switch:
  sim  -> FunctionTools wrapping the Dynatrace simulator (no creds)
  real -> the Dynatrace MCP server mounted over stdio (P2-7; dormant until
          SENTINEL_DT_MODE=real with DT creds)
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from integrations.dynatrace.factory import get as get_dynatrace
from shared.config import settings
from shared.logging import get_logger

from .correlation import get_mr_diff
from .prompt import BRIEFING_INSTRUCTION

log = get_logger(__name__)


def list_problems() -> list[dict]:
    """Return currently open Dynatrace problems (Davis anomalies) as a list of
    dicts: problem_id, title, severity, service, root_cause_entity, evidence."""
    return [p.model_dump(mode="json") for p in get_dynatrace().list_problems()]


def execute_dql(query: str) -> dict:
    """Run a Dynatrace Query Language statement and return the raw result.

    Args:
        query: the DQL statement (e.g. a logs/metrics fetch for a service).
    """
    return get_dynatrace().execute_dql(query)


def _build_tools() -> list:
    if settings.dt_mode == "real":
        from shared.mcp import stdio_mcp

        log.info("production_sentinel: mounting real Dynatrace MCP")
        return [
            stdio_mcp(
                command="npx",
                args=["-y", "@dynatrace-oss/dynatrace-mcp-server@latest"],
                env={
                    "DT_ENVIRONMENT": settings.dt_environment,
                    "DT_PLATFORM_TOKEN": settings.dt_platform_token,
                },
                tool_filter=[
                    "list_problems",
                    "execute_dql",
                    "send_slack_message",
                    "create_dynatrace_notebook",
                ],
            )
        ]
    # get_mr_diff is the cross-pillar correlation seam (P2-4): the agent can pull
    # the suspect deploy's diff from Code Guardian to link an anomaly to a commit.
    return [
        FunctionTool(func=list_problems),
        FunctionTool(func=execute_dql),
        FunctionTool(func=get_mr_diff),
    ]


def build_production_sentinel() -> Agent:
    return Agent(
        model=settings.gemini_model,
        name="production_sentinel",
        instruction=BRIEFING_INSTRUCTION,
        tools=_build_tools(),
    )
