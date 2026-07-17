import { setRequestLocale, getTranslations } from "next-intl/server";
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
  const t = await getTranslations("demo");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/demo",
    locale,
  });
}

export default async function DemoPage({ params }: DemoPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <DemoSection locale={locale as Locale} asPageHero />;
}
