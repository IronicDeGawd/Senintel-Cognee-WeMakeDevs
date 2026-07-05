"""Mode switch for the Arize/Phoenix adapter. `get()` returns the simulator or
the real Phoenix MCP client based on SENTINEL_ARIZE_MODE (settings.arize_mode).
real.py is imported lazily so sim-mode dev needs neither creds nor npx."""

from __future__ import annotations

from integrations.base import build_integration
from shared.config import Mode, settings

from .interface import ArizeIntegration
from .simulator import ArizeSimulator


def _real() -> ArizeIntegration:
    # real.py is built in a separate workstream (Phoenix adapter, plan 05). Until
    # it lands, flipping to real mode fails with a clear, actionable message
    # instead of a raw ImportError from the missing module.
    try:
        from .real import ArizeReal
    except ImportError as exc:
        raise NotImplementedError(
            "SENTINEL_ARIZE_MODE=real needs integrations/arize/real.py (ArizeReal), "
            "which is not implemented yet. Use SENTINEL_ARIZE_MODE=sim, or build the "
            "Phoenix adapter per context/plan/features/05-real-partner-integrations.md."
        ) from exc

    return ArizeReal()


def get(mode: Mode | None = None) -> ArizeIntegration:
    return build_integration(mode or settings.arize_mode, ArizeSimulator, _real)
