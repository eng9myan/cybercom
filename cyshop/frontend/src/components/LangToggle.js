"use client";

import { Globe } from "lucide-react";
import { useT } from "@/lib/i18n";

export default function LangToggle({ compact = false }) {
  const { locale, setLocale } = useT();
  const next = locale === "ar" ? "en" : "ar";
  return (
    <button
      onClick={() => setLocale(next)}
      title="English / العربية"
      className="h-9 px-2.5 rounded-lg border border-[var(--color-line)] hover:bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] hover:text-[var(--color-ink)] flex items-center gap-1.5 text-sm transition"
    >
      <Globe className="w-4 h-4" />
      {!compact && <span>{locale === "ar" ? "EN" : "ع"}</span>}
    </button>
  );
}
