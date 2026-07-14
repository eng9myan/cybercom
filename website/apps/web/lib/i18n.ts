import { getRequestConfig } from "next-intl/server";
import { notFound } from "next/navigation";

export const locales = ["en", "ar"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "en";

export const localeMetadata: Record<Locale, { name: string; dir: "ltr" | "rtl"; hreflang: string }> = {
  en: { name: "English", dir: "ltr", hreflang: "en" },
  ar: { name: "العربية", dir: "rtl", hreflang: "ar" },
};

export default getRequestConfig(async ({ requestLocale }) => {
  const locale = await requestLocale;
  if (!locale || !locales.includes(locale as Locale)) notFound();

  const messages = await import(`../messages/${locale}.json`);
  return {
    locale,
    messages: messages.default,
    timeZone: "Asia/Riyadh",
    now: new Date(),
  };
});
