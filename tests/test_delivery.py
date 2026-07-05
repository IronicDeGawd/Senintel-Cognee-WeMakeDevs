"""P2-5: briefing delivery. Sim writes a file; real posts to Slack (MCP first,
webhook fallback). Offline."""

from types import SimpleNamespace

import pytest

import delivery.briefing as deliv
import integrations.dynatrace.factory as dt_factory
from shared.models import Incident, Severity
from storage.incident_kb import SimilarMatch


class _FakeDT:
    def __init__(self, sent: bool) -> None:
        self._sent = sent

    def send_slack_message(self, text, channel=None) -> bool:
        return self._sent


def _incident() -> Incident:
    return Incident(
        title="Checkout latency spike",
        severity=Severity.HIGH,
        service="checkout-service",
        summary="Checkout p95 ~13x baseline.",
        suspected_cause="N+1 query in checkout/views.py.",
        suspect_commit="abc1234",
        next_action="Roll back commit abc1234.",
    )


def test_render_without_similar():
    md = deliv.render_briefing(_incident())
    assert "# Morning Briefing" in md
    assert "abc1234" in md
    assert "no similar past incident" in md


def test_render_with_similar():
    similar = SimilarMatch(incident=_incident(), score=0.62, incident_id="x")
    md = deliv.render_briefing(_incident(), similar)
    assert "62% match" in md


def test_deliver_sim_writes_file(tmp_path, monkeypatch):
    out = tmp_path / "briefing.md"
    monkeypatch.setattr(deliv, "_OUT", out)
    monkeypatch.setattr(deliv.settings, "delivery_mode", "sim")
    dest = deliv.deliver_briefing(_incident())
    assert dest == str(out)
    assert out.exists()
    assert "Checkout latency spike" in out.read_text(encoding="utf-8")


def test_deliver_real_prefers_mcp(monkeypatch):
    monkeypatch.setattr(deliv.settings, "delivery_mode", "real")
    monkeypatch.setattr(dt_factory, "get", lambda *a, **k: _FakeDT(sent=True))
    assert deliv.deliver_briefing(_incident()) == "slack-mcp"


def test_deliver_real_falls_back_to_webhook(monkeypatch):
    posted = {}

    def fake_post(url, json, timeout):
        posted["url"] = url
        posted["text"] = json["text"]
        return SimpleNamespace(raise_for_status=lambda: None)

    monkeypatch.setattr(deliv.settings, "delivery_mode", "real")
    monkeypatch.setattr(deliv.settings, "slack_webhook_url", "https://hook")
    monkeypatch.setattr(dt_factory, "get", lambda *a, **k: _FakeDT(sent=False))
    monkeypatch.setattr("httpx.post", fake_post)

    assert deliv.deliver_briefing(_incident()) == "slack-webhook"
    assert posted["url"] == "https://hook"
    assert "Checkout latency spike" in posted["text"]


def test_deliver_real_without_any_target_raises(monkeypatch):
    # MCP unavailable (sent=False) and no webhook -> a clear configuration error.
    monkeypatch.setattr(deliv.settings, "delivery_mode", "real")
    monkeypatch.setattr(deliv.settings, "slack_webhook_url", "")
    monkeypatch.setattr(dt_factory, "get", lambda *a, **k: _FakeDT(sent=False))
    with pytest.raises(RuntimeError, match="SLACK_WEBHOOK_URL"):
        deliv.deliver_briefing(_incident())
