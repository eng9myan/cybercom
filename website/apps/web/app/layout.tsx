import type { Metadata } from "next";
import "./globals.css";
import { siteConfig } from "@/lib/metadata";

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: {
    default: "CyberCom Revolution — Intelligent Enterprise Platforms",
    template: "%s | CyberCom Revolution",
  },
  description: siteConfig.description,
  icons: {
    icon: "/icon.svg",
  },
  manifest: "/manifest.webmanifest",
  openGraph: {
    siteName: siteConfig.name,
    type: "website",
    locale: "en_US",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
