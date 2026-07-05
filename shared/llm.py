"""Gemini call wrapper with retry/backoff. ALL pillars call this, never the raw
client — the spike hit Gemini 503 "high demand" under load, so every model call
must survive a transient overload.

Think of it as a phone line that's sometimes busy: we redial a few times with a
growing pause instead of giving up on the first busy signal.

Auth: default path is Vertex AI with Application Default Credentials (run
`gcloud auth application-default login` once). No API key in code or .env. Set
GOOGLE_GENAI_USE_VERTEXAI=false + GEMINI_API_KEY to fall back to AI Studio.
"""

from __future__ import annotations

from google import genai
from google.genai import errors, types
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from shared.config import settings
from shared.logging import get_logger

log = get_logger(__name__)

_client: genai.Client | None = None

# HTTP statuses worth retrying: 503 overloaded, 429 rate-limited, 500/502/504.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, errors.APIError):
        return getattr(exc, "code", None) in _RETRYABLE_STATUS
    return False


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if settings.google_genai_use_vertexai:
            # Vertex AI backend; auth via Application Default Credentials.
            _client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project or None,
                location=settings.google_cloud_location,
            )
        else:
            if not settings.gemini_api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY not set and Vertex disabled — either run "
                    "`gcloud auth application-default login` with "
                    "GOOGLE_GENAI_USE_VERTEXAI=true, or set GEMINI_API_KEY."
                )
            _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    reraise=True,
)
def generate(prompt: str, model: str | None = None) -> str:
    """One-shot Gemini generation, retrying transient overload/rate-limit errors.

    Args:
        prompt: the user/instruction text.
        model: override the configured model (defaults to settings.gemini_model).

    Returns:
        The model's text response.
    """
    client = _get_client()
    target = model or settings.gemini_model
    resp = client.models.generate_content(
        model=target,
        contents=prompt,
        config=types.GenerateContentConfig(),
    )
    text = resp.text or ""
    if not text:
        log.warning("Gemini returned empty text (model=%s)", target)
    return text


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    reraise=True,
)
def generate_json[T: BaseModel](prompt: str, schema: type[T], model: str | None = None) -> T:
    """Structured Gemini generation: returns an instance of `schema` (a pydantic
    model). Uses Gemini's JSON mode + response_schema so the output is parsed and
    validated, not free text. Same retry policy as generate().

    Args:
        prompt: the instruction text.
        schema: a pydantic model class describing the desired output shape.
        model: override the configured model.

    Returns:
        A validated instance of `schema`.
    """
    client = _get_client()
    target = model or settings.gemini_model
    resp = client.models.generate_content(
        model=target,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, schema):
        return parsed
    # Fallback: validate the raw JSON text ourselves.
    return schema.model_validate_json(resp.text or "{}")
