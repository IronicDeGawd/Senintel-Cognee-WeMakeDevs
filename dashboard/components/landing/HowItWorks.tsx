const steps = [
  {
    n: "01",
    t: "06:20",
    role: "DEVELOPER",
    title: "A commit lands with an N+1 regression.",
    body: "checkout/views.py — the select_related/prefetch_related is removed. Tests are mocked; CI passes locally. The push hits GitLab.",
  },
  {
    n: "02",
    t: "06:21",
    role: "CODE GUARDIAN",
    title: "Live review on MR !1. Gemini posts the note.",
    body: "Gateway receives the webhook, returns 202 immediately, runs the cycle. Severity-grouped review lands as a GitLab comment in under 10 seconds.",
  },
  {
    n: "03",
    t: "06:22",
    role: "PRODUCTION SENTINEL",
    title: "Dynatrace sees the p95 spike. Correlates back.",
    body: "Checkout p95 jumps 180 → 2400ms. RCA agent joins the spike to the suspect commit abc1234 — same service, same window. Verdict: roll back MR !1.",
  },
  {
    n: "04",
    t: "06:20",
    role: "AI QUALITY GATE",
    title: "A parallel LLM regression never ships.",
    body: "Evalgen produces 8 adversarial cases; hallucination jumps to 22% on checkout-llm-v2. Gate blocks the deploy before it leaves staging.",
  },
];

export function HowItWorks() {
  return (
    <section className="border-b border-line bg-bg-raised">
      <div className="mx-auto max-w-[1440px] px-6 py-24 lg:px-10 lg:py-32">
        <header className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_2fr] lg:items-end">
          <div>
            <span className="eyebrow">§ 04 · How it works</span>
            <h2 className="display-up mt-6 text-5xl leading-[1.04] text-ink sm:text-6xl">
              <span className="display">A bad commit lands.</span>
              <br />
              Then this happens.
            </h2>
          </div>
          <div className="flex flex-col items-start gap-5 justify-self-end lg:items-end">
            <span className="mono inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent-soft px-4 py-1.5 text-[0.65rem] uppercase tracking-[0.2em] text-accent">
              ≈ 70 s end-to-end
            </span>
            <p className="max-w-xl text-base leading-relaxed text-ink-muted lg:text-right">
              No setup ritual, no runbook. The same regression travels through
              every pillar on its own, and the dashboard freezes the joined
              view as a single verdict.
            </p>
          </div>
        </header>

        <ol className="mt-20 grid grid-cols-1 gap-px overflow-hidden rounded-card-lg border border-line bg-line lg:grid-cols-2">
          {steps.map((s, i) => (
            <li
              key={s.n}
              className="relative flex flex-col gap-6 bg-bg p-8 lg:p-10"
            >
              <div className="flex items-center justify-between">
                <span className="display-up text-5xl text-ink-faint tabular">
                  {s.n}
                </span>
                <span className="mono flex items-center gap-3 text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
                  <span className="tabular text-accent">{s.t}</span>
                  <span className="h-1 w-1 rounded-full bg-line-strong" />
                  {s.role}
                </span>
              </div>
              <h3 className="display-up text-2xl leading-tight text-ink sm:text-3xl">
                {s.title}
              </h3>
              <p className="text-sm leading-relaxed text-ink-muted">{s.body}</p>
              {/* Hairline connector */}
              {i < steps.length - 1 && (
                <span
                  aria-hidden
                  className="mono absolute right-6 top-6 text-accent/40"
                >
                  ↓
                </span>
              )}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
