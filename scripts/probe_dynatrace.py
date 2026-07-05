"""Probe the live Dynatrace tenant through the MCP server.

    python scripts/probe_dynatrace.py

Confirms the token/scopes work and reveals the real payload shapes so we can
finalize the normalizers in integrations/dynatrace/real.py. Requires DT_ENVIRONMENT
(+ DT_PLATFORM_TOKEN for headless; otherwise a browser OAuth window opens).
Calls the MCP directly (DynatraceReal), independent of SENTINEL_DT_MODE.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integrations.dynatrace.real import DynatraceReal  # noqa: E402


def _dump(label: str, value: object) -> None:
    print(f"\n===== {label} =====")
    try:
        print(json.dumps(value, indent=2, default=str))
    except TypeError:
        print(value)


def main() -> None:
    dt = DynatraceReal()

    print("healthcheck:", dt.healthcheck())

    try:
        problems = [p.model_dump(mode="json") for p in dt.list_problems()]
        _dump("list_problems (normalized Problem models)", problems)
    except Exception as exc:  # noqa: BLE001 - probe surfaces every error verbatim
        _dump("list_problems ERROR", str(exc))

    try:
        _dump("execute_dql sample", dt.execute_dql("fetch logs | limit 3"))
    except Exception as exc:  # noqa: BLE001
        _dump("execute_dql ERROR", str(exc))

    try:
        _dump("recent_deployments(checkout-service)", dt.recent_deployments("checkout-service"))
    except Exception as exc:  # noqa: BLE001
        _dump("recent_deployments ERROR", str(exc))


if __name__ == "__main__":
    main()
