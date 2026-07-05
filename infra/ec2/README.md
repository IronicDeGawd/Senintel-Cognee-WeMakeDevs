# Single-EC2 deployment (no Cloud Run)

Runs the whole stack on one Ubuntu 24.04 box (t3.small works): five FastAPI
services + the Next.js dashboard behind Caddy, with Cognee running in local
embedded mode and Gemini via a Vertex AI service account.

Live: https://sentinel-aplus.parakramlabs.com

## Layout on the box

```
/home/ubuntu/sentinel/            repo checkout
├── .env                          from infra/ec2/ec2.env.example
├── .venv/                        python venv (requirements.txt)
├── secrets/gcp-sa.json           Vertex AI service account (chmod 600)
├── cognee-system/databases/      Cognee sqlite + graph (MUST pre-exist)
├── cognee-data/                  Cognee data root
└── dashboard/.next/standalone/   Next build output
```

| Service (systemd) | Port | What |
|---|---|---|
| sentinel-dashboard-api | 8100 | public API (Caddy proxies `/api/*` here) |
| sentinel-gateway | 8101 | webhook gateway (Code Guardian) |
| sentinel-poller | 8102 | Production Sentinel |
| sentinel-eval-runner | 8103 | AI Quality Gate |
| sentinel-demo-director | 8104 | "Run scenario" backend |
| sentinel-dashboard | 3000 | Next.js standalone |

Caddy: the public domain (Cloudflare origin cert in `/etc/caddy/certs/`) and
an `<ip>.sslip.io` fallback both serve `/` → dashboard, `/api/*` → 8100.
The dashboard is built with `NEXT_PUBLIC_API_BASE=/api` (same origin).

## Deploy

```bash
# from your machine
rsync -az --exclude .git --exclude node_modules --exclude .venv \
    ./ ubuntu@<ip>:~/sentinel/
scp infra/ec2/ec2.env.example ubuntu@<ip>:~/sentinel/.env   # then fill secrets
scp <your-gcp-sa>.json ubuntu@<ip>:~/sentinel/secrets/gcp-sa.json
scp infra/ec2/Caddyfile infra/ec2/setup.sh ubuntu@<ip>:~/
ssh ubuntu@<ip> 'bash ~/setup.sh'
```

`setup.sh` installs Caddy/Node 22/venv tooling, adds 2G swap, pip-installs,
builds the dashboard, writes the systemd units, starts everything, and seeds
the team memory.

## Cognee-local gotchas (cost us an evening)

1. `SYSTEM_ROOT_DIRECTORY` / `DATA_ROOT_DIRECTORY` are read from the
   **process environment only** — values in the app's `.env` never reach
   `os.environ`, so they must live in the systemd units (setup.sh does this).
   Without them Cognee writes inside `site-packages`.
2. sqlite does **not** create parent directories: `cognee-system/databases/`
   must exist before first use or every remember/recall fails with
   `unable to open database file` and the adapter silently falls back to
   fixtures — the demo looks alive but the memory is fake.
3. Recall on an empty graph raises `RecallPreconditionError` — run
   `scripts/seed_team_memory.py` once (setup.sh does).
4. With `GEMINI_API_KEY` empty, the adapter routes Cognee's LLM + embeddings
   through Vertex AI using the mounted service account — no AI Studio key
   needed on the box.
