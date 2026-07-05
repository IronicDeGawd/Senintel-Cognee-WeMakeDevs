"use client";

import { useCorrelation } from "@/lib/hooks";

/** Compact one-row correlation strip for the landing-page preview:
 * Problem → suspect commit → review, plus the verdict line. */
export function CorrelationMini() {
  const { data } = useCorrelation();
  const finding = data?.code?.findings?.[0];

  return (
    <div className="rounded-card border border-line bg-bg-card p-5">
      <div className="mono flex flex-wrap items-center gap-x-3 gap-y-2 text-[0.68rem] text-ink-muted">
        <Chip n="01" label="Dynatrace">
          {data?.production?.title ?? "awaiting problem"}
        </Chip>
        <span aria-hidden className="text-accent">
          →
        </span>
        <Chip n="02" label="Commit">
          <span className="text-accent">
            {data?.production?.suspect_commit ?? "—"}
          </span>
        </Chip>
        <span aria-hidden className="text-accent">
          →
        </span>
        <Chip n="03" label="GitLab">
          {finding?.file ?? "awaiting review"}
        </Chip>
      </div>
      <p className="display mt-4 text-xl leading-snug text-ink">
        {data?.verdict ?? "Awaiting correlated verdict…"}
      </p>
    </div>
  );
}

function Chip({
  n,
  label,
  children,
}: {
  n: string;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <span className="inline-flex max-w-full items-center gap-2 rounded-tag border border-line bg-bg px-2.5 py-1">
      <span className="text-ink-dim">{n}</span>
      <span className="uppercase tracking-[0.14em] text-ink-dim">{label}</span>
      <span className="min-w-0 truncate text-ink">{children}</span>
    </span>
  );
}
