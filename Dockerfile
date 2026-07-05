# SentinelAI Cloud Run image. One image, three services: each `services/*/main.py`
# exports a FastAPI `app`. The deploy script overrides the command per service.
#
# Build (locally):
#   docker build -t sentinelai .
# Run (locally):
#   docker run -p 8080:8080 -e PORT=8080 sentinelai

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080

# Node 22 is needed by the partner MCP servers we drive over stdio:
#   - integrations/dynatrace/real.py spawns `npx @dynatrace-oss/dynatrace-mcp-server`
#   - shared/mcp_client.py spawns `npx mcp-remote {gitlab}/api/v4/mcp`
# Python services that stay on the REST or sim paths don't touch Node, but it's
# cheaper to bake it once than to fork the image per service.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first so the layer caches when only code changes.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Ship the source tree. .gcloudignore keeps tests, venv, demo_target, .env out.
COPY . .

EXPOSE 8080

# Default = webhook gateway. Poller + eval_runner override with --command on deploy.
CMD ["sh", "-c", "uvicorn services.webhook_gateway.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
