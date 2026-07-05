"use client";

import { partnerOrder } from "@/lib/mock";
import { useSignals } from "@/lib/hooks";
import { PillarCard } from "@/components/dashboard/PillarCard";

export function StatusCards() {
  const { data } = useSignals();

  return (
    <div>
      <div className="mb-8 flex items-end justify-between">
        <div>
          <span className="eyebrow">§ 01 · Status</span>
          <h2 className="display-up mt-3 text-3xl text-ink">
            Pillar latest.
          </h2>
        </div>
        <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
          latest per pillar · 1 doc each
        </span>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {partnerOrder.map((p, i) => (
          <PillarCard
            key={p.key}
            partner={p.partner}
            label={p.label}
            isLead={i === 0}
            signal={data?.[p.key] ?? null}
          />
        ))}
      </div>
    </div>
  );
}
