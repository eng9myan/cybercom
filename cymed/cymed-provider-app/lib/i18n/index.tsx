"use client";

/**
 * Lightweight, framework-free i18n for the CyMed provider portal — same
 * engine as cycom-erp's lib/i18n/index.tsx (deliberately not next-intl, see
 * that file's docstring for why), locale key renamed to 'cymed.locale' to
 * match this app's own LocaleDirection.
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

/** Dotted-key lookup: t('overview.title'). Returns the key itself if missing (visible in dev). */
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
              return localStorage.getItem("cymed.locale");
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
    if (typeof localStorage !== "undefined") loc = resolveLocale(localStorage.getItem("cymed.locale"));
  } catch {
    /* storage blocked */
  }
  let s = lookup(CATALOGS[loc], key);
  if (s === key && loc !== "en") s = lookup(CATALOGS.en, key);
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
  return s;
}
