# Reconciliation — What the Official Rules Change

> Written 2026-06-07 after scraping the hackathon's own pages + ADK docs + Dynatrace MCP server + example repo source. Read this alongside [README.md](README.md).

## Hard facts from the official Rules/Overview

| Fact | Source | Impact |
|---|---|---|
| **Deadline: June 11, 2026, 2:00 PM PT** (June 12, 2:30 AM IST) | rules §5 / dates | ~4.5 days from today, not 6. |
| **ONE partner track per submission**; prize is per-bucket ($5k/$3k/$2k each) | overview / rules §9 | A 3-partner project still enters only ONE bucket. Judges of that bucket reward depth in **their** partner. |
| **Mandatory: agent built with Gemini + Google Cloud Agent Builder, integrating a Partner's MCP server** | rules §7A | Partner **MCP integration is required**, not optional. For Dynatrace = the Dynatrace MCP server. |
| **Gemini-only AI** — "All other artificial intelligence tools are not permitted" | rules §7B | No non-Google LLMs. Gemini for all reasoning + LLM-eval judge. ✓ already chosen. |
| **No services competing with Google Cloud or the chosen partner** | rules §7B | On Dynatrace track, avoid competing observability. **MongoDB** is a *different partner* — safer to use Google-native storage (Firestore/BigQuery) to stay "Google Cloud + Dynatrace only." |
| **New project only**, created in contest period | rules §7B | Greenfield ✓. |
| **Must run on web/Android/iOS** | rules §7B | Next.js dashboard = web ✓. |
| **Submit:** hosted project URL + public OSS repo w/ visible LICENSE + ≤3-min YouTube/Vimeo video + Devpost form | rules §7 | Need public repo + LICENSE from day 1, a deployed URL, and a tight 3-min demo. |
| **Judging (equal weight):** Technological Implementation (Google Cloud + Partner quality), Design/UX, Potential Impact, Quality of Idea | rules §8 | Stage 1 = pass/fail viability: must meaningfully use the partner + Google Cloud. |
| **Team ≤ 4** | rules §7B | Fine. |
| **$100 GCP credit** request form (was due Jun 4) or free trial | rules §6 | Use free trial / AI Studio key. |

## Pillar 2 (Dynatrace) — RECONCILED

The earlier worry ("is Dynatrace OTel-only, no anomaly polling?") is resolved. The **Dynatrace MCP server** ([dynatrace-mcp.md](dynatrace-mcp.md)) gives exactly the tools Production Sentinel needs:

- `list_problems` — Davis-AI auto-detected problems/anomalies (this IS the "poll anomalies" capability)
- `execute_dql` / `generate_dql_from_natural_language` — query logs, metrics, spans from Grail
- `find_entity_by_name` — service topology
- `list_vulnerabilities`, `list_exceptions` — security + error context
- `chat_with_davis_copilot` — Dynatrace's own AI
- `send_slack_message`, `send_email`, `send_event`, `create_dynatrace_notebook` — deliver the briefing/ticket

**Reconciled design — use Dynatrace BOTH ways (strong track story):**
1. **As a tool (mandatory MCP):** ADK agent mounts the Dynatrace MCP server (`npx @dynatrace-oss/dynatrace-mcp-server`, stdio or `--http`). Cloud Scheduler fires the agent → it calls `list_problems` + `execute_dql`, Gemini reasons over the chain, then `send_slack_message` delivers the morning briefing + creates a notebook/incident.
2. **As observability of itself:** the agent is OTel-instrumented (ADK traces) → exported to Dynatrace `…/api/v2/otlp` with an Api-Token. SentinelAI watches itself in Dynatrace.

Auth: `DT_ENVIRONMENT=https://<env>.apps.dynatrace.com` + browser OAuth (or Platform Token). Mind Grail query costs (`DT_GRAIL_QUERY_BUDGET_GB`). A **simulator** still returns canned `list_problems` payloads for a repeatable demo.

## ADK ↔ "Agent Builder" requirement

Rules say "Google Cloud Agent Builder." ADK is Google's open-source agent framework within the Vertex AI Agent Builder ecosystem; the Arize track explicitly lists **Google ADK** as an accepted code-owned runtime, and the overview frames Agent Builder as "ideal for rapid prototyping" (recommended, not exclusive). **Plan: build on ADK, deploy to Cloud Run / Agent Engine, and frame it as the Agent Builder ecosystem in the submission.** ADK consumes the partner MCP via `McpToolset` (see [adk.md](adk.md) → MCP tools).

## Build templates we now have (source on disk)

- `examples/gemini-hackathon/` — canonical **ADK + Gemini + Phoenix(OTel) + Phoenix-MCP** starter (agent/main.py, instrumentation.py, shopping_demo agent/tools, .gemini/settings.json, Makefile). Closest template to copy.
- `examples/dynatrace-google-adk-sample/` — **multi-agent ADK** (root + sub_agents) instrumented for Dynatrace.
- `examples/dynatrace-mcp-ai-agent/` — agent consuming an MCP server + Dynatrace OTel via Traceloop (`dynatrace.py setup_tracing`).
- `examples/dynatrace-mcp-server/` — a sample MCP server (TS) with OTel tracer.

## STRATEGIC DECISION needed (scope vs. winning)

Official rules confirm the merged-doc's own risks #1 (scope) and #5 (track lock-in):
- Only **one** bucket counts. Judges reward **deep, authentic** use of the chosen partner.
- ~4.5 days. Three full partner-MCP integrations (Dynatrace + GitLab + Arize) is a lot; the two non-chosen pillars **earn no prize points** and risk looking unfocused in a 3-min demo.

**Recommendation:** Submit to the **Dynatrace** track with **Production Sentinel as the whole product**, going deep on the Dynatrace MCP (list_problems → Gemini RCA → Slack briefing + notebook) + self-observability in Dynatrace + a clean Next.js dashboard. Keep Code Guardian / AI Quality Gate as **optional stretch** only if Dynatrace is fully done and demo-ready. This maximizes win probability under the real constraints.

The user previously chose "all 3 pillars real" — but that was before these facts. **Open question for the user/team: focus single-track (recommended) or keep all three?**
