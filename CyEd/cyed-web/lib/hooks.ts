"use client";

import { useEffect, useRef, useState } from "react";

/** Respect the OS reduced-motion setting. */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}

/** Animated count-up to `target`. Skips animation under reduced motion. */
export function useCountUp(target: number, durationMs = 900): number {
  const reduced = useReducedMotion();
  const [value, setValue] = useState(0);
  const raf = useRef<number | null>(null);

  const settle = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (reduced) {
      setValue(target);
      return;
    }
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 4); // ease-out-quart
      setValue(from + (target - from) * eased);
      if (t < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    // Browsers throttle requestAnimationFrame to nothing in a background or
    // unpainted tab. Without this backstop the animation never advances and the
    // number sits at 0 — so a parent who opens the portal in a background tab
    // and comes back reads "0 unpaid" when they owe $400. The count-up is
    // decoration; the number is not, and it must land either way.
    settle.current = setTimeout(() => setValue(target), durationMs + 150);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
      if (settle.current) clearTimeout(settle.current);
    };
  }, [target, durationMs, reduced]);

  return value;
}

export type Theme = "dark" | "light";

/** Light/dark toggle persisted to localStorage; stamps `data-theme` on <html>. */
export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>("dark");
  useEffect(() => {
    const stored = (localStorage.getItem("cyed-theme") as Theme) || null;
    const initial: Theme =
      stored || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    setTheme(initial);
    document.documentElement.setAttribute("data-theme", initial);
  }, []);
  const toggle = () => {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("cyed-theme", next);
      return next;
    });
  };
  return [theme, toggle];
}
