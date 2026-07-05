"""Cognee adapter contract — the team's code-review memory.

Vasu (Python/AI) owns the whole Cognee integration. Four lifecycle operations,
mirroring Cognee's memory-native API so the demo shows full depth:
  - remember(item): store one review finding / post-merge bug (on merge).
  - recall(query, limit): pull the most relevant past memory for a new PR diff.
  - improve(): reinforce/re-index memory over time (Cognee memify).
  - forget(dataset): surgically drop a dataset (a retracted convention).

Sim<->real share this shape: the simulator is an offline JSON + local-embedding
store for tests; the real side is Cognee Cloud.
"""

from __future__ import annotations

from abc import abstractmethod

from integrations.base import Integration
from shared.models import MemoryItem


class CogneeIntegration(Integration):
    name = "cognee"

    @abstractmethod
    def remember(self, item: MemoryItem) -> str:
        """Persist one memory item. Returns its stored id."""
        ...

    @abstractmethod
    def recall(self, query: str, limit: int = 5) -> list[MemoryItem]:
        """Return the most relevant past memory items for a query (e.g. a diff).

        Ordered most-relevant first; may be empty when nothing matches.
        """
        ...

    @abstractmethod
    def improve(self) -> None:
        """Reinforce / re-index memory (Cognee memify). No-op on the simulator."""
        ...

    @abstractmethod
    def forget(self, dataset: str | None = None) -> None:
        """Surgically delete a dataset's memory (defaults to the active dataset)."""
        ...
