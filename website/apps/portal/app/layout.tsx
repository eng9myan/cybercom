import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://portal.cy-com.com"),
  title: {
    default: "Customer Portal — CyberCom Revolution",
    template: "%s | CyberCom Portal",
  },
  description:
    "Access your CyberCom licenses, software downloads, support tickets, and deployment status from one unified portal.",
  robots: {
    index: false,
    follow: false,
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
  openGraph: {
    siteName: "CyberCom Customer Portal",
    type: "website",
    locale: "en_US",
    url: "https://portal.cy-com.com",
    title: "Customer Portal — CyberCom Revolution",
    description: "Manage your CyberCom licenses, downloads, and support.",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0a0a0f",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head />
      <body>
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
