import { notFound } from "next/navigation";
import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { TryFreeSection } from "@/components/sections/TryFreeSection";

// URL slug -> { backend product_code, display name }. Only products with a
// real self-serve demo endpoint belong here — cymed_hospital is deliberately
// excluded (sales-assisted only, enforced server-side too).
const TRYABLE_PRODUCTS: Record<string, { code: string; name: string }> = {
  "cymed-clinic": { code: "cymed_clinic", name: "CyMed Clinic" },
  "cymed-pharmacy": { code: "cymed_pharmacy", name: "CyMed Pharmacy" },
  "cymed-laboratory": { code: "cymed_laboratory", name: "CyMed Laboratory" },
  "cymed-imaging": { code: "cymed_imaging", name: "CyMed Imaging" },
  cyshop: { code: "cyshop", name: "CyShop" },
  cycom: { code: "cycom", name: "CyCom ERP" },
};

interface TryPageProps {
  params: Promise<{ locale: string; product: string }>;
}

export async function generateMetadata({ params }: TryPageProps): Promise<Metadata> {
  const { locale, product } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("tryPage");
  const entry = TRYABLE_PRODUCTS[product];
  return buildMetadata({
    title: entry ? `${t("metaTitlePrefix")} ${entry.name} ${t("metaTitleSuffix")}` : t("metaTitleDefault"),
    description: t("metaDescription"),
    path: `/try/${product}`,
    locale,
  });
}

export default async function TryProductPage({ params }: TryPageProps) {
  const { locale, product } = await params;
  setRequestLocale(locale);
  const entry = TRYABLE_PRODUCTS[product];
  if (!entry) {
    notFound();
  }
  return <TryFreeSection locale={locale as Locale} productCode={entry.code} productName={entry.name} />;
}
