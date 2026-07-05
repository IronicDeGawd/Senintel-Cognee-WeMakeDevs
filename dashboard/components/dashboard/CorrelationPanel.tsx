"use client";

import { useCorrelation } from "@/lib/hooks";

const MR_BASE =
  "https://gitlab.com/parakramlabs-group/rapid-agent-hackathon/-/merge_requests/";

export function CorrelationPanel() {
  const { data } = useCorrelation();
  const prod = data?.production ?? null;
  const code = data?.code ?? null;
  const verdict = data?.verdict ?? null;

  const lead = code?.findings?.[0];
  const review = {
    severity: (lead?.severity ?? "high").toUpperCase(),
    title: lead?.message ?? (code ? "Review available" : ""),
    file: lead?.file ?? "—",
  };

  const mrId = code?.mr_id?.toString() ?? "";
  const mrUrl = mrId ? `${MR_BASE}${mrId}` : MR_BASE + "1";

  return (
    <div>
        <header className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <span className="eyebrow">§ 02 · The money shot</span>
            <h2 className="display-up mt-3 text-4xl text-ink sm:text-5xl">
              <span className="display">Why did checkout</span> slow down?
            </h2>
          </div>
          <span className="mono inline-flex items-center gap-2 rounded-pill border border-line bg-bg-card px-4 py-2 text-[0.65rem] uppercase tracking-[0.22em] text-ink-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            joined live · GET /correlation
          </span>
        </header>

        <div className="mt-12 overflow-hidden rounded-card-lg border border-line">
          <div className="grid grid-cols-1 gap-px bg-line lg:grid-cols-3">
            <Stage
              i="01"
              partner="Dynatrace"
              kind="Problem"
              title={prod?.summary ?? prod?.title ?? "No production signal yet"}
              rows={[
                ["service", prod?.service ?? "—"],
                ["severity", (prod?.severity ?? "—").toUpperCase()],
                ["commit", prod?.suspect_commit ?? "—"],
              ]}
              lead
            />
            <Stage
              i="02"
              partner="Joined"
              kind="Suspect commit"
              title={prod?.suspect_commit ?? "—"}
              rows={[
                ["service", prod?.service ?? "—"],
                ["mr", mrId ? `!${mrId}` : "—"],
                ["join", prod && code ? "matched" : "pending"],
              ]}
            />
            <Stage
              i="03"
              partner="GitLab"
              kind="Review"
              title={code ? `${review.severity} · ${review.title}` : "No review yet"}
              rows={[
                ["file", review.file],
                ["mr", mrId ? `!${mrId}` : "—"],
                ["commit", code?.commit ?? "—"],
              ]}
            />
          </div>

          <div className="bg-bg p-8 lg:p-10">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <span className="eyebrow">Verdict</span>
                <p className="display-up mt-3 text-2xl leading-snug text-ink sm:text-3xl">
                  <span className="display">
                    {verdict ?? "Awaiting correlation…"}
                  </span>
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <a
                  href={mrUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="mono inline-flex items-center gap-2 rounded-pill bg-accent px-6 py-3 text-[0.7rem] uppercase tracking-[0.2em] text-ink-dark transition hover:bg-accent/90"
                >
                  View MR comment on GitLab ↗
                </a>
                <button className="mono inline-flex items-center gap-2 rounded-pill border border-line-strong px-6 py-3 text-[0.7rem] uppercase tracking-[0.2em] text-ink-muted transition hover:border-ink hover:text-ink">
                  Incident JSON →
                </button>
              </div>
            </div>
          </div>
        </div>
    </div>
  );
}

function Stage({
  i,
  partner,
  kind,
  title,
  rows,
  lead,
}: {
  i: string;
  partner: string;
  kind: string;
  title: string;
  rows: [string, string][];
  lead?: boolean;
}) {
  return (
    <div className="relative flex flex-col gap-6 bg-bg p-8 lg:p-10">
      <header className="flex items-center justify-between">
        <span className="mono flex items-center gap-3 text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
          <span className="display-up text-3xl tabular text-ink-faint">{i}</span>
          {partner}
          {lead && (
            <span className="rounded-tag bg-accent/15 px-2 py-0.5 text-[0.6rem] tracking-[0.18em] text-accent">
              Track
            </span>
          )}
        </span>
        <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-muted">
          {kind}
        </span>
      </header>

      <p className="display-up mono break-all text-2xl leading-snug text-ink">
        {title}
      </p>

      <dl className="mono grid grid-cols-1 gap-2 border-t border-line pt-5 text-[0.7rem] uppercase tracking-[0.16em]">
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-baseline justify-between gap-3">
            <dt className="shrink-0 text-ink-dim">{k}</dt>
            <dd className="tabular min-w-0 truncate text-right text-ink">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
