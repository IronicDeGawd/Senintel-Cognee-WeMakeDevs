"use client";

import { useEffect, useState } from "react";

/** Tracks which page section is in view. Pass a module-level constant array
 * so the effect doesn't re-subscribe every render. The middle-band rootMargin
 * means "active" is whatever section crosses the 40–45% viewport line; a
 * scroll-bottom listener lets a short last section still win. */
export function useScrollSpy(ids: readonly string[]): string {
  const [active, setActive] = useState(ids[0] ?? "");

  useEffect(() => {
    const els = ids
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => el !== null);
    if (!els.length) return;

    const visible = new Set<string>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) visible.add(e.target.id);
          else visible.delete(e.target.id);
        }
        const current = ids.find((id) => visible.has(id));
        if (current) setActive(current);
      },
      { rootMargin: "-40% 0px -55% 0px" },
    );
    els.forEach((el) => observer.observe(el));

    const onScroll = () => {
      if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 8) {
        setActive(ids[ids.length - 1]);
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", onScroll);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids.join(",")]);

  return active;
}
