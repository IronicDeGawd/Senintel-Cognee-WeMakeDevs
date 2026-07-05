"""P3-2: eval generation + sub-agent. LLM is mocked so the suite stays offline/
free; the live path is verified separately via scripts/run_eval_gate.py."""

import agents.sentinel.pillars.ai_quality_gate.evalgen as evalgen_mod
from agents.sentinel.pillars.ai_quality_gate.agent import (
    build_ai_quality_gate,
    run_quality_gate,
)
from agents.sentinel.pillars.ai_quality_gate.evalgen import EvalCase, EvalSuite


def _fake_suite() -> EvalSuite:
    return EvalSuite(
        suite="ignored-name",
        cases=[
            EvalCase(
                prompt="What is the order's refund SLA in days?",
                category="hallucination_bait",
                expected_behavior="Say it does not know unless given the policy.",
            )
        ],
    )


def test_generate_eval_suite_forces_caller_name(monkeypatch):
    captured = {}

    def fake_generate_json(prompt, schema, model=None):
        captured["prompt"] = prompt
        captured["schema"] = schema
        return _fake_suite()

    monkeypatch.setattr(evalgen_mod, "generate_json", fake_generate_json)
    suite = evalgen_mod.generate_eval_suite("checkout-llm: new summary prompt", "checkout-llm-v2")

    assert captured["schema"] is EvalSuite
    assert suite.suite == "checkout-llm-v2"  # caller name wins over model echo
    assert "checkout-llm-v2" in captured["prompt"]
    assert len(suite.cases) == 1


def test_run_quality_gate_tool_blocks_regressed_suite():
    sig = run_quality_gate("checkout-llm-v2")
    assert sig["pillar"] == "ai_quality"
    assert sig["status"] == "critical"


def test_run_quality_gate_tool_passes_clean_suite():
    sig = run_quality_gate("checkout-llm-v1")
    assert sig["status"] == "ok"


def test_sub_agent_builds_in_sim():
    agent = build_ai_quality_gate()
    assert agent.name == "ai_quality_gate"
    assert len(agent.tools) == 2  # sim: generate_eval_suite + run_quality_gate
