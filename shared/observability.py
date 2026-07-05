"""Self-observability: ship the agent's own OTel traces to Dynatrace, so
SentinelAI watches itself in the same platform it guards (the track's
self-observability story).

Think of it as the agent wearing a body-cam: every ADK step (model call, tool
call) becomes a span streamed to Dynatrace. Turned OFF by default — a no-op
unless BOTH DT_OTLP_ENDPOINT and DT_API_TOKEN are set, so offline/sim dev and
the test suite stay free and network-free.

Auth differs from the MCP path: OTLP ingest uses a classic Api-Token (dt0c01.)
with the openTelemetryTrace.ingest scope, posted to the .live host's
/api/v2/otlp endpoint — NOT the dt0s16 platform token the MCP server wants.
"""

from __future__ import annotations

import threading

from shared.config import settings
from shared.logging import get_logger

log = get_logger(__name__)

_initialized = False
_lock = threading.Lock()


def traces_url(endpoint: str) -> str:
    """Normalize a Dynatrace OTLP base URL to the traces signal path. Pure +
    testable: callers may pass either the base (.../api/v2/otlp) or the full
    .../v1/traces; we always return the latter."""
    base = endpoint.rstrip("/")
    return base if base.endswith("/v1/traces") else f"{base}/v1/traces"


def init_tracing() -> bool:
    """Wire ADK -> OTel -> Dynatrace once. Returns True if tracing is now on,
    False if disabled (creds unset) or already initialized this process."""
    global _initialized
    if _initialized:
        return True
    if not (settings.dt_otlp_endpoint and settings.dt_api_token):
        log.info("self-observability OFF (DT_OTLP_ENDPOINT / DT_API_TOKEN unset)")
        return False

    # Double-checked lock: under uvicorn two requests could race here and
    # double-register the exporter (duplicate spans). Re-check inside the lock.
    with _lock:
        if _initialized:
            return True
        return _install_tracing()


def _install_tracing() -> bool:
    """Build the provider + instrument ADK. Caller holds _lock."""
    global _initialized
    # Imported lazily so the offline path never pays the OTel import cost.
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    url = traces_url(settings.dt_otlp_endpoint)
    provider = TracerProvider(
        resource=Resource.create({"service.name": settings.otel_service_name})
    )
    exporter = OTLPSpanExporter(
        endpoint=url,
        headers={"Authorization": f"Api-Token {settings.dt_api_token}"},
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    GoogleADKInstrumentor().instrument(tracer_provider=provider)

    _initialized = True
    log.info(
        "self-observability ON -> %s (service=%s)", url, settings.otel_service_name
    )
    return True
