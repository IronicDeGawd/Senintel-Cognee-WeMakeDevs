"""Cognee Cloud adapter — the demo memory backend (memory_mode=real).

The codebase is synchronous but Cognee's SDK is async, so each method bridges
with `asyncio.run(...)`. `cognee` is imported lazily inside the methods (after
_configure sets the env) so the sim/test path never needs the SDK installed.

API used (docs.cognee.ai):
  - remember(data, dataset_name=...) -> RememberResult
  - recall(query_text=..., top_k=..., datasets=[...], only_context=True) -> [result]
    where each result exposes `.text` (attribute access, not dict).
Auth: COGNEE_API_KEY (+ optional COGNEE_SERVICE_URL). LLM: LLM_PROVIDER/LLM_MODEL/
LLM_API_KEY — pointed at Gemini from settings.
improve()/forget() are best-effort (getattr) so a signature drift can't crash a demo.
"""

from __future__ import annotations

import asyncio
import json
import os

from shared.config import settings
from shared.logging import get_logger
from shared.models import MemoryItem, Severity

from .interface import CogneeIntegration

log = get_logger(__name__)


def _configure() -> None:
    """Push credentials + LLM/embedding choice into the env Cognee reads. setdefault
    so an already-exported value (e.g. a real .env) always wins.

    Cognee (via LiteLLM) needs BOTH an LLM and an embedder. It defaults the embedder
    to OpenAI even with a Gemini LLM, so we set both explicitly.

    Two LLM paths:
      1. GEMINI_API_KEY set -> Gemini via AI Studio (simplest).
      2. else Vertex AI via gcloud ADC (no API key) -> LiteLLM vertex_ai/ provider,
         using GOOGLE_CLOUD_PROJECT/LOCATION + Application Default Credentials.
    """
    if settings.cognee_api_key:
        os.environ.setdefault("COGNEE_API_KEY", settings.cognee_api_key)
    if settings.cognee_service_url:
        os.environ.setdefault("COGNEE_SERVICE_URL", settings.cognee_service_url)

    if settings.gemini_api_key:
        # Path 1: Gemini AI Studio key.
        os.environ.setdefault("LLM_PROVIDER", "gemini")
        os.environ.setdefault("LLM_MODEL", f"gemini/{settings.gemini_model}")
        os.environ.setdefault("LLM_API_KEY", settings.gemini_api_key)
        os.environ.setdefault("EMBEDDING_PROVIDER", "gemini")
        os.environ.setdefault("EMBEDDING_MODEL", "gemini/text-embedding-004")
        os.environ.setdefault("EMBEDDING_API_KEY", settings.gemini_api_key)
        os.environ.setdefault("EMBEDDING_DIMENSIONS", "768")
    elif settings.google_cloud_project:
        # Path 2: Vertex AI via gcloud ADC. LiteLLM reads VERTEXAI_* + ADC creds.
        os.environ.setdefault("VERTEXAI_PROJECT", settings.google_cloud_project)
        os.environ.setdefault("VERTEXAI_LOCATION", settings.google_cloud_location)
        os.environ.setdefault("LLM_PROVIDER", "custom")
        os.environ.setdefault("LLM_MODEL", f"vertex_ai/{settings.gemini_model}")
        # Cognee's config often requires a non-empty LLM_API_KEY; Vertex ignores it.
        os.environ.setdefault("LLM_API_KEY", "vertex-adc")
        os.environ.setdefault("EMBEDDING_PROVIDER", "custom")
        os.environ.setdefault("EMBEDDING_MODEL", f"vertex_ai/{settings.embedding_model}")
        os.environ.setdefault("EMBEDDING_API_KEY", "vertex-adc")
        os.environ.setdefault("EMBEDDING_DIMENSIONS", "768")


def _item_text(item: MemoryItem) -> str:
    """Flatten a MemoryItem so Cognee ingests it. We use JSON so the dashboard
    can recover the structured fields (timestamps, rules, etc) perfectly."""
    return item.model_dump_json()


class CogneeReal(CogneeIntegration):
    name = "cognee"

    def __init__(self) -> None:
        _configure()
        self._dataset = settings.cognee_dataset

    def healthcheck(self) -> bool:
        try:
            import cognee  # noqa: F401
        except Exception:
            log.exception("cognee SDK not importable")
            return False
        return True

    def remember(self, item: MemoryItem) -> str:
        async def _run() -> str:
            import cognee

            result = await cognee.remember(_item_text(item), dataset_name=self._dataset)
            return str(getattr(result, "dataset_id", None) or item.id)

        return asyncio.run(_run())

    def recall(self, query: str, limit: int = 5) -> list[MemoryItem]:
        async def _run() -> list:
            import cognee

            results = await cognee.recall(
                query_text=query,
                top_k=limit,
                datasets=[self._dataset],
                only_context=True,
            )
            return list(results or [])

        raw = asyncio.run(_run())
        items: list[MemoryItem] = []
        for r in raw:
            text = getattr(r, "text", None)
            if not text:
                continue  # skip empty graph-completion results
            try:
                data = json.loads(text)
                items.append(MemoryItem(**data))
            except Exception:
                # Fallback if the data was seeded as plain text instead of JSON
                items.append(
                    MemoryItem(
                        repo=self._dataset,
                        file=None,
                        rule="Recalled Context",
                        comment=text,
                        severity=Severity.INFO,
                        source="review",
                        commit="",
                    )
                )
        return items

    def improve(self) -> None:
        async def _run() -> None:
            import cognee

            fn = getattr(cognee, "cognify", None)
            if fn is not None:
                await fn()

        try:
            asyncio.run(_run())
        except Exception:
            log.exception("cognee improve/cognify failed (non-fatal)")

    def forget(self, dataset: str | None = None) -> None:
        target = dataset or self._dataset

        async def _run() -> None:
            import cognee

            forget_fn = getattr(cognee, "forget", None)
            if forget_fn is not None:
                await forget_fn(dataset_name=target)
                return
            prune = getattr(cognee, "prune", None)
            if prune is not None and hasattr(prune, "prune_data"):
                await prune.prune_data()

        try:
            asyncio.run(_run())
        except Exception:
            log.exception("cognee forget failed (non-fatal)")
