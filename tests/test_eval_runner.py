"""P3-3: eval-runner HTTP surface. Offline — sim eval backend, trend store stubbed."""

from fastapi.testclient import TestClient

import services.eval_runner.main as runner_mod
from services.eval_runner.main import app

client = TestClient(app)


class _FakeTrends:
    def __init__(self):
        self.rows = []

    def append(self, result):
        self.rows.append(result)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["pillar"] == "ai_quality"


def test_eval_blocks_regressed_suite(monkeypatch):
    fake = _FakeTrends()
    monkeypatch.setattr(runner_mod, "get_trends", lambda *a, **k: fake)

    res = client.post("/eval", json={"suite": "checkout-llm-v2"})

    assert res.status_code == 200
    body = res.json()
    assert body["pillar"] == "ai_quality"
    assert body["status"] == "critical"
    assert len(fake.rows) == 1  # the run was recorded for trends


def test_eval_passes_clean_suite(monkeypatch):
    fake = _FakeTrends()
    monkeypatch.setattr(runner_mod, "get_trends", lambda *a, **k: fake)

    res = client.post("/eval", json={"suite": "checkout-llm-v1"})

    assert res.status_code == 200
    assert res.json()["status"] == "ok"
