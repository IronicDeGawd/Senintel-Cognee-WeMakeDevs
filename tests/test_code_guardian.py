"""P1-2..P1-4: Code Guardian review + CI diagnosis + cycle + sub-agent. LLM is
mocked so the suite stays offline; the live path is verified separately via
scripts/run_code_review.py."""

from __future__ import annotations

import pytest

import agents.sentinel.pillars.code_guardian.ci as ci_mod
import agents.sentinel.pillars.code_guardian.review as review_mod
from agents.sentinel.pillars.code_guardian.agent import build_code_guardian
from agents.sentinel.pillars.code_guardian.cycle import run_code_guardian_cycle
from agents.sentinel.pillars.code_guardian.note import render_mr_note
from shared.models import Finding, MRReview, Severity


def _fake_review(mr_id: int = 0, commit: str = "wrong") -> MRReview:
    return MRReview(
        mr_id=mr_id,
        commit=commit,
        findings=[
            Finding(
                file="checkout/views.py",
                line=88,
                category="performance",
                severity=Severity.HIGH,
                message="N+1 query: per-order OrderItem fetch in confirm_checkout.",
                suggestion="Restore select_related and prefetch line items.",
            ),
        ],
        ci_root_cause="echoed-from-model",
    )


def test_run_review_uses_sim_diff_and_forces_known_identifiers(monkeypatch):
    captured = {}

    def fake_generate_json(prompt, schema, model=None):
        captured["prompt"] = prompt
        captured["schema"] = schema
        return _fake_review()

    monkeypatch.setattr(review_mod, "generate_json", fake_generate_json)
    review = review_mod.run_review("abc1234")

    assert review.mr_id == 42  # forced from the sim diff header
    assert review.commit == "abc1234"
    assert review.ci_root_cause is None  # cleared; CI is a separate step
    assert review.findings[0].category == "performance"
    # The sim diff (the N+1 regression) was serialized into the prompt.
    assert "select_related" in captured["prompt"]
    assert captured["schema"] is MRReview


def test_run_review_unknown_commit_raises(monkeypatch):
    monkeypatch.setattr(review_mod, "generate_json", lambda *a, **k: _fake_review())
    with pytest.raises(ValueError, match="no merge request found"):
        review_mod.run_review("deadbeef")


def test_diagnose_ci_on_failed_pipeline_returns_text(monkeypatch):
    monkeypatch.setattr(ci_mod, "generate", lambda prompt: "  27 queries vs 5 budget.  ")
    rca = ci_mod.diagnose_ci(42)
    assert rca == "27 queries vs 5 budget."


def test_diagnose_ci_unknown_mr_returns_none(monkeypatch):
    # generate should not be called for an unknown MR.
    monkeypatch.setattr(ci_mod, "generate", lambda prompt: pytest.fail("LLM called"))
    assert ci_mod.diagnose_ci(999) is None


def test_render_mr_note_groups_by_severity_and_includes_ci_section():
    review = MRReview(
        mr_id=42,
        commit="abc1234",
        findings=[
            Finding(file="a.py", line=10, category="security", severity=Severity.CRITICAL,
                    message="SQLi via string concat.", suggestion="Use parameterized query."),
            Finding(file="b.py", line=20, category="performance", severity=Severity.HIGH,
                    message="N+1 loop.", suggestion="Prefetch."),
        ],
        ci_root_cause="Pipeline test:checkout failed: 27 queries vs the 5-query budget.",
    )
    body = render_mr_note(review)
    assert "MR !42" in body
    assert "🔴 CRITICAL" in body and "🟠 HIGH" in body
    # Worst-first grouping: CRITICAL section precedes HIGH.
    assert body.index("🔴 CRITICAL") < body.index("🟠 HIGH")
    assert "## CI failure" in body
    assert "27 queries" in body


def test_render_mr_note_empty_findings():
    review = MRReview(mr_id=7, commit="c0ffee0", findings=[], ci_root_cause=None)
    body = render_mr_note(review)
    assert "No issues found" in body
    assert "## CI failure" not in body


def test_cycle_emits_signal_with_review_and_post_destination(monkeypatch, tmp_path):
    monkeypatch.setattr(review_mod, "generate_json", lambda *a, **k: _fake_review())
    monkeypatch.setattr(ci_mod, "generate", lambda prompt: "Failed: N+1 query budget breached.")
    monkeypatch.setattr("integrations.gitlab.simulator._OUT_DIR", tmp_path)

    sig = run_code_guardian_cycle("abc1234")
    assert sig.pillar == "code"
    assert sig.status == "warning"  # one HIGH finding
    assert "MR !42" in sig.headline
    assert sig.detail["posted_to"].endswith("mr_note_42.md")
    posted = (tmp_path / "mr_note_42.md").read_text(encoding="utf-8")
    assert "🟠 HIGH" in posted
    assert "## CI failure" in posted


def test_cycle_critical_finding_blocks(monkeypatch, tmp_path):
    crit = MRReview(
        mr_id=42,
        commit="abc1234",
        findings=[Finding(file="x.py", line=1, category="security",
                          severity=Severity.CRITICAL, message="!", suggestion=None)],
        ci_root_cause=None,
    )
    monkeypatch.setattr(review_mod, "generate_json", lambda *a, **k: crit)
    def _no_llm(prompt):
        pytest.fail("CI shouldn't run if no failure")

    monkeypatch.setattr(ci_mod, "generate", _no_llm)
    # Force the sim to return success so ci.diagnose_ci returns None.
    monkeypatch.setattr(
        "integrations.gitlab.simulator.GitLabSimulator.get_pipeline_logs",
        lambda self, mr_id: {"mr_id": mr_id, "status": "success", "logs": ""},
    )
    monkeypatch.setattr("integrations.gitlab.simulator._OUT_DIR", tmp_path)

    sig = run_code_guardian_cycle("abc1234")
    assert sig.status == "critical"


def test_sub_agent_builds_in_sim():
    agent = build_code_guardian()
    assert agent.name == "code_guardian"
    assert len(agent.tools) == 3  # review_mr + diagnose_ci + post_review
