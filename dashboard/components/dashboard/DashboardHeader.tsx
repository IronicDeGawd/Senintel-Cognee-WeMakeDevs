"use client";

import { useEffect, useState } from "react";

export function DashboardHeader() {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const i = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(i);
  }, []);

  const secs = tick % 7;

  return (
    <div className="flex flex-wrap items-end justify-between gap-6 border-b border-line pb-10">
      <div>
        <span className="eyebrow">Control room</span>
        <h1 className="display-up mt-3 text-4xl text-ink sm:text-5xl">
          <span className="display">Three pillars,</span> one stream.
        </h1>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-ink-muted">
          Polling the Cloud Run signal-store every five seconds. Dynatrace
          leads the row — your chosen track surfaces first.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span className="inline-flex items-center gap-2 rounded-pill border border-line bg-bg-card px-4 py-2">
          <span className="h-1.5 w-1.5 rounded-full bg-accent pulse-dot" />
          <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-muted">
            Live · last <span className="tabular text-ink">{secs}s</span>
          </span>
        </span>
        <span className="mono inline-flex items-center gap-2 rounded-pill border border-line bg-bg-card px-4 py-2 text-[0.65rem] uppercase tracking-[0.22em] text-ink-muted">
          env: <span className="tabular text-ink">production</span>
        </span>
      </div>
    </div>
  );
}
