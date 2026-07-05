"""THE ADAPTER CONTRACT. Every external integration (Dynatrace, GitLab, Arize)
sits behind this so pillars can run against a deterministic simulator today and
flip to a live MCP server later with no agent-code change.

Per-integration folder layout (built by each pillar, not here):
    integrations/<name>/
        interface.py   # abstract methods specific to that source
        simulator.py   # deterministic fixtures (the sim side)
        real.py        # MCP-backed implementation (the real side)
        factory.py     # get(mode) -> sim | real, via build_integration() below
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar

from shared.config import Mode


class Integration(ABC):
    """Base of every adapter. Subclasses add their own data methods, e.g.
    DynatraceIntegration.list_problems()."""

    name: str

    @abstractmethod
    def healthcheck(self) -> bool:
        """Return True if this adapter is reachable/usable right now."""
        ...


T = TypeVar("T", bound="Integration")
def build_integration(
    mode: Mode,
    sim_factory: Callable[[], T],
    real_factory: Callable[[], T],
) -> T:
    """Generic mode switch used by each pillar's factory.py.

    Example:
        def get(mode: Mode = settings.dt_mode) -> DynatraceIntegration:
            return build_integration(mode, DynatraceSimulator, DynatraceReal)
    """
    return real_factory() if mode == "real" else sim_factory()
