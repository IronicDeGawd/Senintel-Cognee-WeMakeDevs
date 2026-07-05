"""Mode switch for the Dynatrace adapter. `get()` returns the simulator or the
real MCP client based on SENTINEL_DT_MODE (settings.dt_mode). real.py is
imported lazily so sim-mode dev needs neither creds nor npx."""

from __future__ import annotations

from integrations.base import build_integration
from shared.config import Mode, settings

from .interface import DynatraceIntegration
from .simulator import DynatraceSimulator


def _real() -> DynatraceIntegration:
    from .real import DynatraceReal

    return DynatraceReal()


def get(mode: Mode | None = None) -> DynatraceIntegration:
    return build_integration(mode or settings.dt_mode, DynatraceSimulator, _real)
