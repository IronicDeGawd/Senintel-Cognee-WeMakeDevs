"use client";

import Link from "next/link";
import { partnerOrder } from "@/lib/mock";
import { useSignals } from "@/lib/hooks";
import { PillarCard } from "@/components/dashboard/PillarCard";
import { CorrelationMini } from "@/components/dashboard/CorrelationMini";
import { BrowserFrame } from "@/components/landing/BrowserFrame";
import { SectionHeader } from "@/components/ui/SectionHeader";

/** Live mini-dashboard on the landing page. Same SWR hooks and components as
 * /dashboard (keys dedupe; mock fallback keeps it rendering offline). */
export function ProductPreview() {
  const { data } = useSignals();

  return (
    <section className="relative overflow-hidden border-b border-line">
      <div className="absolute inset-x-0 top-0 h-[420px] glow-accent" />
      <div className="relative mx-auto max-w-[1440px] px-6 py-24 lg:px-10 lg:py-32">
        <SectionHeader
          eyebrow="§ 05 · The product"
          title={
            <>
              <span className="display">This is live,</span> not a screenshot.
            </>
          }
          meta={
            <span className="mono inline-flex items-center gap-2 rounded-full border border-line bg-bg-card px-3 py-1 text-[0.65rem] uppercase tracking-[0.2em] text-ink-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-accent pulse-dot" />
              polling · 5s
            </span>
          }
        />
        <p className="mt-6 max-w-2xl text-base leading-relaxed text-ink-muted">
          The same Firestore stream the dashboard renders, polled right here.
          Three pillar cards, one correlated verdict — what your team sees
          when something breaks.
        </p>

        <div className="relative mt-14">
          <BrowserFrame>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              {partnerOrder.map((p, i) => (
                <PillarCard
                  key={p.key}
                  partner={p.partner}
                  label={p.label}
                  isLead={i === 0}
                  signal={data?.[p.key] ?? null}
                  compact
                />
              ))}
            </div>
            <div className="mt-4">
              <CorrelationMini />
            </div>
          </BrowserFrame>
        </div>

        <div className="mt-10 flex justify-center">
          <Link
            href="/dashboard"
            className="group inline-flex items-center gap-3 rounded-pill bg-accent px-7 py-4 text-ink-dark transition hover:bg-accent/90"
          >
            <span className="mono text-[0.7rem] uppercase tracking-[0.22em]">
              Open the full dashboard
            </span>
            <span aria-hidden>→</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
