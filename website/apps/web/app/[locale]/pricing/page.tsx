import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Check, Phone, Building2, Shield, Globe } from "lucide-react";

interface PricingPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: PricingPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("pricingPage");
  return buildMetadata({
    title: t("badge"),
    description: t("subheading"),
    path: "/pricing",
    locale,
  });
}

const TIERS = [
  { key: "starter", ctaHref: "/demo", highlight: false, color: "default" },
  { key: "professional", ctaHref: "/contact", highlight: true, color: "orange" },
  { key: "enterprise", ctaHref: "/contact", highlight: false, color: "default" },
  { key: "government", ctaHref: "/contact", highlight: false, color: "amber" },
];

const MODULE_PRICING_KEYS = ["healthcare", "enterprise", "government", "platform"];

const FAQ_KEYS = ["q1", "q2", "q3", "q4", "q5", "q6"];

export default async function PricingPage({ params }: PricingPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("pricingPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/6" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            {t("badge")}
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            {t("heading")}
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-4">
            {t("subheading")}
          </p>
          <p className="text-sm text-cy-gray-500">
            {t("note")}
          </p>
        </div>
      </div>

      {/* Pricing Tiers */}
      <section className="py-8 pb-20" aria-labelledby="tiers-heading">
        <h2 id="tiers-heading" className="sr-only">Pricing Tiers</h2>
        <div className="section-container">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {TIERS.map((tier) => {
              const features = t.raw(`tiers.${tier.key}.features`) as string[];
              const badge = t(`tiers.${tier.key}.badge`) || null;
              return (
                <div
                  key={tier.key}
                  className={`relative glass-card p-6 rounded-2xl flex flex-col ${tier.highlight ? "border-cy-orange/40 shadow-orange-glow" : "border-cy-glass-border"}`}
                >
                  {badge && (
                    <div className={`absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-2xs font-semibold whitespace-nowrap ${tier.color === "orange" ? "bg-cy-orange text-white" : tier.color === "amber" ? "bg-amber-500 text-white" : "bg-cy-glass-bg border border-cy-glass-border text-cy-gray-200"}`}>
                      {badge}
                    </div>
                  )}

                  <div className="mb-4">
                    <h3 className="text-lg font-heading font-semibold text-white mb-0.5">{t(`tiers.${tier.key}.name`)}</h3>
                    <p className="text-xs text-cy-gray-400">{t(`tiers.${tier.key}.subtitle`)}</p>
                  </div>

                  <div className="mb-6">
                    <span className="text-2xl font-heading font-semibold text-white">{t("customPricing")}</span>
                    <p className="text-xs text-cy-gray-500 mt-1">{t(`tiers.${tier.key}.tagline`)}</p>
                  </div>

                  <ul className="space-y-2.5 flex-1 mb-8">
                    {features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-xs text-cy-gray-200">
                        <Check className="w-3.5 h-3.5 text-cy-orange flex-shrink-0 mt-0.5" aria-hidden="true" />
                        {f}
                      </li>
                    ))}
                  </ul>

                  <Link
                    href={`/${l}${tier.ctaHref}`}
                    className={`w-full justify-center text-sm py-2.5 ${tier.highlight ? "btn-primary" : "btn-secondary"}`}
                  >
                    {t(`tiers.${tier.key}.cta`)}
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Module Pricing */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="modules-heading">
        <div className="section-container">
          <h2 id="modules-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("modules.heading")}
          </h2>
          <p className="text-cy-gray-400 text-center mb-12">
            {t("modules.subheading")}
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            {MODULE_PRICING_KEYS.map((key) => {
              const products = t.raw(`modules.${key}.products`) as string[];
              return (
                <div key={key} className="glass-card p-6 rounded-2xl">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <span className="w-1.5 h-4 rounded-full bg-cy-orange" aria-hidden="true" />
                    {t(`modules.${key}.category`)}
                  </h3>
                  <ul className="space-y-2">
                    {products.map((p) => (
                      <li key={p} className="flex items-center gap-2 text-sm text-cy-gray-300">
                        <Check className="w-3.5 h-3.5 text-cy-orange flex-shrink-0" aria-hidden="true" />
                        {p}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20" aria-labelledby="faq-heading">
        <div className="section-container max-w-3xl">
          <h2 id="faq-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            {t("faq.heading")}
          </h2>
          <div className="space-y-6">
            {FAQ_KEYS.map((key) => (
              <div key={key} className="glass-card p-6 rounded-2xl">
                <h3 className="font-heading font-semibold text-white mb-2">{t(`faq.${key}.q`)}</h3>
                <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`faq.${key}.a`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="pricing-cta">
        <div className="section-container">
          <div className="glass-card p-10 lg:p-14 rounded-3xl">
            <div className="grid lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <h2 id="pricing-cta" className="text-3xl font-heading font-semibold text-white mb-4">
                  {t("cta.heading")}
                </h2>
                <p className="text-cy-gray-400 leading-relaxed mb-6">
                  {t("cta.subheading")}
                </p>
                <div className="flex flex-wrap gap-4">
                  <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
                    {t("cta.requestDemo")}
                    <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
                  </Link>
                  <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                    {t("cta.contactSales")}
                  </Link>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                    <Phone className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{t("cta.salesTeam.title")}</div>
                    <div className="text-xs text-cy-gray-400">{t("cta.salesTeam.desc")}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                    <Building2 className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{t("cta.enterpriseGov.title")}</div>
                    <div className="text-xs text-cy-gray-400">{t("cta.enterpriseGov.desc")}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                    <Globe className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{t("cta.region.title")}</div>
                    <div className="text-xs text-cy-gray-400">{t("cta.region.desc")}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
