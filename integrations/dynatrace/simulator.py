"""Dynatrace simulator (mode = sim). Deterministic, no creds. Promotes the
spike fixture and normalizes the Dynatrace-native payload into the shared
Problem model — the exact shape real.py must also produce, so agent code is
mode-agnostic.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from shared.models import Problem, Severity

from .interface import DynatraceIntegration

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "problems.json"

# Dynatrace problem *category* -> our criticality. Deterministic, data-driven.
_SEVERITY_BY_LEVEL = {
    "PERFORMANCE": Severity.HIGH,
    "RESOURCE_CONTENTION": Severity.MEDIUM,
    "AVAILABILITY": Severity.CRITICAL,
    "ERROR": Severity.HIGH,
}


def _to_problem(raw: dict) -> Problem:
    affected = raw.get("affectedEntities") or [{}]
    return Problem(
        problem_id=raw["displayId"],
        title=raw["title"],
        severity=_SEVERITY_BY_LEVEL.get(raw.get("severityLevel", ""), Severity.LOW),
        status=raw.get("status", "OPEN"),
        service=affected[0].get("name", "unknown"),
        root_cause_entity=(raw.get("rootCauseEntity") or {}).get("name"),
        start_time=datetime.fromisoformat(raw["startTime"].replace("Z", "+00:00")),
        evidence={
            **raw.get("evidenceDetails", {}),
            "severity_level": raw.get("severityLevel"),
            "impact_level": raw.get("impactLevel"),
        },
    )


class DynatraceSimulator(DynatraceIntegration):
    def healthcheck(self) -> bool:
        return True

    def list_problems(self) -> list[Problem]:
        data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        return [_to_problem(p) for p in data["problems"]]

    def execute_dql(self, query: str) -> dict:
        """Canned DQL result: the checkout-service latency timeseries that backs
        the response-time problem. Shape mirrors a Grail records response."""
        svc = "checkout-service"
        return {
            "query": query,
            "records": [
                {"timestamp": "2026-06-08T07:35:00Z", "service": svc, "p95_ms": 180},
                {"timestamp": "2026-06-08T07:40:00Z", "service": svc, "p95_ms": 640},
                {"timestamp": "2026-06-08T07:42:00Z", "service": svc, "p95_ms": 2400},
            ],
        }

    def recent_deployments(self, service: str) -> list[dict]:
        """Canned deploy events. The 07:38 checkout-service deploy (commit
        abc1234) lines up with the 07:40 latency jump — the correlation seam."""
        if service != "checkout-service":
            return []
        return [
            {
                "version": "2026.06.08.1",
                "commit": "abc1234",
                "timestamp": "2026-06-08T07:38:00Z",
            }
        ]

    def send_slack_message(self, text: str, channel: str | None = None) -> bool:
        """No-op in sim: the MCP Slack tool needs a live tenant + Slack Connection.
        Returns False so delivery falls back to the webhook / file path."""
        return False

    def create_notebook(self, title: str, markdown: str) -> str | None:
        """No-op in sim: a Dynatrace notebook needs a live tenant. The offline
        demo artifact is out/briefing.md (delivery layer), so sim skips silently."""
        return None

    def send_event(self, event_type: str, title: str, properties: dict) -> bool:
        """No-op in sim: seeding events into a fake tenant is meaningless.
        Returns False so the Demo Director can flag 'DT not wired' to callers."""
        return False
