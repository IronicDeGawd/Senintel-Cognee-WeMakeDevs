"""P2-3: incident KB (JSON shim) + embedding similarity. All offline — sim
embeddings are deterministic, so no network and no API spend."""

from shared.models import Incident, Severity
from storage.embeddings import cosine, embed
from storage.incident_kb import JsonFileKB


def _incident(title: str, service: str = "checkout-service", cause: str = "N+1 query") -> Incident:
    return Incident(
        title=title,
        severity=Severity.HIGH,
        service=service,
        summary="Checkout p95 latency ~13x baseline after deploy.",
        suspected_cause=cause,
        suspect_commit=None,
        next_action="Roll back the checkout-service deploy.",
    )


def test_sim_embed_is_deterministic_and_normalized():
    a = embed("checkout latency spike n+1 query")
    b = embed("checkout latency spike n+1 query")
    assert a == b
    assert abs(sum(x * x for x in a) - 1.0) < 1e-9  # L2 normalized
    assert cosine(a, b) > 0.999


def test_cosine_higher_for_related_text():
    base = embed("checkout service latency spike caused by n+1 query in deploy")
    near = embed("checkout latency spike from an n+1 query")
    far = embed("payment gateway timeout unrelated network outage")
    assert cosine(base, near) > cosine(base, far)


def test_kb_save_and_recent_roundtrip(tmp_path):
    kb = JsonFileKB(path=tmp_path / "kb.json")
    kb.save(_incident("Checkout latency spike"))
    kb.save(_incident("Checkout DB pool saturation", cause="connection pool exhausted"))
    recent = kb.recent("checkout-service")
    assert len(recent) == 2
    assert recent[0].title == "Checkout DB pool saturation"  # newest first


def test_recent_filters_by_service(tmp_path):
    kb = JsonFileKB(path=tmp_path / "kb.json")
    kb.save(_incident("Checkout latency spike", service="checkout-service"))
    kb.save(_incident("Cart errors", service="cart-service"))
    assert len(kb.recent("checkout-service")) == 1
    assert kb.recent("checkout-service")[0].service == "checkout-service"


def test_similar_finds_prior_incident(tmp_path):
    kb = JsonFileKB(path=tmp_path / "kb.json")
    kb.save(_incident("Checkout latency spike from N+1 query"))
    match = kb.similar(_incident("Checkout latency spike caused by N+1 query"))
    assert match is not None
    assert match.score >= 0.55
    assert "Checkout latency" in match.incident.title


def test_similar_returns_none_below_threshold(tmp_path):
    kb = JsonFileKB(path=tmp_path / "kb.json")
    kb.save(_incident("Checkout latency spike from N+1 query"))
    # Same service, totally different symptom text -> below threshold.
    other = _incident(
        "TLS certificate expired on edge proxy",
        cause="expired certificate blocked all inbound https",
    )
    assert kb.similar(other) is None
