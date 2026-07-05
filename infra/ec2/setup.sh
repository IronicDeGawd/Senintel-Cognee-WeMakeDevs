#!/usr/bin/env bash
# SentinelAI EC2 setup — Ubuntu 24.04, run as ubuntu after code rsync.
# Phase 1 (OS): swap, caddy, node22, python venv tooling.
# Phase 2 (app): venv + pip, Next standalone build, systemd units, caddy.
set -euo pipefail

APP=/home/ubuntu/sentinel

# --- Phase 1: OS deps -----------------------------------------------------
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
  sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
fi

sudo apt-get update -qq
sudo apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https curl python3-venv python3-dev build-essential

if ! command -v caddy >/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --yes --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null
  sudo apt-get update -qq && sudo apt-get install -y -qq caddy
fi

if ! command -v node >/dev/null || [ "$(node -v | cut -c2-3)" -lt 22 ]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash - > /dev/null
  sudo apt-get install -y -qq nodejs
fi

# --- Phase 2: app ----------------------------------------------------------
cd "$APP"
# Cognee (local mode) storage. Two hard-won facts: the SDK honors
# SYSTEM_ROOT_DIRECTORY/DATA_ROOT_DIRECTORY from the PROCESS env only (the
# app's .env is not exported to os.environ), and sqlite will not create the
# databases/ parent dir itself — without it every remember/recall fails with
# "unable to open database file" and the code silently falls back to fixtures.
mkdir -p "$APP/cognee-system/databases" "$APP/cognee-data"
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt

# Next.js standalone build (API base is same-origin /api).
cd "$APP/dashboard"
npm install --no-audit --no-fund --loglevel=error
NEXT_PUBLIC_API_BASE=/api npx next build
cp -r .next/static .next/standalone/.next/static
[ -d public ] && cp -r public .next/standalone/public || true

# --- systemd units ----------------------------------------------------------
declare -A SVC=(
  [sentinel-dashboard-api]="services.dashboard_api.main:app 8100"
  [sentinel-gateway]="services.webhook_gateway.main:app 8101"
  [sentinel-poller]="services.poller.main:app 8102"
  [sentinel-eval-runner]="services.eval_runner.main:app 8103"
  [sentinel-demo-director]="services.demo_director.main:app 8104"
)
for name in "${!SVC[@]}"; do
  set -- ${SVC[$name]}
  sudo tee /etc/systemd/system/${name}.service > /dev/null <<UNIT
[Unit]
Description=SentinelAI ${name}
After=network.target

[Service]
User=ubuntu
WorkingDirectory=${APP}
Environment=SYSTEM_ROOT_DIRECTORY=${APP}/cognee-system
Environment=DATA_ROOT_DIRECTORY=${APP}/cognee-data
ExecStart=${APP}/.venv/bin/uvicorn $1 --host 127.0.0.1 --port $2
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT
done

sudo tee /etc/systemd/system/sentinel-dashboard.service > /dev/null <<UNIT
[Unit]
Description=SentinelAI dashboard (Next.js standalone)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=${APP}/dashboard
Environment=PORT=3000
Environment=HOSTNAME=127.0.0.1
ExecStart=/usr/bin/node ${APP}/dashboard/.next/standalone/server.js
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

# --- caddy ------------------------------------------------------------------
sudo mkdir -p /etc/caddy/certs
sudo mv /home/ubuntu/sentinel-aplus.parakramlabs.com.pem /home/ubuntu/sentinel-aplus.parakramlabs.com.key /etc/caddy/certs/ 2>/dev/null || true
sudo chown -R root:caddy /etc/caddy/certs && sudo chmod 640 /etc/caddy/certs/*
PUBIP=$(curl -4 -s --max-time 5 ifconfig.me)
sudo sed "s/SSLIP_PLACEHOLDER/$(echo $PUBIP | tr . -).sslip.io/" /home/ubuntu/Caddyfile | sudo tee /etc/caddy/Caddyfile > /dev/null
sudo caddy validate --config /etc/caddy/Caddyfile

sudo systemctl daemon-reload
sudo systemctl enable --now sentinel-dashboard-api sentinel-gateway sentinel-poller sentinel-eval-runner sentinel-demo-director sentinel-dashboard
sudo systemctl reload caddy || sudo systemctl restart caddy

chmod 600 "$APP/.env" "$APP/secrets/gcp-sa.json"

# Seed the team memory once (idempotent enough for a demo box; comment out
# to keep an existing graph). Recall on an EMPTY local Cognee raises
# RecallPreconditionError — seeding is not optional for the demo.
cd "$APP"
export SYSTEM_ROOT_DIRECTORY="$APP/cognee-system" DATA_ROOT_DIRECTORY="$APP/cognee-data"
./.venv/bin/python scripts/seed_team_memory.py || echo "WARN: memory seed failed — demo will use fixture fallback"

echo "SETUP_OK public=$PUBIP"
