import { partnerOrder } from "@/lib/mock";
import { SectionHeader } from "@/components/ui/SectionHeader";

const copy: Record<string, { tagline: string; verbs: string[] }> = {
  production: {
    tagline:
      "Picks up the Davis problem the moment it opens, RCAs it with Gemini, and pins the spike to the suspect commit.",
    verbs: ["OBSERVE", "RCA", "CORRELATE"],
  },
  code: {
    tagline:
      "Reviews every merge request as it lands — catches N+1s and security gaps, then posts the note right on the MR.",
    verbs: ["REVIEW", "DIAGNOSE", "COMMENT"],
  },
  ai_quality: {
    tagline:
      "Runs adversarial eval suites against your model and blocks the deploy when quality regresses — before it ships.",
    verbs: ["GENERATE", "EVALUATE", "GATE"],
  },
};

export function Solution() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1440px] px-6 py-24 lg:px-10 lg:py-32">
        <SectionHeader
          eyebrow="§ 02 · The solution"
          title={
            <>
              <span className="display">It runs the loop</span> inside the
              tools you already use.
            </>
          }
        />
        <p className="mt-6 max-w-2xl text-base leading-relaxed text-ink-muted">
          No new pager, no new tab. Three autonomous agents read from Dynatrace,
          GitLab, and Arize, and write their findings back where your team
          already looks — each emitting the same <code>Signal</code> into one
          live stream.
        </p>

        <div className="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {partnerOrder.map((p, i) => {
            const c = copy[p.key];
            const isLead = i === 0;
            return (
              <article
                key={p.key}
                className={`group relative flex flex-col rounded-card-lg p-8 transition lg:p-10 ${
                  isLead
                    ? "card-depth gradient-border"
                    : "border border-line bg-bg-card hover:border-line-strong"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
                    P{i + 1} · {p.partner}
                  </span>
                  {isLead ? (
                    <span className="mono rounded-tag bg-accent/15 px-2 py-0.5 text-[0.6rem] uppercase tracking-[0.18em] text-accent">
                      Dynatrace track
                    </span>
                  ) : (
                    <span className="mono text-[0.65rem] text-ink-dim">
                      /{p.key}
                    </span>
                  )}
                </div>

                <h3 className="display-up mt-6 text-3xl text-ink">{p.label}</h3>

                <p className="mt-4 text-sm leading-relaxed text-ink-muted">
                  {c.tagline}
                </p>

                <ul className="mono mt-10 grid grid-cols-1 gap-2 border-t border-line pt-6 text-[0.7rem] uppercase tracking-[0.18em] text-ink-muted">
                  {c.verbs.map((v) => (
                    <li key={v} className="flex items-center gap-3">
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          isLead ? "bg-accent" : "bg-line-strong"
                        }`}
                      />
                      {v}
                    </li>
                  ))}
                </ul>

                <div
                  className={`mt-10 flex items-end justify-between border-t border-line pt-5 ${
                    isLead ? "text-accent" : "text-ink-dim"
                  }`}
                >
                  <span className="mono text-[0.65rem] uppercase tracking-[0.22em]">
                    MCP · REST · Gemini
                  </span>
                  <span className="display-up text-3xl tabular">0{i + 1}</span>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
