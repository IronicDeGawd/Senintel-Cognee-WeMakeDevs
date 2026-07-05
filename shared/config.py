"""Central config. Loaded once from the environment (.env in dev, real env in
prod). Every pillar imports `settings` instead of reading os.environ directly.

We also call load_dotenv() at import so libraries that read os.environ directly
(google-genai picks up GEMINI_API_KEY) see the same values the settings object
does — the spike relied on this.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_FILE)

Mode = Literal["sim", "real"]


class Settings(BaseSettings):
    """Typed view over the environment. Append-only: pillars add fields here as
    they wire real credentials; never rename or remove existing fields."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core (Gemini via Vertex AI + Application Default Credentials) ---
    # Default auth path: ADC (gcloud auth application-default login). No API key.
    # These three names are also what ADK reads directly from the environment.
    google_genai_use_vertexai: bool = True
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    gemini_model: str = "gemini-2.5-flash"

    # Optional fallback: AI Studio API key (only used if use_vertexai is false).
    gemini_api_key: str = ""

    # --- Pillar modes ---
    dt_mode: Mode = Field("sim", validation_alias="SENTINEL_DT_MODE")
    gl_mode: Mode = Field("sim", validation_alias="SENTINEL_GL_MODE")
    arize_mode: Mode = Field("sim", validation_alias="SENTINEL_ARIZE_MODE")

    # --- Incident KB + embeddings (P2-3) ---
    # sim = JSON-file shim + deterministic local embeddings (offline, free).
    # real = Firestore collection + Vertex AI text embeddings.
    kb_mode: Mode = Field("sim", validation_alias="SENTINEL_KB_MODE")
    kb_path: str = ""  # JSON shim path; defaults to out/incident_kb.json
    firestore_collection: str = "incidents"
    embedding_model: str = "text-embedding-005"

    # --- Delivery (P2-5) ---
    # sim = write the briefing to out/briefing.md. real = post to Slack.
    delivery_mode: Mode = Field("sim", validation_alias="SENTINEL_DELIVERY_MODE")
    slack_webhook_url: str = ""
    # Preferred real-mode Slack path: the Dynatrace MCP send_slack_message tool
    # (the partner-MCP story). Needs a Slack Connection configured in the tenant
    # (slack_connection_id) + a target channel. Delivery falls back to the
    # webhook above when the connection id is unset or the MCP send fails.
    slack_connection_id: str = ""
    slack_channel: str = ""

    # --- P2 Dynatrace creds (only used when dt_mode=real) ---
    dt_environment: str = ""
    dt_platform_token: str = ""
    # Cap Grail bytes scanned per MCP session to control DQL cost (base 1000 GB).
    dt_grail_query_budget_gb: int = 50

    # --- Classic Events API ingest token (D8 Demo Director seeding) ---
    # The MCP send_event tool gates behind a human-approval elicit prompt that
    # auto-denies in a headless service. Seeding falls back to the classic
    # Events API at {dt_classic_url}/api/v2/events/ingest with this dt0c01.
    # token (needs scope events.ingest). dt_classic_url defaults to the .live
    # twin of dt_environment.
    dt_classic_url: str = ""
    dt_events_token: str = ""

    # --- P2-8 self-observability (OTel traces -> Dynatrace) ---
    # No-op unless BOTH are set, so offline/sim dev and tests stay network-free.
    # OTLP ingest uses a classic Api-Token (dt0c01.) with openTelemetryTrace.ingest
    # scope at https://<env-id>.live.dynatrace.com/api/v2/otlp (note: .live, not .apps).
    dt_otlp_endpoint: str = ""
    dt_api_token: str = ""
    otel_service_name: str = "sentinelai"

    # --- P1 GitLab creds (only used when gl_mode=real) ---
    gitlab_url: str = "https://gitlab.com"
    gitlab_token: str = ""
    # Numeric project ID (visible on the project page). Required by every MCP
    # tool call against the GitLab MCP server.
    gitlab_project_id: int = 0
    # The demo MR iid (e.g. 1 for !1). Used by scripts/probe_gitlab.py and the
    # live smoke script; webhook reads the iid from the event payload instead.
    gitlab_demo_mr_iid: int = 0
    # Shared secret GitLab sends as X-Gitlab-Token on the webhook. Empty in dev
    # lets the local POST through; production MUST set this.
    gitlab_webhook_token: str = ""

    # --- P3 Arize/Phoenix creds (only used when arize_mode=real) ---
    phoenix_endpoint: str = ""
    phoenix_api_key: str = ""

    # --- P3 eval trends (drift-over-time store) ---
    trends_mode: Mode = Field("sim", validation_alias="SENTINEL_TRENDS_MODE")
    trends_path: str = ""  # sim JSON shim path; defaults to out/eval_trends.json
    bq_dataset: str = "sentinelai"  # BigQuery dataset (trends_mode=real)
    bq_table: str = "eval_runs"  # BigQuery table (trends_mode=real)

    # --- D1 Signal store (dashboard cross-pillar stream) ---
    # Every pillar's cycle appends its emitted Signal here so the dashboard can
    # render latest-per-pillar + a single timeline + a correlation join.
    # sim = JSON-file ring shim. real = Firestore (one collection, server id).
    signal_store_mode: Mode = Field("sim", validation_alias="SENTINEL_SIGNAL_STORE_MODE")
    signal_store_path: str = ""  # sim shim path; defaults to out/signals.json
    firestore_signals_collection: str = "signals"

    # --- D2 Dashboard API trigger URLs ----------------------------------------
    # The dashboard's three big "Run X" buttons proxy through dashboard_api to
    # the matching pillar service on Cloud Run. Empty in dev = trigger returns
    # 503 (sim mode), which keeps the unit tests offline.
    dashboard_trigger_gateway_url: str = ""  # POST {url}/gitlab/webhook
    dashboard_trigger_poller_url: str = ""  # POST {url}/run
    dashboard_trigger_eval_runner_url: str = ""  # POST {url}/eval
    # Demo Director URL (D8): the dashboard's "Run Scenario" button proxies
    # through dashboard_api -> demo_director. Empty = button returns 503.
    dashboard_demo_director_url: str = ""  # POST {url}/demo/run


settings = Settings()
