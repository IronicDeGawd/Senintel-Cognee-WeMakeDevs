"use client";

import { useHistory } from "@/lib/hooks";
import type { Pillar, Status } from "@/lib/types";

const pillarLabel: Record<Pillar, string> = {
  production: "PROD · DYNATRACE",
  code: "CODE · GITLAB",
  ai_quality: "AI · ARIZE",
};

const dotColor: Record<Status, string> = {
  ok: "bg-ok",
  warning: "bg-warn",
  critical: "bg-crit",
};

export function ActivityTimeline() {
  const { data } = useHistory(20);
  const rows = data ?? [];

  return (
    <div className="flex h-full flex-col rounded-card-lg border border-line bg-bg-card p-7">
      <header className="flex items-end justify-between border-b border-line pb-5">
        <div>
          <span className="eyebrow">§ 03 · Timeline</span>
          <h3 className="display-up mt-3 text-2xl text-ink">All pillars.</h3>
        </div>
        <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
          last {rows.length || 20}
        </span>
      </header>

      <ol className="mt-5 grid grid-cols-1 gap-0">
        {rows.map((s, i) => (
          <li
            key={s.id ?? `${s.pillar}-${s.ts}-${i}`}
            className="grid grid-cols-[64px_1fr_auto] items-start gap-4 border-b border-line/60 py-4 last:border-b-0"
          >
            <span className="mono pt-0.5 text-[0.7rem] tabular uppercase tracking-[0.18em] text-ink-dim">
              {new Date(s.ts).toISOString().slice(11, 16)}
            </span>
            <div className="flex min-w-0 items-start gap-3">
              <span
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${dotColor[s.status]} ${
                  i === 0 ? "pulse-dot" : ""
                }`}
              />
              <div className="min-w-0">
                <p className="mono text-[0.6rem] uppercase tracking-[0.2em] text-ink-dim">
                  {pillarLabel[s.pillar]}
                </p>
                <p className="mt-1 truncate text-sm text-ink">{s.headline}</p>
              </div>
            </div>
            <span className="mono mt-1 hidden text-[0.6rem] uppercase tracking-[0.18em] text-ink-dim sm:inline">
              {(s.id ?? "").slice(-4)}
            </span>
          </li>
        ))}
        {rows.length === 0 && (
          <li className="py-6 text-sm text-ink-muted">
            Waiting on first Signals…
          </li>
        )}
      </ol>
    </div>
  );
}
