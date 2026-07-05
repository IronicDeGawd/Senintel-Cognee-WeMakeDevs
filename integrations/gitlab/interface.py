"""GitLab adapter contract.

P1 (Code Guardian, Dev B) owns the full GitLab adapter. Three operations:
  - get_mr_diff(commit): the cross-pillar seam Production Sentinel calls during
    correlation (frozen by the spike fixture; identical shape sim<->real).
  - get_pipeline_logs(mr_id): the failing CI log text used for plain-English RCA.
  - post_mr_note(mr_id, body): post the rendered review comment back on the MR
    (sim writes to out/mr_note.md, real posts via GitLab MCP).
"""

from __future__ import annotations

from abc import abstractmethod

from integrations.base import Integration


class GitLabIntegration(Integration):
    name = "gitlab"

    @abstractmethod
    def get_mr_diff(self, commit: str) -> dict:
        """Return the merge-request diff + metadata for a commit SHA.

        Shape: {commit, mr_id, mr_title, author, merged_at, service,
        files_changed, diff}. On an unknown commit: {error, known_commit}.
        """
        ...

    @abstractmethod
    def get_pipeline_logs(self, mr_id: int) -> dict:
        """Return the failing CI pipeline logs for an MR.

        Shape: {mr_id, pipeline_id, status, failed_job, logs}. On an unknown MR:
        {error, known_mr_id}.
        """
        ...

    @abstractmethod
    def post_mr_note(self, mr_id: int, body: str) -> str:
        """Post a markdown comment on an MR. Returns a destination identifier
        (sim: written file path; real: comment URL/id)."""
        ...
