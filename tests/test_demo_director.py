"""Demo Director seeders + service surface. Offline — partner calls stubbed."""

from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

import agents.sentinel.demo_director.scenario as scenario_mod
import agents.sentinel.demo_director.seeders as seeders_mod
from agents.sentinel.demo_director import seeders
from services.demo_director.main import app


class _FakeDT:
    def __init__(self, ok: bool = True) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self._ok = ok

    def send_event(self, event_type, title, properties):
        self.calls.append((event_type, title, properties))
        if not self._ok:
            raise RuntimeError("seed failed")
        return True


def test_seed_dynatrace_pushes_spike_and_deploy(monkeypatch):
    fake = _FakeDT()
    monkeypatch.setattr(seeders, "get_dynatrace", lambda *a, **k: fake)
    # The seeder optionally looks up the live MR head SHA when GitLab creds
    # are set; force the fallback path here so the test doesn't try to hit
    # gitlab.com offline.
    monkeypatch.setattr(seeders, "_live_mr_head_commit", lambda: None)
    receipt = seeders.seed_dynatrace_problem()
    assert receipt["spike_ingested"] is True
    assert receipt["deploy_ingested"] is True
    assert receipt["service"] == "checkout-service"
    assert receipt["commit"] == "abc1234"
    # Two events: spike + deployment.
    assert {c[0] for c in fake.calls} == {"CUSTOM_ALERT", "CUSTOM_DEPLOYMENT"}


def test_seed_dynatrace_no_url_in_seeders_raises_up(monkeypatch):
    fake = _FakeDT(ok=False)
    monkeypatch.setattr(seeders, "get_dynatrace", lambda *a, **k: fake)
    # First send_event raises; the seeder lets it bubble so the service handler
    # surfaces it as a 500 with the trace.
    import pytest
    with pytest.raises(RuntimeError):
        seeders.seed_dynatrace_problem()


def test_seed_gitlab_skips_when_url_unset(monkeypatch):
    monkeypatch.setattr(seeders_mod.settings, "dashboard_trigger_gateway_url", "")
    receipt = seeders.seed_gitlab_webhook()
    assert receipt == {"posted": False, "reason": "gateway_url unset"}


def test_seed_gitlab_proxies_to_gateway(monkeypatch):
    monkeypatch.setattr(
        seeders_mod.settings,
        "dashboard_trigger_gateway_url",
        "https://gateway.example",
    )

    seen: dict[str, object] = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["url"] = str(req.url)
        seen["body"] = req.content
        return httpx.Response(202, json={"queued": True})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def make_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(seeders_mod.httpx, "Client", make_client)

    receipt = seeders.seed_gitlab_webhook()
    assert receipt["posted"] is True
    assert receipt["status_code"] == 202
    assert seen["url"] == "https://gateway.example/gitlab/webhook"
    body = (seen["body"] or b"").decode()
    assert "merge_request" in body
    assert "abc1234" in body


def test_seed_eval_skips_when_url_unset(monkeypatch):
    monkeypatch.setattr(seeders_mod.settings, "dashboard_trigger_eval_runner_url", "")
    receipt = seeders.seed_eval_regression()
    assert receipt == {"posted": False, "reason": "eval_runner_url unset"}


def test_full_scenario_runs_each_step(monkeypatch):
    monkeypatch.setattr(
        scenario_mod.seeders,
        "seed_dynatrace_problem",
        lambda: {"spike_ingested": True, "deploy_ingested": True},
    )
    monkeypatch.setattr(
        scenario_mod.seeders,
        "seed_gitlab_webhook",
        lambda: {"posted": True, "status_code": 202},
    )
    monkeypatch.setattr(
        scenario_mod.seeders,
        "seed_eval_regression",
        lambda: {"posted": True, "status_code": 200},
    )
    monkeypatch.setattr(
        scenario_mod, "_fire_poller", lambda *a, **k: {"posted": True, "status_code": 200}
    )

    receipt = scenario_mod.run_checkout_scenario()
    assert receipt["ok"] is True
    assert set(receipt["steps"].keys()) == {"dynatrace", "gitlab", "ai_quality", "production"}


def test_service_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "demo_director"


def test_service_demo_run_proxies_to_scenario(monkeypatch):
    monkeypatch.setattr(
        scenario_mod,
        "run_checkout_scenario",
        lambda: {"scenario": "checkout-n-plus-one", "steps": {}, "ok": True},
    )
    body = TestClient(app).post("/demo/run").json()
    assert body["ok"] is True
    assert body["scenario"] == "checkout-n-plus-one"


def test_service_surfaces_seeder_errors(monkeypatch):
    def _boom():
        raise RuntimeError("dynatrace down")
    monkeypatch.setattr(
        "services.demo_director.main.seeders.seed_dynatrace_problem",
        _boom,
    )
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/demo/dynatrace")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"] == "RuntimeError"
    assert "dynatrace down" in body["message"]
