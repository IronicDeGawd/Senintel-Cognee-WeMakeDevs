"use client";

import { partnerOrder } from "@/lib/mock";
import { useSignals } from "@/lib/hooks";
import { useScrollSpy } from "@/lib/useScrollSpy";
import type { Status } from "@/lib/types";

const SECTIONS = [
  { id: "overview", label: "Overview" },
  { id: "correlation", label: "Correlation" },
  { id: "timeline", label: "Timeline" },
  { id: "quality", label: "AI Quality" },
  { id: "triggers", label: "Triggers" },
] as const;

const SECTION_IDS = SECTIONS.map((s) => s.id);

const dotColor: Record<Status, string> = {
  ok: "bg-ok",
  warning: "bg-warn",
  critical: "bg-crit",
};

/** Dashboard section-anchor nav. Desktop: sticky left sidebar with scroll-spy
 * + per-pillar live status dots. Mobile: sticky horizontal pill bar. Reuses
 * the dashboard's SWR key, so no extra polling. */
export function SidebarNav() {
  const active = useScrollSpy(SECTION_IDS);
  const { data } = useSignals();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:block">
        <div className="sticky top-16 flex h-[calc(100vh-4rem)] flex-col gap-10 overflow-y-auto border-r border-line py-10 pr-8">
          <nav aria-label="Dashboard sections">
            <p className="eyebrow mb-4">Sections</p>
            <ul className="grid gap-1">
              {SECTIONS.map((s) => (
                <li key={s.id}>
                  <a
                    href={`#${s.id}`}
                    aria-current={active === s.id ? "true" : undefined}
                    className={`mono flex items-center gap-3 rounded-tag border-l-2 px-3 py-2 text-[0.7rem] uppercase tracking-[0.16em] transition ${
                      active === s.id
                        ? "border-accent bg-accent/10 text-accent"
                        : "border-transparent text-ink-muted hover:bg-bg-card hover:text-ink"
                    }`}
                  >
                    {s.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div>
            <p className="eyebrow mb-4">Pillars</p>
            <ul className="grid gap-2.5">
              {partnerOrder.map((p) => {
                const status = data?.[p.key]?.status;
                return (
                  <li
                    key={p.key}
                    className="mono flex items-center gap-3 text-[0.65rem] uppercase tracking-[0.18em] text-ink-muted"
                  >
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        status ? `pulse-dot ${dotColor[status]}` : "bg-line-strong"
                      }`}
                    />
                    {p.partner}
                  </li>
                );
              })}
            </ul>
          </div>

          <div className="mt-auto grid grid-cols-1 gap-3 border-t border-line pt-6">
            <span className="mono inline-flex items-center gap-2 text-[0.6rem] uppercase tracking-[0.2em] text-ink-dim">
              <span className="h-1.5 w-1.5 rounded-full bg-accent pulse-dot" />
              polling · 5s
            </span>
            <a
              href="#triggers"
              className="mono inline-flex items-center gap-2 rounded-pill border border-accent/40 bg-accent/10 px-4 py-2 text-[0.65rem] uppercase tracking-[0.18em] text-accent transition hover:bg-accent hover:text-ink-dark"
            >
              ▶ Run scenario
            </a>
          </div>
        </div>
      </aside>

      {/* Mobile pill bar */}
      <div className="no-scrollbar sticky top-16 z-30 -mx-6 overflow-x-auto border-b border-line bg-bg/90 px-6 py-3 backdrop-blur-md lg:hidden">
        <ul className="flex gap-2">
          {SECTIONS.map((s) => (
            <li key={s.id} className="shrink-0">
              <a
                href={`#${s.id}`}
                aria-current={active === s.id ? "true" : undefined}
                className={`mono inline-flex items-center rounded-pill border px-4 py-1.5 text-[0.65rem] uppercase tracking-[0.16em] transition ${
                  active === s.id
                    ? "border-accent/40 bg-accent/10 text-accent"
                    : "border-line text-ink-muted"
                }`}
              >
                {s.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
