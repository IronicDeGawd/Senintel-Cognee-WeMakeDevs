import { SectionHeader } from "@/components/ui/SectionHeader";

const tools = [
  {
    name: "Observability",
    pain: "Dynatrace pages at 2am. Someone stares at the problem card, guessing which deploy did it.",
    actor: "on-call engineer",
  },
  {
    name: "Code review",
    pain: "Someone else greps git log, opens the MR, and scrolls the diff looking for anything suspicious.",
    actor: "second engineer",
  },
  {
    name: "AI quality",
    pain: "A third person digs the eval dashboard to check if the model regressed too. Nobody connects the dots.",
    actor: "ML engineer",
  },
];

export function Problem() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1440px] px-6 py-24 lg:px-10 lg:py-32">
        <SectionHeader
          eyebrow="§ 01 · The problem"
          title={
            <>
              <span className="display">Every team runs</span> the same broken
              loop.
            </>
          }
        />
        <p className="mt-6 max-w-2xl text-base leading-relaxed text-ink-muted">
          Production pages, Slack panics, someone greps <code>git log</code>,
          someone else opens the MR, someone else digs the eval dashboard.{" "}
          <span className="text-ink">
            Three tools, three contexts, three humans, fifteen minutes of
            guessing
          </span>{" "}
          — then a roll-back nobody trusts.
        </p>

        {/* Broken loop: three disconnected tools */}
        <div className="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {tools.map((t, i) => (
            <article
              key={t.name}
              className="relative rounded-card-lg border border-crit/25 bg-crit-bg/40 p-7 lg:p-8"
            >
              <div className="flex items-center justify-between">
                <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-crit">
                  Context {i + 1}
                </span>
                <span className="mono text-[0.65rem] text-ink-dim">
                  {t.actor}
                </span>
              </div>
              <h3 className="display-up mt-5 text-2xl text-ink">{t.name}</h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                {t.pain}
              </p>
              {/* Dashed connector to the next disconnected context */}
              {i < tools.length - 1 && (
                <div
                  aria-hidden
                  className="absolute -right-6 top-1/2 hidden w-6 border-t border-dashed border-crit/40 lg:block"
                />
              )}
            </article>
          ))}
        </div>

        {/* Counter-stat handoff */}
        <div className="mt-16 grid grid-cols-1 gap-px overflow-hidden rounded-card-lg border border-line bg-line sm:grid-cols-2">
          <div className="bg-bg-card p-8 lg:p-10">
            <span className="display text-5xl text-crit sm:text-6xl">15 min</span>
            <p className="mono mt-4 text-[0.7rem] uppercase tracking-[0.2em] text-ink-dim">
              of guessing, every incident
            </p>
          </div>
          <div className="card-depth p-8 lg:p-10">
            <span className="display-up text-5xl text-accent sm:text-6xl">
              70 s
            </span>
            <p className="mono mt-4 text-[0.7rem] uppercase tracking-[0.2em] text-ink-muted">
              with the receipts — SentinelAI runs the loop for you ↓
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
