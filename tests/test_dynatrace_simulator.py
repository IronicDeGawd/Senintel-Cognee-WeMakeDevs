"""P2-1: Dynatrace simulator + mode switch. Sim path needs no creds."""

from integrations.dynatrace.factory import get
from integrations.dynatrace.simulator import DynatraceSimulator
from shared.models import Problem, Severity


def test_factory_sim_returns_simulator():
    assert isinstance(get("sim"), DynatraceSimulator)


def test_list_problems_normalized_to_model():
    problems = get("sim").list_problems()
    assert len(problems) == 2
    assert all(isinstance(p, Problem) for p in problems)


def test_problems_share_root_cause():
    problems = get("sim").list_problems()
    assert {p.root_cause_entity for p in problems} == {"checkout-service"}


def test_top_problem_fields():
    top = next(p for p in get("sim").list_problems() if p.problem_id == "P-2506081")
    assert top.severity == Severity.HIGH
    assert top.service == "checkout-service"
    assert top.evidence["currentMs"] == 2400


def test_execute_dql_returns_records():
    res = get("sim").execute_dql("fetch logs | filter service == 'checkout-service'")
    assert res["records"] and res["records"][-1]["p95_ms"] == 2400


def test_healthcheck():
    assert get("sim").healthcheck() is True


def test_create_notebook_is_noop_in_sim():
    # Sim has no live tenant, so notebook delivery returns None (choice B).
    assert get("sim").create_notebook("Checkout latency spike", "# md") is None


def test_send_slack_message_is_noop_in_sim():
    # Sim can't reach the MCP Slack tool; returns False so delivery falls back.
    assert get("sim").send_slack_message("hi", "#ops") is False
