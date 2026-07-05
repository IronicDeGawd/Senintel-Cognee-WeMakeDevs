"""P2-4: cross-pillar correlation. LLM mocked so the suite stays offline/free;
the live link is verified via scripts/run_briefing.py."""

import agents.sentinel.pillars.production_sentinel.correlation as corr_mod
from shared.models import Incident, Severity


def _draft() -> Incident:
    return Incident(
        title="Checkout latency spike",
        severity=Severity.HIGH,
        service="checkout-service",
        summary="Checkout p95 ~13x baseline.",
        suspected_cause="p95 latency 180ms -> 2400ms coincident with a deploy.",
        suspect_commit=None,
        next_action="Roll back the checkout-service deploy.",
    )


def _correlated() -> Incident:
    return Incident(
        title="Checkout latency spike",
        severity=Severity.HIGH,
        service="checkout-service",
        summary="Checkout p95 ~13x baseline.",
        suspected_cause="N+1 query introduced in checkout/views.py (removed select_related).",
        suspect_commit="abc1234",
        next_action="Roll back commit abc1234 on checkout-service.",
    )


def test_suspect_commit_derived_from_deploys():
    assert corr_mod.suspect_commit_for("checkout-service") == "abc1234"
    assert corr_mod.suspect_commit_for("unknown-service") is None


def test_correlate_links_incident_to_commit(monkeypatch):
    captured = {}

    def fake_generate_json(prompt, schema, model=None):
        captured["prompt"] = prompt
        return _correlated()

    monkeypatch.setattr(corr_mod, "generate_json", fake_generate_json)
    result = corr_mod.correlate_incident(_draft())

    assert result.suspect_commit == "abc1234"
    # Both the draft incident and the suspect diff were handed to the model.
    assert "checkout-service" in captured["prompt"]
    assert "select_related" in captured["prompt"]  # the diff was included


def test_correlate_skips_when_no_deploy(monkeypatch):
    # A service with no deploys -> no LLM call, draft returned unchanged.
    def boom(*a, **k):
        raise AssertionError("generate_json should not be called without a commit")

    monkeypatch.setattr(corr_mod, "generate_json", boom)
    draft = _draft()
    draft.service = "unknown-service"
    result = corr_mod.correlate_incident(draft)
    assert result is draft
    assert result.suspect_commit is None


def test_correlate_skips_on_unknown_commit(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("generate_json should not run when the diff errors")

    monkeypatch.setattr(corr_mod, "generate_json", boom)
    result = corr_mod.correlate_incident(_draft(), commit="deadbeef")
    assert result.suspect_commit is None


def test_correlate_degrades_when_diff_source_raises(monkeypatch):
    # A flaky diff source (e.g. real GitLab MCP down) must not sink the briefing.
    def raising_get_mr_diff(commit):
        raise RuntimeError("gitlab mcp unreachable")

    def boom(*a, **k):
        raise AssertionError("generate_json should not run when the diff fetch fails")

    monkeypatch.setattr(corr_mod, "get_mr_diff", raising_get_mr_diff)
    monkeypatch.setattr(corr_mod, "generate_json", boom)
    draft = _draft()
    result = corr_mod.correlate_incident(draft)
    assert result is draft
    assert result.suspect_commit is None
