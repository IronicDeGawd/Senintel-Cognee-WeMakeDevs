# 04 — Dashboard (Next.js) — REVISED for submission (Jun 10)

> Owner: this session (Dev A). Two pages: **Landing** (marketing/story) +
> **Dashboard** (live operational view). All three pillars already emit
> `Signal`; the dashboard reads them out of Firestore and renders six pieces.
> Submission-aligned: **Dynatrace as the lead track**, GitLab and Arize as
> supporting integrations. Partner names in plain text labels only (rules §7B).
>
> Prereq: `Signal` shape frozen (✓), pillar cycles emit Signals (✓ for P2/P3
> sim, ✓ for P1 real). New: append every emitted Signal to Firestore.

## Why two pages

A single dashboard page is enough for operators but bad for judges:

- The judge clicks the hosted URL cold. They need to know *what SentinelAI is*
  before they can read the live data. Landing page does that in 10 seconds.
- The 3-min demo video needs a hero shot (Landing) and a live shot (Dashboard).
- Design judging cares about narrative + polish, not just data density.

Stack: Next.js 15 App Router + TypeScript + Tailwind + shadcn/ui + Vercel.
Static landing + ISR dashboard (or client-side polling).

---

## Page 1 — Landing (`/`)

**Goal:** A judge clicking the hosted URL understands SentinelAI in 10 seconds
and can click through to the live demo.

```
┌──────────────────────────────────────────────────────────────────┐
│  Nav: SentinelAI                              [GitHub] [Demo →]  │
├──────────────────────────────────────────────────────────────────┤
│  HERO                                                            │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ "Autonomous DevOps. Three signals. One dashboard."       │    │
│  │ Sub: "SentinelAI watches your production with Dynatrace, │    │
│  │  reviews every merge request, and gates AI quality —     │    │
│  │  powered by Gemini on Google Cloud."                     │    │
│  │ [Open live dashboard →]  [View source]                   │    │
│  └──────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────┤
│  THE PILLARS (3 cards, side by side)                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                    │
│  │ Production │ │   Code     │ │ AI Quality │                    │
│  │ Sentinel   │ │  Guardian  │ │   Gate     │                    │
│  │ ▸ Dynatrace│ │  ▸ GitLab  │ │ ▸ Arize    │                    │
│  │   MCP      │ │    MCP/REST│ │   Phoenix  │                    │
│  │ Watches    │ │ Reviews    │ │ Blocks     │                    │
│  │ prod, RCAs │ │ MRs,       │ │ regressed  │                    │
│  │ incidents  │ │ catches    │ │ LLM        │                    │
│  │            │ │ N+1s, etc. │ │ deploys    │                    │
│  └────────────┘ └────────────┘ └────────────┘                    │
│  (Dynatrace card first + visually heaviest — our chosen track)   │
├──────────────────────────────────────────────────────────────────┤
│  THE STORY (the demo arc, illustrated)                           │
│  Scrollytelling or 3-step diagram:                               │
│   1. Developer pushes a commit with N+1 regression.              │
│   2. Code Guardian reviews the MR live — comment lands.          │
│   3. The deploy ships, Dynatrace sees latency spike,             │
│      Production Sentinel correlates back to the same commit.     │
│   4. Meanwhile, AI Quality Gate blocks a parallel LLM regression │
│      before it ever ships.                                       │
│  → all three pillar Signals flow into the dashboard.             │
├──────────────────────────────────────────────────────────────────┤
│  ARCHITECTURE SECTION (#6 — static SVG)                          │
│   diagram: pillars → Signal envelope → Firestore → dashboard;    │
│   side lanes for partner MCP/REST + Gemini on Vertex AI          │
├──────────────────────────────────────────────────────────────────┤
│  CTA strip + footer                                              │
│  [Open the live dashboard →]                                     │
│  • GitHub repo  • Live MR !1  • Apache-2.0                       │
└──────────────────────────────────────────────────────────────────┘
```

**Implementation notes**
- Pure server-rendered. No data fetching on landing.
- Use shadcn/ui Card + AspectRatio for the pillar cards.
- Architecture SVG hand-written (or Excalidraw export). Single file under
  `dashboard/public/architecture.svg`. **No partner logos** — name labels only.
- Color palette: status colors only for the live dashboard; landing stays
  brand-neutral (slate + one accent). Avoid mimicking partner brand colors.

---

## Page 2 — Dashboard (`/dashboard`)

**Goal:** Live operational view. Polls `/signals` every 5s, renders pillar
status + correlation + activity + drift + trigger panel.

