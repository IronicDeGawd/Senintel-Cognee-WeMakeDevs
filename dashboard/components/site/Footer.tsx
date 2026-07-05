export function Footer() {
  return (
    <footer className="mt-32 border-t border-line">
      <div className="mx-auto grid max-w-[1440px] gap-10 px-6 py-14 sm:grid-cols-2 lg:grid-cols-4 lg:px-10">
        <div className="lg:col-span-2">
          <p className="display-up text-2xl text-ink">
            SentinelAI<span className="mono ml-2 text-xs text-ink-dim">v0.1</span>
          </p>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-ink-muted">
            Three signals. One envelope. An autonomous guardian for the
            software delivery lifecycle.
          </p>
        </div>

        <div>
          <p className="eyebrow">Demo</p>
          <ul className="mt-3 space-y-2 text-sm text-ink-muted">
            <li>
              <a className="hover:text-ink" href="/dashboard">
                /dashboard
              </a>
            </li>
            <li>
              <a
                className="hover:text-ink"
                href="https://gitlab.com/parakramlabs-group/rapid-agent-hackathon/-/merge_requests/1"
                target="_blank"
                rel="noreferrer"
              >
                Live MR !1 ↗
              </a>
            </li>
          </ul>
        </div>

        <div>
          <p className="eyebrow">Project</p>
          <ul className="mt-3 space-y-2 text-sm text-ink-muted">
            <li>
              <a
                className="hover:text-ink"
                href="https://github.com/IronicDeGawd/Senintel-Cognee-WeMakeDevs"
                target="_blank"
                rel="noreferrer"
              >
                GitHub ↗
              </a>
            </li>
            <li className="mono text-xs uppercase tracking-[0.18em] text-ink-dim">
              Apache-2.0
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-line">
        <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-3 px-6 py-5 lg:px-10">
          <p className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
            Built on Gemini · Vertex AI · Cloud Run · Firestore
          </p>
          <p className="mono text-[0.65rem] uppercase tracking-[0.22em] text-ink-dim">
            ◢◣ sentinelai · 2026
          </p>
        </div>
      </div>
    </footer>
  );
}
