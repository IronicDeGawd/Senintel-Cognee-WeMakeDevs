"""Structured-ish logging. One configured logger factory so every module logs
the same way (timestamp, level, name). Call get_logger(__name__).
"""

from __future__ import annotations

import logging
import os

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s | %(message)s"
_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format=_FORMAT)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger with shared formatting."""
    _configure()
    return logging.getLogger(name)
