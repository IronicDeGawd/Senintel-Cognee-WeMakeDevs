"""Render an MRReview into a markdown comment fit for posting back on the MR.

Severity-grouped, worst-first, with the suggestion inline so the reviewer can
act on one line. CI root cause goes in its own section when present.
"""

from __future__ import annotations

from shared.models import Finding, MRReview, Severity

_SEVERITY_ORDER = (
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
    Severity.INFO,
)

_SEVERITY_BADGE = {
    Severity.CRITICAL: "🔴 CRITICAL",
    Severity.HIGH: "🟠 HIGH",
    Severity.MEDIUM: "🟡 MEDIUM",
    Severity.LOW: "🔵 LOW",
    Severity.INFO: "⚪ INFO",
}


def _finding_block(f: Finding) -> str:
    loc = f"`{f.file}:{f.line}`" if f.line else f"`{f.file}`"
    head = f"- **{_SEVERITY_BADGE[f.severity]}** · _{f.category}_ · {loc}"
    lines = [head, f"  {f.message}"]
    if f.suggestion:
        lines.append(f"  _Fix:_ {f.suggestion}")
    return "\n".join(lines)


def render_mr_note(review: MRReview) -> str:
    """Render an MRReview as markdown for posting on the MR."""
    n = len(review.findings)
    worst = _worst_severity(review.findings)
    headline = (
        f"# SentinelAI Code Guardian — MR !{review.mr_id}\n"
        f"**Commit:** `{review.commit}` · **Findings:** {n}"
        + (f" · **Worst:** {_SEVERITY_BADGE[worst]}" if worst else "")
    )

    if n == 0:
        sections = [headline, "\nNo issues found in this diff. ✅"]
    else:
        sections = [headline]
        by_sev: dict[Severity, list[Finding]] = {s: [] for s in _SEVERITY_ORDER}
        for f in review.findings:
            by_sev[f.severity].append(f)
        for sev in _SEVERITY_ORDER:
            if not by_sev[sev]:
                continue
            sections.append(f"\n## {_SEVERITY_BADGE[sev]}")
            sections.extend(_finding_block(f) for f in by_sev[sev])

    if review.ci_root_cause:
        sections.append("\n## CI failure\n")
        sections.append(review.ci_root_cause)

    return "\n".join(sections) + "\n"


def _worst_severity(findings: list[Finding]) -> Severity | None:
    if not findings:
        return None
    for sev in _SEVERITY_ORDER:
        if any(f.severity == sev for f in findings):
            return sev
    return None
