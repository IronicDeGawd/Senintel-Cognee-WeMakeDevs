#!/usr/bin/env bash
# Deploy one SentinelAI service to Cloud Run.
#
# Backend services share one image (sentinelai:latest) built once per run:
#   ./infra/deploy.sh gateway          # webhook_gateway
#   ./infra/deploy.sh poller           # production sentinel poller
#   ./infra/deploy.sh eval_runner      # AI quality gate
#   ./infra/deploy.sh dashboard_api    # dashboard backend (D2/D7)
#
# Frontend has its own image (sentinelai-dashboard:latest) — Next.js standalone:
#   ./infra/deploy.sh dashboard        # sentinelai-dashboard (the Vercel-style URL)
#
# Aggregate:
#   ./infra/deploy.sh all              # all five, in order
#
# Required env (or override on CLI): GCP_PROJECT, GCP_REGION.
#
# Notes for dashboard_api:
#   - It reads from the same Firestore the three pillars write to, so all four
#     services run with SENTINEL_SIGNAL_STORE_MODE=real here. The pillars also
#     stay on Firestore-backed incident_kb / trends so the dashboard correlation
#     + drift endpoints have real data.
#   - The three DASHBOARD_TRIGGER_*_URL env vars are resolved at deploy time
#     by asking gcloud for each sibling service's URL.

set -euo pipefail

PROJECT="${GCP_PROJECT:-project-8feccae3-bcae-4254-b60}"
REGION="${GCP_REGION:-us-central1}"
IMAGE="gcr.io/${PROJECT}/sentinelai:latest"

service_url() {
  # Resolve a Cloud Run service URL by name (empty if not yet deployed).
  gcloud run services describe "$1" \
    --project="${PROJECT}" --region="${REGION}" \
    --format='value(status.url)' 2>/dev/null || true
}

build_image() {
  echo "==> building ${IMAGE}"
  gcloud builds submit --project="${PROJECT}" --tag "${IMAGE}" .
}

deploy_gateway() {
  echo "==> deploying sentinelai-gateway"
  gcloud run deploy sentinelai-gateway \
    --project="${PROJECT}" --region="${REGION}" \
    --image="${IMAGE}" \
    --command=sh \
    --args="-c,uvicorn services.webhook_gateway.main:app --host 0.0.0.0 --port \${PORT:-8080}" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION},SENTINEL_GL_MODE=real,SENTINEL_DT_MODE=sim,SENTINEL_ARIZE_MODE=sim,SENTINEL_KB_MODE=sim,SENTINEL_DELIVERY_MODE=sim,SENTINEL_TRENDS_MODE=sim,SENTINEL_SIGNAL_STORE_MODE=real,GITLAB_URL=https://gitlab.com,GITLAB_PROJECT_ID=83079708" \
    --set-secrets="GITLAB_TOKEN=gitlab-pat:latest,GITLAB_WEBHOOK_TOKEN=gitlab-webhook-secret:latest"
}

deploy_poller() {
  echo "==> deploying sentinelai-poller"
  gcloud run deploy sentinelai-poller \
    --project="${PROJECT}" --region="${REGION}" \
    --image="${IMAGE}" \
    --command=sh \
    --args="-c,uvicorn services.poller.main:app --host 0.0.0.0 --port \${PORT:-8080}" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION},SENTINEL_DT_MODE=real,SENTINEL_GL_MODE=real,SENTINEL_ARIZE_MODE=sim,SENTINEL_KB_MODE=real,SENTINEL_DELIVERY_MODE=sim,SENTINEL_TRENDS_MODE=sim,SENTINEL_SIGNAL_STORE_MODE=real,DT_ENVIRONMENT=https://bbm54450.apps.dynatrace.com,DT_GRAIL_QUERY_BUDGET_GB=50,GITLAB_URL=https://gitlab.com,GITLAB_PROJECT_ID=83079708,GITLAB_DEMO_MR_IID=1" \
    --set-secrets="DT_PLATFORM_TOKEN=dt-platform-token:latest,GITLAB_TOKEN=gitlab-pat:latest"
}

deploy_eval_runner() {
  echo "==> deploying sentinelai-eval-runner"
  gcloud run deploy sentinelai-eval-runner \
    --project="${PROJECT}" --region="${REGION}" \
    --image="${IMAGE}" \
    --command=sh \
    --args="-c,uvicorn services.eval_runner.main:app --host 0.0.0.0 --port \${PORT:-8080}" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION},SENTINEL_ARIZE_MODE=sim,SENTINEL_DT_MODE=sim,SENTINEL_GL_MODE=sim,SENTINEL_KB_MODE=sim,SENTINEL_DELIVERY_MODE=sim,SENTINEL_TRENDS_MODE=sim,SENTINEL_SIGNAL_STORE_MODE=real"
}

