import Link from "next/link";

export function CTAStrip() {
  return (
    <section className="relative overflow-hidden border-b border-line bg-gradient-to-br from-accent via-accent to-accent-dim text-ink-dark">
      <div className="absolute inset-0 hairgrid opacity-15" />
      <div className="relative mx-auto max-w-[1440px] px-6 py-24 lg:px-10 lg:py-32">
        <div className="grid grid-cols-1 items-end gap-12 lg:grid-cols-[2fr_1fr]">
          <div>
            <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dark/70">
              § 07 · Try it
            </span>
            <h2 className="display-up mt-6 text-5xl leading-[1.04] sm:text-7xl">
              See the <span className="display">correlation</span> light up.
            </h2>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-ink-dark/80">
              The live dashboard pulls Signals from Firestore every five
              seconds. Trigger a cycle from the panel and watch it land.
            </p>
          </div>

          <div className="flex flex-col gap-4 lg:items-end">
            <Link
              href="/dashboard"
              className="group inline-flex items-center justify-between gap-6 rounded-card border-2 border-ink-dark bg-bg px-7 py-5 text-ink transition hover:bg-ink-dark hover:text-bg lg:w-[320px]"
            >
              <span className="mono text-[0.7rem] uppercase tracking-[0.22em]">
                Open live dashboard
              </span>
              <span aria-hidden className="text-xl">
                →
              </span>
            </Link>
            <a
              href="https://gitlab.com/parakramlabs-group/rapid-agent-hackathon/-/merge_requests/1"
              target="_blank"
              rel="noreferrer"
              className="mono inline-flex items-center gap-2 text-[0.7rem] uppercase tracking-[0.22em] text-ink-dark hover:underline"
            >
              View live MR comment ↗
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
