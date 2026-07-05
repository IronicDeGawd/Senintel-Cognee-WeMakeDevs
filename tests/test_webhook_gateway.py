"""P1-6: GitLab webhook gateway. Cycle is stubbed so the suite stays offline."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import services.webhook_gateway.main as gateway
from shared.config import settings
from shared.models import Signal

_MR_PAYLOAD = {
    "object_kind": "merge_request",
    "object_attributes": {
        "action": "open",
        "iid": 42,
        "last_commit": {"id": "abc1234"},
    },
}


def _fake_signal() -> Signal:
    return Signal(
        pillar="code",
        status="warning",
        headline="MR !42: 1 finding(s) — 1 high",
        detail={"posted_to": "out/mr_note_42.md"},
        ts=datetime.now(timezone.utc),
    )


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(gateway, "run_code_guardian_cycle", lambda commit: _fake_signal())
    monkeypatch.setattr(settings, "gitlab_webhook_token", "")  # dev: no secret
    return TestClient(gateway.app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["pillar"] == "code"


def test_mr_open_event_queues_review_and_returns_202(client, monkeypatch):
    seen = []
    monkeypatch.setattr(
        "services.webhook_gateway.main._run_cycle_in_background",
        lambda commit: seen.append(commit),
    )
    resp = client.post("/gitlab/webhook", json=_MR_PAYLOAD)
    # 202 Accepted: the cycle is launched in a background task so the webhook
    # response beats GitLab's ~10s delivery timeout.
    assert resp.status_code == 202
    assert seen == ["abc1234"]


def test_non_mr_event_returns_204(client):
    resp = client.post("/gitlab/webhook", json={"object_kind": "push"})
    assert resp.status_code == 204


def test_ignored_mr_action_returns_204(client):
    payload = {
        "object_kind": "merge_request",
        "object_attributes": {"action": "close", "iid": 42, "last_commit": {"id": "abc1234"}},
    }
    resp = client.post("/gitlab/webhook", json=payload)
    assert resp.status_code == 204


def test_mr_event_without_commit_returns_422(client):
    payload = {"object_kind": "merge_request", "object_attributes": {"action": "open", "iid": 42}}
    resp = client.post("/gitlab/webhook", json=payload)
    assert resp.status_code == 422


def test_wrong_token_returns_401(monkeypatch):
    monkeypatch.setattr(gateway, "run_code_guardian_cycle", lambda commit: _fake_signal())
    monkeypatch.setattr(settings, "gitlab_webhook_token", "expected-secret")
    client = TestClient(gateway.app)

    resp = client.post(
        "/gitlab/webhook",
        json=_MR_PAYLOAD,
        headers={"X-Gitlab-Token": "wrong"},
    )
    assert resp.status_code == 401


def test_correct_token_passes(monkeypatch):
    monkeypatch.setattr(gateway, "run_code_guardian_cycle", lambda commit: _fake_signal())
    monkeypatch.setattr(settings, "gitlab_webhook_token", "expected-secret")
    client = TestClient(gateway.app)

    resp = client.post(
        "/gitlab/webhook",
        json=_MR_PAYLOAD,
        headers={"X-Gitlab-Token": "expected-secret"},
    )
    assert resp.status_code == 202
