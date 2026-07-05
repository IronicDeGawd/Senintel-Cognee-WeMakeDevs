# SentinelAI Cloud Run runbook

One image, three Cloud Run services. Webhook gateway is the only one that needs
a public custom domain (`sentinel.parakramlabs.com`); the poller and
eval-runner stay on Cloud Run default `*.run.app` URLs because they're triggered
internally (Cloud Scheduler, or the agent's tool calls).

## One-time setup (per project)

```bash
PROJECT=project-8feccae3-bcae-4254-b60
REGION=us-central1

# 1. Enable APIs.
gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com \
  aiplatform.googleapis.com --project="$PROJECT"

# 2. Create secrets.
echo -n "<GITLAB_PAT>"            | gcloud secrets create gitlab-pat            --data-file=- --project="$PROJECT"
echo -n "<GITLAB_WEBHOOK_SECRET>" | gcloud secrets create gitlab-webhook-secret --data-file=- --project="$PROJECT"

# 3. Let Cloud Run's default compute SA read secrets + call Vertex.
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
for role in secretmanager.secretAccessor aiplatform.user; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:$SA" --role="roles/$role"
done
```

## Deploy

```bash
./infra/deploy.sh gateway       # webhook gateway only
./infra/deploy.sh poller        # production sentinel
./infra/deploy.sh eval_runner   # AI quality gate
./infra/deploy.sh all           # all three, one image build, three services
```

Each prints the resulting `*.run.app` URL on success.

## Subdomain: sentinel.parakramlabs.com -> gateway

```bash
# Print the CNAME target Google wants you to add at Cloudflare.
gcloud beta run domain-mappings create \
  --service=sentinelai-gateway \
  --domain=sentinel.parakramlabs.com \
  --region=us-central1 \
  --project=project-8feccae3-bcae-4254-b60
```

At Cloudflare DNS for `parakramlabs.com`:
1. Add CNAME: `sentinel` -> `ghs.googlehosted.com` (target may differ — use whatever the gcloud command above prints).
2. **Set Proxy status to DNS only (grey cloud)**, not Proxied. Cloudflare's proxy
   terminates TLS, which blocks Google's Let's-Encrypt ACME challenge. After
   the cert provisions (15-30 min), you can optionally flip it back on if you
   want Cloudflare in front, but DNS-only is the simpler setup.
3. Verify cert is ready: `curl -I https://sentinel.parakramlabs.com/health`
   should return 200 once the cert is issued.

## Point GitLab webhook at the gateway

GitLab project (`parakramlabs-group/rapid-agent-hackathon`) -> Settings ->
Webhooks:

- URL: `https://sentinel.parakramlabs.com/gitlab/webhook`
- Secret token: same value used for `gitlab-webhook-secret` in Secret Manager.
- Trigger: Merge request events. (Optional: Pipeline events.)

Push a commit on `feature/show-full-order-history` to fire the webhook end-to-end.

## Tail logs

```bash
gcloud run services logs tail sentinelai-gateway --region=us-central1 \
  --project=project-8feccae3-bcae-4254-b60
```

## Cleanup

```bash
for svc in sentinelai-gateway sentinelai-poller sentinelai-eval-runner; do
  gcloud run services delete "$svc" --region=us-central1 \
    --project=project-8feccae3-bcae-4254-b60 --quiet
done
gcloud beta run domain-mappings delete --domain=sentinel.parakramlabs.com \
  --region=us-central1 --project=project-8feccae3-bcae-4254-b60 --quiet
```
