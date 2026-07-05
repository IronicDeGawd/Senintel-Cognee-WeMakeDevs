# AI Quality Gate — Decisions

The gate blocks a deploy when an LLM release regresses past the quality threshold (hallucination or drift). Two sim runs below: a clean release ships, a regressed one is blocked.

## checkout-llm-v1 — ✅ PASS

Quality gate passed: checkout-llm-v1 within thresholds

| Metric | Value | Threshold |
|---|---|---|
| Hallucination rate | 6% | 10% |
| Drift | 3% | 10% |
| Gate passed | True | — |

## checkout-llm-v2 — 🔴 BLOCKED

Deploy blocked: checkout-llm-v2 regressed (hallucination 22%, drift 18%, threshold 10%)

| Metric | Value | Threshold |
|---|---|---|
| Hallucination rate | 22% | 10% |
| Drift | 18% | 10% |
| Gate passed | False | — |
