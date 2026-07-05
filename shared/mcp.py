"""Reusable MCP mount helper. Proven path from the spike (`dt_real.py`):
McpToolset over stdio launched via npx.

Spike finding: Windows stdio startup is occasionally flaky (first connect threw
an asyncio TaskGroup error, second was clean). The real connect happens lazily
inside ADK on first tool use, so we cannot retry the handshake from here; what
we *can* do cheaply is retry construction of the toolset and surface a clear
error. For production prefer running on Linux (Cloud Run).
"""

from __future__ import annotations

from collections.abc import Sequence

from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters
from tenacity import retry, stop_after_attempt, wait_fixed

from shared.logging import get_logger

log = get_logger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
def stdio_mcp(
    command: str,
    args: Sequence[str],
    env: dict[str, str] | None = None,
    tool_filter: Sequence[str] | None = None,
) -> McpToolset:
    """Mount an external stdio MCP server as an ADK toolset.

    Args:
        command: launcher, e.g. "npx".
        args: command args, e.g. ["-y", "@dynatrace-oss/dynatrace-mcp-server@latest"].
        env: env vars passed to the server process (creds live here).
        tool_filter: keep the exposed tool surface narrow (e.g. ["list_problems"]).
    """
    log.info("mounting MCP server: %s %s", command, " ".join(args))
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=command,
                args=list(args),
                env=env or {},
            )
        ),
        tool_filter=list(tool_filter) if tool_filter else None,
    )
