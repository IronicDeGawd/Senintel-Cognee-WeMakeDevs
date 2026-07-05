"""P2-7 Stage 1: offline unit tests for the real Dynatrace adapter's pure
helpers. The live MCP path needs creds and is exercised by
scripts/probe_dynatrace.py, not here."""

from types import SimpleNamespace

import integrations.dynatrace.real as real_mod
from integrations.dynatrace.real import DynatraceReal
from shared.mcp_client import _parse_result


def test_parse_result_prefers_structured_content():
    res = SimpleNamespace(structuredContent={"records": [1, 2]}, content=[])
    assert _parse_result(res) == {"records": [1, 2]}


def test_parse_result_parses_json_text_blocks():
    res = SimpleNamespace(
        structuredContent=None,
        content=[SimpleNamespace(text='{"a": 1}')],
    )
    assert _parse_result(res) == {"a": 1}


def test_parse_result_wraps_plain_text():
    res = SimpleNamespace(structuredContent=None, content=[SimpleNamespace(text="hello")])
    assert _parse_result(res) == {"text": "hello"}


def test_parse_result_empty():
    res = SimpleNamespace(structuredContent=None, content=[])
    assert _parse_result(res) == {}


def test_extract_problem_dicts_handles_shapes():
    assert DynatraceReal._extract_problem_dicts({"problems": [{"x": 1}]}) == [{"x": 1}]
    assert DynatraceReal._extract_problem_dicts([{"a": 1}, "skip"]) == [{"a": 1}]
    assert DynatraceReal._extract_problem_dicts({"text": "markdown summary"}) == []
    assert DynatraceReal._extract_problem_dicts("nonsense") == []
    # Unrecognised dict (no "problems"/"text") is treated as a single entry.
    assert DynatraceReal._extract_problem_dicts({"foo": 1}) == [{"foo": 1}]


def test_execute_dql_wraps_non_dict_result(monkeypatch):
    # When the MCP returns a bare list, execute_dql wraps it under "records".
    monkeypatch.setattr(DynatraceReal, "__init__", lambda self: None)
    monkeypatch.setattr(
        DynatraceReal, "_call", lambda self, tool, args=None: [{"p95_ms": 2400}]
    )
    assert DynatraceReal().execute_dql("fetch x") == {"records": [{"p95_ms": 2400}]}


def test_list_problems_normalizes_api_v2_shape(monkeypatch):
    # A problems-API v2 style entry (same shape as the sim fixture) normalizes
    # into a Problem via the shared _to_problem template.
    sample = {
        "displayId": "P-9001",
        "title": "Response time degradation",
        "severityLevel": "PERFORMANCE",
        "status": "OPEN",
        "impactLevel": "SERVICE",
        "startTime": "2026-06-09T10:00:00Z",
        "affectedEntities": [{"name": "checkout-service"}],
        "rootCauseEntity": {"name": "checkout-service"},
        "evidenceDetails": {"metric": "service.response.time"},
    }
    monkeypatch.setattr(DynatraceReal, "__init__", lambda self: None)
    monkeypatch.setattr(
        DynatraceReal, "_call", lambda self, tool, args=None: {"problems": [sample]}
    )

    problems = DynatraceReal().list_problems()
    assert len(problems) == 1
    assert problems[0].problem_id == "P-9001"
    assert problems[0].service == "checkout-service"


def test_notebook_ref_extracts_from_shapes():
    assert DynatraceReal._notebook_ref({"url": "https://dt/nb/1"}) == "https://dt/nb/1"
    # url wins over id when both present.
    assert DynatraceReal._notebook_ref({"id": "abc", "url": "u"}) == "u"
    assert DynatraceReal._notebook_ref({"documentId": "doc-9"}) == "doc-9"
    assert DynatraceReal._notebook_ref({"text": "created"}) == "created"
    assert DynatraceReal._notebook_ref("nb-7") == "nb-7"
    assert DynatraceReal._notebook_ref({}) is None
    assert DynatraceReal._notebook_ref(None) is None


def test_create_notebook_calls_tool_and_returns_ref(monkeypatch):
    captured = {}

    def fake_call(self, tool, args=None):
        captured["tool"] = tool
        captured["args"] = args
        return {"id": "nb-42"}

    monkeypatch.setattr(DynatraceReal, "__init__", lambda self: None)
    monkeypatch.setattr(DynatraceReal, "_call", fake_call)

    ref = DynatraceReal().create_notebook("Checkout latency spike", "# md")
    assert ref == "nb-42"
    assert captured["tool"] == "create_dynatrace_notebook"
    assert captured["args"] == {"name": "Checkout latency spike", "markdown": "# md"}


def test_create_notebook_degrades_on_failure(monkeypatch):
    def boom(self, tool, args=None):
        raise RuntimeError("MCP down")

    monkeypatch.setattr(DynatraceReal, "__init__", lambda self: None)
    monkeypatch.setattr(DynatraceReal, "_call", boom)
    # A notebook failure must never raise — it returns None so the cycle ships.
    assert DynatraceReal().create_notebook("t", "md") is None


def test_send_slack_message_skips_without_connection(monkeypatch):
    # No Slack Connection configured -> return False without ever calling the MCP.
    monkeypatch.setattr(DynatraceReal, "__init__", lambda self: None)
    monkeypatch.setattr(real_mod.settings, "slack_connection_id", "")

    def must_not_call(self, tool, args=None):
        raise AssertionError("MCP should not be invoked without a connection")

    monkeypatch.setattr(DynatraceReal, "_call", must_not_call)
    assert DynatraceReal().send_slack_message("hi", "#ops") is False


def test_send_slack_message_calls_tool(monkeypatch):
    captured = {}

    def fake_call(self, tool, args=None):
        captured["tool"] = tool
        captured["args"] = args
        return {"ok": True}

    monkeypatch.setattr(DynatraceReal, "__init__", lambda self: None)
    monkeypatch.setattr(real_mod.settings, "slack_connection_id", "conn-1")
    monkeypatch.setattr(real_mod.settings, "slack_channel", "#fallback")
    monkeypatch.setattr(DynatraceReal, "_call", fake_call)

    assert DynatraceReal().send_slack_message("hi", "#ops") is True
    assert captured["tool"] == "send_slack_message"
    assert captured["args"] == {"channel": "#ops", "message": "hi"}


def test_send_slack_message_channel_defaults_to_none(monkeypatch):
    # No explicit channel and no configured slack_channel -> pass None, never "".
    captured = {}

    def fake_call(self, tool, args=None):
        captured["args"] = args
        return {"ok": True}

    monkeypatch.setattr(DynatraceReal, "__init__", lambda self: None)
    monkeypatch.setattr(real_mod.settings, "slack_connection_id", "conn-1")
    monkeypatch.setattr(real_mod.settings, "slack_channel", "")
    monkeypatch.setattr(DynatraceReal, "_call", fake_call)

    assert DynatraceReal().send_slack_message("hi") is True
    assert captured["args"]["channel"] is None


def test_send_slack_message_degrades_on_failure(monkeypatch):
    monkeypatch.setattr(DynatraceReal, "__init__", lambda self: None)
    monkeypatch.setattr(real_mod.settings, "slack_connection_id", "conn-1")

    def boom(self, tool, args=None):
        raise RuntimeError("MCP down")

    monkeypatch.setattr(DynatraceReal, "_call", boom)
    # Failure returns False so the caller falls back to the webhook.
    assert DynatraceReal().send_slack_message("hi") is False