```
┌──────────────────────────────────────────────────────────────────┐
│  Nav: SentinelAI ▸ Dashboard       ● live · last 7s · [Home]     │
├──────────────────────────────────────────────────────────────────┤
│  (#1) THREE PILLAR STATUS CARDS                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │
│  │ 🔴 PRODUCTION│ │ 🟠 CODE      │ │ 🔴 AI QUALITY│              │
│  │ Checkout p95 │ │ MR !1: 1 HIGH│ │ Deploy       │              │
│  │ 180→2400ms   │ │ N+1 query    │ │ blocked      │              │
│  │ suspect      │ │ in views.py  │ │ hallucin 22% │              │
│  │ abc1234      │ │ [View MR ↗]  │ │ thr 10%      │              │
│  │ [Expand]     │ │ [Expand]     │ │ [Expand]     │              │
│  └──────────────┘ └──────────────┘ └──────────────┘              │
│  (Dynatrace card first — chosen track)                           │
├──────────────────────────────────────────────────────────────────┤
│  (#2) CORRELATION PANEL — the money shot                         │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ Title: "Why did checkout slow down?"                     │    │
│  │                                                          │    │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐           │    │
│  │   │Dynatrace │ →  │Suspect   │ →  │GitLab MR │           │    │
│  │   │problem   │    │ commit   │    │diff +    │           │    │
│  │   │p95 spike │    │abc1234   │    │review    │           │    │
│  │   │ts 07:38  │    │service:  │    │HIGH:N+1  │           │    │
│  │   │checkout  │    │checkout  │    │views.py  │           │    │
│  │   └──────────┘    └──────────┘    └──────────┘           │    │
│  │                                                          │    │
│  │  Verdict: ROLL BACK MR !42 / commit abc1234              │    │
│  │  [View incident JSON] [View MR comment on GitLab ↗]      │    │
│  └──────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────┤
│  (#3) ACTIVITY TIMELINE       │ (#4) AI QUALITY DRIFT            │
│  ─────────────────────────    │ ───────────────────────────       │
│  • 06:22 code: MR !1 review   │  hallucin ━╱╲━━╱─╲━              │
│  • 06:21 prod: incident saved │  drift    ─╲─╲╱──╲─              │
│  • 06:20 ai_quality: pass     │  threshold ───────── 10%         │
│  • 06:15 prod: incident saved │   (last 30 evals)                │
│  • …  scroll                  │                                  │
├──────────────────────────────────────────────────────────────────┤
│  (#5) TRIGGER DEMO                                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│  │ ▶ Run Production│ │ ▶ Run Code      │ │ ▶ Run AI Gate   │     │
│  │   Cycle (P2)    │ │   Review on MR1 │ │   (P3)          │     │
│  │ POST /run       │ │ POST /webhook   │ │ POST /eval      │     │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘     │
│  status pill under each: idle / running / done · 7s              │
├──────────────────────────────────────────────────────────────────┤
│  footer (link back to landing)                                   │
└──────────────────────────────────────────────────────────────────┘
```

**Per-component sources of truth**

| Piece | Reads from | Writes path |
|---|---|---|
| (1) Pillar cards | `GET /signals` → latest 1 per pillar from Firestore | Each pillar's cycle.py appends emitted Signal |
| (2) Correlation panel | `GET /correlation` → joins latest prod Incident.suspect_commit to most recent code MRReview | nothing new — joins existing Signals |
| (3) Activity timeline | `GET /history?limit=20` → mixed-pillar Signals desc by ts | same Firestore collection |
| (4) Quality drift chart | `GET /trends/quality?limit=30` → reuses existing eval_trends store | already wired (P3-4) |
| (5) Trigger buttons | `POST /trigger/{pillar}` → proxies to the matching Cloud Run service | fire-and-forget |
| (6) Architecture SVG | static, no API | shipped under `public/` |

---

## Backend — `services/dashboard_api/main.py`

New FastAPI, fourth Cloud Run service. Same image, override command.

```python
GET  /signals                  # {production, code, ai_quality}: latest Signal each
GET  /history?pillar=&limit=   # last N Signals, ordered by ts desc
GET  /correlation              # joined latest prod Incident <-> code MRReview
GET  /trends/quality?limit=    # EvalResult time series from out/eval_trends.json
                               #   or BigQuery in real mode
POST /trigger/{pillar}         # proxies to gateway/poller/eval_runner Cloud Run
GET  /health
```

**Storage decision (per AskUserQuestion answer): Firestore.**

