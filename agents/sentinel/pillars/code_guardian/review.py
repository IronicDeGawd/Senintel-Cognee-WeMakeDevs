"""Diff review: ask Gemini for severity-rated Findings on one MR's diff.

The structured path used by the webhook cycle. Pulls the diff from the GitLab
adapter (sim or real, by mode), formats a metadata header + raw diff prompt, and
asks Gemini — via the shared structured helper — for a validated MRReview. The
caller fills ci_root_cause separately (see ci.py); CI diagnosis is its own LLM
call to keep prompts tight and parseable.
"""

from __future__ import annotations

import json

from integrations.gitlab.factory import get as get_gitlab
from shared.llm import generate_json
from shared.logging import get_logger
from shared.models import MRReview

from .prompt import REVIEW_INSTRUCTION

log = get_logger(__name__)


def _diff_payload(diff: dict) -> str:
    """Header + raw diff. Stripping the diff back out as text (not JSON) keeps
    Gemini's attention on the patch, not the wrapper schema."""
    header = {
        "mr_id": diff["mr_id"],
        "commit": diff["commit"],
        "mr_title": diff.get("mr_title"),
        "author": diff.get("author"),
        "service": diff.get("service"),
        "files_changed": diff.get("files_changed", []),
    }
    return f"MR METADATA:\n{json.dumps(header, indent=2)}\n\nDIFF:\n{diff['diff']}"


def run_review(commit: str) -> MRReview:
    """Review the MR that shipped `commit` and return an MRReview (no CI RCA).

    Args:
        commit: a commit SHA (full or short) on the target MR.

    Raises:
        ValueError: if the GitLab adapter cannot resolve the commit to an MR.
    """
    log.info("running code review for commit %s", commit)
    diff = get_gitlab().get_mr_diff(commit)
    if "error" in diff:
        raise ValueError(diff["error"])

    prompt = f"{REVIEW_INSTRUCTION}\n\n{_diff_payload(diff)}"
    review = generate_json(prompt, MRReview)
    # Force the known identifiers; Gemini may echo or alter them.
    review.mr_id = diff["mr_id"]
    review.commit = diff["commit"]
    review.ci_root_cause = None
    return review
