"""Cross-pillar Signal store: every pillar's cycle appends its emitted Signal
here so the dashboard can render three things off one source:

  - latest_per_pillar()  -> {production, code, ai_quality}: the most recent doc
  - recent(limit, pillar) -> a flat timeline newest-first, optionally filtered
  - save_signal(sig)     -> append, server-assigned id

Two backends behind one interface (picked by `settings.signal_store_mode`):
- sim  : JSON-file shim (out/signals.json) — no GCP, local dev never blocked.
- real : Firestore collection (settings.firestore_signals_collection).

Mirrors the shape of `storage/incident_kb.py` (same factory pattern, same lazy
Firestore client) so the dashboard_api can treat both stores symmetrically.
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field

from shared.config import settings
from shared.logging import get_logger
from shared.models import Signal

log = get_logger(__name__)

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "out" / "signals.json"


class StoredSignal(BaseModel):
    """One Signal stream row: the Signal plus a stable id for the dashboard."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    signal: Signal


Pillar = str  # "production" | "code" | "ai_quality" — keep loose so future
# pillars can be added without a contract change.


class SignalStore(ABC):
    """Common interface. Backends implement persistence; ordering is shared."""

    name: str

    @abstractmethod
    def save(self, signal: Signal) -> str:
        """Persist a Signal; return its store id."""

    @abstractmethod
    def recent(self, limit: int = 20, pillar: Pillar | None = None) -> list[Signal]:
        """Most-recent Signals, newest first. Optionally filter to one pillar."""

    def latest_per_pillar(self) -> dict[Pillar, Signal]:
        """Latest Signal for each known pillar. Pillars with no row are absent."""
        out: dict[Pillar, Signal] = {}
        # A bounded scan is fine for the demo + free Firestore tier; revisit if
        # the collection grows beyond a few hundred docs.
        for sig in self.recent(limit=200):
            if sig.pillar not in out:
                out[sig.pillar] = sig
        return out


class JsonFileSignalStore(SignalStore):
    """JSON-file shim. Whole file is a list of StoredSignal rows."""

    name = "json"

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path or settings.signal_store_path or _DEFAULT_PATH)

    def _load(self) -> list[StoredSignal]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8") or "[]")
        return [StoredSignal.model_validate(r) for r in raw]

    def _write(self, rows: list[StoredSignal]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [r.model_dump(mode="json") for r in rows]
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def save(self, signal: Signal) -> str:
        rows = self._load()
        record = StoredSignal(signal=signal)
        rows.append(record)
        self._write(rows)
        log.info("signal-store(json) saved %s for %s", record.id, signal.pillar)
        return record.id

    def recent(self, limit: int = 20, pillar: Pillar | None = None) -> list[Signal]:
        rows = self._load()
        if pillar:
            rows = [r for r in rows if r.signal.pillar == pillar]
        rows.sort(key=lambda r: r.signal.ts, reverse=True)
        return [r.signal for r in rows[:limit]]


class FirestoreSignalStore(SignalStore):
    """Firestore-backed store. Lazy client so sim never touches GCP."""

    name = "firestore"

    def __init__(self) -> None:
        from google.cloud import firestore  # lazy: only when signal_store_mode=real

        self._db = firestore.Client(project=settings.google_cloud_project or None)
        self._col = self._db.collection(settings.firestore_signals_collection)

    def save(self, signal: Signal) -> str:
        record = StoredSignal(signal=signal)
        self._col.document(record.id).set(record.model_dump(mode="json"))
        log.info("signal-store(firestore) saved %s for %s", record.id, signal.pillar)
        return record.id

    def recent(self, limit: int = 20, pillar: Pillar | None = None) -> list[Signal]:
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = self._col
        if pillar:
            query = query.where(filter=FieldFilter("signal.pillar", "==", pillar))
        # Firestore needs an explicit composite index when filter+order_by hit
        # different fields. The /history endpoint will surface the one-click
        # index link on first call.
        docs = query.order_by("signal.ts", direction="DESCENDING").limit(limit).stream()
        return [StoredSignal.model_validate(d.to_dict()).signal for d in docs]


def get_signal_store(mode: str | None = None) -> SignalStore:
    """Factory: JSON shim (sim) or Firestore (real), by mode."""
    chosen = mode or settings.signal_store_mode
    if chosen == "real":
        return FirestoreSignalStore()
    return JsonFileSignalStore()


def save_signal(signal: Signal) -> str:
    """Cycle entry point: append the emitted Signal to the configured store.

    Best-effort: a store failure must not erase the upstream cycle's work. The
    Signal is the dashboard contract; a missed write costs one timeline row,
    not the whole pillar run.
    """
    try:
        return get_signal_store().save(signal)
    except Exception:
        log.exception("save_signal failed; continuing without store write")
        return ""
