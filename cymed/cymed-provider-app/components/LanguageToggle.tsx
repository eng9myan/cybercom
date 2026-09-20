"use client";

import { useEffect, useState } from "react";

import { applyLocale, currentLocale } from "@/components/LocaleDirection";
import { SUPPORTED_LOCALES } from "@/lib/i18n";

const LABELS: Record<string, string> = { en: "EN", ar: "ع" };

/**
 * EN / ع switch. Writes the locale (LocaleDirection.applyLocale flips <html dir>
 * + persists) and reloads so bundled catalogs + server components pick it up.
 */
export default function LanguageToggle() {
  const [loc, setLoc] = useState<string>("en");
  useEffect(() => setLoc(currentLocale().slice(0, 2)), []);

  function pick(next: string) {
    if (next === loc) return;
    applyLocale(next);
    // full reload: I18nProvider reads locale at mount, and RTL utility classes
    // resolve at render — cheapest correct way to re-render the whole tree.
    window.location.reload();
  }

  return (
    <div className="inline-flex rounded-md border border-white/15 overflow-hidden text-xs">
      {SUPPORTED_LOCALES.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => pick(l)}
          aria-pressed={loc === l}
          className={
            "px-2 py-1 transition-colors " +
            (loc === l ? "bg-white/15 text-white" : "text-white/60 hover:text-white")
          }
        >
          {LABELS[l] ?? l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
