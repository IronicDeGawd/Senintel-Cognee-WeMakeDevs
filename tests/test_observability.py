"""P2-8 self-observability: offline tests. The live OTLP export needs a
Dynatrace Api-Token and is exercised by running an agent turn with creds set,
not here. These cover the pure URL helper and the disabled (no-op) path."""

import shared.observability as obs
from shared.observability import init_tracing, traces_url


def test_traces_url_appends_signal_path():
    assert (
        traces_url("https://abc.live.dynatrace.com/api/v2/otlp")
        == "https://abc.live.dynatrace.com/api/v2/otlp/v1/traces"
    )


def test_traces_url_idempotent_and_strips_trailing_slash():
    full = "https://abc.live.dynatrace.com/api/v2/otlp/v1/traces"
    assert traces_url(full) == full
    assert traces_url("https://abc.live.dynatrace.com/api/v2/otlp/") == full


def test_init_tracing_noop_when_creds_unset(monkeypatch):
    monkeypatch.setattr(obs.settings, "dt_otlp_endpoint", "")
    monkeypatch.setattr(obs.settings, "dt_api_token", "")
    monkeypatch.setattr(obs, "_initialized", False)
    assert init_tracing() is False
    assert obs._initialized is False


def test_init_tracing_noop_when_only_endpoint_set(monkeypatch):
    monkeypatch.setattr(obs.settings, "dt_otlp_endpoint", "https://x.live.dynatrace.com/api/v2/otlp")
    monkeypatch.setattr(obs.settings, "dt_api_token", "")
    monkeypatch.setattr(obs, "_initialized", False)
    assert init_tracing() is False


def test_init_tracing_short_circuits_when_already_initialized(monkeypatch):
    monkeypatch.setattr(obs, "_initialized", True)
    # creds unset, but the already-initialized guard must win and return True
    monkeypatch.setattr(obs.settings, "dt_otlp_endpoint", "")
    monkeypatch.setattr(obs.settings, "dt_api_token", "")
    assert init_tracing() is True
