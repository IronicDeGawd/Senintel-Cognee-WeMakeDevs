"""Per-partner seed functions. Each returns a small dict the orchestrator
captures so the dashboard can render exactly what got seeded."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from integrations.dynatrace.factory import get as get_dynatrace
from shared.config import settings
from shared.logging import get_logger

log = get_logger(__name__)

# The checkout demo scenario — single source so every seed call agrees on the
# narrative. Edit here to retell the same story with a different service/commit.
SCENARIO_SERVICE = "checkout-service"
SCENARIO_COMMIT = "abc1234"
SCENARIO_MR_IID = 1
SCENARIO_EVAL_SUITE = "checkout-llm-v2"


def seed_dynatrace_problem() -> dict:
    """Push a custom event into Dynatrace mimicking a checkout p95 spike, and
    a deployment event tagged to the suspect commit. Real cycle's
    `recent_deployments` DQL picks the deployment up; the custom event leaves a
    breadcrumb in Grail for the operator.

    Uses the live MR !1 head SHA as the suspect commit when GitLab creds are
    set so the dashboard's correlation panel pins prod ↔ code by exact commit.
    Falls back to the canonical fake SHA for sim / no-creds dev."""
    dt = get_dynatrace()
    now = datetime.now(timezone.utc).isoformat()
    commit = _live_mr_head_commit() or SCENARIO_COMMIT

    spike_ok = dt.send_event(
        event_type="CUSTOM_ALERT",
        title=f"{SCENARIO_SERVICE} p95 latency spike — 180ms → 2400ms",
        properties={
            "service": SCENARIO_SERVICE,
            "metric": "p95",
            "baseline_ms": "180",
            "observed_ms": "2400",
            "suspect_commit": commit,
            "scenario": "sentinelai-demo",
            "seeded_at": now,
        },
    )

    deploy_ok = dt.send_event(
        event_type="CUSTOM_DEPLOYMENT",
        title=f"Deployed {SCENARIO_SERVICE} {commit[:8]}",
        properties={
            "service": SCENARIO_SERVICE,
            "deployment.commit": commit,
            "deployment.version": "demo-001",
            "scenario": "sentinelai-demo",
            "seeded_at": now,
        },
    )

    return {
        "spike_ingested": spike_ok,
        "deploy_ingested": deploy_ok,
        "service": SCENARIO_SERVICE,
        "commit": commit,
    }


def _live_mr_head_commit() -> str | None:
    """Look up the current head commit of the real demo MR (`!1` on the
    parakramlabs demo project). Returns None if the lookup fails — the
    seeder then falls back to the canonical fake SHA, which is fine for sim
    GitLab but 404s on the real adapter."""
    if not (settings.gitlab_token and settings.gitlab_project_id):
        return None
    url = (
        f"{settings.gitlab_url.rstrip('/')}/api/v4/projects/"
        f"{settings.gitlab_project_id}/merge_requests/{SCENARIO_MR_IID}"
    )
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers={"PRIVATE-TOKEN": settings.gitlab_token})
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        log.warning("MR !%s lookup failed: %s", SCENARIO_MR_IID, exc)
        return None
    return payload.get("sha") or payload.get("head_pipeline", {}).get("sha")


def seed_gitlab_webhook(gateway_url: str | None = None) -> dict:
    """Synthesize a GitLab `merge_request` webhook payload and POST it to the
    gateway, exactly mimicking a real MR open/update. Gateway then runs the
    Code Guardian cycle end-to-end against the real MR !1 (the demo repo).

    The Gateway runs in real GitLab mode, so the seeded commit MUST actually
    exist in the demo project — using a fake SHA returns 404. We resolve the
    current head SHA of MR !1 at seed time so the cycle reviews the latest
    real diff, and fall back to the canonical fake SHA only if the lookup
    fails (which still works for the sim-mode dev path)."""
    target = (gateway_url or settings.dashboard_trigger_gateway_url).rstrip("/")
    if not target:
        log.warning("no gateway URL configured; skipping GitLab seed")
        return {"posted": False, "reason": "gateway_url unset"}

    commit = _live_mr_head_commit() or SCENARIO_COMMIT

    payload = {
        "object_kind": "merge_request",
        "object_attributes": {
            "action": "update",
            "iid": SCENARIO_MR_IID,
            "last_commit": {"id": commit},
        },
        "project": {"id": settings.gitlab_project_id},
    }
    headers = {"Content-Type": "application/json"}
    if settings.gitlab_webhook_token:
        headers["X-Gitlab-Token"] = settings.gitlab_webhook_token

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{target}/gitlab/webhook", json=payload, headers=headers)
    except httpx.HTTPError as exc:
        log.warning("GitLab seed POST failed: %s", exc)
        return {"posted": False, "reason": str(exc)}

    return {
        "posted": resp.status_code in (200, 202, 204),
        "status_code": resp.status_code,
        "mr_id": SCENARIO_MR_IID,
        "commit": commit,
    }


def seed_eval_regression(eval_runner_url: str | None = None) -> dict:
    """POST to the eval-runner's /eval endpoint with the regressed suite.
    Arize stays sim until the Phoenix adapter lands, but the eval-runner still
    emits a real Signal to Firestore + the dashboard renders it live."""
    target = (eval_runner_url or settings.dashboard_trigger_eval_runner_url).rstrip("/")
    if not target:
        log.warning("no eval-runner URL configured; skipping eval seed")
        return {"posted": False, "reason": "eval_runner_url unset"}

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{target}/eval",
                json={"suite": SCENARIO_EVAL_SUITE, "dataset": []},
            )
    except httpx.HTTPError as exc:
        log.warning("eval seed POST failed: %s", exc)
        return {"posted": False, "reason": str(exc)}

    return {
        "posted": resp.status_code == 200,
        "status_code": resp.status_code,
        "suite": SCENARIO_EVAL_SUITE,
    }
