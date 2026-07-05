"""Offline simulator for the Cognee memory adapter.

Whole file is a JSON list of MemoryItem rows (out/team_memory.json). remember()
appends; recall() re-embeds the query + each stored item with the deterministic
local embedding (storage.embeddings) and returns the closest matches. No network,
no creds — this is the tests/CI backend, never the demo.
"""

from __future__ import annotations

import json
from pathlib import Path

from shared.config import settings
from shared.logging import get_logger
from shared.models import MemoryItem
from storage.embeddings import cosine, embed

from .interface import CogneeIntegration

log = get_logger(__name__)

_DEFAULT_PATH = Path(__file__).resolve().parent.parent.parent / "out" / "team_memory.json"


def _item_text(item: MemoryItem) -> str:
    """The text we embed for similarity — the learned rule, the note, the file."""
    return f"{item.rule}\n{item.comment}\n{item.file or ''}"


class CogneeSimulator(CogneeIntegration):
    """JSON-file shim mirroring storage.incident_kb.JsonFileKB."""

    name = "cognee"

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path or settings.memory_path or _DEFAULT_PATH)

    def healthcheck(self) -> bool:
        return True

    def _load(self) -> list[MemoryItem]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8") or "[]")
        return [MemoryItem.model_validate(r) for r in raw]

    def _write(self, items: list[MemoryItem]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [it.model_dump(mode="json") for it in items]
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def remember(self, item: MemoryItem) -> str:
        items = self._load()
        items.append(item)
        self._write(items)
        log.info("memory(sim) remembered %s (%s) for %s", item.id, item.rule, item.repo)
        return item.id

    def recall(self, query: str, limit: int = 5) -> list[MemoryItem]:
        items = self._load()
        if not items:
            return []
        q = embed(query)
        scored = [(it, cosine(q, embed(_item_text(it)))) for it in items]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [it for it, score in scored[:limit] if score > 0.0]

    def improve(self) -> None:
        # No-op offline: the deterministic embedding needs no re-indexing.
        return None

    def forget(self, dataset: str | None = None) -> None:
        # Sim ignores the dataset name and clears the whole shim.
        self._write([])
        log.info("memory(sim) forgot all items")
