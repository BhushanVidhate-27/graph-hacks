"use client";

import { useEffect } from "react";

const LOADING_DURATION = 1_800;

export function LoadingController() {
  useEffect(() => {
    const loading = document.querySelector<HTMLElement>(".loading");
    if (!loading) return;

    const percent = loading.querySelector<HTMLElement>(
      ".loading-progress-txt-percent",
    );
    const progressItems = loading.querySelectorAll<HTMLElement>(
      ".loading-progress-item",
    );
    const coordinates = loading.querySelectorAll<HTMLElement>(
      "[data-loading-control]",
    );
    const start = performance.now();
    let frame = 0;
    let fadeTimer = 0;
    let cancelled = false;

    loading.classList.add("active");
    loading.setAttribute("aria-busy", "true");
    if (percent) percent.textContent = "0";
    progressItems.forEach((item) => {
      item.style.width = "0%";
    });

    const update = (now: number) => {
      if (cancelled) return;

      const progress = Math.min((now - start) / LOADING_DURATION, 1);
      const value = Math.floor(progress * 100);

      if (percent) percent.textContent = String(value);
      progressItems.forEach((item) => {
        item.style.width = `${value}%`;
      });
      coordinates.forEach((coordinate) => {
        coordinate.textContent = String(Math.floor(1131 * progress));
      });

      if (progress < 1) {
        frame = requestAnimationFrame(update);
        return;
      }

      fadeTimer = window.setTimeout(() => {
        loading.classList.remove("active");
        loading.setAttribute("aria-busy", "false");
      }, 400);
    };

    frame = requestAnimationFrame(update);
    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
      window.clearTimeout(fadeTimer);
    };
  }, []);

  return null;
}
