"""Scenario orchestration. Runs the seeders in narrative order:
  1. Seed Dynatrace with the spike + suspect deployment.
  2. Fire the GitLab MR webhook (gateway runs Code Guardian).
  3. Trigger the AI Quality Gate with the regression suite.
  4. Trigger the Production Sentinel poller so the dashboard's correlation
     panel hydrates with the freshly seeded prod data + suspect commit.

Each step is best-effort: a failed seed reports the failure but never raises
so the dashboard can render partial results when one partner is down."""

from __future__ import annotations

from typing import Any

import httpx

from shared.config import settings
from shared.logging import get_logger

from . import seeders

log = get_logger(__name__)


def _fire_poller(poller_url: str | None = None) -> dict[str, Any]:
    target = (poller_url or settings.dashboard_trigger_poller_url).rstrip("/")
    if not target:
        return {"posted": False, "reason": "poller_url unset"}
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{target}/run")
    except httpx.HTTPError as exc:
        log.warning("poller trigger failed: %s", exc)
        return {"posted": False, "reason": str(exc)}
    return {"posted": resp.status_code == 200, "status_code": resp.status_code}


def run_checkout_scenario() -> dict[str, Any]:
    """Run the canonical N+1 / checkout scenario end-to-end against real
    partners. Returns a structured receipt the dashboard can inspect."""
    receipt: dict[str, Any] = {"scenario": "checkout-n-plus-one", "steps": {}}

    log.info("Demo Director: step 1 — seed Dynatrace")
    try:
        receipt["steps"]["dynatrace"] = seeders.seed_dynatrace_problem()
    except Exception as exc:
        log.exception("dynatrace seed failed")
        receipt["steps"]["dynatrace"] = {"error": str(exc)}

    log.info("Demo Director: step 2 — seed GitLab webhook")
    receipt["steps"]["gitlab"] = seeders.seed_gitlab_webhook()

    log.info("Demo Director: step 3 — seed AI Quality Gate")
    receipt["steps"]["ai_quality"] = seeders.seed_eval_regression()

    log.info("Demo Director: step 4 — trigger Production Sentinel cycle")
    receipt["steps"]["production"] = _fire_poller()

    receipt["ok"] = all(
        isinstance(v, dict) and v.get("error") is None for v in receipt["steps"].values()
    )
    return receipt
