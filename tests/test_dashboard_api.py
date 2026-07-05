"""D2: dashboard_api endpoints. Offline — stores stubbed via monkeypatch,
upstream Cloud Run hits stubbed via an httpx transport."""

from datetime import datetime, timezone, timedelta

import httpx
from fastapi.testclient import TestClient

import services.dashboard_api.main as api_mod
from services.dashboard_api.main import app
from shared.models import Signal


def _signal(
    pillar: str,
    *,
    headline: str = "h",
    detail: dict | None = None,
    minutes_ago: int = 0,
) -> Signal:
    return Signal(
        pillar=pillar,
        status="warning",
        headline=headline,
        detail=detail or {},
        ts=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
    )


class _FakeStore:
    def __init__(self, rows: list[Signal]) -> None:
        # newest-first list
        self._rows = sorted(rows, key=lambda s: s.ts, reverse=True)

    def recent(self, limit: int = 20, pillar: str | None = None) -> list[Signal]:
        rows = [s for s in self._rows if pillar is None or s.pillar == pillar]
        return rows[:limit]

    def latest_per_pillar(self) -> dict[str, Signal]:
        out: dict[str, Signal] = {}
        for s in self._rows:  # already newest-first
            out.setdefault(s.pillar, s)
        return out


class _FakeTrends:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def recent(self, suite: str | None = None, limit: int = 50) -> list[dict]:
        return self._rows[:limit]


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "dashboard_api"


def test_signals_returns_latest_per_pillar(monkeypatch):
    store = _FakeStore(
        [
            _signal("production", headline="prod-old", minutes_ago=10),
            _signal("production", headline="prod-new", minutes_ago=1),
            _signal("code", headline="code-1", minutes_ago=2),
        ]
    )
    monkeypatch.setattr(api_mod, "get_signal_store", lambda: store)

    body = TestClient(app).get("/signals").json()
    assert body["production"]["headline"] == "prod-new"
    assert body["code"]["headline"] == "code-1"
    # No ai_quality row -> placeholder for the awaiting card.
    assert body["ai_quality"] is None


def test_history_filters_and_caps_limit(monkeypatch):
    store = _FakeStore(
        [
            _signal("production", headline=f"p{i}", minutes_ago=i)
            for i in range(150)
        ]
        + [_signal("code", headline="c1", minutes_ago=200)]
    )
    monkeypatch.setattr(api_mod, "get_signal_store", lambda: store)

    # limit=1e6 must clamp to 100 (silent cap on the endpoint).
    body = TestClient(app).get("/history", params={"limit": 1_000_000}).json()
    assert len(body) == 100
    assert all(row["pillar"] == "production" for row in body[:10]) or any(
        row["pillar"] == "code" for row in body
    )

    code_only = TestClient(app).get("/history", params={"pillar": "code"}).json()
    assert len(code_only) == 1
    assert code_only[0]["headline"] == "c1"


def test_correlation_joins_prod_to_matching_code(monkeypatch):
    prod = _signal(
        "production",
        headline="checkout p95 spike",
        detail={
            "incident": {
                "title": "Checkout latency spike",
                "service": "checkout-service",
                "suspect_commit": "abc1234",
            }
        },
        minutes_ago=1,
    )
    code_match = _signal(
        "code",
        headline="MR !1 review",
        detail={
            "review": {
                "mr_id": 1,
                "commit": "abc1234",
                "findings": [{"severity": "high", "file": "checkout/views.py"}],
            }
        },
        minutes_ago=2,
    )
    monkeypatch.setattr(api_mod, "get_signal_store", lambda: _FakeStore([prod, code_match]))

    body = TestClient(app).get("/correlation").json()
    assert body["production"]["suspect_commit"] == "abc1234"
    assert body["code"]["mr_id"] == 1
    assert body["verdict"] == "Roll back MR !1 / commit abc1234"


def test_correlation_empty_when_no_signals(monkeypatch):
    monkeypatch.setattr(api_mod, "get_signal_store", lambda: _FakeStore([]))
    body = TestClient(app).get("/correlation").json()
    assert body["production"] is None
    assert body["code"] is None
    assert body["verdict"] is None


