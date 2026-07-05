"""Incident knowledge base: remember past incidents so the briefing can say
"we've seen this before" instead of treating every anomaly as brand new.

Two backends behind one interface (picked by `settings.kb_mode`):
- sim  : JSON-file shim (out/incident_kb.json) — no GCP, Dev A never blocked.
- real : Firestore collection (settings.firestore_collection).

Each stored record keeps the Incident plus an embedding of its text, so the
`similar()` lookup is a cheap cosine compare against recent records.
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from shared.config import settings
from shared.logging import get_logger
from shared.models import Incident
from storage.embeddings import embed, most_similar

log = get_logger(__name__)

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "out" / "incident_kb.json"


def _incident_text(inc: Incident) -> str:
    """The text we embed for similarity — title + symptom + cause."""
    return f"{inc.title}\n{inc.summary}\n{inc.suspected_cause}"


class StoredIncident(BaseModel):
    """One KB row: the Incident plus bookkeeping for ordering and similarity."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    incident: Incident
    embedding: list[float]


class SimilarMatch(BaseModel):
    """Result of a similarity lookup against the KB."""

    incident: Incident
    score: float
    incident_id: str


class IncidentKB(ABC):
    """Common interface. Backends implement persistence; similarity is shared."""

    name: str

    @abstractmethod
    def save(self, incident: Incident) -> str:
        """Persist an incident (embedding computed here). Returns its KB id."""

    @abstractmethod
    def recent(self, service: str, limit: int = 20) -> list[Incident]:
        """Most-recent incidents for a service, newest first."""

    @abstractmethod
    def _recent_records(self, service: str, limit: int = 20) -> list[StoredIncident]:
        """Internal: recent rows with embeddings, for the similarity compare."""

    def similar(self, incident: Incident, min_score: float = 0.55) -> SimilarMatch | None:
        """Closest prior incident on the same service, or None below threshold."""
        records = self._recent_records(incident.service)
        if not records:
            return None
        query = embed(_incident_text(incident))
        match = most_similar(query, [(r, r.embedding) for r in records])
        if match is None or match[1] < min_score:
            return None
        rec, score = match
        return SimilarMatch(incident=rec.incident, score=score, incident_id=rec.id)


class JsonFileKB(IncidentKB):
    """JSON-file shim. Whole file is a list of StoredIncident rows."""

    name = "json"

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path or settings.kb_path or _DEFAULT_PATH)

    def _load(self) -> list[StoredIncident]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8") or "[]")
        return [StoredIncident.model_validate(r) for r in raw]

    def _write(self, rows: list[StoredIncident]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [r.model_dump(mode="json") for r in rows]
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def save(self, incident: Incident) -> str:
        rows = self._load()
        record = StoredIncident(incident=incident, embedding=embed(_incident_text(incident)))
        rows.append(record)
        self._write(rows)
        log.info("KB(json) saved incident %s for %s", record.id, incident.service)
        return record.id

    def _recent_records(self, service: str, limit: int = 20) -> list[StoredIncident]:
        rows = [r for r in self._load() if r.incident.service == service]
        rows.sort(key=lambda r: r.ts, reverse=True)
        return rows[:limit]

    def recent(self, service: str, limit: int = 20) -> list[Incident]:
        return [r.incident for r in self._recent_records(service, limit)]


class FirestoreKB(IncidentKB):
    """Firestore-backed KB. Lazy client so sim never touches GCP."""

    name = "firestore"

    def __init__(self) -> None:
        from google.cloud import firestore  # lazy: only when kb_mode=real

        self._db = firestore.Client(project=settings.google_cloud_project or None)
        self._col = self._db.collection(settings.firestore_collection)

    def save(self, incident: Incident) -> str:
        record = StoredIncident(incident=incident, embedding=embed(_incident_text(incident)))
        self._col.document(record.id).set(record.model_dump(mode="json"))
        log.info("KB(firestore) saved incident %s for %s", record.id, incident.service)
        return record.id

    def _recent_records(self, service: str, limit: int = 20) -> list[StoredIncident]:
        from google.cloud.firestore_v1.base_query import FieldFilter

        docs = (
            self._col.where(filter=FieldFilter("incident.service", "==", service))
            .order_by("ts", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [StoredIncident.model_validate(d.to_dict()) for d in docs]

    def recent(self, service: str, limit: int = 20) -> list[Incident]:
        return [r.incident for r in self._recent_records(service, limit)]


def get_kb(mode: str | None = None) -> IncidentKB:
    """Factory: JSON shim (sim) or Firestore (real), by mode."""
    chosen = mode or settings.kb_mode
    if chosen == "real":
        return FirestoreKB()
    return JsonFileKB()
