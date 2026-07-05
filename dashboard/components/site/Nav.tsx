import Link from "next/link";

export function Nav({ trail }: { trail?: string }) {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-6 lg:px-10">
        <Link href="/" className="flex items-baseline gap-3">
          <span className="mono text-[0.65rem] uppercase tracking-[0.3em] text-accent">
            ◢◣
          </span>
          <span className="display-up text-xl text-ink">SentinelAI</span>
          {trail && (
            <>
              <span className="mono text-ink-faint">/</span>
              <span className="mono text-xs uppercase tracking-[0.18em] text-ink-muted">
                {trail}
              </span>
            </>
          )}
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          <a
            href="https://github.com/pandeyVasu/Senintel-Cognee-WeMakeDevs"
            target="_blank"
            rel="noreferrer"
            className="mono hidden text-[0.7rem] uppercase tracking-[0.2em] text-ink-muted hover:text-ink sm:inline-flex items-center gap-2 px-3 py-2"
          >
            Source ↗
          </a>
          <Link
            href={trail === "Dashboard" ? "/" : "/dashboard"}
            className="mono inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-4 py-2 text-[0.7rem] uppercase tracking-[0.18em] text-accent transition hover:bg-accent hover:text-ink-dark"
          >
            {trail === "Dashboard" ? "← Home" : "Live demo →"}
          </Link>
        </nav>
      </div>
    </header>
  );
}
