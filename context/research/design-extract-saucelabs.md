# Design Extract — saucelabs.com

> Source: https://saucelabs.com/ (homepage) — captured Jun 10, 2026 via Playwright + system Chrome.
> Purpose: extract the underlying design *system* (tokens, rhythm, hierarchy) to inform SentinelAI's landing + dashboard rebuild. We borrow the **bones** (spacing, type scale, radii, section composition), NOT the literal palette or assets.

## Raw artifacts

- Screenshots: `saucelabs-{desktop,tablet,mobile}.png` (1280 / 768 / 375)
- Token JSON dump: `/tmp/design-extract/out/tokens.json`
- Hierarchy + headings: `/tmp/design-extract/out/hierarchy.json`
- Image refs: `/tmp/design-extract/out/images.json`

## Palette (their system — do NOT lift directly)

| Role | Color | Use |
|------|-------|-----|
| Surface primary (dark) | `#132322` (rgb 19,35,34) | hero, dark sections, default text on light |
| Surface raised (dark) | `rgba(10,19,18,.51)` | translucent cards on dark hero |
| Surface light | `#FFFFFF` | white sections, card backgrounds |
| Surface tinted | `#B1F1D3` (mint) / `#F9F9F7` (cream) | section blocks |
| Accent — primary | `#3DDC91` (bright mint-green) | CTA pills, links, key numbers |
| Accent — alt | `rgba(82,199,144,.6)` (soft mint) | secondary chips, hover states |
| Accent — pop | `#FFCD48` (warm yellow) | one section block ("Ready to Start") |
| Borders (dark) | `#000` / `rgba(19,35,34,.5)` | hairlines on dark |
| Borders (light) | `#D0D3D3` | hairlines on light cards |

**The takeaway for re-skin:** dark surface + ONE bright accent + alternating section backgrounds. They chose forest-green / mint. We can swap to any dark-base + bright-accent pair (slate + electric blue, near-black + Dynatrace purple, etc.) and keep the same system.

## Type scale

**Family:** `Aeonik, sans-serif` (display/body, 1044 uses) + `AeonikFono, sans-serif` (mono, 81 uses for numerics + code-style accents).

**Weight is the standout choice** — almost the entire site is `font-weight: 400` (1138 uses). One single `500` (7 uses). NO bold. This is what makes saucelabs feel "calm editorial" instead of "marketing loud."

**Size scale (px):**

| Token | Size | Line-height | Use |
|-------|------|-------------|-----|
| `display-xl` | 64 | 78.08 (1.22) | h1 hero only |
| `display-lg` | 48 | 52.8 (1.1) | section h2 (3× on page) |
| `display-md` | 40 | 44 (1.1) | secondary section h2 |
| `display-sm` | 32 | 41.6 (1.3) | feature h2 |
| `heading` | 24 | 33.6 (1.4) | card titles (h3) |
| `body-lg` | 20 | 28 (1.4) | section subtitles |
| `body` | 18 | 26.1 (1.45) | paragraph |
| `body-sm` | 16 | 24 (1.5) | default text |
| `body-xs` | 15 / 14 | 24 / 20 | nav links, captions |
| `eyebrow` | 14 (uppercase, tracked) | 20 | h3 section eyebrows ("CASE STUDIES", "INTEGRATE & SETUP") |
| `micro` | 9 | — | legal / micro labels |

**Pattern they reuse on every section:** small uppercase eyebrow (h3, 14px) → big h2 (48px, weight 400) → 18–20px subtitle. Very consistent.

## Spacing — classic 8pt grid, generous

**Padding scale (most-used):** 32, 24, 16, 20, 64, 80, 40, 48, 56, 8, 4
**Margin scale:** 24, 8, 32, 16, 48, 72, 96
**Gap (flex/grid):** 32 dominant, 24, 12
**Section vertical padding:** typically 64–96px top/bottom on desktop
**Container max-width:** `1620px` (very wide — borders close to viewport edges on standard laptops)
**Card max-widths seen:** 340, 400, 550, 655, 957

**Re-skin guidance:** keep the 8pt grid (`4, 8, 16, 24, 32, 48, 64, 80, 96, 128`), keep section padding generous (64+ desktop, 40+ mobile), but our dashboard probably wants a tighter container (1280–1440 max) for data density.

## Radii — large, signature

**Scale:** 6, 8, 10, 16, 20, 32, 50% (circles), 56, 60, 80px

