"""Programmatic (non-ADK) stdio MCP client.

The ADK agent mounts MCP servers as toolsets (`shared/mcp.py`). The poller and
briefing run *outside* an agent loop, so they need to call MCP tools directly.
This spawns the stdio MCP server, runs one tool, and returns the parsed result.

Think of it as a one-shot phone call: dial the server, ask one question, hang up.
Per-call spawn is fine for a 5-min poller; a persistent session is a later
optimization. Windows stdio startup was flaky in the spike, so we retry.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.shared.context import RequestContext
from tenacity import retry, stop_after_attempt, wait_fixed

from shared.logging import get_logger

log = get_logger(__name__)


_TRUTHY_BY_TYPE: dict[str, Any] = {
    "boolean": True,
    "string": "yes",
    "integer": 1,
    "number": 1,
    "array": [],
    "object": {},
}


def _fill_required(schema: dict | None) -> dict:
    """Return a payload that satisfies every `required` field on an MCP elicit
    schema with a truthy value of the right primitive type. Dynatrace's
    send_event needs `approval: boolean=true`; other servers may add fields,
    so we generalize by reading the schema."""
    if not isinstance(schema, dict):
        return {}
    required = schema.get("required") or []
    properties = schema.get("properties") or {}
    content: dict[str, Any] = {}
    for field in required:
        spec = properties.get(field) or {}
        kind = spec.get("type") or "boolean"
        content[field] = _TRUTHY_BY_TYPE.get(kind, True)
    return content


async def _auto_approve_elicit(
    _context: RequestContext[ClientSession, Any],
    params: types.ElicitRequestParams,
) -> types.ElicitResult:
    """Auto-approve every elicitation request from the MCP server.

    Some servers (Dynatrace MCP, notably its `send_event` tool) gate
    side-effecting calls behind a `human-in-the-loop` elicit prompt. Default
    SDK behavior is to return an error, which the server reads as "decline"
    and cancels the operation. SentinelAI runs headless on Cloud Run — the
    operator has already approved by clicking "Run Scenario" on the dashboard
    — so we accept every elicit automatically.

    The Dynatrace server validates the response against the schema attached
    to its elicit request (e.g. `approval: boolean` must be present). We fill
    every required field from the schema with a truthy value of the right
    primitive type. Restrict to specific tools later if any server adds
    destructive operations behind elicit prompts."""
    msg = params.message[:160] if params.message else "<no message>"
    schema = getattr(params, "requestedSchema", None) or getattr(
        params, "requested_schema", None
    )
    content = _fill_required(schema if isinstance(schema, dict) else None)
    log.info("MCP elicit auto-accepted: %s (content=%s)", msg, content)
    return types.ElicitResult(action="accept", content=content)


def _parse_result(result: Any) -> Any:
    """Turn a CallToolResult into plain Python. Prefer structured content; else
    join text blocks and try JSON; else return the raw text under {"text": ...}."""
    structured = getattr(result, "structuredContent", None)
    if structured:
        return structured
    texts = [
        block.text
        for block in (getattr(result, "content", None) or [])
        if getattr(block, "text", None) is not None
    ]
    joined = "\n".join(texts).strip()
    if not joined:
        return {}
    try:
        return json.loads(joined)
    except json.JSONDecodeError:
        return {"text": joined}


async def _call(params: StdioServerParameters, tool: str, arguments: dict) -> Any:
    async with stdio_client(params) as (read, write), ClientSession(
        read,
        write,
        elicitation_callback=_auto_approve_elicit,
    ) as session:
        await session.initialize()
        result = await session.call_tool(tool, arguments)
        if getattr(result, "isError", False):
            raise RuntimeError(f"MCP tool {tool!r} returned an error: {_parse_result(result)}")
        return _parse_result(result)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
def call_tool(
    command: str,
    args: Sequence[str],
    env: dict[str, str] | None,
    tool: str,
    arguments: dict | None = None,
) -> Any:
    """Spawn a stdio MCP server, call one tool, return the parsed result.

    Args:
        command: launcher, e.g. "npx".
        args: command args, e.g. ["-y", "@dynatrace-oss/dynatrace-mcp-server@latest"].
        env: env vars (creds) passed to the server process.
        tool: tool name to call, e.g. "list_problems".
        arguments: tool arguments dict.
    """
    # This spawns its own loop via asyncio.run, so it must NOT run inside an
    # already-running loop (would raise "event loop is already running"). The
    # sync poller endpoint is safe (FastAPI runs sync defs in a threadpool).
    # An async caller should await the async _call() helper directly instead.
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass  # no running loop — safe to asyncio.run below
    else:
        raise RuntimeError(
            "call_tool() owns its event loop and cannot run inside an async "
            "context; await shared.mcp_client._call() directly instead."
        )

    params = StdioServerParameters(command=command, args=list(args), env=env or {})
    log.info("MCP call: tool=%s via %s", tool, command)
    return asyncio.run(_call(params, tool, arguments or {}))
