"""One full Production Sentinel cycle, ending in a Signal for the dashboard.

This is the single sequence the poller (and the CLI) run:
  RCA -> cross-pillar correlation -> KB lookup/save -> deliver -> emit Signal.

The dashboard only ever speaks Signal (the common envelope), so the pillar-
specific Incident rides inside Signal.detail.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from delivery.briefing import deliver_briefing, render_briefing
from shared.logging import get_logger
from shared.models import Incident, Severity, Signal

from .correlation import correlate_incident
from .rca import run_rca

log = get_logger(__name__)

Status = Literal["ok", "warning", "critical"]


def _status_for(severity: Severity) -> Status:
    """Map an incident's severity onto the dashboard's status light. An emitted
    incident always means something is wrong, so it never reads "ok" — "ok" is
    reserved for the future no-open-problems path."""
    if severity == Severity.CRITICAL:
        return "critical"
    return "warning"


def run_production_cycle() -> Signal:
    """Run one production-sentinel pass and return the emitted Signal."""
    from integrations.dynatrace.factory import get as get_dynatrace  # lazy, mode-aware
    from storage.incident_kb import get_kb  # lazy: keeps sim import light
    from storage.signal_store import save_signal  # lazy: free in sim mode

    incident: Incident = run_rca()
    incident = correlate_incident(incident)

    kb = get_kb()
    # Look up a prior match BEFORE saving so the new incident can't match itself.
    similar = kb.similar(incident)
    kb.save(incident)

    # Delivery is best-effort: the Signal is the dashboard contract, so a flaky
    # Slack/webhook must not erase the incident. Log and emit anyway.
    try:
        dest = deliver_briefing(incident, similar)
    except Exception:
        log.exception("delivery failed; emitting Signal without delivery")
        dest = "delivery-failed"

    # Share the draft incident as a Dynatrace notebook. Real mode posts it; sim
    # no-ops (returns None). Best-effort — a notebook hiccup must not sink the Signal.
    try:
        notebook = get_dynatrace().create_notebook(
            incident.title, render_briefing(incident, similar)
        )
    except Exception:
        log.exception("notebook delivery failed; continuing")
        notebook = None
    log.info("production cycle complete: %s (delivered -> %s)", incident.title, dest)

    signal = Signal(
        pillar="production",
        status=_status_for(incident.severity),
        headline=incident.title,
        detail={
            "incident": incident.model_dump(mode="json"),
            "similar": similar.model_dump(mode="json") if similar else None,
            "delivered_to": dest,
            "notebook": notebook,
        },
        ts=datetime.now(UTC),
    )
    save_signal(signal)
    return signal
