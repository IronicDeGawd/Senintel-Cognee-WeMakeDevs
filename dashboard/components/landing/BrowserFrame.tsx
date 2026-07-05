/** Browser-chrome frame around the live dashboard preview. */
export function BrowserFrame({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-hidden rounded-card-lg gradient-border card-depth">
      {/* Chrome bar */}
      <div className="flex items-center gap-4 border-b border-line bg-bg-raised px-5 py-3">
        <div className="flex gap-1.5" aria-hidden>
          <span className="h-2.5 w-2.5 rounded-full bg-crit/60" />
          <span className="h-2.5 w-2.5 rounded-full bg-warn/60" />
          <span className="h-2.5 w-2.5 rounded-full bg-ok/60" />
        </div>
        <div className="mono grow rounded-tag border border-line bg-bg px-3 py-1 text-center text-[0.65rem] text-ink-dim">
          sentinel.parakramlabs.com/dashboard
        </div>
      </div>
      <div className="p-5 lg:p-7">{children}</div>
    </div>
  );
}
