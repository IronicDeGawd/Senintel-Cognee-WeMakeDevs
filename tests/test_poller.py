"""P2-6: production cycle -> Signal, and the poller HTTP surface. Offline —
the LLM-heavy steps and delivery are stubbed."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import agents.sentinel.pillars.production_sentinel.cycle as cycle_mod
import storage.incident_kb as kb_mod
from services.poller.main import app
from shared.models import Incident, Severity, Signal


def _incident(severity: Severity = Severity.HIGH) -> Incident:
    return Incident(
        title="Checkout latency spike",
        severity=severity,
        service="checkout-service",
        summary="Checkout p95 ~13x baseline.",
        suspected_cause="N+1 query in checkout/views.py.",
        suspect_commit="abc1234",
        next_action="Roll back commit abc1234.",
    )


class _FakeKB:
    def similar(self, incident, min_score=0.55):
        return None

    def save(self, incident):
        return "fake-id"


@pytest.mark.parametrize(
    ("severity", "expected"),
    [
        (Severity.CRITICAL, "critical"),
        (Severity.HIGH, "warning"),
        (Severity.MEDIUM, "warning"),
        # An emitted incident is never "ok", even at low severity.
        (Severity.LOW, "warning"),
        (Severity.INFO, "warning"),
    ],
)
def test_status_for_maps_severity(severity, expected):
    assert cycle_mod._status_for(severity) == expected


def test_run_production_cycle_emits_signal(monkeypatch):
    monkeypatch.setattr(cycle_mod, "run_rca", lambda: _incident())
    monkeypatch.setattr(cycle_mod, "correlate_incident", lambda inc: inc)
    monkeypatch.setattr(cycle_mod, "deliver_briefing", lambda inc, sim=None: "test-dest")
    monkeypatch.setattr(kb_mod, "get_kb", lambda *a, **k: _FakeKB())

    signal = cycle_mod.run_production_cycle()

    assert isinstance(signal, Signal)
    assert signal.pillar == "production"
    assert signal.status == "warning"  # HIGH
    assert signal.headline == "Checkout latency spike"
    assert signal.detail["incident"]["suspect_commit"] == "abc1234"
    assert signal.detail["delivered_to"] == "test-dest"
    assert signal.detail["similar"] is None
    # Notebook delivery runs through the sim Dynatrace adapter (no creds), which
    # no-ops to None — the key is always present for the dashboard.
    assert signal.detail["notebook"] is None


def test_cycle_emits_signal_even_when_delivery_fails(monkeypatch):
    def failing_delivery(inc, sim=None):
        raise RuntimeError("slack down")

    monkeypatch.setattr(cycle_mod, "run_rca", lambda: _incident())
    monkeypatch.setattr(cycle_mod, "correlate_incident", lambda inc: inc)
    monkeypatch.setattr(cycle_mod, "deliver_briefing", failing_delivery)
    monkeypatch.setattr(kb_mod, "get_kb", lambda *a, **k: _FakeKB())

    signal = cycle_mod.run_production_cycle()

    assert signal.pillar == "production"
    assert signal.detail["delivered_to"] == "delivery-failed"


def test_poller_run_returns_signal(monkeypatch):
    fake = Signal(
        pillar="production",
        status="warning",
        headline="Checkout latency spike",
        detail={"incident": _incident().model_dump(mode="json")},
        ts=datetime.now(timezone.utc),
    )
    monkeypatch.setattr("services.poller.main.run_production_cycle", lambda: fake)

    client = TestClient(app)
    resp = client.post("/run")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pillar"] == "production"
    assert body["headline"] == "Checkout latency spike"


def test_poller_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
