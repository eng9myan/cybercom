import type { Metadata } from "next";
import { Sora, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { TopNav } from "@/components/TopNav";
import { DevLoginBanner } from "@/components/DevLoginBanner";

const sora = Sora({ variable: "--font-display", subsets: ["latin"], weight: ["500", "600"] });
const plexSans = IBM_Plex_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500"],
});
const plexMono = IBM_Plex_Mono({ variable: "--font-mono", subsets: ["latin"], weight: ["400", "500"] });

export const metadata: Metadata = {
  title: "CyMart",
  description: "Talk, and it feeds you toward your goal.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${sora.variable} ${plexSans.variable} ${plexMono.variable} h-full`}>
      <body className="min-h-full flex flex-col" style={{ background: "var(--ground)", color: "var(--ink)" }}>
        <Providers>
          <DevLoginBanner />
          <TopNav />
          <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-4">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
