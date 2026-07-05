"""Real GitLab adapter — reads and writes via the GitLab REST API.

GitLab Duo's MCP server (mounted by `npx mcp-remote {GITLAB_URL}/api/v4/mcp`)
*does* connect and expose 20 tools as of GitLab 19.1, but its `mcp`-scoped
OAuth token still returns 404 on project-scoped reads of private projects (the
Beta hasn't wired the user's project ACL into the MCP request context yet —
documented as `Status: Beta` in GitLab's MCP server docs). So this adapter does
its work through REST with a Personal Access Token (settings.gitlab_token, `api`
scope), which has full access.

The ADK sub-agent still mounts `mcp-remote` in `agents/sentinel/pillars/
code_guardian/agent.py` so the conversational path can call tools that don't
need project ACL (`get_mcp_server_version`, `search`, `search_labels`). The day
GitLab fixes the OAuth scope, this adapter can swap reads back to MCP without
touching any other layer.

Auth: settings.gitlab_token (a Personal Access Token with `api` scope).
"""

from __future__ import annotations

from typing import Any

import httpx

from shared.config import settings
from shared.logging import get_logger

from .interface import GitLabIntegration

log = get_logger(__name__)


class GitLabReal(GitLabIntegration):
    def __init__(self) -> None:
        if not settings.gitlab_url:
            raise RuntimeError(
                "GITLAB_URL is unset — set it (e.g. https://gitlab.com) to use "
                "SENTINEL_GL_MODE=real."
            )
        if not settings.gitlab_project_id:
            raise RuntimeError(
                "GITLAB_PROJECT_ID is unset — set the numeric project id "
                "(visible on the project page) to use SENTINEL_GL_MODE=real."
            )
        if not settings.gitlab_token:
            raise RuntimeError(
                "GITLAB_TOKEN is unset — set a Personal Access Token (api scope) "
                "to use SENTINEL_GL_MODE=real."
            )

    # ----- REST transport -----

    def _rest_headers(self) -> dict[str, str]:
        return {"PRIVATE-TOKEN": settings.gitlab_token}

    def _rest(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{settings.gitlab_url}/api/v4{path}"
        with httpx.Client(timeout=30.0) as client:
            resp = client.request(method, url, headers=self._rest_headers(), **kwargs)
        resp.raise_for_status()
        return resp.json()

    # ----- contract -----

    def healthcheck(self) -> bool:
        try:
            self._rest("GET", f"/projects/{settings.gitlab_project_id}")
            return True
        except Exception:
            log.exception("GitLab healthcheck failed")
            return False

    def get_mr_diff(self, commit: str) -> dict:
        mr_iid = self._resolve_mr_for_commit(commit)
        if mr_iid is None:
            return {
                "error": f"no merge request found for commit {commit}",
                "known_commit": commit,
            }
        mr = self._rest(
            "GET", f"/projects/{settings.gitlab_project_id}/merge_requests/{mr_iid}"
        )
        # `/changes` is the legacy endpoint that returns a flat changes[] list.
        # GitLab also exposes `/diffs` (paged); changes[] is enough for our use.
        diffs = self._rest(
            "GET",
            f"/projects/{settings.gitlab_project_id}/merge_requests/{mr_iid}/changes",
        )
        return self._to_mr_diff(commit, mr, diffs)

    def get_pipeline_logs(self, mr_id: int) -> dict:
        pipelines = self._rest(
            "GET",
            f"/projects/{settings.gitlab_project_id}/merge_requests/{mr_id}/pipelines",
        )
        head = self._first_pipeline(pipelines)
        if head is None:
            return {"error": f"no pipeline found for MR {mr_id}", "known_mr_id": mr_id}
        pipeline_id = head.get("id")
        status = head.get("status", "unknown")
        if status != "failed":
            return {
                "mr_id": mr_id,
                "pipeline_id": pipeline_id,
                "status": status,
                "failed_job": None,
                "logs": "",
            }
        jobs = self._rest(
            "GET",
            f"/projects/{settings.gitlab_project_id}/pipelines/{pipeline_id}/jobs",
        )
        failed_job = self._first_failed_job(jobs)
        if failed_job is None:
            return {
                "mr_id": mr_id,
                "pipeline_id": pipeline_id,
                "status": status,
                "failed_job": None,
                "logs": "",
            }
        # /jobs/:id/trace returns plain text, not JSON — call httpx directly.
        url = (
            f"{settings.gitlab_url}/api/v4/projects/{settings.gitlab_project_id}"
            f"/jobs/{failed_job.get('id')}/trace"
        )
        with httpx.Client(timeout=30.0) as client:
            r = client.get(url, headers=self._rest_headers())
        r.raise_for_status()
        return {
            "mr_id": mr_id,
            "pipeline_id": pipeline_id,
            "status": status,
            "failed_job": failed_job.get("name", ""),
            "logs": r.text,
        }

    def post_mr_note(self, mr_id: int, body: str) -> str:
        path = (
            f"/projects/{settings.gitlab_project_id}"
            f"/merge_requests/{mr_id}/notes"
        )
        result = self._rest("POST", path, json={"body": body})
        if isinstance(result, dict):
            note_id = result.get("id", "unknown")
            return (
                result.get("web_url")
                or f"{settings.gitlab_url}/-/notes/{note_id}"
            )
        return "note:posted"

    # ----- helpers -----

    def _resolve_mr_for_commit(self, commit: str) -> int | None:
        path = (
            f"/projects/{settings.gitlab_project_id}"
            f"/repository/commits/{commit}/merge_requests"
        )
        try:
            mrs = self._rest("GET", path)
        except httpx.HTTPStatusError as exc:
            log.warning("commit -> MR lookup failed: %s", exc)
            return None
        if not isinstance(mrs, list) or not mrs:
            return None
        first = mrs[0]
        iid = first.get("iid") if isinstance(first, dict) else None
        return int(iid) if iid is not None else None

    def _to_mr_diff(self, commit: str, mr: dict, diffs: Any) -> dict:
        changes = self._extract_changes(diffs)
        files_changed: list[str] = []
        diff_chunks: list[str] = []
        for ch in changes:
            new_path = ch.get("new_path") or ch.get("old_path") or ""
            if new_path:
                files_changed.append(new_path)
            patch = ch.get("diff") or ch.get("patch") or ""
            if patch:
                old_path = ch.get("old_path") or new_path
                diff_chunks.append(f"--- a/{old_path}\n+++ b/{new_path}\n{patch}")
        author = mr.get("author") or {}
        return {
            "commit": commit,
            "mr_id": int(mr.get("iid") or 0),
            "mr_title": mr.get("title", ""),
            "author": author.get("username") if isinstance(author, dict) else str(author),
            "merged_at": mr.get("merged_at") or mr.get("updated_at") or "",
            "service": settings.gitlab_url.rsplit("/", 1)[-1] or "service",
            "files_changed": files_changed,
            "diff": "\n".join(diff_chunks),
        }

    @staticmethod
    def _extract_changes(raw: Any) -> list[dict]:
        if isinstance(raw, dict):
            for key in ("changes", "diffs", "items"):
                if isinstance(raw.get(key), list):
                    return [c for c in raw[key] if isinstance(c, dict)]
            return [raw]
        if isinstance(raw, list):
            return [c for c in raw if isinstance(c, dict)]
        return []

    @staticmethod
    def _first_pipeline(raw: Any) -> dict | None:
        """Pick the newest pipeline (highest id) — GitLab's /merge_requests/
        :iid/pipelines endpoint orders by updated_at but interleaves stale and
        live runs, so id-desc is the more reliable "head pipeline" signal."""
        items = raw if isinstance(raw, list) else (raw or {}).get("items") or []
        dicts = [p for p in items if isinstance(p, dict)]
        return max(dicts, key=lambda p: p.get("id", 0)) if dicts else None

    @staticmethod
    def _first_failed_job(raw: Any) -> dict | None:
        items = raw if isinstance(raw, list) else (raw or {}).get("items") or []
        return next(
            (j for j in items if isinstance(j, dict) and j.get("status") == "failed"),
            None,
        )