- One collection: `signals`. Each doc: `{pillar, status, headline, detail,
  ts, id}` — the exact `Signal` shape, with a server-set id.
- Composite index needed: `(pillar, ts desc)` for `/history` and the latest-per-
  pillar lookup. Created on first real run.
- Sim mode (no Firestore creds): fall back to local JSON ring buffer at
  `out/signals.json`. Keeps local dev cheap.

**Signal write hook**

Each pillar's `cycle.py` already returns a `Signal`. Add one call after emit:

```python
from storage.signal_store import save_signal
...
save_signal(signal)   # appends to Firestore (real) or out/signals.json (sim)
```

`storage/signal_store.py` mirrors `storage/incident_kb.py`: interface +
JsonFileStore (sim) + FirestoreStore (real), mode-switched by
`SENTINEL_SIGNAL_STORE_MODE`.

---

## Frontend — `dashboard/` (Next.js)

**Stack**
- Next.js 15 App Router, TypeScript strict.
- Tailwind v4. shadcn/ui (Card, Badge, Button, Skeleton, ScrollArea, Sheet).
- `lucide-react` for icons (allowed, no partner-branded glyphs).
- Charts: `recharts` for the drift chart (small, tree-shakeable).
- Polling: `useSWR` with `refreshInterval: 5000`.

**File map**
```
dashboard/
  app/
    layout.tsx            # global nav + footer
    page.tsx              # Landing (Page 1)
    dashboard/page.tsx    # Live dashboard (Page 2)
    api/                  # (optional) thin proxy to dashboard_api Cloud Run
  components/
    landing/Hero.tsx
    landing/PillarOverview.tsx
    landing/StorySteps.tsx
    landing/ArchitectureDiagram.tsx
    dashboard/StatusCards.tsx
    dashboard/CorrelationPanel.tsx
    dashboard/ActivityTimeline.tsx
    dashboard/DriftChart.tsx
    dashboard/TriggerPanel.tsx
    ui/* (shadcn copies)
  lib/
    api.ts                # client for dashboard_api
    types.ts              # mirror Signal/Incident/MRReview/EvalResult from shared/models.py
  public/
    architecture.svg
  next.config.ts
  package.json
```

**Types stay in sync** with Python:
- Hand-write TS interfaces in `lib/types.ts` matching `shared/models.py`.
- A CI check that pings `dashboard_api`'s schema (or just the live `/signals`)
  on every dashboard build catches drift fast.

---

## Routing the frontend at the Cloud Run backend

Vercel hosts the static + SSR Next.js app. The dashboard polls
`dashboard_api` on Cloud Run via:

- `NEXT_PUBLIC_API_BASE` env at Vercel = the dashboard_api Cloud Run URL.
- CORS allowed origin = the Vercel domain.
- Or proxy via Next.js Route Handlers (`/app/api/signals/route.ts` calls
  Cloud Run server-side) — hides the Cloud Run URL and avoids CORS.

Recommend **Route Handler proxy** for the demo (no CORS pain, no env leak).

---

## Step-by-step (no code yet)

### D1 — Signal store (Python side)
- `storage/signal_store.py`: interface + JsonFileStore (sim, default) +
  FirestoreStore (real). `save_signal()` + `latest_per_pillar()` +
  `recent(limit, pillar=None)`.
- Add `save_signal(signal)` at the end of each pillar cycle.py
  (production_sentinel/cycle.py, code_guardian/cycle.py, eval_runner/main.py).
- Tests: 5-ish (sim roundtrip, latest-per-pillar, recent filter, factory).
- Config: `SENTINEL_SIGNAL_STORE_MODE`, `signal_store_path`, optional
  `firestore_signals_collection`.

### D2 — Dashboard API service
- `services/dashboard_api/main.py`: 6 endpoints listed above.
- Reuse existing stores: `incident_kb` for the correlation join, `eval_trends`
  for the drift chart, `signal_store` for everything else.
- `POST /trigger/{pillar}` calls the corresponding Cloud Run service URL
  (env vars at deploy: GATEWAY_URL, POLLER_URL, EVAL_RUNNER_URL).
- Tests: 6-ish endpoint tests with stores stubbed.

### D3 — Next.js scaffold (no data)
- `npx create-next-app@latest dashboard --typescript --tailwind --app --src-dir false`
- shadcn init, add components (card, badge, button, skeleton, scroll-area).
- Layout, nav, footer skeleton. Routes `/` and `/dashboard` empty shells.
- Vercel project linked (subdomain `*.vercel.app`).

