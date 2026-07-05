"""Code Guardian ADK sub-agent. Conversational path used by the orchestrator +
webhook gateway.

Tools follow the same mode switch as the other pillars:
  sim  -> FunctionTools wrapping the GitLab simulator + Gemini review (no creds)
  real -> the GitLab MCP server mounted over stdio (P1-7; dormant until
          SENTINEL_GL_MODE=real with GitLab creds + Duo namespace)
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from integrations.gitlab.factory import get as get_gitlab
from shared.config import settings
from shared.logging import get_logger

from .ci import diagnose_ci as _diagnose_ci
from .prompt import GUARDIAN_INSTRUCTION
from .review import run_review

log = get_logger(__name__)


def review_mr(commit: str) -> dict:
    """Run a security + performance + logic review on the MR that introduced
    `commit`. Returns an MRReview with severity-rated findings.

    Args:
        commit: a commit SHA (full or short) on the target MR.
    """
    return run_review(commit).model_dump(mode="json")


def diagnose_ci(mr_id: int) -> dict:
    """Pull the failing CI logs for `mr_id` and return a plain-English root cause.

    Args:
        mr_id: the merge-request id (e.g. 42 for !42).
    """
    return {"mr_id": mr_id, "ci_root_cause": _diagnose_ci(mr_id)}


def post_review(mr_id: int, body: str) -> dict:
    """Post a markdown review comment back on the MR.

    Args:
        mr_id: the merge-request id to post the comment on.
        body: the markdown body of the comment.
    """
    dest = get_gitlab().post_mr_note(mr_id, body)
    return {"mr_id": mr_id, "posted_to": dest}


def _build_tools() -> list:
    if settings.gl_mode == "real":
        from shared.mcp import stdio_mcp

        # GitLab's MCP server (Beta) is hosted at /api/v4/mcp; we reach it via
        # the `mcp-remote` stdio proxy. Auth is OAuth 2.0 DCR — the first call
        # opens a browser; subsequent calls reuse the cache at ~/.mcp-auth/.
        log.info(
            "code_guardian: mounting real GitLab MCP via mcp-remote (%s/api/v4/mcp)",
            settings.gitlab_url,
        )
        return [
            stdio_mcp(
                command="npx",
                args=["-y", "mcp-remote", f"{settings.gitlab_url}/api/v4/mcp"],
                env={},
            )
        ]
    return [
        FunctionTool(func=review_mr),
        FunctionTool(func=diagnose_ci),
        FunctionTool(func=post_review),
    ]


def build_code_guardian() -> Agent:
    return Agent(
        model=settings.gemini_model,
        name="code_guardian",
        instruction=GUARDIAN_INSTRUCTION,
        tools=_build_tools(),
    )
