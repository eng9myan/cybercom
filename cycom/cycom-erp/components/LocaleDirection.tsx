'use client';

import { useEffect } from 'react';

// Minimal RTL foundation. Full bilingual i18n (string catalogs, next-intl) is a
// sized feature — see RTL_AUDIT.md. This piece establishes the one thing every
// RTL screen needs first: the document direction + lang, driven by the viewer's
// locale and persisted per browser. Wire a language toggle to `applyLocale`.

export const LOCALE_KEY = 'cycom.locale';
export const RTL_LOCALES = ['ar', 'he', 'fa', 'ur'];

export function applyLocale(locale: string): void {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  root.lang = locale;
  root.dir = RTL_LOCALES.includes(locale) ? 'rtl' : 'ltr';
  try {
    localStorage.setItem(LOCALE_KEY, locale);
  } catch {
    /* private mode / storage blocked — direction still applied for this session */
  }
}

export function currentLocale(): string {
  try {
    return localStorage.getItem(LOCALE_KEY) || 'en';
  } catch {
    return 'en';
  }
}

/** Applies the stored locale's direction on load. Render once in the root layout. */
export default function LocaleDirection() {
  useEffect(() => {
    applyLocale(currentLocale());
  }, []);
  return null;
}
