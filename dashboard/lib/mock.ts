import type { EvalPoint, Signal } from "./types";

// Local CorrelationView shape — used only by mock.ts to build the
// CorrelationResponse fallback in lib/hooks.ts. The live API exposes
// CorrelationResponse instead (see lib/types.ts).
interface CorrelationView {
  prod: { service: string; metric: string; before: string; after: string; ts: string };
  commit: { sha: string; service: string; author: string; mr_id: string };
  review: { severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"; title: string; file: string };
  verdict: string;
  mr_url: string;
}

// Mocked Signals — used until dashboard_api/Firestore wiring lands (D6).
// Dynatrace pillar = "production". Always listed first in UI.

export const mockSignals: Record<Signal["pillar"], Signal> = {
  production: {
    pillar: "production",
    status: "critical",
    headline: "checkout-service p95 180 → 2400ms",
    detail: {
      service: "checkout-service",
      suspect_commit: "abc1234",
      next_action: "Roll back MR !42 / commit abc1234",
      observed_ms: 2400,
      baseline_ms: 180,
    },
    ts: "2026-06-10T06:22:17Z",
    id: "sig_prod_8f1c",
  },
  code: {
    pillar: "code",
    status: "warning",
    headline: "MR !1 — 1 HIGH (N+1 query in views.py)",
    detail: {
      mr_id: "1",
      severity: "1 high · 2 med",
      posted_to: "gitlab.com/...#note_3440188164",
    },
    ts: "2026-06-10T06:21:55Z",
    id: "sig_code_4a72",
  },
  ai_quality: {
    pillar: "ai_quality",
    status: "critical",
    headline: "Deploy blocked — hallucination 22%, drift 18%",
    detail: {
      suite: "checkout-llm-v2",
      hallucination: 0.22,
      drift: 0.18,
      threshold: 0.1,
    },
    ts: "2026-06-10T06:20:09Z",
    id: "sig_ai_b1d8",
  },
};

export const mockTimeline: Signal[] = [
  mockSignals.production,
  mockSignals.code,
  mockSignals.ai_quality,
  {
    pillar: "code",
    status: "ok",
    headline: "MR !1 — re-review clean",
    detail: { mr_id: "1" },
    ts: "2026-06-10T06:15:02Z",
    id: "sig_code_2c11",
  },
  {
    pillar: "production",
    status: "warning",
    headline: "checkout-service query volume 8×",
    detail: { service: "checkout-service" },
    ts: "2026-06-10T06:14:48Z",
    id: "sig_prod_7e22",
  },
  {
    pillar: "ai_quality",
    status: "ok",
    headline: "checkout-llm-v1 eval pass",
    detail: { suite: "checkout-llm-v1" },
    ts: "2026-06-10T06:08:31Z",
    id: "sig_ai_3f50",
  },
  {
    pillar: "production",
    status: "ok",
    headline: "checkout-service p95 nominal",
    detail: { service: "checkout-service" },
    ts: "2026-06-10T05:58:12Z",
    id: "sig_prod_9aa0",
  },
  {
    pillar: "code",
    status: "ok",
    headline: "MR !2 — clean diff",
    detail: { mr_id: "2" },
    ts: "2026-06-10T05:52:00Z",
    id: "sig_code_117f",
  },
];

export const mockDrift: EvalPoint[] = Array.from({ length: 30 }, (_, i) => {
  const base = i / 29;
  const hallucination =
    i < 18
      ? 0.04 + Math.sin(i * 0.6) * 0.015 + 0.01
      : 0.05 + (i - 18) * 0.014 + Math.sin(i * 0.4) * 0.01;
  const drift =
    i < 20
      ? 0.03 + Math.cos(i * 0.5) * 0.015 + 0.015
      : 0.04 + (i - 20) * 0.018 + Math.cos(i * 0.3) * 0.01;
  return {
    ts: new Date(Date.now() - (29 - i) * 6 * 60_000).toISOString(),
    hallucination: Math.max(0.005, Math.min(0.3, hallucination)),
    drift: Math.max(0.005, Math.min(0.3, drift)),
    threshold: 0.1,
    _i: base,
  } as EvalPoint;
});

export const mockCorrelation: CorrelationView = {
  prod: {
    service: "checkout-service",
    metric: "p95",
    before: "180ms",
    after: "2400ms",
    ts: "2026-06-10T06:22:17Z",
  },
  commit: {
    sha: "abc1234",
    service: "checkout-service",
    author: "dev@parakramlabs",
    mr_id: "!1",
  },
  review: {
    severity: "HIGH",
    title: "N+1 query — removed select_related/prefetch_related",
    file: "checkout/views.py",
  },
  verdict: "Roll back MR !1 / commit abc1234",
  mr_url:
    "https://gitlab.com/parakramlabs-group/rapid-agent-hackathon/-/merge_requests/1",
};

export const partnerOrder: { key: Signal["pillar"]; partner: string; label: string }[] = [
  { key: "production", partner: "Dynatrace", label: "Production Sentinel" },
  { key: "code", partner: "GitLab", label: "Code Guardian" },
  { key: "ai_quality", partner: "Arize", label: "AI Quality Gate" },
];
