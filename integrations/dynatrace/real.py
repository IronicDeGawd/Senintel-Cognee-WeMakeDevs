"""Real Dynatrace adapter — talks to the live tenant through the Dynatrace MCP
server (npx @dynatrace-oss/dynatrace-mcp-server) over stdio.

Same contract as the simulator, so the agent/poller code is mode-agnostic. The
normalizers (list_problems / recent_deployments) are written defensively against
the Dynatrace problems-API v2 shape and finalized once scripts/probe_dynatrace.py
shows the real payload from the tenant.

Auth: DT_PLATFORM_TOKEN if set (needed for the headless poller); otherwise the
MCP server falls back to browser OAuth (fine for a local probe, not for a
service). See context/research/dynatrace-mcp.md for the required token scopes.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from shared.config import settings
from shared.logging import get_logger
from shared.mcp_client import call_tool
from shared.models import Problem

from .interface import DynatraceIntegration
from .simulator import _to_problem  # normalizer template (DT problems-API v2 shape)

log = get_logger(__name__)

_DT_CMD = "npx"
_DT_ARGS = ["-y", "@dynatrace-oss/dynatrace-mcp-server@latest"]

# DQL responses from the Dynatrace MCP App-UI render path come back as
# markdown with the row data inside a fenced ```json``` block. This regex
# pulls the JSON body so callers can deserialize it into actual records.
_JSON_FENCE = re.compile(r"```json\s*([\s\S]+?)```", re.MULTILINE)


def _extract_records_from_text(text: str) -> list[dict]:
    match = _JSON_FENCE.search(text)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        log.warning("DQL markdown JSON block failed to parse: %s", match.group(1)[:200])
        return []
    if isinstance(parsed, list):
        return [r for r in parsed if isinstance(r, dict)]
    if isinstance(parsed, dict):
        records = parsed.get("records")
        if isinstance(records, list):
            return [r for r in records if isinstance(r, dict)]
    return []


class DynatraceReal(DynatraceIntegration):
    def __init__(self) -> None:
        if not settings.dt_environment:
            raise RuntimeError(
                "DT_ENVIRONMENT is unset — set it (https://<env>.apps.dynatrace.com) "
                "and DT_PLATFORM_TOKEN in .env to use SENTINEL_DT_MODE=real."
            )

    def _env(self) -> dict[str, str]:
        env = {
            "DT_ENVIRONMENT": settings.dt_environment,
            "DT_GRAIL_QUERY_BUDGET_GB": str(settings.dt_grail_query_budget_gb),
            "DT_MCP_DISABLE_TELEMETRY": "true",
        }
        if settings.dt_platform_token:
            env["DT_PLATFORM_TOKEN"] = settings.dt_platform_token
        # send_slack_message reads the Slack Connection from this env var.
        if settings.slack_connection_id:
            env["SLACK_CONNECTION_ID"] = settings.slack_connection_id
        return env

    def _call(self, tool: str, arguments: dict | None = None) -> Any:
        return call_tool(_DT_CMD, _DT_ARGS, self._env(), tool, arguments)

    def healthcheck(self) -> bool:
        try:
            self._call("list_problems", {})
            return True
        except Exception:
            log.exception("Dynatrace healthcheck failed")
            return False

    @staticmethod
    def _extract_problem_dicts(raw: Any) -> list[dict]:
        """Pull a list of problem dicts out of whatever the MCP returned."""
        if isinstance(raw, dict):
            if isinstance(raw.get("problems"), list):
                return raw["problems"]
            if "text" in raw:
                log.warning(
                    "list_problems returned unstructured text; run "
                    "scripts/probe_dynatrace.py to finalize the normalizer"
                )
                return []
            log.debug("unrecognised problem dict shape, treating as single entry: %s", raw)
            return [raw]
        if isinstance(raw, list):
            return [p for p in raw if isinstance(p, dict)]
        return []

    def list_problems(self) -> list[Problem]:
        raw = self._call("list_problems", {})
        problems: list[Problem] = []
        for entry in self._extract_problem_dicts(raw):
            try:
                problems.append(_to_problem(entry))
            except Exception:
                log.warning("skipping unparseable problem entry: %s", entry)
        if not problems:
            # Davis only auto-promotes anomalies it detects from monitored
            # entities; bare custom events from Demo Director live in Grail but
            # never reach list_problems. Fall back to a DQL fetch of recent
            # Demo Director events so the cycle has something to RCA against.
            problems = self._seeded_problems_from_dql()
        log.info("Dynatrace returned %d problem(s)", len(problems))
        return problems

    def _seeded_problems_from_dql(self) -> list[Problem]:
        """Query Grail for the active CUSTOM_ALERT events that Davis just
        auto-promoted to Davis problems, and project them onto the shared
        Problem model. The Demo Director feeds the events here via the MCP
        `send_event` tool — Davis takes care of marking them as DAVIS_PROBLEM
        within seconds.

        Bounded to a 30-minute window so older demo seeds fall off the radar
        and the cycle returns to a quiet baseline once the demo ends."""
        # `events` is the Grail table that receives both raw custom events
        # (event.category=CUSTOM_ALERT) AND Davis-managed problem snapshots
        # (event.kind=DAVIS_PROBLEM). Filtering on both narrows to the
        # Demo Director's seeds after Davis has wrapped them up.
        # Davis takes 20-60s to wrap a raw CUSTOM_ALERT into a DAVIS_PROBLEM
        # snapshot — the cycle can run before that happens, so filter on the
        # category only and let both shapes through. Picking the newest row
        # naturally prefers the Davis-managed version once it appears.
        dql = (
            "fetch events, from:now()-30m"
            " | filter event.category == \"CUSTOM_ALERT\""
            " | sort timestamp desc"
            " | limit 5"
        )
        try:
            result = self.execute_dql(dql)
        except Exception:
            log.exception("seeded-problems DQL failed; returning []")
            return []
        records = result.get("records", []) if isinstance(result, dict) else []
        problems: list[Problem] = []
        for r in records:
            if not isinstance(r, dict):
                continue
            affected = r.get("affected_entity_names") or []
            service = affected[0] if affected else "checkout-service"
            shaped = {
                "displayId": str(r.get("display_id") or r.get("event.id") or "demo-event"),
                "title": r.get("event.name") or "Demo-seeded alert",
                "severityLevel": "PERFORMANCE",
                "status": r.get("event.status") or "ACTIVE",
                "affectedEntities": [{"name": service}],
                "rootCauseEntity": None,
                "startTime": r.get("event.start")
                or r.get("timestamp")
                or datetime.now(timezone.utc).isoformat(),
                "evidenceDetails": {
                    "description": r.get("event.description"),
                    "category": r.get("event.category"),
                    "kind": r.get("event.kind"),
                    "source": "demo-director",
                },
                "impactLevel": "SERVICE",
            }
            try:
                problems.append(_to_problem(shaped))
            except Exception:
                log.warning("skipping unparseable seeded event: %s", r)
        log.info("Dynatrace seeded-event fallback returned %d problem(s)", len(problems))
        return problems

    def execute_dql(self, query: str) -> dict:
        """Run one DQL statement and return `{records: [...]}` always, even when
        the MCP server speaks markdown.

        The Dynatrace MCP App-UI render path returns `{"text": <markdown>}`
        with the result rows wrapped inside a ```json ... ``` fenced block.
        Parsing that out here lets every caller treat the response uniformly
        instead of duplicating markdown-stripping logic at the call site."""
        # Tool arg name confirmed against the tenant via the probe script.
        result = self._call("execute_dql", {"dqlStatement": query})
        if isinstance(result, dict) and isinstance(result.get("records"), list):
            return result
        if isinstance(result, list):
            return {"records": result}
        text = ""
        if isinstance(result, dict):
            text = result.get("text") or ""
        elif isinstance(result, str):
            text = result
        records = _extract_records_from_text(text) if text else []
        return {"records": records, "raw_text": text} if text else {"records": records}

    def recent_deployments(self, service: str) -> list[dict]:
        """Recent deployment events for a service from Grail.

        The Dynatrace MCP `send_event` tool with eventType=CUSTOM_DEPLOYMENT
        lands rows in the `events` table with event.type=CUSTOM_DEPLOYMENT
        (rather than the older `event.kind=DEPLOYMENT_EVENT` shape that
        OneAgent-instrumented services use). Match on event.type to pick up
        both Demo Director seeds and any future OneAgent deployments —
        OneAgent versions usually set event.type=CUSTOM_DEPLOYMENT too."""
        dql = (
            "fetch events, from:now()-1h"
            " | filter event.type == \"CUSTOM_DEPLOYMENT\""
            f" | filter service == \"{service}\""
            " | sort timestamp desc"
            " | limit 5"
        )
        try:
            result = self.execute_dql(dql)
        except Exception:
            log.exception("recent_deployments DQL failed; returning []")
            return []
        records = result.get("records", []) if isinstance(result, dict) else []
        deploys: list[dict] = []
        for r in records:
            if not isinstance(r, dict):
                continue
            deploys.append(
                {
                    "version": r.get("deployment.version") or r.get("version", ""),
                    "commit": r.get("deployment.commit") or r.get("commit", ""),
                    "timestamp": r.get("timestamp", ""),
                }
            )
        kept = [d for d in deploys if d["commit"]]
        dropped = len(deploys) - len(kept)
        if dropped:
            log.debug("recent_deployments dropped %d deploy event(s) with no commit", dropped)
        log.info("Dynatrace recent_deployments for %s -> %d deploy(s)", service, len(kept))
        return kept

    def send_slack_message(self, text: str, channel: str | None = None) -> bool:
        """Post to Slack via the MCP send_slack_message tool. Skips (returns
        False) when no Slack Connection is configured so delivery falls back to
        the webhook. The arg shape is defensive/probe-finalizable like the other
        tools — scripts/probe_dynatrace.py confirms the exact names. Best-effort:
        any failure returns False rather than raising."""
        if not settings.slack_connection_id:
            log.debug("no SLACK_CONNECTION_ID set; skipping MCP Slack send")
            return False
        try:
            self._call(
                "send_slack_message",
                {"channel": channel or settings.slack_channel or None, "message": text},
            )
        except Exception:
            log.exception("send_slack_message via MCP failed; caller will fall back")
            return False
        log.info("delivered briefing to Slack via Dynatrace MCP")
        return True

    @staticmethod
    def _notebook_ref(raw: Any) -> str | None:
        """Pull a usable notebook id/url out of whatever the MCP returned."""
        if isinstance(raw, dict):
            for key in ("url", "id", "documentId", "notebookId"):
                value = raw.get(key)
                if isinstance(value, str) and value:
                    return value
            if isinstance(raw.get("text"), str) and raw["text"]:
                return raw["text"]
        if isinstance(raw, str) and raw:
            return raw
        return None

    def create_notebook(self, title: str, markdown: str) -> str | None:
        """Post the draft incident as a Dynatrace notebook via the MCP
        create_dynatrace_notebook tool (needs the document:documents:write scope).
        The arg shape is defensive and probe-finalizable like the other
        normalizers — scripts/probe_dynatrace.py confirms the exact arg names
        against the tenant. Best-effort: a notebook failure returns None so the
        cycle's Signal still ships."""
        try:
            raw = self._call(
                "create_dynatrace_notebook", {"name": title, "markdown": markdown}
            )
        except Exception:
            log.exception("create_dynatrace_notebook failed; skipping notebook delivery")
            return None
        ref = self._notebook_ref(raw)
        log.info("created Dynatrace notebook: %s", ref or "(no ref returned)")
        return ref

    def send_event(self, event_type: str, title: str, properties: dict) -> bool:
        """Seed one event via the MCP send_event tool (needs scope
        storage:events:write). Used by the Demo Director to push scenario data
        — a fake p95 spike, a deployment event tagged to a commit — into the
        live tenant so the rest of the cycle reads actual partner data.

        Lets exceptions propagate so the Demo Director can surface auth/scope
        failures to the dashboard (e.g. missing storage:events:write scope)
        instead of silently no-op'ing."""
        payload = {
            "eventType": event_type,
            "title": title,
            "properties": properties,
        }
        raw = self._call("send_event", payload)
        log.info("Dynatrace send_event %s -> %s", event_type, raw)
        return True
