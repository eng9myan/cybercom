import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { QueryProvider } from "@/context/QueryProvider";
import ProviderLayoutWrapper from "@/components/layout/ProviderLayoutWrapper";
import LocaleDirection from "@/components/LocaleDirection";
import { I18nProvider } from "@/lib/i18n";

export const metadata: Metadata = {
  title: "CyMed Provider Portal",
  description: "CyMed clinician portal — today's schedule, patient roster and priority alerts.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" dir="ltr" className="scroll-smooth" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-[#030712] text-white">
        <LocaleDirection />
        <I18nProvider>
          <AuthProvider>
            <QueryProvider>
              <ProviderLayoutWrapper>{children}</ProviderLayoutWrapper>
            </QueryProvider>
          </AuthProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
