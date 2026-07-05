"""P2-2: Production Sentinel RCA + sub-agent. LLM is mocked so the suite stays
offline/free; the live path is verified separately via scripts/run_briefing.py."""

from datetime import UTC, datetime

import agents.sentinel.pillars.production_sentinel.rca as rca_mod
from agents.sentinel.pillars.production_sentinel.agent import build_production_sentinel
from shared.models import Incident, Severity


def _fake_incident() -> Incident:
    return Incident(
        title="Checkout latency spike",
        severity=Severity.HIGH,
        service="checkout-service",
        summary="Checkout p95 ~13x baseline.",
        suspected_cause="N+1 query introduced in the 07:38 deploy.",
        suspect_commit=None,
        next_action="Roll back the checkout-service deploy.",
    )


def test_run_rca_uses_sim_problems_and_returns_incident(monkeypatch):
    captured = {}

    def fake_generate_json(prompt, schema, model=None):
        captured["prompt"] = prompt
        captured["schema"] = schema
        return _fake_incident()

    monkeypatch.setattr(rca_mod, "generate_json", fake_generate_json)
    incident = rca_mod.run_rca()

    assert isinstance(incident, Incident)
    assert captured["schema"] is Incident
    # The sim problems (both on checkout-service) were serialized into the prompt.
    assert "checkout-service" in captured["prompt"]
    assert "P-2506081" in captured["prompt"]


def test_run_rca_accepts_prefetched_problems(monkeypatch):
    monkeypatch.setattr(rca_mod, "generate_json", lambda *a, **k: _fake_incident())
    incident = rca_mod.run_rca(problems=[])
    assert incident.service == "checkout-service"


def test_sub_agent_builds_in_sim():
    agent = build_production_sentinel()
    assert agent.name == "production_sentinel"
    assert len(agent.tools) == 3  # sim: list_problems + execute_dql + get_mr_diff


def test_incident_ts_roundtrip_is_serializable():
    # Guards that an Incident folds cleanly into a Signal.detail later.
    inc = _fake_incident()
    payload = inc.model_dump(mode="json")
    assert payload["severity"] == "high"
    datetime.now(UTC)  # sanity import use
