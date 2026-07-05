"use client";

import useSWR from "swr";
import { fetcher, ApiUnconfiguredError } from "./api";
import {
  mockCorrelation,
  mockDrift,
  mockSignals,
  mockTimeline,
} from "./mock";
import type {
  CorrelationResponse,
  Pillar,
  QualityTrendRow,
  Signal,
} from "./types";

const REFRESH_MS = 5000;

// Translate our mocked CorrelationView shape into the API CorrelationResponse
// shape, so the panel can speak one type even when running on mocks.
const mockCorrelationResponse: CorrelationResponse = {
  production: {
    title: "Checkout latency spike",
    service: mockCorrelation.prod.service,
    suspect_commit: mockCorrelation.commit.sha,
    summary: `${mockCorrelation.prod.metric.toUpperCase()} ${mockCorrelation.prod.before} → ${mockCorrelation.prod.after}`,
    severity: "high",
  },
  code: {
    mr_id: 1,
    commit: mockCorrelation.commit.sha,
    findings: [
      {
        severity: mockCorrelation.review.severity.toLowerCase(),
        file: mockCorrelation.review.file,
        message: mockCorrelation.review.title,
        category: "performance",
      },
    ],
  },
  verdict: mockCorrelation.verdict,
};

const mockSignalsResponse: Record<Pillar, Signal | null> = {
  production: mockSignals.production,
  code: mockSignals.code,
  ai_quality: mockSignals.ai_quality,
};

function fallbackOnUnconfigured<T>(value: T) {
  return (err: unknown) => {
    if (err instanceof ApiUnconfiguredError) return value;
    throw err;
  };
}

export function useSignals() {
  return useSWR<Record<Pillar, Signal | null>>(
    "/signals",
    (path: string) =>
      fetcher<Record<Pillar, Signal | null>>(path).catch(
        fallbackOnUnconfigured(mockSignalsResponse),
      ),
    {
      refreshInterval: REFRESH_MS,
      fallbackData: mockSignalsResponse,
      keepPreviousData: true,
    },
  );
}

export function useHistory(limit = 20) {
  return useSWR<Signal[]>(
    `/history?limit=${limit}`,
    (path: string) =>
      fetcher<Signal[]>(path).catch(fallbackOnUnconfigured(mockTimeline)),
    {
      refreshInterval: REFRESH_MS,
      fallbackData: mockTimeline,
      keepPreviousData: true,
    },
  );
}

export function useCorrelation() {
  return useSWR<CorrelationResponse>(
    "/correlation",
    (path: string) =>
      fetcher<CorrelationResponse>(path).catch(
        fallbackOnUnconfigured(mockCorrelationResponse),
      ),
    {
      refreshInterval: REFRESH_MS,
      fallbackData: mockCorrelationResponse,
      keepPreviousData: true,
    },
  );
}

export function useQualityTrends(limit = 30) {
  // Map our richer EvalPoint mocks (with explicit threshold) into the API row
  // shape (hallucination_rate / drift / threshold), so the chart speaks one
  // type. Reverses to oldest-first for the time series axis.
  const fallback: QualityTrendRow[] = mockDrift.map((p) => ({
    hallucination_rate: p.hallucination,
    drift: p.drift,
    threshold: p.threshold,
    ts: p.ts,
  }));
  return useSWR<QualityTrendRow[]>(
    `/trends/quality?limit=${limit}`,
    (path: string) =>
      fetcher<QualityTrendRow[]>(path).catch(fallbackOnUnconfigured(fallback)),
    {
      refreshInterval: REFRESH_MS,
      fallbackData: fallback,
      keepPreviousData: true,
    },
  );
}

export function useMemory() {
  const fallback: any[] = [
    {
      id: "mem-001",
      repo: "main-backend",
      file: "checkout/views.py",
      rule: "Avoid N+1 queries in loops",
      comment: "In PR #42 (commit abc1234), we introduced a severe N+1 query by looping over orders and querying items individually. This caused a DB outage during peak traffic. Always use `select_related` or `prefetch_related` instead of querying inside a loop.",
      severity: "critical",
      source: "post_merge_bug",
      commit: "abc1234",
      ts: "2026-06-10T12:00:00Z"
    }
  ];
  return useSWR<any[]>(
    `/memory/recall`,
    (path: string) => fetcher<any[]>(path).catch(fallbackOnUnconfigured(fallback)),
    {
      refreshInterval: REFRESH_MS,
      fallbackData: fallback,
      keepPreviousData: true,
    },
  );
}

