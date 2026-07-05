"""GitLab webhook gateway for Code Guardian.

One endpoint: POST /gitlab/webhook receives a GitLab `merge_request` event,
verifies the shared secret, runs one Code Guardian cycle on the head commit, and
returns the emitted Signal. GitLab Webhooks panel points at this URL in prod
(Cloud Run); locally you POST a sample payload:

    uvicorn services.webhook_gateway.main:app --reload
    curl -X POST localhost:8000/gitlab/webhook \\
      -H "X-Gitlab-Token: <secret>" \\
      -H "Content-Type: application/json" \\
      -d '{"object_kind":"merge_request","object_attributes":{"action":"open",
           "iid":42,"last_commit":{"id":"abc1234"}}}'

Only `open` and `update` MR events trigger a review; other events return 204.
"""

from __future__ import annotations

from typing import Any

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, Response, status

from agents.sentinel.pillars.code_guardian.cycle import run_code_guardian_cycle
from shared.config import settings
from shared.logging import get_logger

log = get_logger(__name__)

app = FastAPI(title="SentinelAI — Code Guardian webhook gateway")

_REVIEW_ACTIONS = {"open", "update", "reopen"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "pillar": "code"}


@app.post("/gitlab/webhook")
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_gitlab_token: str | None = Header(default=None),
) -> Response:
    """Receive a GitLab webhook, verify the shared secret, run a review.

    The cycle (REST + two Gemini calls) takes ~10s, which is right at GitLab's
    webhook timeout. We accept the request, fire the cycle in the background
    via FastAPI's BackgroundTasks, and return 202 immediately so GitLab marks
    the delivery as successful. The Cloud Run instance keeps running long
    enough to finish the cycle and POST the note back.
    """
    _verify_token(x_gitlab_token)

    payload: dict[str, Any] = await request.json()
    if payload.get("object_kind") != "merge_request":
        log.info("ignoring %s event", payload.get("object_kind"))
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    attrs = payload.get("object_attributes") or {}
    action = attrs.get("action")
    if action not in _REVIEW_ACTIONS:
        log.info("ignoring MR action %s", action)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    commit = _extract_commit(attrs)
    if not commit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="missing commit SHA on merge_request event",
        )

    log.info("review queued: MR action=%s commit=%s", action, commit)
    background_tasks.add_task(_run_cycle_in_background, commit)
    return Response(status_code=status.HTTP_202_ACCEPTED)


def _run_cycle_in_background(commit: str) -> None:
    try:
        signal = run_code_guardian_cycle(commit)
        log.info("background cycle done: %s -> %s", signal.headline, signal.status)
    except Exception:
        log.exception("background cycle failed for commit %s", commit)


def _verify_token(received: str | None) -> None:
    expected = settings.gitlab_webhook_token
    if not expected:
        return  # dev mode: no shared secret configured
    if received != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid webhook token"
        )


def _extract_commit(attrs: dict) -> str | None:
    last_commit = attrs.get("last_commit") or {}
    return last_commit.get("id") or attrs.get("sha") or attrs.get("merge_commit_sha")
