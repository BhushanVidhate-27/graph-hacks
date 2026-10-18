"use client";

import { useEffect } from "react";

/**
 * Publishes the live header height as `--header-h`.
 *
 * The captured header is position:fixed, so any route that reuses it has to
 * reserve the space itself. Hardcoding that height does not work: the header is
 * two rows on desktop, collapses to one on mobile, and grows again the moment a
 * nav label wraps. Measuring it is the only version that stays correct across
 * breakpoints and across future label edits.
 *
 * Runs in an effect rather than during render so the server HTML and the first
 * client render agree — measuring during render is what causes hydration
 * mismatches.
 */
export function HeaderOffset() {
  useEffect(() => {
    const root = document.documentElement;

    const publish = () => {
      const header = document.querySelector<HTMLElement>("header.header");
      if (!header) return;
      const h = Math.ceil(header.getBoundingClientRect().bottom);
      root.style.setProperty("--header-h", `${h}px`);
    };

    publish();

    // The nav controller changes the header's classes as it runs, and the
    // breakpoint changes the row count, so measure on both rather than once.
    const ro = new ResizeObserver(publish);
    const header = document.querySelector<HTMLElement>("header.header");
    if (header) ro.observe(header);
    window.addEventListener("resize", publish);

    return () => {
      ro.disconnect();
      window.removeEventListener("resize", publish);
    };
  }, []);

  return null;
}