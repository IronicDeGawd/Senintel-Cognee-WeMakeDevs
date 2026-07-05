# Track Research — Index

Scraped from the Devpost hackathon resource pages on 2026-06-07 (full page content, every linked doc/repo). Authoritative reference for implementation — re-read during build and validation (per context-management rules).

> ⚠️ **Read [RECONCILIATION.md](RECONCILIATION.md) FIRST** — the official rules change the strategy (one-track prize, mandatory partner MCP, ~4.5-day deadline, Gemini-only).

| Doc | What | File |
|---|---|---|
| **Reconciliation** | What the official rules change + reconciled Pillar 2 + strategic decision | [RECONCILIATION.md](RECONCILIATION.md) |
| **Hackathon official** | Rules, submission, judging, prizes, dates, eligibility | [hackathon.md](hackathon.md) |
| **Google ADK** | Build framework: install, multi-agent, MCP tools, Cloud Run, traces | [adk.md](adk.md) |
| **Dynatrace MCP server** | MANDATORY partner MCP for Dynatrace track (list_problems, execute_dql, …) | [dynatrace-mcp.md](dynatrace-mcp.md) |
| **Example source** | Cloned templates: gemini-hackathon, dynatrace-google-adk-sample, dynatrace-mcp-ai-agent, dynatrace-mcp-server | [examples/](examples/) |

### Partner track resources (partner-provided pages)

| Track | Pillar | File | Key resources |
|---|---|---|---|
| **Dynatrace** (primary) | Pillar 2 — Production Sentinel | [dynatrace.md](dynatrace.md) | Vertex AI hub, AI coding-agent monitoring blog, OTel instrumentation examples repo, Bindplane pipeline, free trial |
| **GitLab** | Pillar 1 — Code Guardian | [gitlab.md](gitlab.md) | Get started, custom agents, custom flows, AI Catalog, **MCP server**, MCP clients, trial |
| **Arize Phoenix** | Pillar 3 — AI Quality Gate | [arize.md](arize.md) | Phoenix docs, **Phoenix MCP server**, LLM evals, gemini-hackathon example repo, Phoenix + OpenInference GitHub, ADK/Vertex/genai instrumentors, Vertex tracing guide |

## Cross-track facts that shape our build

- **Agent runtime:** Arize track explicitly requires a *code-owned* runtime (Gemini CLI, Agent Platform SDK, **Google ADK**, Agent Runtime, or Cloud Run). Visual Agent Builder alone is NOT supported for tracing. Confirms our ADK choice.
- **Tracing standard:** Both Arize and Dynatrace use **OpenTelemetry / OpenInference**. One instrumentation layer can feed both (Phoenix for eval/introspection, Dynatrace for production observability).
- **ADK instrumentor:** `openinference-instrumentation-google-adk` (PyPI) auto-instruments our ADK agent → traces flow to Phoenix and/or Dynatrace.
- **GitLab MCP:** Beta, part of Duo Agent Platform. External MCP clients calling GitLab must set a default Duo namespace (see gitlab-05-mcp-server). 30-day Ultimate trial, 24 Duo credits/user, no access codes.
- **Phoenix MCP:** `@arizeai/phoenix-mcp` via npx; lets the agent query its own traces/prompts/datasets/experiments at runtime — powers the self-improvement loop.
- **Deadline:** Jun 12, 2026 @ 2:30am GMT+5:30 (per Devpost pages).

## Notes / gaps

- `dynatrace-06-signup` and `gitlab-07-free-trial` are sign-up/marketing pages (thin content) — included for the access URLs only.
- Phoenix Cloud app (`app.phoenix.arize.com`) and GCP Marketplace listing are login-gated — not scraped; access links recorded in the track files.
- Raw per-page scrapes were stitched into the three track files; the temp `scrape/` working dir was removed after stitching.
