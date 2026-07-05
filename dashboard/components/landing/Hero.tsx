import Link from "next/link";

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-line">
      <div className="absolute inset-0 hairgrid-soft opacity-60" />
      <div className="absolute inset-x-0 top-0 h-[520px] glow-accent" />

      <div className="relative mx-auto max-w-[1440px] px-6 pt-20 pb-28 lg:px-10 lg:pt-32 lg:pb-40">
        {/* Eyebrow + status */}
        <div className="flex flex-wrap items-center gap-4 rise">
          <span className="eyebrow">Operations · Code · AI Quality</span>
          <span className="inline-flex items-center gap-2 rounded-full border border-line bg-bg-card px-3 py-1">
            <span className="h-1.5 w-1.5 rounded-full bg-accent pulse-dot" />
            <span className="mono text-[0.65rem] uppercase tracking-[0.2em] text-ink-muted">
              Live · Dynatrace track
            </span>
          </span>
        </div>

        {/* Display */}
        <h1 className="mt-10 max-w-5xl text-[clamp(2.4rem,6.4vw,5.8rem)] leading-[1.04] text-ink rise rise-delay-1">
          <span className="display-up">The autonomous engineer</span>
          <br />
          <span className="display">that watches your</span>{" "}
          <span className="display-up">delivery pipeline.</span>
        </h1>

        {/* Sub */}
        <p className="mt-10 max-w-2xl text-lg leading-relaxed text-ink-muted rise rise-delay-2">
          When production spikes, SentinelAI finds the suspect commit, reviews
          the diff, gates the regressed model, and hands your team one verdict —
          inside{" "}
          <span className="text-ink underline decoration-accent decoration-2 underline-offset-4">
            Dynatrace
          </span>
          , <span className="text-ink">GitLab</span>, and{" "}
          <span className="text-ink">Arize</span>, powered by Gemini on Google
          Cloud.
        </p>

        {/* CTA row */}
        <div className="mt-12 flex flex-wrap items-center gap-4 rise rise-delay-3">
          <Link
            href="/dashboard"
            className="group inline-flex items-center gap-3 rounded-pill bg-accent px-7 py-4 text-ink-dark transition hover:bg-accent/90"
          >
            <span className="mono text-[0.7rem] uppercase tracking-[0.22em]">
              Open dashboard
            </span>
            <span aria-hidden>→</span>
          </Link>
          <a
            href="https://github.com/pandeyVasu/Senintel-Cognee-WeMakeDevs"
            target="_blank"
            rel="noreferrer"
            className="mono inline-flex items-center gap-2 rounded-pill border border-line-strong px-6 py-4 text-[0.7rem] uppercase tracking-[0.2em] text-ink-muted transition hover:border-ink hover:text-ink"
          >
            View source ↗
          </a>
        </div>

        {/* Product hint — the verdict SentinelAI actually produces */}
        <div className="mono mt-8 inline-flex max-w-full flex-wrap items-center gap-x-3 gap-y-1.5 rounded-tag border border-line bg-bg-card/80 px-4 py-2.5 text-[0.7rem] text-ink-muted rise rise-delay-4">
          <span className="rounded-full bg-crit/15 px-2 py-0.5 text-[0.6rem] uppercase tracking-[0.18em] text-crit">
            Verdict
          </span>
          <span>
            Roll back <span className="text-ink">MR !1</span> · commit{" "}
            <span className="text-accent">91d2dd2c</span> · N+1 in
            checkout/views.py
          </span>
        </div>

        {/* Numbers strip */}
        <div className="mt-20 grid grid-cols-2 gap-6 border-t border-line pt-10 sm:grid-cols-4 rise rise-delay-5">
          <HeroNum k="3" label="autonomous pillars" />
          <HeroNum k="138" label="tests green" />
          <HeroNum k="~70s" label="incident to verdict" />
          <HeroNum k="6" label="Cloud Run services" />
        </div>
      </div>

      {/* Phosphor scan line on right edge */}
      <div className="pointer-events-none absolute right-0 top-0 hidden h-full w-px bg-accent/40 lg:block" />
    </section>
  );
}

function HeroNum({ k, label }: { k: string; label: string }) {
  return (
    <div className="flex flex-col gap-2">
      <span className="display-up text-5xl tabular text-ink">{k}</span>
      <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
        {label}
      </span>
    </div>
  );
}
