# SentinelAI Setup Runbook (Jun 10 session)

> Reproducible log of everything we did to take SentinelAI from "branch on a
> fresh Linux box" to "three Cloud Run services live + GitLab demo wired".
> Commands are in execution order. Secret values are placeholders — never
> commit the real ones.

## 0. Inventory before this session
- `main` already had Foundation + P2 (Production Sentinel / Dynatrace) + P3 (AI
  Quality Gate / Arize). 77 tests green.
- Linux dev box `/project/Google-Rapid-Hackathon/`, branch `main`, no `.venv`,
  no `.env`, no `gcloud`, no git identity, no SSH keys registered with GitLab.

---

## 1. gcloud CLI install + Application Default Credentials

Installed via Google's apt repo (sudo password gated; you ran the steps with
the password I had been given for that turn):

```bash
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates gnupg curl
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg -o /tmp/gcloud-key.gpg
sudo bash -c 'gpg --dearmor < /tmp/gcloud-key.gpg > /usr/share/keyrings/cloud.google.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  > /etc/apt/sources.list.d/google-cloud-sdk.list'
sudo apt-get update && sudo apt-get install -y google-cloud-cli
# -> google-cloud-cli 572.0.0 installed at /usr/bin/gcloud
```

Auth (interactive, you ran with `! ` prefix to open the browser):

```bash
gcloud auth login --no-launch-browser
gcloud auth application-default login --no-launch-browser
gcloud auth application-default set-quota-project project-8feccae3-bcae-4254-b60
gcloud config set project project-8feccae3-bcae-4254-b60
```

State after: active account `parakramlabs.tech@gmail.com`, ADC at
`~/.config/gcloud/application_default_credentials.json`, quota project set.

---

## 2. Python env (uv venv) + deps

```bash
which uv || python3 -m pip install --user uv   # uv 0.11.16
uv venv .venv                                  # Python 3.12.8
source .venv/bin/activate
uv pip install -r requirements.txt
```

State after: `.venv` at repo root (already in `.gitignore`), all deps including
google-adk, google-genai, fastapi, httpx, mcp, opentelemetry pins, pytest.

---

## 3. Git identity (global)

You authorised setting these globally for this box:

```bash
git config --global user.name "IronicDeGawd"
git config --global user.email "adityasrivastava807@gmail.com"
```

---

## 4. SSH for gitlab.com

SSH keys existed locally (`~/.ssh/id_ed25519_personal.pub`) but none were
registered with your GitLab account, so `ssh -T git@gitlab.com` was
`Permission denied (publickey)`.

You added the public key in GitLab UI:
- GitLab → User Settings → SSH Keys → paste contents of
  `~/.ssh/id_ed25519_personal.pub` → save.

Then I added a host block so gitlab.com uses the right key (and only that key):

```bash
cat >> ~/.ssh/config <<'EOF'

# GitLab (SentinelAI)
Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/id_ed25519_personal
    IdentitiesOnly yes
EOF

ssh -T git@gitlab.com   # -> "Hi @parakramlabs.tech! …"
```

---

## 5. Demo target app — push to GitLab

