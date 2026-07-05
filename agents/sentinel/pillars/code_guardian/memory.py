"""Team code-review memory for Code Guardian (WeMakeDevs / Cognee).

Two directions:
  - recall_context(diff): before a review, pull the team's relevant past
    conventions + bugs and format them as a prompt block the LLM can apply.
  - remember_review(review): after a cycle, store each finding so the next PR
    review can recall it — the "learn from history" loop.

Backend is the Cognee adapter (offline JSON sim in tests, Cognee Cloud in the
demo), selected by SENTINEL_MEMORY_MODE. This module stays a thin glue layer.
"""

from __future__ import annotations

from integrations.cognee.factory import get as get_cognee
from shared.config import settings
from shared.llm import generate
from shared.logging import get_logger
from shared.models import MemoryItem, MRReview

log = get_logger(__name__)

_DEFAULT_REPO = "sentinel"

_SUMMARY_PROMPT = (
    "In one sentence, describe what this code change does, focusing on data-access "
    "patterns, loops, database queries, and structure, so it can be matched against "
    "past code-review lessons. Output only the sentence, no preamble.\n\n"
)


def _diff_query(diff: dict) -> str:
    """What we ask memory about — the service, the touched files, the patch."""
    files = " ".join(diff.get("files_changed", []) or [])
    return f"{diff.get('service', '')} {files}\n{diff.get('diff', '')}"


def _recall_query(diff: dict) -> str:
    """The query we hand to the memory backend.

    Cognee's semantic retrieval matches on intent-language, not raw code — a unified
    diff embeds too far from a stored rule like "avoid N+1 queries" and recalls
    nothing. So in real (Cognee) mode we first ask the LLM for a one-line natural-
    language summary of the change and query with that. The sim backend uses
    deterministic token embeddings that match the raw diff fine, and its tests must
    stay offline, so sim keeps the raw query (no LLM call)."""
    raw = _diff_query(diff)
    if settings.memory_mode != "real":
        return raw
    try:
        summary = generate(_SUMMARY_PROMPT + raw).strip()
        if summary:
            return summary
    except Exception:
        log.exception("diff summary for recall failed; falling back to raw diff")
    return raw


def recall_context(diff: dict, limit: int = 5) -> str:
    """Return a 'TEAM MEMORY' prompt block for this diff, or '' if nothing recalls."""
    items = get_cognee().recall(_recall_query(diff), limit=limit)
    if not items:
        return ""
    lines = ["TEAM MEMORY — conventions and past bugs this team has learned:"]
    for it in items:
        loc = f" ({it.file})" if it.file else ""
        lines.append(f"- [{it.severity.value}] {it.rule}{loc}: {it.comment}")
    lines.append(
        "Apply these to the diff below. If a past bug pattern recurs, flag it explicitly "
        "and say it has been seen before."
    )
    return "\n".join(lines)


def remember_review(review: MRReview, repo: str = _DEFAULT_REPO) -> None:
    """Store each finding of a completed review as team memory."""
    mem = get_cognee()
    for f in review.findings:
        item = MemoryItem(
            repo=repo,
            file=f.file,
            rule=f.category,
            comment=f.message,
            severity=f.severity,
            source="review",
            commit=review.commit,
        )
        mem.remember(item)
    log.info("remembered %d finding(s) from MR !%s", len(review.findings), review.mr_id)
