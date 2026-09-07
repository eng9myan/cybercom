"use client";

/**
 * Lightweight bilingual layer — no framework. Locale lives in localStorage +
 * a cookie (so SSR can pick it up), `t(key)` does a dotted lookup with a
 * {param} interpolation, and switching locale flips <html dir/lang>.
 */
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import en from "./messages/en";
import ar from "./messages/ar";

const CATALOGS = { en, ar };
const RTL = new Set(["ar"]);

function lookup(cat, key) {
  return key.split(".").reduce((o, k) => (o == null ? o : o[k]), cat);
}

export function translate(locale, key, params) {
  let s = lookup(CATALOGS[locale] || en, key);
  if (s == null) s = lookup(en, key);
  if (s == null) return key;
  if (params) {
    for (const [k, v] of Object.entries(params)) s = s.replaceAll(`{${k}}`, String(v));
  }
  return s;
}

export function applyLocale(locale) {
  if (typeof document === "undefined") return;
  const html = document.documentElement;
  html.lang = locale;
  html.dir = RTL.has(locale) ? "rtl" : "ltr";
}

export function getStoredLocale() {
  if (typeof window === "undefined") return "en";
  try { return localStorage.getItem("locale") || "en"; } catch { return "en"; }
}

const I18nCtx = createContext({ locale: "en", setLocale: () => {}, t: (k) => k, dir: "ltr" });

export function I18nProvider({ children }) {
  const [locale, setLocaleState] = useState("en");

  useEffect(() => {
    const l = getStoredLocale();
    setLocaleState(l);
    applyLocale(l);
  }, []);

  const setLocale = (l) => {
    setLocaleState(l);
    try {
      localStorage.setItem("locale", l);
      document.cookie = `locale=${l}; path=/; max-age=31536000`;
    } catch {}
    applyLocale(l);
  };

  const t = (key, params) => translate(locale, key, params);
  return (
    <I18nCtx.Provider value={{ locale, setLocale, t, dir: RTL.has(locale) ? "rtl" : "ltr" }}>
      {children}
    </I18nCtx.Provider>
  );
}

export function useT() {
  return useContext(I18nCtx);
}
