import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { DemoSection } from "@/components/sections/DemoSection";

interface DemoPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: DemoPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Request a Demo",
    description: "Schedule a personalized demonstration of CyberCom platforms — CyMed, CyCom, CyGov, CyAI and more. Our specialists will walk you through the platform tailored to your needs.",
    path: "/demo",
    locale,
  });
}

export default async function DemoPage({ params }: DemoPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <DemoSection locale={locale as Locale} asPageHero />;
}
