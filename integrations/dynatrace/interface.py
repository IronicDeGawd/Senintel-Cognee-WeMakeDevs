"""Dynatrace adapter contract. Both the simulator and the real MCP client
implement these, so the agent code is identical regardless of mode.

Methods mirror the Dynatrace MCP server tools the agent uses:
  - list_problems  -> open Davis problems, normalized to the shared Problem model
  - execute_dql    -> run a DQL query (logs/metrics), raw result dict
"""

from __future__ import annotations

from abc import abstractmethod

from integrations.base import Integration
from shared.models import Problem


class DynatraceIntegration(Integration):
    name = "dynatrace"

    @abstractmethod
    def list_problems(self) -> list[Problem]:
        """Return currently open problems as normalized Problem models."""
        ...

    @abstractmethod
    def execute_dql(self, query: str) -> dict:
        """Run a Dynatrace Query Language statement; return the raw result."""
        ...

    @abstractmethod
    def recent_deployments(self, service: str) -> list[dict]:
        """Recent deployment events for a service, newest first. Each event:
        {version, commit, timestamp}. This is how a prod anomaly is traced back
        to the commit that shipped — the input to P2-4 cross-pillar correlation.
        """
        ...

    @abstractmethod
    def send_slack_message(self, text: str, channel: str | None = None) -> bool:
        """Post a message to Slack through the Dynatrace MCP send_slack_message
        tool (P2-5, the partner-MCP delivery path). Returns True on a confirmed
        send, False when unavailable (the simulator no-ops, and the real adapter
        returns False with no Slack Connection or on failure) so the caller can
        fall back to a plain webhook.
        """
        ...

    @abstractmethod
    def create_notebook(self, title: str, markdown: str) -> str | None:
        """Share the draft incident as a Dynatrace notebook (P2-5 delivery).
        Returns a notebook reference (id/url) on success, or None when it is not
        available: the simulator no-ops because notebooks need a live tenant, and
        the real adapter degrades to None on failure so a notebook hiccup never
        sinks the cycle's Signal.
        """
        ...

    @abstractmethod
    def send_event(self, event_type: str, title: str, properties: dict) -> bool:
        """Push one event into Dynatrace via the MCP `send_event` tool (needs
        scope `storage:events:write`). Used by the Demo Director to seed
        reproducible scenario data — a fake p95 spike, a deployment event tagged
        to a commit — into the real Grail backend so the rest of the pillar can
        run unchanged against actual partner data.

        Returns True on confirmed ingest. Simulator no-ops (returns False).
        Real adapter raises on auth/scope failure so the seeder surfaces a
        clear error to the dashboard.
        """
        ...
