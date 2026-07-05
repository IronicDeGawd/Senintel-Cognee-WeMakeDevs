"""P3-4: eval trend store (sim JSON shim). Offline — no GCP."""

from agents.sentinel.pillars.ai_quality_gate.gate import run_gate
from storage.eval_trends import JsonFileTrends, get_trends


def _result(suite: str):
    # run_gate(...).detail is the EvalResult payload; rebuild via the sim adapter.
    from integrations.arize.factory import get

    return get("sim").run_eval(suite, [])


def test_factory_sim_returns_json_backend():
    assert isinstance(get_trends("sim"), JsonFileTrends)


def test_append_then_recent_roundtrip(tmp_path):
    store = JsonFileTrends(path=tmp_path / "trends.json")
    store.append(_result("checkout-llm-v1"))
    store.append(_result("checkout-llm-v2"))
    rows = store.recent()
    assert len(rows) == 2
    assert {r["suite"] for r in rows} == {"checkout-llm-v1", "checkout-llm-v2"}
    assert all("ts" in r and "hallucination_rate" in r for r in rows)


def test_recent_filters_by_suite(tmp_path):
    store = JsonFileTrends(path=tmp_path / "trends.json")
    store.append(_result("checkout-llm-v1"))
    store.append(_result("checkout-llm-v2"))
    rows = store.recent(suite="checkout-llm-v2")
    assert len(rows) == 1
    assert rows[0]["suite"] == "checkout-llm-v2"
    assert rows[0]["passed"] is False


def test_empty_store_returns_no_rows(tmp_path):
    store = JsonFileTrends(path=tmp_path / "trends.json")
    assert store.recent() == []


def test_run_gate_result_is_recordable(tmp_path):
    # The same Signal payload the eval-runner records should round-trip.
    sig = run_gate("checkout-llm-v2", mode="sim")
    assert sig.detail["suite"] == "checkout-llm-v2"