def test_trends_quality_returns_rows(monkeypatch):
    monkeypatch.setattr(
        api_mod,
        "get_trends",
        lambda: _FakeTrends([{"hallucination": 0.1, "drift": 0.05} for _ in range(40)]),
    )
    body = TestClient(app).get("/trends/quality", params={"limit": 15}).json()
    assert len(body) == 15
    assert body[0]["hallucination"] == 0.1


def test_trends_quality_falls_back_to_ai_quality_signals(monkeypatch):
    """Empty trends store (per-container JSON on Cloud Run) -> rows derived
    from ai_quality Signals in the shared signal store instead."""
    monkeypatch.setattr(api_mod, "get_trends", lambda: _FakeTrends([]))
    sig = _signal(
        "ai_quality",
        headline="Deploy blocked",
        detail={
            "suite": "checkout-llm-v2",
            "hallucination_rate": 0.22,
            "drift": 0.18,
            "threshold": 0.1,
            "passed": False,
        },
        minutes_ago=1,
    )
    monkeypatch.setattr(api_mod, "get_signal_store", lambda: _FakeStore([sig]))

    body = TestClient(app).get("/trends/quality").json()
    assert len(body) == 1
    assert body[0]["hallucination_rate"] == 0.22
    assert body[0]["suite"] == "checkout-llm-v2"
    assert "ts" in body[0]


def test_trigger_returns_503_when_url_unset(monkeypatch):
    monkeypatch.setattr(api_mod.settings, "dashboard_trigger_poller_url", "")
    resp = TestClient(app).post("/trigger/production")
    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"]


def test_trigger_proxies_to_upstream(monkeypatch):
    monkeypatch.setattr(
        api_mod.settings,
        "dashboard_trigger_poller_url",
        "https://poller.example/",
    )

    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["method"] = request.method
        return httpx.Response(202, json={"ok": True})

    transport = httpx.MockTransport(handler)

    # Patch AsyncClient so the endpoint uses our MockTransport.
    real_client_cls = httpx.AsyncClient

    def make_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client_cls(*args, **kwargs)

    monkeypatch.setattr(api_mod.httpx, "AsyncClient", make_client)

    body = TestClient(app).post("/trigger/production").json()
    assert body["pillar"] == "production"
    assert body["upstream_status"] == 202
    assert seen["url"] == "https://poller.example/run"
    assert seen["method"] == "POST"


def _mock_async_client(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_client_cls = httpx.AsyncClient

    def make_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client_cls(*args, **kwargs)

    monkeypatch.setattr(api_mod.httpx, "AsyncClient", make_client)


def test_trigger_code_routes_via_demo_director(monkeypatch):
    """The gateway 401s on an empty webhook POST; the code trigger must go
    through the Demo Director's /demo/gitlab seeder instead."""
    monkeypatch.setattr(
        api_mod.settings, "dashboard_demo_director_url", "https://demo.example"
    )
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"posted": True})

    _mock_async_client(monkeypatch, handler)

    body = TestClient(app).post("/trigger/code").json()
    assert seen["url"] == "https://demo.example/demo/gitlab"
    assert body["upstream_status"] == 200


def test_trigger_ai_quality_sends_eval_request_body(monkeypatch):
    """/eval validates an EvalRequest — the trigger must name a suite."""
    monkeypatch.setattr(
        api_mod.settings,
        "dashboard_trigger_eval_runner_url",
        "https://evals.example",
    )
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content
        return httpx.Response(200, json={"pillar": "ai_quality"})

    _mock_async_client(monkeypatch, handler)

    TestClient(app).post("/trigger/ai_quality")
    assert seen["url"] == "https://evals.example/eval"
    assert b"checkout-llm-v2" in seen["body"]


def test_trigger_read_timeout_returns_accepted(monkeypatch):
    """A slow synchronous cycle (poller /run) must read as accepted-202,
    not as a 502."""
    monkeypatch.setattr(
        api_mod.settings,
        "dashboard_trigger_poller_url",
        "https://poller.example",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("upstream still working", request=request)

    _mock_async_client(monkeypatch, handler)

    resp = TestClient(app).post("/trigger/production")
    assert resp.status_code == 200
    assert resp.json()["upstream_status"] == 202
