import Link from "next/link";
import { SectionHeader } from "@/components/ui/SectionHeader";

const metrics = [
  { k: "138", label: "pytest green" },
  { k: "~70s", label: "incident to verdict" },
  { k: "6", label: "Cloud Run services" },
  { k: "0", label: "ruff findings" },
];

const useCases = [
  {
    pillar: "Production",
    title: "p95 spikes at 2am",
    body: "A real Davis problem opens in Dynatrace. SentinelAI names the file, the regression class, and the rollback target — before anyone is paged awake.",
  },
  {
    pillar: "Code",
    title: "An MR opens",
    body: "The webhook fires, Gemini reviews the diff, and a severity-grouped note lands on the merge request in under ten seconds.",
  },
  {
    pillar: "AI Quality",
    title: "A model regresses",
    body: "Adversarial evals catch hallucination jumping to 22% — and the deploy gate closes before the model leaves staging.",
  },
];

export function Trust() {
  return (
    <section className="border-b border-line bg-bg-raised">
      <div className="mx-auto max-w-[1440px] px-6 py-24 lg:px-10 lg:py-32">
        <SectionHeader
          eyebrow="§ 06 · Receipts"
          title={
            <>
              <span className="display">No staged screenshots.</span> Real
              backends, real artifacts.
            </>
          }
        />

        {/* Metric strip — every number is true */}
        <div className="mt-14 grid grid-cols-2 gap-px overflow-hidden rounded-card-lg border border-line bg-line lg:grid-cols-4">
          {metrics.map((m) => (
            <div key={m.label} className="bg-bg-card p-7 lg:p-8">
              <span className="display-up text-4xl tabular text-ink lg:text-5xl">
                {m.k}
              </span>
              <p className="mono mt-3 text-[0.65rem] uppercase tracking-[0.2em] text-ink-dim">
                {m.label}
              </p>
            </div>
          ))}
        </div>

        {/* Receipt links */}
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <a
            href="https://gitlab.com/parakramlabs-group/rapid-agent-hackathon/-/merge_requests/1"
            target="_blank"
            rel="noreferrer"
            className="group rounded-card-lg border border-line bg-bg-card p-7 transition hover:border-accent/40 lg:p-8"
          >
            <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
              Receipt · GitLab
            </span>
            <h3 className="display-up mt-4 text-2xl text-ink">
              The review note is on a real MR.{" "}
              <span aria-hidden className="text-accent transition group-hover:translate-x-1">
                ↗
              </span>
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-ink-muted">
              Open MR !1 and read the Gemini-authored, severity-grouped comment
              SentinelAI posted — on gitlab.com, not in a mock.
            </p>
          </a>
          <Link
            href="/dashboard"
            className="group rounded-card-lg border border-line bg-bg-card p-7 transition hover:border-accent/40 lg:p-8"
          >
            <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
              Receipt · Dynatrace
            </span>
            <h3 className="display-up mt-4 text-2xl text-ink">
              The problem is a real Davis problem.{" "}
              <span aria-hidden className="text-accent transition group-hover:translate-x-1">
                →
              </span>
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-ink-muted">
              Scenario events land in a live Dynatrace tenant; Davis promotes
              them into real problems the cycle picks up. Watch it on the
              dashboard.
            </p>
          </Link>
        </div>

        {/* Use cases */}
        <div className="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {useCases.map((u) => (
            <article
              key={u.pillar}
              className="rounded-card-lg border border-line bg-bg-card p-7 lg:p-8"
            >
              <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-accent">
                {u.pillar}
              </span>
              <h3 className="display-up mt-4 text-2xl text-ink">{u.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                {u.body}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
