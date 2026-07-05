"""GitLab simulator (mode = sim). Promotes the spike `mr_diff.json` and returns
the same shape a GitLab MCP `get_mr_diff` call would, so correlation logic is
identical against the real MCP later.

Also serves canned failing CI logs (P1-3) and writes posted MR notes to disk
(P1-4: sim post -> out/mr_note.md, one file per MR).
"""

from __future__ import annotations

import json
from pathlib import Path

from .interface import GitLabIntegration

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_MR_DIFF = _FIXTURES / "mr_diff.json"
_PIPELINE = _FIXTURES / "pipeline_logs.json"

_OUT_DIR = Path(__file__).resolve().parents[2] / "out"


class GitLabSimulator(GitLabIntegration):
    def healthcheck(self) -> bool:
        return True

    def get_mr_diff(self, commit: str) -> dict:
        data = json.loads(_MR_DIFF.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for pr in data:
                if commit and commit in (pr["commit"], pr["commit"][:7]):
                    return pr
            return {
                "error": f"no merge request found for commit {commit}",
                "known_commit": data[0]["commit"] if data else None,
            }

        if commit and commit not in (data["commit"], data["commit"][:7]):
            return {
                "error": f"no merge request found for commit {commit}",
                "known_commit": data["commit"],
            }
        return data

    def get_pipeline_logs(self, mr_id: int) -> dict:
        data = json.loads(_PIPELINE.read_text(encoding="utf-8"))
        if mr_id and mr_id != data["mr_id"]:
            return {
                "error": f"no pipeline found for MR {mr_id}",
                "known_mr_id": data["mr_id"],
            }
        return data

    def post_mr_note(self, mr_id: int, body: str) -> str:
        _OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = _OUT_DIR / f"mr_note_{mr_id}.md"
        path.write_text(body, encoding="utf-8")
        return str(path)
