"use client";

import { useState } from "react";
import type { Signal, Status } from "@/lib/types";

const statusClasses: Record<Status, { tag: string; ring: string; dot: string }> = {
  ok: {
    tag: "bg-ok-bg text-ok border-ok/30",
    ring: "border-line",
    dot: "bg-ok",
  },
  warning: {
    tag: "bg-warn-bg text-warn border-warn/30",
    ring: "border-warn/30",
    dot: "bg-warn",
  },
  critical: {
    tag: "bg-crit-bg text-crit border-crit/30",
    ring: "border-crit/30",
    dot: "bg-crit",
  },
};

/** One pillar's latest-Signal card. `compact` renders the small landing-page
 * preview variant: tighter padding, no detail rows, no footer. */
export function PillarCard({
  partner,
  label,
  isLead,
  signal,
  compact = false,
}: {
  partner: string;
  label: string;
  isLead: boolean;
  signal: Signal | null;
  compact?: boolean;
}) {
  const klass = signal ? statusClasses[signal.status] : statusClasses.ok;
  const [expanded, setExpanded] = useState(false);
  const detailRows = Object.entries(signal?.detail ?? {}).filter(
    ([, v]) => typeof v !== "object" || v === null,
  );

  return (
    <article
      className={`rounded-card-lg border bg-bg-card transition ${klass.ring} ${
        isLead ? "ring-1 ring-accent/30" : ""
      } ${compact ? "p-5" : "p-7"}`}
    >
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`h-2 w-2 rounded-full pulse-dot ${klass.dot}`} />
          <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-muted">
            {partner}
          </span>
          {isLead && !compact && (
            <span className="mono rounded-tag bg-accent/15 px-2 py-0.5 text-[0.6rem] uppercase tracking-[0.18em] text-accent">
              Track
            </span>
          )}
        </div>
        {signal ? (
          <span
            className={`mono rounded-tag border px-2 py-1 text-[0.6rem] uppercase tracking-[0.2em] ${klass.tag}`}
          >
            {signal.status}
          </span>
        ) : (
          <span className="mono rounded-tag border border-line px-2 py-1 text-[0.6rem] uppercase tracking-[0.2em] text-ink-dim">
            awaiting
          </span>
        )}
      </header>

      <h3
        className={`display-up leading-snug text-ink ${
          compact ? "mt-4 text-lg" : "mt-7 text-2xl"
        }`}
      >
        {label}
      </h3>
      <p
        className={`leading-relaxed text-ink-muted ${
          compact ? "mt-2 line-clamp-2 text-xs" : "mt-3 text-sm"
        }`}
      >
        {signal?.headline ?? "Waiting on first Signal from this pillar."}
      </p>

      {!compact && (
        <>
          <dl className="mono mt-6 grid grid-cols-1 gap-2 border-t border-line pt-5 text-[0.7rem] uppercase tracking-[0.16em]">
            {(expanded ? detailRows : detailRows.slice(0, 3)).map(([k, v]) => (
              <div key={k} className="flex items-baseline justify-between gap-3">
                <dt className="shrink-0 text-ink-dim">{k.replace(/_/g, " ")}</dt>
                <dd
                  className={`tabular min-w-0 text-right text-ink ${
                    expanded ? "break-all" : "truncate"
                  }`}
                >
                  {expanded ? String(v) : String(v).slice(0, 32)}
                </dd>
              </div>
            ))}
          </dl>

          <footer className="mt-7 flex items-center justify-between border-t border-line pt-5">
            <span className="mono text-[0.6rem] uppercase tracking-[0.22em] text-ink-dim">
              {signal
                ? new Date(signal.ts).toUTCString().slice(17, 25) + " UTC"
                : "—"}
            </span>
            {detailRows.length > 3 && (
              <button
                onClick={() => setExpanded((e) => !e)}
                aria-expanded={expanded}
                className="mono rounded-pill border border-line-strong px-4 py-1.5 text-[0.6rem] uppercase tracking-[0.2em] text-ink-muted transition hover:border-ink hover:text-ink"
              >
                {expanded ? "Collapse ←" : "Expand →"}
              </button>
            )}
          </footer>
        </>
      )}
    </article>
  );
}
