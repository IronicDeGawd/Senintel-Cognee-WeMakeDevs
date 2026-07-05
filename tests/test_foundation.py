"""Foundation smoke tests: contracts import, config defaults to sim, the mode
switch returns the sim adapter, and the root agent builds."""

from datetime import UTC, datetime

import pytest

from integrations.base import Integration, build_integration
from shared.config import settings
from shared.models import (
    Incident,
    Severity,
    Signal,
)


def test_config_defaults_to_sim():
    assert settings.dt_mode == "sim"
    assert settings.gl_mode == "sim"
    assert settings.arize_mode == "sim"
    assert settings.gemini_model  # non-empty default


def test_signal_carries_incident_payload():
    incident = Incident(
        title="Checkout latency spike",
        severity=Severity.HIGH,
        service="checkout-service",
        summary="p95 13x baseline",
        suspected_cause="N+1 query in commit abc1234",
        suspect_commit="abc1234",
        next_action="rollback MR !42",
    )
    sig = Signal(
        pillar="production",
        status="critical",
        headline="Checkout degraded",
        detail=incident.model_dump(),
        ts=datetime.now(UTC),
    )
    assert sig.pillar == "production"
    assert sig.detail["suspect_commit"] == "abc1234"
    assert Severity(sig.detail["severity"]) is Severity.HIGH


def test_integration_is_abstract():
    with pytest.raises(TypeError):
        Integration()  # type: ignore[abstract]


def test_build_integration_mode_switch():
    sim = object()
    real = object()
    assert build_integration("sim", lambda: sim, lambda: real) is sim
    assert build_integration("real", lambda: sim, lambda: real) is real


def test_root_agent_builds():
    from agents.sentinel.agent import root_agent

    assert root_agent.name == "sentinel"
