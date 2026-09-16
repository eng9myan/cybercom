"use client";

import { useEffect } from "react";
import { usePrefs } from "@/lib/prefs";

/**
 * Reflects display preferences onto the document root so CSS can act on them
 * (`[data-density]`, `[data-reduce-motion]`). Kept separate from the panel so
 * the settings live in one place but apply app-wide.
 */
export default function PrefsApplier() {
  const { prefs, ready } = usePrefs();

  useEffect(() => {
    if (!ready) return;
    const root = document.documentElement;
    root.setAttribute("data-density", prefs.density);
    if (prefs.reduceMotion === true) {
      root.setAttribute("data-reduce-motion", "true");
    } else {
      root.removeAttribute("data-reduce-motion");
    }
  }, [ready, prefs.density, prefs.reduceMotion]);

  return null;
}