deploy_dashboard() {
  # Next.js standalone frontend. Built from the dashboard/ subtree so the
  # backend image (sentinelai:latest) doesn't carry npm + Node 24.
  # NEXT_PUBLIC_API_BASE is baked into the bundle at build time (NEXT_PUBLIC_*
  # is read at compile, not runtime), so we resolve it from the dashboard_api
  # service URL right before the build.
  echo "==> deploying sentinelai-dashboard (Next.js frontend)"
  local api_base
  api_base="$(service_url sentinelai-dashboard-api)"
  if [[ -z "${api_base}" ]]; then
    echo "warn: sentinelai-dashboard-api URL empty — frontend will fall back to mocks"
  fi
  local image="gcr.io/${PROJECT}/sentinelai-dashboard:latest"
  echo "==> building ${image} with NEXT_PUBLIC_API_BASE=${api_base}"

  # Write a temporary cloudbuild.yaml inside the dashboard/ context so the
  # build-arg lands at docker build time (Cloud Build's --tag doesn't support
  # --build-arg directly).
  local cb_yaml
  cb_yaml="$(mktemp)"
  cat >"${cb_yaml}" <<EOF
steps:
- name: gcr.io/cloud-builders/docker
  args:
    - build
    - --build-arg
    - NEXT_PUBLIC_API_BASE=${api_base}
    - -t
    - ${image}
    - .
images:
- ${image}
EOF
  gcloud builds submit dashboard \
    --project="${PROJECT}" \
    --config="${cb_yaml}"
  rm -f "${cb_yaml}"

  gcloud run deploy sentinelai-dashboard \
    --project="${PROJECT}" --region="${REGION}" \
    --image="${image}" \
    --allow-unauthenticated \
    --port=8080
}

deploy_dashboard_api() {
  echo "==> deploying sentinelai-dashboard-api"
  local gw poll er demo
  gw="$(service_url sentinelai-gateway)"
  poll="$(service_url sentinelai-poller)"
  er="$(service_url sentinelai-eval-runner)"
  demo="$(service_url sentinelai-demo-director)"
  if [[ -z "${gw}" || -z "${poll}" || -z "${er}" ]]; then
    echo "warn: one or more sibling service URLs is empty — trigger endpoints will return 503 until those services are deployed and re-deployed:"
    echo "  gateway       = ${gw:-<missing>}"
    echo "  poller        = ${poll:-<missing>}"
    echo "  eval_runner   = ${er:-<missing>}"
    echo "  demo_director = ${demo:-<missing>}"
  fi
  gcloud run deploy sentinelai-dashboard-api \
    --project="${PROJECT}" --region="${REGION}" \
    --image="${IMAGE}" \
    --command=sh \
    --args="-c,uvicorn services.dashboard_api.main:app --host 0.0.0.0 --port \${PORT:-8080}" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION},SENTINEL_SIGNAL_STORE_MODE=real,SENTINEL_KB_MODE=real,SENTINEL_TRENDS_MODE=sim,DASHBOARD_TRIGGER_GATEWAY_URL=${gw},DASHBOARD_TRIGGER_POLLER_URL=${poll},DASHBOARD_TRIGGER_EVAL_RUNNER_URL=${er},DASHBOARD_DEMO_DIRECTOR_URL=${demo}"
}

deploy_demo_director() {
  # Demo Director seeds the three pillars with scenario data on demand.
  # DT seeder uses the real MCP send_event tool, so this service needs the
  # same Dynatrace creds the poller has (DT_PLATFORM_TOKEN secret +
  # DT_ENVIRONMENT). GitLab + eval-runner seeders need the sibling URLs.
  echo "==> deploying sentinelai-demo-director"
  local gw poll er
  gw="$(service_url sentinelai-gateway)"
  poll="$(service_url sentinelai-poller)"
  er="$(service_url sentinelai-eval-runner)"
  gcloud run deploy sentinelai-demo-director \
    --project="${PROJECT}" --region="${REGION}" \
    --image="${IMAGE}" \
    --command=sh \
    --args="-c,uvicorn services.demo_director.main:app --host 0.0.0.0 --port \${PORT:-8080}" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION},SENTINEL_DT_MODE=real,SENTINEL_GL_MODE=sim,SENTINEL_ARIZE_MODE=sim,SENTINEL_KB_MODE=sim,SENTINEL_DELIVERY_MODE=sim,SENTINEL_TRENDS_MODE=sim,SENTINEL_SIGNAL_STORE_MODE=real,DT_ENVIRONMENT=https://bbm54450.apps.dynatrace.com,DT_GRAIL_QUERY_BUDGET_GB=50,DASHBOARD_TRIGGER_GATEWAY_URL=${gw},DASHBOARD_TRIGGER_POLLER_URL=${poll},DASHBOARD_TRIGGER_EVAL_RUNNER_URL=${er},GITLAB_URL=https://gitlab.com,GITLAB_PROJECT_ID=83079708,GITLAB_DEMO_MR_IID=1" \
    --set-secrets="DT_PLATFORM_TOKEN=dt-platform-token:latest,GITLAB_TOKEN=gitlab-pat:latest,GITLAB_WEBHOOK_TOKEN=gitlab-webhook-secret:latest"
}

case "${1:-}" in
  gateway)        build_image; deploy_gateway ;;
  poller)         build_image; deploy_poller ;;
  eval_runner)    build_image; deploy_eval_runner ;;
  dashboard_api)  build_image; deploy_dashboard_api ;;
  demo_director)  build_image; deploy_demo_director ;;
  dashboard)      deploy_dashboard ;;       # frontend has its own image, no build_image
  all)            build_image; deploy_gateway; deploy_poller; deploy_eval_runner; deploy_dashboard_api; deploy_demo_director; deploy_dashboard ;;
  *)
    echo "usage: $0 {gateway|poller|eval_runner|dashboard_api|demo_director|dashboard|all}" >&2
    exit 2
    ;;
esac
