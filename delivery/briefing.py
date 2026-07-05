"""Briefing delivery. One render, two destinations by SENTINEL_DELIVERY_MODE:

- sim  : write the markdown briefing to out/briefing.md (offline demo artifact).
- real : post it to Slack. Preferred path is the Dynatrace MCP send_slack_message
         tool (the partner-MCP story); falls back to a plain incoming-webhook URL
         when no Slack Connection is configured or the MCP send fails.

The render lives here (not in the run script) so the poller service reuses the
exact same artifact the CLI produces.
"""

from __future__ import annotations

from pathlib import Path

from shared.config import settings
from shared.logging import get_logger
from shared.models import Incident
from storage.incident_kb import SimilarMatch

log = get_logger(__name__)

_OUT = Path(__file__).resolve().parent.parent / "out" / "briefing.md"


def render_briefing(incident: Incident, similar: SimilarMatch | None = None) -> str:
    """Render an Incident (+ optional KB match) as the morning-briefing markdown."""
    if similar is None:
        seen = "_no similar past incident on record_"
    else:
        pct = round(similar.score * 100)
        seen = (
            f"**{pct}% match** to a prior incident: "
            f"_{similar.incident.title}_ — {similar.incident.next_action}"
        )
    return (
        f"# Morning Briefing — Draft Incident\n\n"
        f"**{incident.title}**  \n"
        f"Severity: `{incident.severity.value}` · Service: `{incident.service}`\n\n"
        f"## Summary\n{incident.summary}\n\n"
        f"## Suspected cause\n{incident.suspected_cause}\n\n"
        f"## Suspect commit\n{incident.suspect_commit or '_none identified_'}\n\n"
        f"## Seen before?\n{seen}\n\n"
        f"## Next action\n{incident.next_action}\n"
    )


def _post_to_slack(markdown: str) -> str:
    """Prefer the Dynatrace MCP send_slack_message tool; fall back to a webhook."""
    from integrations.dynatrace.factory import get as get_dynatrace  # lazy, mode-aware

    if get_dynatrace().send_slack_message(markdown, settings.slack_channel or None):
        return "slack-mcp"
    return _post_to_webhook(markdown)


def _post_to_webhook(markdown: str) -> str:
    import httpx

    if not settings.slack_webhook_url:
        raise RuntimeError(
            "SENTINEL_DELIVERY_MODE=real but no delivery path is configured: set up a "
            "Dynatrace Slack Connection (SLACK_CONNECTION_ID) or SLACK_WEBHOOK_URL"
        )
    resp = httpx.post(settings.slack_webhook_url, json={"text": markdown}, timeout=10)
    resp.raise_for_status()
    log.info("delivered briefing to Slack via webhook")
    return "slack-webhook"


def _write_file(markdown: str) -> str:
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(markdown, encoding="utf-8")
    log.info("wrote briefing to %s", _OUT)
    return str(_OUT)


def deliver_briefing(incident: Incident, similar: SimilarMatch | None = None) -> str:
    """Render and deliver the briefing. Returns the destination (file path or
    "slack"). Mode-driven: sim writes the file, real posts to Slack."""
    markdown = render_briefing(incident, similar)
    if settings.delivery_mode == "real":
        return _post_to_slack(markdown)
    return _write_file(markdown)
