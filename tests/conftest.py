"""Pytest setup. Force every pillar into sim mode so tests are deterministic and
need no external credentials. Set before any project module imports settings.
"""

import os

import pytest

os.environ.setdefault("SENTINEL_DT_MODE", "sim")
os.environ.setdefault("SENTINEL_GL_MODE", "sim")
os.environ.setdefault("SENTINEL_ARIZE_MODE", "sim")
os.environ.setdefault("SENTINEL_KB_MODE", "sim")
# A dummy key keeps import-time client construction happy without hitting network.
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-used")


@pytest.fixture(autouse=True)
def _reset_llm_client():
    """The Gemini client is cached in a module global. Reset it around each test
    so a test that mutates settings can't leak a stale client into the next."""
    import shared.llm as _llm

    _llm._client = None
    yield
    _llm._client = None
