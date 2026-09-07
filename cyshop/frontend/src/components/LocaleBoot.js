"use client";

import { useEffect } from "react";
import { applyLocale, getStoredLocale } from "@/lib/i18n";

// Applies the stored locale to <html> before first paint of interactive content.
export default function LocaleBoot() {
  useEffect(() => { applyLocale(getStoredLocale()); }, []);
  return null;
}
