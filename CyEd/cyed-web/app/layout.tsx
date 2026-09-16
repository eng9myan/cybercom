import type { Metadata, Viewport } from "next";
import "./globals.css";
import AppShell from "@/components/AppShell";
import PWARegister from "@/components/PWARegister";
import { ToastProvider } from "@/components/Toast";
import PrefsApplier from "@/components/PrefsApplier";

export const metadata: Metadata = {
  title: "CyEd — School Management",
  description: "CyberCom school management system (AU, ACARA-aligned).",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "CyEd", statusBarStyle: "black-translucent" },
  icons: { apple: "/icons/apple-touch-icon.png" },
};

export const viewport: Viewport = {
  themeColor: "#0a0e17",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

// Set the theme before paint to avoid a flash of the wrong mode.
const THEME_SCRIPT = `(function(){try{var t=localStorage.getItem('cyed-theme');if(!t){t=window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';}document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','dark');}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body>
        <a href="#main" className="skip-link">
          Skip to main content
        </a>
        <PrefsApplier />
        <ToastProvider>
          <AppShell>{children}</AppShell>
        </ToastProvider>
        <PWARegister />
      </body>
    </html>
  );
}
