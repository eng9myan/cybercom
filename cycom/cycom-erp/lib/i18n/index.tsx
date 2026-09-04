"use client";

/**
 * Lightweight, framework-free i18n for cycom-erp.
 *
 * Deliberately NOT next-intl: that needs URL-segment restructuring across every
 * route, which is too invasive to land mid-launch (RTL_AUDIT.md). This gives us
 * translated strings + a locale switch now; a next-intl migration can come later
 * without changing call sites (they use `t('pos.checkout')` either way).
 *
 * Locale source: the 'cycom.locale' key written by components/LocaleDirection's
 * applyLocale(). Catalogs are small and bundled (no async load).
 */
import React, { createContext, useCallback, useContext, useMemo } from "react";

import ar from "./messages/ar";
import en, { type Messages } from "./messages/en";

export const SUPPORTED_LOCALES = ["en", "ar"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

const CATALOGS: Record<Locale, Messages> = { en, ar };

function resolveLocale(raw: string | null | undefined): Locale {
  const base = (raw || "en").slice(0, 2).toLowerCase();
  return (SUPPORTED_LOCALES as readonly string[]).includes(base) ? (base as Locale) : "en";
}

/** Dotted-key lookup: t('pos.checkout'). Returns the key itself if missing (visible in dev). */
function lookup(cat: Messages, key: string): string {
  const val = key.split(".").reduce<unknown>((acc, part) => {
    if (acc && typeof acc === "object" && part in (acc as Record<string, unknown>)) {
      return (acc as Record<string, unknown>)[part];
    }
    return undefined;
  }, cat);
  return typeof val === "string" ? val : key;
}

type TFn = (key: string, vars?: Record<string, string | number>) => string;

const I18nContext = createContext<{ locale: Locale; t: TFn }>({
  locale: "en",
  t: (k) => k,
});

export function I18nProvider({
  locale: forced,
  children,
}: {
  locale?: string;
  children: React.ReactNode;
}) {
  const locale = resolveLocale(
    forced ??
      (typeof window !== "undefined"
        ? (() => {
            try {
              return localStorage.getItem("cycom.locale");
            } catch {
              return null;
            }
          })()
        : null),
  );

  const t = useCallback<TFn>(
    (key, vars) => {
      let s = lookup(CATALOGS[locale], key);
      if (s === key && locale !== "en") s = lookup(CATALOGS.en, key); // fall back to en
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
        }
      }
      return s;
    },
    [locale],
  );

  const value = useMemo(() => ({ locale, t }), [locale, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useT(): TFn {
  return useContext(I18nContext).t;
}

export function useLocale(): Locale {
  return useContext(I18nContext).locale;
}

/** Non-component helper (e.g. formatters). Reads localStorage directly. */
export function t(key: string, vars?: Record<string, string | number>): string {
  let loc: Locale = "en";
  try {
    if (typeof localStorage !== "undefined") loc = resolveLocale(localStorage.getItem("cycom.locale"));
  } catch {
    /* storage blocked */
  }
  let s = lookup(CATALOGS[loc], key);
  if (s === key && loc !== "en") s = lookup(CATALOGS.en, key);
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
  return s;
}
