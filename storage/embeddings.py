"""Text embeddings + cosine similarity for the incident KB "have we seen this
before?" check.

Two backends, picked by `settings.kb_mode`:
- sim  : deterministic feature-hashing embedding — offline, free, repeatable.
         Overlapping words -> high cosine, so "same incident" still scores high
         in a demo without spending a single API call.
- real : Vertex AI text embeddings (settings.embedding_model).

Think of an embedding as turning a sentence into a point in space; two sentences
that mean similar things land close together, so "closeness" = "similarity".
"""

from __future__ import annotations

import hashlib
import math
import re

from shared.config import settings
from shared.logging import get_logger

log = get_logger(__name__)

_SIM_DIM = 256
_TOKEN = re.compile(r"[a-z0-9]+")


def _sim_embed(text: str) -> list[float]:
    """Feature-hashing embedding: bucket each word into a fixed-size vector, then
    L2-normalize. No model, no network — same text always yields the same vector."""
    vec = [0.0] * _SIM_DIM
    for tok in _TOKEN.findall(text.lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % _SIM_DIM] += 1.0
    return _normalize(vec)


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def _real_embed(text: str) -> list[float]:
    """Vertex AI text embedding via the shared genai client (ADC auth)."""
    from shared.llm import _get_client  # lazy: avoid client construction in sim

    client = _get_client()
    resp = client.models.embed_content(model=settings.embedding_model, contents=text)
    embeddings = resp.embeddings or []
    if not embeddings:
        raise RuntimeError(f"Vertex returned no embedding for model {settings.embedding_model}")
    return list(embeddings[0].values)


def embed(text: str) -> list[float]:
    """Embed one text into a vector, using the backend selected by kb_mode."""
    if settings.kb_mode == "real":
        return _real_embed(text)
    return _sim_embed(text)


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity in [-1, 1]; 1.0 = identical direction."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def most_similar[T](
    query: list[float], candidates: list[tuple[T, list[float]]]
) -> tuple[T, float] | None:
    """Return the (item, score) whose stored vector is closest to `query`, or
    None if there are no candidates."""
    best: tuple[T, float] | None = None
    for item, vec in candidates:
        score = cosine(query, vec)
        if best is None or score > best[1]:
            best = (item, score)
    return best
