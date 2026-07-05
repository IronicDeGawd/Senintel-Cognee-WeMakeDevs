"use client";

import { useState } from "react";
import { postTrigger, postDemoScenario, ApiUnconfiguredError } from "@/lib/api";
import type { Pillar } from "@/lib/types";
import { HintChip } from "@/components/ui/HintChip";

type RunState = "idle" | "running" | "done" | "error";

const triggers: ReadonlyArray<{
  key: Pillar;
  partner: string;
  label: string;
  api: string;
  service: string;
  lead: boolean;
}> = [
  {
    key: "production",
    partner: "Dynatrace",
    label: "Run Production Cycle",
    api: "POST /trigger/production",
    service: "sentinelai-poller",
    lead: true,
  },
  {
    key: "code",
    partner: "GitLab",
    label: "Run Code Review · MR !1",
    api: "POST /trigger/code",
    service: "sentinelai-gateway",
    lead: false,
  },
  {
    key: "ai_quality",
    partner: "Arize",
    label: "Run AI Quality Gate",
    api: "POST /trigger/ai_quality",
    service: "sentinelai-eval-runner",
    lead: false,
  },
];

export function TriggerPanel() {
  return (
    <div>
      <header className="mb-8 flex items-end justify-between">
        <div>
          <span className="eyebrow">§ 05 · Triggers</span>
          <h2 className="display-up mt-3 text-3xl text-ink">
            <span className="display">Fire</span> a cycle. Watch it land.
          </h2>
        </div>
        <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
          proxies through dashboard_api → cloud run
        </span>
      </header>

      <div className="mb-5">
        <HintChip id="run-scenario">
          First time here? Press <span className="text-ink">▶ Run scenario</span>{" "}
          — the full 70s arc lights up every panel above.
        </HintChip>
      </div>

      <DemoScenarioCard />

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3">
        {triggers.map((t) => (
          <TriggerCard key={t.key} t={t} />
        ))}
      </div>
    </div>
  );
}

function DemoScenarioCard() {
  const [state, setState] = useState<RunState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [errMsg, setErrMsg] = useState<string | null>(null);
  const [steps, setSteps] = useState<Record<string, unknown> | null>(null);

  const run = async () => {
    setState("running");
    setElapsed(0);
    setErrMsg(null);
    setSteps(null);
    const interval = setInterval(() => setElapsed((e) => e + 1), 1000);
    try {
      const out = await postDemoScenario();
      clearInterval(interval);
      setSteps((out.result?.steps as Record<string, unknown>) ?? null);
      setState("done");
      setTimeout(() => setState("idle"), 8000);
    } catch (err) {
      clearInterval(interval);
      const msg =
        err instanceof ApiUnconfiguredError
          ? "Demo Director not wired (dev mode)"
          : err instanceof Error
            ? err.message
            : "unknown error";
      setErrMsg(msg);
      setState("error");
      setTimeout(() => setState("idle"), 6000);
    }
  };

  const stateCopy =
    state === "idle"
      ? "idle"
      : state === "running"
        ? `running · ${elapsed}s`
        : state === "done"
          ? "done — check timeline + status cards"
          : errMsg ?? "error";

  const stateColor =
    state === "idle"
      ? "text-ink-dim border-line"
      : state === "running"
        ? "text-accent border-accent/40 bg-accent/10"
        : state === "done"
          ? "text-ok border-ok/30 bg-ok-bg"
          : "text-crit border-crit/30 bg-crit-bg";

  return (
    <article className="rounded-card-lg border border-accent/40 bg-bg-card p-7 ring-1 ring-accent/30 lg:p-9">
      <header className="flex items-start justify-between gap-4">
        <div>
          <span className="mono text-[0.6rem] uppercase tracking-[0.22em] text-accent">
            Demo Director
          </span>
          <h3 className="display-up mt-2 text-2xl leading-tight text-ink sm:text-3xl">
            <span className="display">Run scenario</span> — checkout N+1.
          </h3>
          <p className="mt-2 max-w-2xl text-sm text-ink-muted">
            Seeds Dynatrace with a fake p95 spike + deployment event, fires the
            real GitLab MR webhook, runs the AI Quality Gate, and triggers the
            Production Sentinel cycle. All four pillar cards refresh live below.
          </p>
        </div>
        <button
          onClick={run}
          disabled={state === "running"}
          className="mono shrink-0 rounded-pill bg-accent px-6 py-3 text-[0.7rem] uppercase tracking-[0.2em] text-ink-dark transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          ▶ Run scenario
        </button>
      </header>

      <div className="mt-7 flex flex-wrap items-center gap-3 border-t border-line pt-5">
        <span
          className={`mono inline-flex items-center gap-2 rounded-pill border px-3 py-1.5 text-[0.6rem] uppercase tracking-[0.2em] ${stateColor}`}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-current" />
          {stateCopy}
        </span>
        {steps &&
          Object.entries(steps).map(([k, v]) => {
            const ok =
              typeof v === "object" &&
              v !== null &&
              !(v as Record<string, unknown>).error &&
              (v as Record<string, unknown>).posted !== false;
            return (
              <span
                key={k}
                className={`mono inline-flex items-center gap-2 rounded-tag border px-2 py-1 text-[0.6rem] uppercase tracking-[0.18em] ${
                  ok
                    ? "border-ok/30 bg-ok-bg text-ok"
                    : "border-warn/30 bg-warn-bg text-warn"
                }`}
              >
                {k}
                <span>{ok ? "✓" : "skip"}</span>
              </span>
            );
          })}
      </div>
    </article>
  );
}

