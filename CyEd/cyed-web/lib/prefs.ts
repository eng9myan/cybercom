"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ALL_NAV, NAV_GROUPS } from "@/lib/nav";

/**
 * Per-user workspace preferences.
 *
 * CyEd exposes ~28 modules. Nobody uses all of them: a teacher never touches
 * bank reconciliation, and a payroll officer never opens the Socratic tutor.
 * Showing everything to everyone is the single biggest usability problem in the
 * app, so each person picks what their sidebar contains.
 *
 * Stored locally rather than server-side on purpose: this is a display
 * preference, it must survive offline (the app is a PWA), and reading it must
 * not cost a round-trip before the first paint. The shape is versioned so a
 * future server-sync can adopt it without a migration.
 */

const KEY = "cyed-workspace-prefs-v1";

export type Density = "comfortable" | "compact";

export type Prefs = {
  /** hrefs the user has chosen to hide from navigation */
  hidden: string[];
  /** hrefs pinned to the top of the sidebar and to the mobile bottom bar */
  pinned: string[];
  density: Density;
  /** user override for motion; `null` means "follow the OS setting" */
  reduceMotion: boolean | null;
  preset: string | null;
};

export const DEFAULT_PREFS: Prefs = {
  hidden: [],
  pinned: ["/", "/students", "/attendance"],
  density: "comfortable",
  reduceMotion: null,
  preset: null,
};

/**
 * Role presets. A new user should not have to untick twenty modules to get a
 * usable sidebar — one tap gives them a sensible workspace they can then adjust.
 * Each preset lists what stays VISIBLE; everything else is hidden.
 */
export const PRESETS: { id: string; label: string; description: string; visible: string[] }[] = [
  {
    id: "teacher",
    label: "Teacher",
    description: "Classes, marking and teaching tools",
    visible: [
      "/", "/students", "/attendance", "/gradebook", "/assessment", "/curriculum",
      "/reports", "/lms", "/teacher-tools", "/review", "/wellbeing", "/at-risk", "/tutor",
    ],
  },
  {
    id: "office",
    label: "Front Office",
    description: "Admissions, students, fees and transport",
    visible: ["/", "/admissions", "/students", "/attendance", "/fees", "/billing", "/transport", "/bus-tracking", "/data-import"],
  },
  {
    id: "finance",
    label: "Finance & Payroll",
    description: "Ledger, payroll, procurement and assets",
    visible: ["/", "/fees", "/billing", "/erp/finance", "/erp/payroll", "/erp/procurement", "/erp/inventory", "/erp/hr", "/erp/staff-attendance"],
  },
  {
    id: "leadership",
    label: "Leadership",
    description: "Whole-school view across academics and back office",
    visible: [
      "/", "/students", "/attendance", "/reports", "/at-risk", "/review",
      "/erp/hr", "/erp/finance", "/erp/staff-attendance", "/erp/documents", "/settings",
    ],
  },
  {
    id: "everything",
    label: "Everything",
    description: "Show all modules",
    visible: [],  // empty = hide nothing
  },
];

function read(): Prefs {
  if (typeof window === "undefined") return DEFAULT_PREFS;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return DEFAULT_PREFS;
    const parsed = JSON.parse(raw) as Partial<Prefs>;
    return { ...DEFAULT_PREFS, ...parsed };
  } catch {
    return DEFAULT_PREFS;
  }
}

function write(prefs: Prefs) {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(prefs));
    // Same-tab listeners: `storage` only fires in *other* tabs.
    window.dispatchEvent(new CustomEvent("cyed-prefs-changed"));
  } catch {
    /* storage full or blocked — preferences simply don't persist */
  }
}

export function applyPreset(id: string): Prefs {
  const preset = PRESETS.find((p) => p.id === id);
  const current = read();
  if (!preset) return current;
  const hidden =
    preset.visible.length === 0
      ? []
      : ALL_NAV.map((n) => n.href).filter((h) => !preset.visible.includes(h));
  const next: Prefs = { ...current, hidden, preset: id };
  write(next);
  return next;
}

export function usePrefs() {
  const [prefs, setPrefs] = useState<Prefs>(DEFAULT_PREFS);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setPrefs(read());
    setReady(true);
    const sync = () => setPrefs(read());
    window.addEventListener("cyed-prefs-changed", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("cyed-prefs-changed", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const update = useCallback((patch: Partial<Prefs>) => {
    const next = { ...read(), ...patch };
    write(next);
    setPrefs(next);
  }, []);

  const toggleHidden = useCallback((href: string) => {
    const cur = read();
    const hidden = cur.hidden.includes(href)
      ? cur.hidden.filter((h) => h !== href)
      : [...cur.hidden, href];
    // Hiding a module also unpins it, otherwise it would linger in the bottom bar.
    const pinned = hidden.includes(href) ? cur.pinned.filter((p) => p !== href) : cur.pinned;
    const next = { ...cur, hidden, pinned, preset: null };
    write(next);
    setPrefs(next);
  }, []);

  const togglePinned = useCallback((href: string) => {
    const cur = read();
    const pinned = cur.pinned.includes(href)
      ? cur.pinned.filter((p) => p !== href)
      : [...cur.pinned, href].slice(-5); // bottom nav holds at most 5 (Material)
    const next = { ...cur, pinned };
    write(next);
    setPrefs(next);
  }, []);

  const reset = useCallback(() => {
    write(DEFAULT_PREFS);
    setPrefs(DEFAULT_PREFS);
  }, []);

  return { prefs, ready, update, toggleHidden, togglePinned, reset, applyPreset };
}

/** Nav groups with hidden modules removed, and empty groups dropped. */
export function useVisibleNav(prefs: Prefs) {
  return useMemo(() => {
    const hidden = new Set(prefs.hidden);
    return NAV_GROUPS.map((g) => ({ ...g, items: g.items.filter((i) => !hidden.has(i.href)) })).filter(
      (g) => g.items.length > 0
    );
  }, [prefs.hidden]);
}

/** Pinned items, in nav order, for the mobile bottom bar. Falls back to the
    first few visible items so the bar is never empty. */
export function useBottomNav(prefs: Prefs) {
  return useMemo(() => {
    const hidden = new Set(prefs.hidden);
    const visible = ALL_NAV.filter((n) => !hidden.has(n.href));
    const pinned = visible.filter((n) => prefs.pinned.includes(n.href));
    return (pinned.length ? pinned : visible).slice(0, 5);
  }, [prefs.hidden, prefs.pinned]);
}
