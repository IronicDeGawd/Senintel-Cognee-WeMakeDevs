"""WeMakeDevs: team code-review memory (Cognee sim backend + glue). All offline —
memory_mode defaults to sim and sim embeddings are deterministic, so no network
and no API spend.
"""

from integrations.cognee.factory import get as get_cognee
from integrations.cognee.simulator import CogneeSimulator
from shared.config import settings
from shared.models import Finding, MemoryItem, MRReview, Severity

from agents.sentinel.pillars.code_guardian.memory import recall_context, remember_review


def _item(rule: str, comment: str, file: str | None = "app/serializers.py") -> MemoryItem:
    return MemoryItem(
        repo="sentinel",
        file=file,
        rule=rule,
        comment=comment,
        severity=Severity.HIGH,
        source="review",
        commit="abc1234",
    )


def _diff() -> dict:
    return {
        "service": "checkout-service",
        "files_changed": ["app/serializers.py"],
        "diff": "+ for item in items:\n+     item.owner.name  # a query per item",
    }


# --- simulator backend -----------------------------------------------------


def test_remember_recall_roundtrip(tmp_path):
    mem = CogneeSimulator(path=tmp_path / "mem.json")
    mem.remember(_item("n+1-query", "Loop issues a query per item; use select_related."))
    mem.remember(_item("naming", "Constants should be UPPER_SNAKE_CASE.", file="app/const.py"))
    hits = mem.recall("serializers n+1 query per item")
    assert hits, "expected a recall hit for the n+1 query"
    assert hits[0].rule == "n+1-query"  # most relevant first


def test_recall_empty_when_no_memory(tmp_path):
    mem = CogneeSimulator(path=tmp_path / "mem.json")
    assert mem.recall("anything at all") == []


def test_forget_clears_memory(tmp_path):
    mem = CogneeSimulator(path=tmp_path / "mem.json")
    mem.remember(_item("n+1-query", "Use select_related to avoid N+1."))
    assert mem.recall("n+1 query") != []
    mem.forget()
    assert mem.recall("n+1 query") == []


def test_improve_is_noop(tmp_path):
    mem = CogneeSimulator(path=tmp_path / "mem.json")
    mem.improve()  # must not raise


# --- glue over the mode-selected backend -----------------------------------


def test_recall_context_formats_block(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "memory_path", str(tmp_path / "mem.json"))
    get_cognee().remember(_item("n+1-query", "Use select_related to avoid N+1."))
    block = recall_context(_diff())
    assert "TEAM MEMORY" in block
    assert "n+1-query" in block


def test_recall_context_empty_when_no_memory(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "memory_path", str(tmp_path / "mem.json"))
    assert recall_context(_diff()) == ""


def test_remember_review_stores_findings_for_next_recall(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "memory_path", str(tmp_path / "mem.json"))
    review = MRReview(
        mr_id=1,
        commit="abc1234",
        findings=[
            Finding(
                file="app/serializers.py",
                category="n+1-query",
                severity=Severity.HIGH,
                message="Loop issues a query per item; use select_related.",
            )
        ],
    )
    remember_review(review)
    hits = get_cognee().recall("serializers n+1 query per item")
    assert any(it.rule == "n+1-query" for it in hits)
    assert hits[0].source == "review"