function TriggerCard({
  t,
}: {
  t: (typeof triggers)[number];
}) {
  const [state, setState] = useState<RunState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const run = async () => {
    setState("running");
    setElapsed(0);
    setErrMsg(null);
    const interval = setInterval(() => setElapsed((e) => e + 1), 1000);

    try {
      await postTrigger(t.key);
      clearInterval(interval);
      setState("done");
      setTimeout(() => setState("idle"), 4000);
    } catch (err) {
      clearInterval(interval);
      const msg =
        err instanceof ApiUnconfiguredError
          ? "API not wired (dev mode)"
          : err instanceof Error
            ? err.message
            : "unknown error";
      setErrMsg(msg);
      setState("error");
      setTimeout(() => setState("idle"), 5000);
    }
  };

  const stateCopy =
    state === "idle"
      ? "idle"
      : state === "running"
        ? `running · ${elapsed}s`
        : state === "done"
          ? "done"
          : errMsg ?? "error";

  const stateColor =
    state === "idle"
      ? "text-ink-dim border-line"
      : state === "running"
        ? "text-accent border-accent/40 bg-accent/10"
        : state === "done"
          ? "text-ok border-ok/30 bg-ok-bg"
          : "text-crit border-crit/30 bg-crit-bg";

  return (
    <article
      className={`rounded-card-lg border bg-bg-card p-7 ${
        t.lead ? "border-accent/40 ring-1 ring-accent/20" : "border-line"
      }`}
    >
      <header className="flex items-center justify-between">
        <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
          {t.partner}
        </span>
        {t.lead && (
          <span className="mono rounded-tag bg-accent/15 px-2 py-0.5 text-[0.6rem] uppercase tracking-[0.18em] text-accent">
            Track
          </span>
        )}
      </header>

      <h3 className="display-up mt-6 text-2xl leading-tight text-ink">
        {t.label}
      </h3>

      <p className="mono mt-5 text-[0.65rem] uppercase tracking-[0.18em] text-ink-muted">
        {t.api}
        <span className="mx-2 text-ink-faint">·</span>
        {t.service}
      </p>

      <div className="mt-7 flex items-center justify-between border-t border-line pt-5">
        <span
          className={`mono inline-flex items-center gap-2 rounded-pill border px-3 py-1.5 text-[0.6rem] uppercase tracking-[0.2em] ${stateColor}`}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-current" />
          {stateCopy}
        </span>
        <button
          onClick={run}
          disabled={state === "running"}
          className={`mono inline-flex items-center gap-2 rounded-pill px-5 py-2 text-[0.65rem] uppercase tracking-[0.2em] transition disabled:cursor-not-allowed disabled:opacity-50 ${
            t.lead
              ? "bg-accent text-ink-dark hover:bg-accent/90"
              : "border border-line-strong text-ink hover:border-ink"
          }`}
        >
          ▶ Run
        </button>
      </div>
    </article>
  );
}
