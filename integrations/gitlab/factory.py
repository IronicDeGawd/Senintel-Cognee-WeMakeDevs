"""Mode switch for the GitLab adapter. `get()` returns the simulator or the real
MCP client based on SENTINEL_GL_MODE (settings.gl_mode). real.py is imported
lazily; until Dev B lands it, real mode raises on import (sim path unaffected).
"""

from __future__ import annotations

from integrations.base import build_integration
from shared.config import Mode, settings

from .interface import GitLabIntegration
from .simulator import GitLabSimulator


def _real() -> GitLabIntegration:
    from .real import GitLabReal

    return GitLabReal()


def get(mode: Mode | None = None) -> GitLabIntegration:
    return build_integration(mode or settings.gl_mode, GitLabSimulator, _real)
