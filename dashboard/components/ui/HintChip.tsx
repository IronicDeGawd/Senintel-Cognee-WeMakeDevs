"use client";

import { useSyncExternalStore } from "react";

const DISMISS_EVENT = "sentinel-hint-dismiss";

function subscribe(cb: () => void) {
  window.addEventListener("storage", cb);
  window.addEventListener(DISMISS_EVENT, cb);
  return () => {
    window.removeEventListener("storage", cb);
    window.removeEventListener(DISMISS_EVENT, cb);
  };
}

/** Dismissible onboarding cue. Server snapshot is "hidden", so SSR and the
 * first client paint always match; the real localStorage state applies right
 * after hydration. */
export function HintChip({ id, children }: { id: string; children: React.ReactNode }) {
  const key = `sentinel-hint-${id}`;
  const visible = useSyncExternalStore(
    subscribe,
    () => !localStorage.getItem(key),
    () => false,
  );

  if (!visible) return null;

  return (
    <div className="mono flex items-center gap-3 rounded-tag border border-accent/30 bg-accent-soft px-4 py-2.5 text-[0.7rem] text-ink-muted">
      <span className="text-accent">✦</span>
      <span className="grow">{children}</span>
      <button
        aria-label="Dismiss hint"
        className="text-ink-dim transition hover:text-ink"
        onClick={() => {
          localStorage.setItem(key, "1");
          window.dispatchEvent(new Event(DISMISS_EVENT));
        }}
      >
        ✕
      </button>
    </div>
  );
}
