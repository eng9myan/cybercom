'use client';

import { useEffect } from 'react';

// The viewer's locale is persisted in a cookie (so the server renders the
// right <html lang/dir> and strings on the very first paint -- no English
// flash, no hydration mismatch) and mirrored in localStorage for older code.
// Wire a language toggle to `applyLocale`.

export const LOCALE_KEY = 'cycom.locale';
export const LOCALE_COOKIE = 'cycom.locale';
export const RTL_LOCALES = ['ar', 'he', 'fa', 'ur'];

function readCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const m = document.cookie.match(/(?:^|;\s*)cycom\.locale=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

function readStorage(): string | null {
  try {
    return localStorage.getItem(LOCALE_KEY);
  } catch {
    return null;
  }
}

export function applyLocale(locale: string): void {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  root.lang = locale;
  root.dir = RTL_LOCALES.includes(locale) ? 'rtl' : 'ltr';
  document.cookie = `${LOCALE_COOKIE}=${encodeURIComponent(locale)}; path=/; max-age=31536000; samesite=lax`;
  try {
    localStorage.setItem(LOCALE_KEY, locale);
  } catch {
    /* private mode / storage blocked — the cookie still carries it */
  }
}

export function currentLocale(): string {
  return readCookie() || readStorage() || 'en';
}

/**
 * One-time migration: a browser that chose a language before the cookie
 * existed has it only in localStorage, so the server rendered the default.
 * Copy it into the cookie and reload once; from then on SSR matches.
 */
export default function LocaleDirection() {
  useEffect(() => {
    const stored = readStorage();
    if (!readCookie() && stored && stored !== document.documentElement.lang) {
      applyLocale(stored);
      window.location.reload();
    }
  }, []);
  return null;
}