### D4 — Landing page
- Hero, PillarOverview (3 cards), StorySteps (4-step illustration),
  ArchitectureDiagram (SVG).
- Run `/web-design-guidelines` after first pass.
- Deploy to Vercel; verify lighthouse + accessibility green at 375/768/1280.

### D5 — Dashboard page — static layout
- Skeleton everywhere; no live data yet. Tests rendering at three widths.

### D6 — Dashboard page — wire to API
- `useSWR` hooks for each section. Polling 5s.
- StatusCards: 3 cards from `/signals`.
- CorrelationPanel: from `/correlation`.
- ActivityTimeline: from `/history?limit=20`.
- DriftChart: from `/trends/quality?limit=30` — recharts line + threshold rule.
- TriggerPanel: 3 buttons POST `/trigger/{pillar}`; show running / done badges.

### D7 — Deploy backend
- Add `dashboard_api` to `infra/deploy.sh`. Fourth Cloud Run service.
- Same image, override command. Same env baseline + the three sibling URLs.

### D8 — Verify end-to-end
- From a fresh browser: visit Vercel URL → landing → click "Open dashboard" →
  cards render real Signals (P2 sim, P1 real after MR !1 webhook, P3 sim).
- Click "Run Production Cycle" → new incident appears in timeline within 5s.
- Click "Run Code Review on MR !1" → after ~60s, new entry in timeline.
- Screenshot at 3 widths.

### D9 — Docs + commit
- Update `README.md` with the hosted URL + brief feature list.
- Update `context/progress.md` with the dashboard completion + lessons.
- Update `context/structure.md` with the new `dashboard/` tree + the
  `dashboard_api/` service.

---

## Verification + Definition of done

- `npm run build` clean in `dashboard/`.
- Playwright `browser_take_screenshot` at 375 / 768 / 1280.
- All three pillar cards render real-time data from Firestore (or sim store).
- Correlation panel renders the prod↔commit link from a real incident.
- Trigger buttons fire real Cloud Run services, new Signals appear in <10s.
- Hosted URL on Vercel (e.g. `sentinelai.vercel.app`).
- Committed artifact: 3 screenshots in `out/dashboard/`.

---

## Submission alignment cross-check

| Submission criterion | How the dashboard scores |
|---|---|
| **Hosted URL** | Vercel URL = the submission URL. |
| **Public repo** | GitHub repo already public + Apache-2.0. |
| **≤3-min video** | Demo flows through landing (10s) → dashboard live cards (20s) → trigger button → live update → MR !1 comment lands → end. |
| **Track selection: Dynatrace** | Dynatrace pillar shown FIRST in every triad. Correlation panel emphasises Dynatrace problem as the starting point. Tagline: "Watches your production with Dynatrace, …". |
| **Tech Implementation** | Three live services + Firestore + Vertex Gemini + Cloud Run + partner MCP — all visible from the dashboard or its API. |
| **Design** | Two-page narrative + responsive + accessible (WCAG AA via shadcn defaults). |
| **Potential Impact** | Story copy frames the prod↔code↔eval correlation as something every SRE team rebuilds badly. |
| **Quality of the Idea** | "Three pillars, one envelope" is novel; correlation panel is the demo climax. |

---

## What's deferred / explicitly out of scope

- Custom domain (`sentinel.parakramlabs.com`) — Vercel subdomain is fine for
  submission; map later if cert provisioning gets unstuck.
- Real Dynatrace tenant in P2 (we're sim-mode for the demo); the demo arc
  works because the simulator emits a realistic Incident.
- Real Arize Phoenix MCP (P3-5) — sim mode covers the AI Quality Gate path.
- Authentication on the dashboard — public read-only; trigger buttons
  unauthenticated for the demo but rate-limited at Cloud Run.
- BigQuery quality trends in the dashboard — sim JSON-file trends work; flip
  to BigQuery only if the time is there.

---

## Risks

- **5s polling × multiple readers × Firestore reads**: free tier is 50k/day,
  one user at 5s polling = ~17k/day across 4 widgets = within limits.
  Mitigate with a single batch `/signals/all` endpoint if it spikes.
- **Trigger buttons + Cloud Run cold start**: Gateway's `min-instances=1` is
  set; poller and eval_runner are not — first click may take 10s. Either set
  min-instances=1 on all three (small cost), or display "warming up…" spinner.
- **Demo timing in the video**: live Gemini calls are 4-8s each. Pre-warm by
  clicking the relevant button ~10s before the recording start.
