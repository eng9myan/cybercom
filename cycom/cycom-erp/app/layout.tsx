import type { Metadata } from "next";
import { cookies } from "next/headers";
import "./globals.css";
import { CompanyProvider } from "@/context/CompanyContext";
import { AuthProvider } from "@/context/AuthContext";
import { QueryProvider } from "@/context/QueryProvider";
import CycomLayoutWrapper from "@/components/layout/CycomLayoutWrapper";
import { CyCommandBar } from "@/components/CyCommandBar";
import LocaleDirection from "@/components/LocaleDirection";
import { I18nProvider } from "@/lib/i18n";

// Kept here (not imported from the "use client" i18n module, whose exports
// are client references in a server component).
const LOCALES = ["en", "ar"];
const RTL = ["ar", "he", "fa", "ur"];

export const metadata: Metadata = {
  title: "Cycom ERP — Enterprise Resource Planning",
  description: "Cycom ERP — Cycom enterprise management system covering HR, Payroll, Attendance, POS, Sales, Inventory and more.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // The locale cookie (set by the language toggle) decides lang/dir and the
  // strings on the server, so the first paint is already in the right
  // language -- previously SSR always rendered English and the client
  // re-rendered in Arabic after hydration.
  const raw = (await cookies()).get("cycom.locale")?.value?.slice(0, 2).toLowerCase() ?? "en";
  const locale = LOCALES.includes(raw) ? raw : "en";
  return (
    <html lang={locale} dir={RTL.includes(locale) ? "rtl" : "ltr"} className="scroll-smooth" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-[#030712] text-white">
        <LocaleDirection />
        <I18nProvider locale={locale}>
          <AuthProvider>
            <QueryProvider>
              <CompanyProvider>
                <CycomLayoutWrapper>
                  {children}
                  <CyCommandBar />
                </CycomLayoutWrapper>
              </CompanyProvider>
            </QueryProvider>
          </AuthProvider>
        </I18nProvider>
      </body>
    </html>
  );
}

