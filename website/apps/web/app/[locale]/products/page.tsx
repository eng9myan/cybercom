import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight } from "lucide-react";

interface ProductsPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: ProductsPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("productsPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/products",
    locale,
  });
}

const PLATFORM_CATEGORIES = [
  {
    key: "healthcare",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/5",
    borderColor: "border-emerald-500/20",
    products: [
      { name: "CyMed Clinic", slug: "cymed-clinic" },
      { name: "CyMed Hospital", slug: "cymed-hospital" },
      { name: "CyMed Laboratory", slug: "cymed-laboratory" },
      { name: "CyMed Imaging", slug: "cymed-imaging" },
      { name: "CyMed Pharmacy", slug: "cymed-pharmacy" },
      { name: "CyMed Patient Portal", slug: "cymed-patient-portal" },
      { name: "CyMed Provider Portal", slug: "cymed-provider-portal" },
      { name: "CyMed Revenue Cycle", slug: "cymed-revenue-cycle" },
      { name: "CyMed Population Health", slug: "cymed-population-health" },
    ],
  },
  {
    key: "retail",
    color: "text-cy-orange",
    bgColor: "bg-cy-orange/5",
    borderColor: "border-cy-orange/20",
    products: [
      { name: "CyShop", slug: "cyshop" },
    ],
  },
  {
    key: "enterprise",
    color: "text-blue-400",
    bgColor: "bg-blue-500/5",
    borderColor: "border-blue-500/20",
    products: [
      { name: "CyCom ERP", slug: "cycom" },
      { name: "CyCom Finance", slug: "cycom-finance" },
      { name: "CyCom Accounting", slug: "cycom-accounting" },
      { name: "CyCom Procurement", slug: "cycom-procurement" },
      { name: "CyCom Inventory", slug: "cycom-inventory" },
      { name: "CyCom HR", slug: "cycom-hr" },
      { name: "CyCom Payroll", slug: "cycom-payroll" },
      { name: "CyCom CRM", slug: "cycom-crm" },
      { name: "CyCom Assets", slug: "cycom-assets" },
      { name: "CyCom Manufacturing", slug: "cycom-manufacturing" },
      { name: "CyCom Retail", slug: "cycom-retail" },
      { name: "CyCom BI", slug: "cycom-bi" },
      { name: "CyGov", slug: "cygov" },
      { name: "CyCitizen", slug: "cycitizen" },
    ],
  },
  {
    key: "intelligence",
    color: "text-pink-400",
    bgColor: "bg-pink-500/5",
    borderColor: "border-pink-500/20",
    products: [
      { name: "CyAI", slug: "cyai" },
      { name: "CyData", slug: "cydata" },
    ],
  },
  {
    key: "infrastructure",
    color: "text-violet-400",
    bgColor: "bg-violet-500/5",
    borderColor: "border-violet-500/20",
    products: [
      { name: "CyIdentity", slug: "cyidentity" },
      { name: "CyIntegrationHub", slug: "cyintegrationhub" },
      { name: "CyConnect", slug: "cyconnect" },
    ],
  },
  {
    key: "developer",
    color: "text-violet-300",
    bgColor: "bg-violet-400/5",
    borderColor: "border-violet-400/20",
    products: [
      { name: "CyDeveloper", slug: "cydeveloper" },
    ],
  },
];

export default async function ProductsPage({ params }: ProductsPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("productsPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Header */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/8" />
        </div>
        <div className="section-container relative z-10 text-center">
          <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">{t("badge")}</p>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-4">
            {t("heading")}
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto">
            {t("subheading")}
          </p>
        </div>
      </div>

      {/* Categories */}
      <div className="section-container pb-24">
        <div className="space-y-16">
          {PLATFORM_CATEGORIES.map((category) => (
            <section key={category.key} aria-labelledby={`cat-${category.key}`}>
              <div className="flex items-center gap-3 mb-6">
                <div className={`w-2 h-6 rounded-full ${category.bgColor} border ${category.borderColor}`} aria-hidden="true" />
                <div>
                  <h2 id={`cat-${category.key}`} className={`text-xl font-heading font-semibold ${category.color}`}>
                    {t(`categories.${category.key}.name`)}
                  </h2>
                  <p className="text-sm text-cy-gray-400">{t(`categories.${category.key}.desc`)}</p>
                </div>
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {category.products.map((product) => (
                  <Link
                    key={product.slug}
                    href={`/${l}/products/${product.slug}`}
                    className="glass-card block p-5 rounded-xl border border-cy-glass-border hover:border-current/20 group transition-all duration-300"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className={`font-medium text-sm mb-0.5 group-hover:${category.color} transition-colors`}>
                          {product.name}
                        </div>
                        <div className="text-xs text-cy-gray-400">{t(`products.${product.slug}`)}</div>
                      </div>
                      <ArrowRight
                        className="w-4 h-4 text-cy-gray-600 group-hover:text-white group-hover:translate-x-0.5 transition-all duration-200 flex-shrink-0 rtl:rotate-180"
                        aria-hidden="true"
                      />
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>

        {/* Demo CTA */}
        <div className="mt-16 glass-card p-8 rounded-2xl text-center">
          <h2 className="text-2xl font-heading font-semibold text-white mb-3">
            {t("ctaHeading")}
          </h2>
          <p className="text-cy-gray-400 mb-6">
            {t("ctaDesc")}
          </p>
          <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
            {t("ctaButton")}
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </div>
  );
}
