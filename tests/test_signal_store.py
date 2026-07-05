"""D1: cross-pillar Signal store (JSON shim).

Offline-only — sim writes go to a tmp_path JSON file, real (Firestore) is the
lazy import path and is exercised by integration smoke against a live tenant."""

from datetime import datetime, timezone, timedelta

from shared.models import Signal
from storage.signal_store import (
    JsonFileSignalStore,
    get_signal_store,
    save_signal,
)


def _signal(
    pillar: str,
    *,
    status: str = "warning",
    headline: str = "test",
    minutes_ago: int = 0,
) -> Signal:
    return Signal(
        pillar=pillar,
        status=status,
        headline=headline,
        detail={"k": "v"},
        ts=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
    )


def test_save_and_recent_roundtrip(tmp_path):
    store = JsonFileSignalStore(path=tmp_path / "signals.json")
    id1 = store.save(_signal("production", minutes_ago=2))
    id2 = store.save(_signal("code", minutes_ago=1))
    id3 = store.save(_signal("ai_quality", minutes_ago=0))
    assert id1 and id2 and id3 and len({id1, id2, id3}) == 3

    recent = store.recent(limit=10)
    assert len(recent) == 3
    # Newest first.
    assert [s.pillar for s in recent] == ["ai_quality", "code", "production"]


def test_recent_filters_by_pillar(tmp_path):
    store = JsonFileSignalStore(path=tmp_path / "signals.json")
    store.save(_signal("production", headline="p1", minutes_ago=3))
    store.save(_signal("code", headline="c1", minutes_ago=2))
    store.save(_signal("production", headline="p2", minutes_ago=1))

    prod = store.recent(pillar="production")
    assert [s.headline for s in prod] == ["p2", "p1"]
    assert all(s.pillar == "production" for s in prod)


def test_latest_per_pillar_returns_newest_per_key(tmp_path):
    store = JsonFileSignalStore(path=tmp_path / "signals.json")
    # Older production signal first, then a newer one. latest_per_pillar
    # must pick the newer one and ignore the older one.
    store.save(_signal("production", headline="old", minutes_ago=5))
    store.save(_signal("code", headline="c", minutes_ago=4))
    store.save(_signal("production", headline="new", minutes_ago=1))

    latest = store.latest_per_pillar()
    assert set(latest.keys()) == {"production", "code"}
    assert latest["production"].headline == "new"
    assert latest["code"].headline == "c"


def test_factory_returns_json_in_sim_mode(tmp_path, monkeypatch):
    # Make absolutely sure the default path lookup ends up under tmp_path,
    # so the test can't accidentally write into the repo's out/ tree.
    monkeypatch.setattr(
        "storage.signal_store.settings.signal_store_path",
        str(tmp_path / "signals.json"),
    )
    store = get_signal_store()
    assert store.name == "json"
    assert isinstance(store, JsonFileSignalStore)


def test_save_signal_helper_is_resilient(tmp_path, monkeypatch):
    # Happy path uses the sim store.
    monkeypatch.setattr(
        "storage.signal_store.settings.signal_store_path",
        str(tmp_path / "signals.json"),
    )
    out_id = save_signal(_signal("production"))
    assert out_id  # non-empty id on success

    # If the store factory raises, save_signal must swallow and return "" —
    # the upstream cycle's Signal is the dashboard contract, a flaky store
    # must not crash the pillar.
    def _boom(*_a, **_k):
        raise RuntimeError("store unavailable")

    monkeypatch.setattr("storage.signal_store.get_signal_store", _boom)
    assert save_signal(_signal("code")) == ""
