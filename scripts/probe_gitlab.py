"""Live probe for the GitLab MCP server.

What it does, in order:
  1. Spawns `npx mcp-remote {GITLAB_URL}/api/v4/mcp` and lists every tool the
     server exposes. First run opens a browser for OAuth 2.0 DCR; subsequent
     runs reuse the cache at ~/.mcp-auth/.
  2. Tries each tool name `integrations/gitlab/real.py` expects. Prints PASS or
     FAIL + the raw payload, so we can finalize names + normalizers against the
     Beta server.
  3. With --post, fires a throwaway note ("SentinelAI probe — please ignore")
     on GITLAB_DEMO_MR_IID. Skipped by default.

Usage:
    python scripts/probe_gitlab.py            # read-only catalogue + smokes
    python scripts/probe_gitlab.py --post     # also creates a probe note

Required env: GITLAB_URL, GITLAB_PROJECT_ID, GITLAB_DEMO_MR_IID + a commit SHA
that has an open MR (defaults to GITLAB_PROBE_COMMIT env var).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Allow running as a script from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

from shared.config import settings  # noqa: E402
from shared.logging import get_logger  # noqa: E402

log = get_logger(__name__)


def _params() -> StdioServerParameters:
    return StdioServerParameters(
        command="npx",
        args=["-y", "mcp-remote", f"{settings.gitlab_url}/api/v4/mcp"],
        env={},
    )


def _summarize(value: Any, limit: int = 800) -> str:
    text = json.dumps(value, indent=2, default=str) if not isinstance(value, str) else value
    return text if len(text) <= limit else text[:limit] + f"\n… (+{len(text) - limit} bytes)"


async def _probe(post: bool, commit: str) -> int:
    if not settings.gitlab_url or not settings.gitlab_project_id:
        log.error("GITLAB_URL and GITLAB_PROJECT_ID must be set in .env")
        return 1
    print(f"== GitLab MCP probe — {settings.gitlab_url}/api/v4/mcp ==")
    print(f"   project_id={settings.gitlab_project_id}  commit={commit}")
    print(f"   mr_iid={settings.gitlab_demo_mr_iid}  post={post}\n")

    async with stdio_client(_params()) as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        print("[1/5] listing tools …")
        catalogue = await session.list_tools()
        names = [t.name for t in catalogue.tools]
        head = ", ".join(names[:20]) + (" …" if len(names) > 20 else "")
        print(f"   {len(names)} tool(s): {head}\n")
        for tool in catalogue.tools:
            desc = (tool.description or "").splitlines()[0][:80]
            print(f"   - {tool.name:<48} {desc}")
        print()

        async def _try(label: str, tool: str, arguments: dict) -> Any:
            print(f"[{label}] {tool}({json.dumps(arguments)})")
            if tool not in names:
                print(f"   SKIP — server does not expose {tool!r}\n")
                return None
            try:
                result = await session.call_tool(tool, arguments)
            except Exception as exc:  # noqa: BLE001
                print(f"   FAIL — {exc}\n")
                return None
            print(f"   OK — payload:\n{_summarize(_unwrap(result))}\n")
            return result

        pid = settings.gitlab_project_id
        iid = settings.gitlab_demo_mr_iid
        # Server-info call (no project scope) — confirms MCP itself works.
        await _try("server", "get_mcp_server_version", {})
        await _try("2/6", "get_merge_request", {"project_id": pid, "merge_request_iid": iid})
        await _try(
            "3/6", "get_merge_request_diffs", {"project_id": pid, "merge_request_iid": iid}
        )
        pipes = await _try(
            "4/6", "get_merge_request_pipelines", {"project_id": pid, "merge_request_iid": iid}
        )
        # Drill into the first failed pipeline to confirm jobs + log calls work.
        pipe_id = _first_pipeline_id(_unwrap(pipes)) if pipes is not None else None
        if pipe_id is not None:
            jobs = await _try(
                "5/6", "get_pipeline_jobs", {"project_id": pid, "pipeline_id": pipe_id}
            )
            job_id = _first_failed_job_id(_unwrap(jobs)) if jobs is not None else None
            if job_id is not None:
                await _try("6/6 read", "get_job_log", {"project_id": pid, "job_id": job_id})
            else:
                print("[6/6 read] skipped — no failed job on the head pipeline\n")
        else:
            print("[5/6] skipped — no pipeline on the MR yet\n")
        if post and iid:
            await _try(
                "post",
                "create_workitem_note",
                {
                    "project_id": pid,
                    "merge_request_iid": iid,
                    "body": "SentinelAI probe — please ignore.",
                },
            )
        else:
            print("[post] skipped (use --post to fire a probe note)\n")

    print("== probe done ==")
    return 0


def _first_pipeline_id(raw: Any) -> int | None:
    items = raw if isinstance(raw, list) else (raw or {}).get("items") or []
    head = next((p for p in items if isinstance(p, dict)), None)
    return head.get("id") if head else None


def _first_failed_job_id(raw: Any) -> int | None:
    items = raw if isinstance(raw, list) else (raw or {}).get("items") or []
    head = next(
        (j for j in items if isinstance(j, dict) and j.get("status") == "failed"),
        None,
    )
    return head.get("id") if head else None


def _unwrap(result: Any) -> Any:
    if result is None:
        return None
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
        return joined


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--post", action="store_true", help="also post a throwaway probe note")
    parser.add_argument(
        "--commit",
        default=os.environ.get("GITLAB_PROBE_COMMIT", ""),
        help="commit SHA on the demo MR (defaults to $GITLAB_PROBE_COMMIT)",
    )
    args = parser.parse_args()
    if not args.commit:
        log.error("pass --commit <sha> (or set GITLAB_PROBE_COMMIT)")
        return 2
    return asyncio.run(_probe(post=args.post, commit=args.commit))


if __name__ == "__main__":
    raise SystemExit(main())
