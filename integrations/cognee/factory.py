"""Mode switch for the Cognee memory adapter. `get()` returns the offline JSON
simulator or the Cognee Cloud client based on SENTINEL_MEMORY_MODE
(settings.memory_mode). real.py is imported lazily so the sim/test path never
needs the cognee SDK installed.
"""

from __future__ import annotations

from integrations.base import build_integration
from shared.config import Mode, settings

from .interface import CogneeIntegration
from .simulator import CogneeSimulator


def _real() -> CogneeIntegration:
    from .real import CogneeReal

    return CogneeReal()


def get(mode: Mode | None = None) -> CogneeIntegration:
    return build_integration(mode or settings.memory_mode, CogneeSimulator, _real)
