import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, ExternalLink, Play, Calendar } from "lucide-react";

interface DemoCenterProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: DemoCenterProps): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations("demoCenterPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/demo-center",
    locale,
  });
}

interface DemoProduct {
  key: string;
  color: string;
  accentClass: string;
  pillClass: string;
  demoUrl: string;
  productSlug: string;
}

const DEMO_PRODUCTS: DemoProduct[] = [
  { key: "hospital", color: "emerald", accentClass: "from-emerald-900/20 to-transparent", pillClass: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", demoUrl: "https://cymed.cy-com.com/hospital", productSlug: "cymed-hospital" },
  { key: "clinic", color: "emerald", accentClass: "from-emerald-900/15 to-transparent", pillClass: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", demoUrl: "https://cymed.cy-com.com/clinic", productSlug: "cymed-clinic" },
  { key: "pharmacy", color: "emerald", accentClass: "from-teal-900/15 to-transparent", pillClass: "text-teal-400 bg-teal-500/10 border-teal-500/20", demoUrl: "https://cymed.cy-com.com/pharmacy", productSlug: "cymed-pharmacy" },
  { key: "laboratory", color: "emerald", accentClass: "from-cyan-900/15 to-transparent", pillClass: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20", demoUrl: "https://cymed.cy-com.com/laboratory", productSlug: "cymed-laboratory" },
  { key: "imaging", color: "indigo", accentClass: "from-indigo-900/15 to-transparent", pillClass: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20", demoUrl: "https://cymed.cy-com.com/imaging", productSlug: "cymed-imaging" },
  { key: "cyshop", color: "orange", accentClass: "from-orange-900/20 to-transparent", pillClass: "text-orange-400 bg-orange-500/10 border-orange-500/20", demoUrl: "https://cyshop.cy-com.com", productSlug: "cyshop" },
  { key: "erp", color: "blue", accentClass: "from-blue-900/20 to-transparent", pillClass: "text-blue-400 bg-blue-500/10 border-blue-500/20", demoUrl: "https://health.cy-com.com", productSlug: "cycom-erp" },
];

export default async function DemoCenterPage({ params }: DemoCenterProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("demoCenterPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[700px] h-[700px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/5" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            {t("badge")}
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-semibold text-white mb-4 leading-tight">
            {t("heading")}
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-8 leading-relaxed">
            {t("subheading")}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href={`/${l}/demo`} className="btn-primary-glow px-8 py-3.5 text-base">
              {t("requestGuided")}
              <Calendar className="w-4 h-4" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/products`} className="btn-secondary px-8 py-3.5 text-base">
              {t("viewAllProducts")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      {/* Demo product cards */}
      <section className="pb-32">
        <div className="section-container">
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
            {DEMO_PRODUCTS.map(product => {
              const forWho = t(`products.${product.key}.forWho`);
              const keyModules = t.raw(`products.${product.key}.keyModules`) as string[];
              const erpModules = t.raw(`products.${product.key}.erpModules`) as string[];
              return (
                <div
                  key={product.key}
                  className={`glass-card rounded-2xl overflow-hidden border border-cy-glass-border hover:border-cy-glass-bg-hover transition-all duration-300 group bg-gradient-to-br ${product.accentClass}`}
                >
                  {/* Card header */}
                  <div className="p-6 pb-4">
                    <span className={`product-badge mb-3 ${product.pillClass}`}>
                      {forWho.split(",")[0]?.trim() ?? forWho}
                    </span>
                    <h2 className="text-xl font-heading font-semibold text-white mb-1">{t(`products.${product.key}.name`)}</h2>
                    <p className="text-sm text-cy-gray-400">{t(`products.${product.key}.subtitle`)}</p>
                    <p className="text-xs text-cy-gray-500 mt-1">{t("forLabel")} {forWho}</p>
                  </div>

                  {/* Key modules */}
                  <div className="px-6 pb-4">
                    <p className="text-xs font-medium text-cy-gray-400 uppercase tracking-wider mb-2">{t("keyModulesLabel")}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {keyModules.map(mod => (
                        <span key={mod} className="text-[10px] px-2 py-0.5 rounded-md bg-white/[0.04] text-cy-gray-300 border border-cy-glass-border">
                          {mod}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* ERP modules */}
                  <div className="px-6 pb-4">
                    <p className="text-xs font-medium text-blue-400 uppercase tracking-wider mb-2">{t("erpModulesLabel")}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {erpModules.map(mod => (
                        <span key={mod} className="text-[10px] px-2 py-0.5 rounded-md bg-blue-500/5 text-blue-300 border border-blue-500/15">
                          {mod}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="p-4 border-t border-cy-glass-border flex gap-2">
                    <a
                      href={product.demoUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="flex-1 inline-flex items-center justify-center gap-2 bg-cy-orange hover:bg-cy-orange-light text-white text-sm font-medium px-4 py-2.5 rounded-xl transition-all duration-200"
                    >
                      <Play className="w-3.5 h-3.5" aria-hidden="true" />
                      {t("launchDemo")}
                      <ExternalLink className="w-3 h-3 opacity-60" aria-hidden="true" />
                    </a>
                    <Link
                      href={`/${l}/products/${product.productSlug}`}
                      className="inline-flex items-center justify-center gap-2 btn-secondary text-sm px-4 py-2.5 flex-1"
                    >
                      {t("learnMore")}
                      <ArrowRight className="w-3.5 h-3.5 rtl:rotate-180" aria-hidden="true" />
                    </Link>
                  </div>

                  {/* Guided demo CTA */}
                  <div className="px-4 pb-4">
                    <Link
                      href={`/${l}/demo?product=${product.productSlug}`}
                      className="w-full text-xs text-cy-gray-400 hover:text-white transition-colors text-center py-2 inline-block"
                    >
                      <Calendar className="w-3 h-3 inline mr-1" aria-hidden="true" />
                      {t("guidedDemo")}
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="py-20 bg-cy-dark/40">
        <div className="section-container text-center">
          <h2 className="text-3xl font-heading font-semibold text-white mb-4">{t("bottomCta.heading")}</h2>
          <p className="text-lg text-cy-gray-400 max-w-xl mx-auto mb-8">
            {t("bottomCta.subheading")}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href={`/${l}/demo`} className="btn-primary-glow px-8 py-3.5 text-base">
              {t("bottomCta.bookDemo")}
              <Calendar className="w-4 h-4" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3.5 text-base">
              {t("bottomCta.contactSales")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