The "big radii" is the second signature move (after the light font weight):
- **Pills** (CTA buttons): radius 56–60px (fully rounded)
- **Cards**: radius 20–32px (chunky, friendly)
- **Avatars/icons**: 50% (circles)
- **Section blocks**: radius 80px on the rounded section corners

**Re-skin guidance:** keep pill buttons + 20–24px card radii — it's what makes the system feel modern. We can dial down section radii (80→24) for a dashboard since data density wants crisper edges.

## Shadows — almost none

Only one shadow detected: `rgba(0,0,0,.04) 1px 0px 9px 2px` — a very soft right-side shadow used in 3 places. Everything else is flat. This is intentional: contrast comes from background color shifts, not elevation.

**Re-skin guidance:** stay flat. Use a 1px border + background tint for "raised" instead of shadow.

## Page hierarchy & section composition

The landing is a **vertical block stack** — each section is its own visual island with its own background color. No floating cards across boundaries.

```
[Header — sticky, 82px, dark]
[Hero — dark forest-green, h1 64px, mint CTA pill, illustration right]
[Logo strip — dark, partner logos in grayscale]
[Section: "One Platform for Continuous Quality" — WHITE bg, h2 48px, product cards]
[Section: "The secret sauce..." — MINT-GREEN bg, h2 48px, quote/testimonial]
[Section: "Sauce Labs + Your Tools" — DARK bg, h2 48px, integration grid]
[Section: "Ready to Start Testing?" — YELLOW bg, h2 48px, CTA pill]
[Section: "What's New" — WHITE bg, h2 40px, 3 article cards]
[Footer — dark, multi-column link grid]
```

**Each content section follows the same recipe:**
1. Small uppercase eyebrow (h3, 14px tracked)
2. Big h2 (48px, weight 400, often 2 lines)
3. Optional 18–20px subtitle line
4. Content block (cards / grid / quote / form)
5. Optional CTA pill

That repeatability is what makes the site feel "designed" without much code surface.

## What translates well to SentinelAI

| Pattern | Keep? | Why |
|---------|-------|-----|
| Dark hero + bright accent | YES | matches "monitoring / agent" mood |
| Pill CTAs (radius ~56px) | YES | distinctive, modern |
| Large 20–24px card radii | YES | friendly, current |
| Weight 400 everywhere | MOSTLY | very calm; we may need 500 for status badges so critical alerts stand out |
| 8pt spacing + generous section padding | YES | proven |
| Alternating section backgrounds | YES (landing) | gives the marketing page rhythm |
| Section composition (eyebrow → big h2 → CTA) | YES | clean editorial |
| No shadows | YES | flat = modern |
| Mono family for numbers | YES | perfect for incident IDs, commit SHAs, p95 numbers |
| 1620px container | NO | too wide for dashboard density |

## What we re-skin (palette swap)

The Sauce Labs palette is theirs. For SentinelAI we want a palette that signals:
- **Observability / "watching the system"** → dark base
- **AI agent presence** → one bold accent
- **Dynatrace track alignment** (chosen track) → echo their visual rhythm without copying logo

Suggested directions for `/frontend-design` to choose between:

1. **Slate + electric cyan** — `#0B1220` base, `#22D3EE` accent. Reads "infra dashboard."
2. **Near-black + violet** — `#0A0A0F` base, `#8B5CF6` accent. Reads "AI / agent."
3. **Deep navy + lime** — `#0F172A` base, `#A3E635` accent. Echoes Dynatrace green without copying it.

(All three keep the same SYSTEM: dark surface, one bright accent, pill buttons, 20px card radii, flat, 8pt grid, weight 400 with 500 reserved for badges.)

## Hand-off to /frontend-design

Treat this file as the design brief. The system above is the constraint set. Apply it to:
1. **Landing page (`/`)** — hero + 3-pillar overview + architecture SVG + CTA. Same block-stack rhythm as saucelabs.
2. **Dashboard (`/dashboard`)** — six pieces from `context/plan/features/04-dashboard.md`. Tighter container (~1440 max), keep card radii at 20px, pill on action buttons only.

Hard rules from `context/plan/features/04-dashboard.md`:
- Dynatrace pillar shown FIRST in every triad.
- Partner names as plain text labels only — no decorative logos (rules §7B).
- Next.js 15 + Tailwind + shadcn/ui stack.
