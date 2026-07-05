"""P3-1: Arize simulator + mode switch + quality gate. Sim path needs no creds."""

import pytest

from agents.sentinel.pillars.ai_quality_gate.gate import decide, evaluate, run_gate
from integrations.arize.factory import get
from integrations.arize.simulator import ArizeSimulator
from shared.models import EvalResult


def test_factory_sim_returns_simulator():
    assert isinstance(get("sim"), ArizeSimulator)


def test_factory_real_raises_clear_error_until_implemented():
    # real.py (the Phoenix adapter) is a separate workstream; until it exists,
    # real mode must fail with an actionable NotImplementedError, not ImportError.
    with pytest.raises(NotImplementedError, match="not implemented yet"):
        get("real")


def test_healthcheck():
    assert get("sim").healthcheck() is True


def test_baseline_passes():
    base = get("sim").get_baseline("checkout-llm")
    assert isinstance(base, EvalResult)
    assert base.passed is True


def test_clean_run_passes():
    res = get("sim").run_eval("checkout-llm-v1", [])
    assert res.passed is True
    assert res.hallucination_rate < res.threshold and res.drift < res.threshold


def test_regressed_run_fails():
    res = get("sim").run_eval("checkout-llm-v2", [])
    assert res.passed is False
    assert res.hallucination_rate >= res.threshold or res.drift >= res.threshold


def test_unknown_suite_falls_back_to_clean():
    res = get("sim").run_eval("never-seen", [])
    assert res.passed is True


def test_evaluate_rule_boundary():
    # Strictly-less-than threshold: a value exactly at the threshold fails.
    assert evaluate(0.09, 0.09, 0.10) is True
    assert evaluate(0.10, 0.0, 0.10) is False
    assert evaluate(0.0, 0.10, 0.10) is False


def test_decide_ok_signal_on_pass():
    res = get("sim").run_eval("checkout-llm-v1", [])
    sig = decide(res)
    assert sig.pillar == "ai_quality"
    assert sig.status == "ok"
    assert sig.detail["suite"] == "checkout-llm-v1"


def test_decide_blocks_deploy_on_fail():
    res = get("sim").run_eval("checkout-llm-v2", [])
    sig = decide(res)
    assert sig.status == "critical"
    assert "blocked" in sig.headline.lower()


def test_run_gate_end_to_end():
    sig = run_gate("checkout-llm-v2", mode="sim")
    assert sig.pillar == "ai_quality"
    assert sig.status == "critical"
