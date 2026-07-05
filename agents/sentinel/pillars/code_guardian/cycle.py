"""One Code Guardian cycle, ending in a Signal for the dashboard.

Sequence:
  review (diff -> Findings) -> diagnose_ci (logs -> RCA) -> render markdown ->
  post comment back on the MR -> emit Signal.

The dashboard only ever speaks Signal; the pillar-specific MRReview rides inside
Signal.detail.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from integrations.gitlab.factory import get as get_gitlab
from shared.logging import get_logger
from shared.models import Finding, MRReview, Severity, Signal

from .ci import diagnose_ci
from .note import render_mr_note
from .review import run_review

log = get_logger(__name__)

Status = Literal["ok", "warning", "critical"]


def _status_for(findings: list[Finding]) -> Status:
    """A critical finding blocks the merge; high warns; anything else is ok."""
    severities = {f.severity for f in findings}
    if Severity.CRITICAL in severities:
        return "critical"
    if Severity.HIGH in severities:
        return "warning"
    return "ok"


def _headline(review: MRReview) -> str:
    n = len(review.findings)
    if n == 0:
        return f"MR !{review.mr_id}: clean review"
    by_sev: dict[Severity, int] = {}
    for f in review.findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
    parts = [
        f"{by_sev[s]} {s.value}"
        for s in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO)
        if by_sev.get(s)
    ]
    return f"MR !{review.mr_id}: {n} finding(s) — " + ", ".join(parts)


def run_code_guardian_cycle(commit: str) -> Signal:
    """Run one Code Guardian pass against `commit` and return the Signal."""
    from storage.signal_store import save_signal  # lazy: free in sim mode

    review = run_review(commit)
    review.ci_root_cause = diagnose_ci(review.mr_id)

    body = render_mr_note(review)

    try:
        dest = get_gitlab().post_mr_note(review.mr_id, body)
    except Exception:
        log.exception("post_mr_note failed; emitting Signal without delivery")
        dest = "post-failed"

    log.info(
        "code guardian cycle complete: MR !%s -> %d finding(s) (posted -> %s)",
        review.mr_id,
        len(review.findings),
        dest,
    )

    signal = Signal(
        pillar="code",
        status=_status_for(review.findings),
        headline=_headline(review),
        detail={
            "review": review.model_dump(mode="json"),
            "posted_to": dest,
        },
        ts=datetime.now(UTC),
    )
    save_signal(signal)
    return signal