The GitLab project `parakramlabs-group/rapid-agent-hackathon` was empty (just
GitLab's "Initial commit" with their auto-README). I authored a minimal Django
checkout-service under `/project/checkout-service-demo/` (sibling, not in our
git tree) and pushed it:

```bash
cd /project/checkout-service-demo
git init -b main
git add . && git -c user.email=adityasrivastava807@gmail.com \
                 -c user.name=IronicDeGawd \
                 commit -m "feat: baseline checkout-service (5-query budget)"
git remote add origin git@gitlab.com:parakramlabs-group/rapid-agent-hackathon.git
git fetch origin
git rebase origin/main           # conflict on README.md (their auto-template
                                 # vs ours). Resolved by keeping ours.
git push -u origin main          # baseline ✓

git checkout -b feature/show-full-order-history
cp /project/checkout-service-demo.regression-views.py checkout/views.py
git commit -am "feat: show full order history on checkout confirmation"
git push -u origin feature/show-full-order-history   # regression ✓
```

Regression file `/project/checkout-service-demo.regression-views.py` is kept
*outside* the repo as the canonical "swap this in to break CI" version.

---

## 6. GitLab Personal Access Token + .env

Project was private; group visibility blocked making it public. You created a
PAT with `api` + `write_repository` scopes (User Settings → Access Tokens) and
pasted it. I wrote it to `.env` (already gitignored, chmod 600):

```bash
cat > /project/Google-Rapid-Hackathon/.env <<EOF
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=project-8feccae3-bcae-4254-b60
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash

SENTINEL_DT_MODE=sim
SENTINEL_GL_MODE=sim
SENTINEL_ARIZE_MODE=sim
SENTINEL_KB_MODE=sim
SENTINEL_DELIVERY_MODE=sim
SENTINEL_TRENDS_MODE=sim

GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=<your-glpat-here>
GITLAB_PROJECT_ID=83079708
GITLAB_DEMO_MR_IID=1
GITLAB_WEBHOOK_TOKEN=<generated-by-step-12>
GITLAB_PROBE_COMMIT=954d6ac0330e8a0395f1f133e5a8bf21124b0a3d
EOF
chmod 600 /project/Google-Rapid-Hackathon/.env
```

**Reminder:** revoke the PAT after the demo is recorded.

---

## 7. Create MR via API

API call with PAT to open MR !1 (commit `954d6ac` → `feature/show-full-order-
history` → `main`):

```bash
TOKEN=$(grep '^GITLAB_TOKEN=' .env | cut -d= -f2-)
curl -sS -X POST -H "PRIVATE-TOKEN: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source_branch":"feature/show-full-order-history","target_branch":"main",
       "title":"Show full order history on checkout confirmation",
       "remove_source_branch":false}' \
  "https://gitlab.com/api/v4/projects/83079708/merge_requests"
# -> MR !1, web_url https://gitlab.com/parakramlabs-group/rapid-agent-hackathon/-/merge_requests/1
```

---

## 8. GitLab Duo Ultimate trial + toggles (UI)

You enabled these in the GitLab UI:
1. Group `parakramlabs-group` → Settings → Billing → "Start your free Ultimate
   trial" → confirm (29 days remaining as of session).
2. Group → Settings → GitLab Duo → enable Duo.
3. Group → Settings → GitLab Duo → Change configuration → enable beta /
   experimental features.
4. Group → Settings → GitLab Duo → Change configuration → **Allow external MCP
   tools** checkbox ON.

---

## 9. GitLab MCP OAuth (mcp-remote)

First call to `npx mcp-remote https://gitlab.com/api/v4/mcp` opens a browser
window for OAuth 2.0 Dynamic Client Registration. After Approve, tokens cache
on disk and survive subprocess spawns:

```
~/.mcp-auth/mcp-remote-0.1.37/
├── 252ab552f8636c5b82dfd2622f4486b1_code_verifier.txt
├── 252ab552f8636c5b82dfd2622f4486b1_client_info.json
└── 252ab552f8636c5b82dfd2622f4486b1_tokens.json
```

Probe to discover the live tool catalogue:

```bash
source .venv/bin/activate
python -u scripts/probe_gitlab.py   # 20 tools listed; project-scoped calls
                                    # return 404 because GitLab Duo's
                                    # composite-identity restriction needs a
                                    # service account on the project too.
```

**Lesson:** if a probe Python parent dies mid-OAuth, mcp-remote orphans the
listener on port 12849. Clean up with:
```bash
pkill -f mcp-remote
rm -rf ~/.mcp-auth/   # forces a fresh OAuth on the next call
```

See `context/progress.md` for the full composite-identity decision; we shipped
hybrid (MCP for connect/catalogue, REST + PAT for project reads/writes).

---

## 10. Identity verification (CC) for CI runners

Group runners were enabled but pipelines failed instantly with 0 jobs as the
project bot user. GitLab.com requires identity verification at the *user*
account level before shared runners dispatch.

UI step (you completed):
- https://gitlab.com/-/profile/account → Identity verification → add credit
  card (refundable hold). Account flips to "Verified".

Trigger fresh pipeline:
```bash
cd /project/checkout-service-demo
git commit --allow-empty -am "ci: re-trigger pipeline after identity verification"
# (We actually added an empty newline to README.md; --allow-empty also works)
git push
```

Pipeline `2589914908` then ran for 20s and produced the real failure trace
(`Failed: Expected to perform 5 queries or less but 7 were done`, 15978 bytes).

---

## 11. SentinelAI: push to GitHub (public submission home)

GitHub remote was already configured:
```bash
git remote -v
# origin  git@github.com:IronicDeGawd/Google-Rapid-Hackathon.git (push)
```

SSH auth via `~/.ssh/id_ed25519_personal` already wired (configured in your
prior `~/.ssh/config` for `Host github.com`). Pushed:

```bash
git push origin main   # 8 commits ahead, pushed cleanly
```

Public at: https://github.com/IronicDeGawd/Google-Rapid-Hackathon

---

## 12. GCP — enable APIs, create secrets, grant IAM

```bash
PROJECT=project-8feccae3-bcae-4254-b60

# 12.1 APIs
gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com \
  aiplatform.googleapis.com --project="$PROJECT"

# 12.2 Secrets (values: GITLAB_TOKEN from your PAT; WEBHOOK_SECRET generated)
WEBHOOK_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
TOKEN=$(grep '^GITLAB_TOKEN=' .env | cut -d= -f2-)
echo -n "$TOKEN"          | gcloud secrets create gitlab-pat            --data-file=- --project="$PROJECT"
echo -n "$WEBHOOK_SECRET" | gcloud secrets create gitlab-webhook-secret --data-file=- --project="$PROJECT"
sed -i "s|^GITLAB_WEBHOOK_TOKEN=.*|GITLAB_WEBHOOK_TOKEN=$WEBHOOK_SECRET|" .env

# 12.3 IAM bindings on Cloud Run's default compute SA
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
for role in \
    secretmanager.secretAccessor \
    aiplatform.user \
    storage.objectAdmin \
    logging.logWriter \
    artifactregistry.createOnPushWriter \
    artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:$SA" --role="roles/$role" --condition=None
done
```

Each role's reason:
- `secretmanager.secretAccessor` — reads `gitlab-pat`, `gitlab-webhook-secret`.
- `aiplatform.user` — Vertex AI Gemini calls from inside the container.
- `storage.objectAdmin` — Cloud Build uploads source tarball to GCS.
- `logging.logWriter` — Cloud Build writes build logs.
- `artifactregistry.createOnPushWriter` + `artifactregistry.writer` — Cloud
  Build creates the `gcr.io` repo on first push and pushes layers.

State of secrets: stored in Secret Manager, never in code or env files at rest.

---

## 13. Cloud Build + Cloud Run deploy

`Dockerfile`, `.gcloudignore`, `infra/deploy.sh` added on the merge commit.
Deploy ran:

```bash
./infra/deploy.sh gateway       # build image + deploy gateway
./infra/deploy.sh poller        # reuses image, deploys poller
./infra/deploy.sh eval_runner   # reuses image, deploys eval_runner
# Or all at once: ./infra/deploy.sh all
```

Equivalent raw commands (helpful if the script is unavailable):

```bash
PROJECT=project-8feccae3-bcae-4254-b60; REGION=us-central1
IMAGE="gcr.io/$PROJECT/sentinelai:latest"

gcloud builds submit --project="$PROJECT" --tag "$IMAGE" .

gcloud run deploy sentinelai-gateway --project="$PROJECT" --region="$REGION" \
  --image="$IMAGE" --allow-unauthenticated \
  --command=sh --args="-c,uvicorn services.webhook_gateway.main:app --host 0.0.0.0 --port \${PORT:-8080}" \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_LOCATION=$REGION,SENTINEL_GL_MODE=real,SENTINEL_DT_MODE=sim,SENTINEL_ARIZE_MODE=sim,SENTINEL_KB_MODE=sim,SENTINEL_DELIVERY_MODE=sim,SENTINEL_TRENDS_MODE=sim,GITLAB_URL=https://gitlab.com,GITLAB_PROJECT_ID=83079708" \
  --set-secrets="GITLAB_TOKEN=gitlab-pat:latest,GITLAB_WEBHOOK_TOKEN=gitlab-webhook-secret:latest"

# Poller + eval_runner: same image, different --args + simpler env (all sim).
```

Live URLs (default Cloud Run hosts):
- gateway      `https://sentinelai-gateway-552996008511.us-central1.run.app`
- poller       `https://sentinelai-poller-552996008511.us-central1.run.app`
- eval_runner  `https://sentinelai-eval-runner-552996008511.us-central1.run.app`

All three `GET /health` return 200.

---

## 14. Custom domain (`sentinel.parakramlabs.com`) — IN PROGRESS

Verification required before mapping:

```bash
gcloud domains verify sentinel.parakramlabs.com   # opens Webmaster Central
```

UI flow:
1. Webmaster Central shows a `google-site-verification=…` TXT record.
2. Add it at Cloudflare DNS for `parakramlabs.com` (DNS-only / grey cloud).
3. Click Verify in Webmaster Central.

Then:

```bash
gcloud beta run domain-mappings create \
  --service=sentinelai-gateway \
  --domain=sentinel.parakramlabs.com \
  --region=us-central1 \
  --project=project-8feccae3-bcae-4254-b60
# Prints the CNAME target (usually ghs.googlehosted.com).
```

UI flow:
4. At Cloudflare DNS: add `CNAME sentinel -> ghs.googlehosted.com`. **Proxy
   status DNS-only (grey cloud)** so Google's Let's-Encrypt ACME challenge
   reaches the origin. (Optional to flip orange-cloud back after cert issues.)
5. Wait 15-30 min for cert. Verify: `curl -I https://sentinel.parakramlabs.com/health` → 200.

---

## 15. Wire GitLab webhook at the public URL

Once the custom domain (or even the default `*.run.app`) is reachable:

GitLab → `parakramlabs-group/rapid-agent-hackathon` → Settings → Webhooks:
- URL: `https://sentinel.parakramlabs.com/gitlab/webhook` (or the default URL).
- Secret token: the value stored in `gitlab-webhook-secret` (Cloud Run reads it
  from Secret Manager; you can `gcloud secrets versions access latest --secret=gitlab-webhook-secret`
  to copy-paste).
- Trigger: Merge request events. (Optional: Pipeline events.)
- Save → "Test" → Push events → should return 200.

Push any new commit to `feature/show-full-order-history` to fire the webhook;
the gateway runs the cycle and posts a new review comment on MR !1.

---

## 16. Logs + cleanup

Tail Cloud Run logs:
```bash
gcloud run services logs tail sentinelai-gateway --region=us-central1 \
  --project=project-8feccae3-bcae-4254-b60
```

Full teardown if needed:
```bash
for svc in sentinelai-gateway sentinelai-poller sentinelai-eval-runner; do
  gcloud run services delete "$svc" --region=us-central1 \
    --project=project-8feccae3-bcae-4254-b60 --quiet
done
gcloud beta run domain-mappings delete --domain=sentinel.parakramlabs.com \
  --region=us-central1 --project=project-8feccae3-bcae-4254-b60 --quiet
for s in gitlab-pat gitlab-webhook-secret; do
  gcloud secrets delete "$s" --project=project-8feccae3-bcae-4254-b60 --quiet
done
```

GitLab: revoke the PAT at User Settings → Access Tokens after the demo
recording is locked.
