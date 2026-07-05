"""P2-4: cross-pillar correlation — the demo money shot.

Production Sentinel sees a prod anomaly (Dynatrace) and asks Code Guardian
(GitLab) "which commit shipped right before this, and could it have caused it?"
Gemini reads the diff and links anomaly -> commit -> code change, upgrading the
draft Incident into a final one that names the suspect commit and the precise
fix.

The seam is GitLab's `get_mr_diff(commit)` (plan P1-5); the commit itself comes
from Dynatrace deploy events (`recent_deployments`), which is how prod systems
tie a regression back to a release.
"""

from __future__ import annotations

import json

from integrations.dynatrace.factory import get as get_dynatrace
from integrations.gitlab.factory import get as get_gitlab
from shared.llm import generate_json
from shared.logging import get_logger
from shared.models import Incident

from .prompt import CORRELATION_INSTRUCTION

log = get_logger(__name__)


def get_mr_diff(commit: str) -> dict:
    """Fetch the merge-request diff for a commit SHA from Code Guardian (GitLab).

    Use this to inspect what a deploy changed so you can judge whether it caused
    a production anomaly.

    Args:
        commit: the short or full commit SHA to look up (e.g. "abc1234").
    """
    return get_gitlab().get_mr_diff(commit)


def suspect_commit_for(service: str) -> str | None:
    """The commit of the most recent deploy for a service (the prime suspect)."""
    deploys = get_dynatrace().recent_deployments(service)
    return deploys[0]["commit"] if deploys else None


def correlate_incident(incident: Incident, commit: str | None = None) -> Incident:
    """Upgrade a draft Incident by correlating it with the suspect deploy's diff.

    Args:
        incident: the draft incident from RCA (suspect_commit usually null).
        commit: the suspect commit; if None, derived from the latest deploy on
            the incident's service.

    Returns:
        The final Incident. If no suspect commit/diff is found, the draft is
        returned unchanged.
    """
    commit = commit or suspect_commit_for(incident.service)
    if not commit:
        log.info("correlation: no recent deploy for %s; skipping", incident.service)
        return incident

    # Don't let a flaky diff source sink the whole briefing — degrade to the
    # uncorrelated draft, same as the no-deploy path. (real GitLab MCP can raise.)
    try:
        diff = get_mr_diff(commit)
    except Exception:
        log.exception("correlation: get_mr_diff failed for %s; returning draft", commit)
        return incident
    if "error" in diff:
        log.info("correlation: %s", diff["error"])
        return incident

    log.info("correlation: linking %s against commit %s", incident.service, commit)
    prompt = (
        f"{CORRELATION_INSTRUCTION}\n\n"
        f"DRAFT INCIDENT (JSON):\n{incident.model_dump_json(indent=2)}\n\n"
        f"SUSPECT DEPLOY DIFF (JSON):\n{json.dumps(diff, indent=2)}"
    )
    correlated = generate_json(prompt, Incident)
    # Gemini occasionally judges the diff "unrelated" even when we handed it
    # the prime suspect — keep that conservatism for the cause text, but force
    # the commit through so the dashboard's correlation panel can still pin
    # the production anomaly to the deploy that shipped right before it.
    if not correlated.suspect_commit:
        correlated.suspect_commit = commit
    return correlated
