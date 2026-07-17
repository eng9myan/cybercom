import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Check } from "lucide-react";

interface PartnersPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: PartnersPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("partnersPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/partners",
    locale,
  });
}

const PARTNER_TIERS = [
  { key: "authorized", color: "text-cy-gray-400", border: "border-cy-glass-border" },
  { key: "silver", color: "text-slate-300", border: "border-slate-400/30" },
  { key: "gold", color: "text-amber-400", border: "border-amber-500/30", featured: true },
  { key: "platinum", color: "text-cy-cyan", border: "border-cy-cyan/30" },
];

const PARTNER_TYPES = [
  { key: "implementation", icon: "⚙️" },
  { key: "reseller", icon: "🤝" },
  { key: "technology", icon: "🔗" },
  { key: "consulting", icon: "💡" },
];

export default async function PartnersPage({ params }: PartnersPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("partnersPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/8" />
        </div>
        <div className="section-container relative z-10 text-center">
          <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">{t("badge")}</p>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-4">
            {t("heading")}
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-8">
            {t("subheading")}
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href={`/${locale}/contact`} className="btn-primary px-8 py-3">
              {t("applyButton")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${locale}/demo`} className="btn-secondary px-8 py-3">
              {t("partnerLogin")}
            </Link>
          </div>
        </div>
      </div>

      {/* Partner types */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="types-heading">
        <div className="section-container">
          <h2 id="types-heading" className="text-3xl font-heading font-semibold text-white mb-10 text-center">
            {t("types.heading")}
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {PARTNER_TYPES.map((pt) => (
              <div key={pt.key} className="glass-card p-6 rounded-2xl text-center">
                <div className="text-3xl mb-4" aria-hidden="true" role="img">{pt.icon}</div>
                <h3 className="font-heading font-semibold text-white mb-2">{t(`types.${pt.key}.type`)}</h3>
                <p className="text-xs text-cy-gray-400 leading-relaxed">{t(`types.${pt.key}.desc`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tiers */}
      <section className="py-20" aria-labelledby="tiers-heading">
        <div className="section-container">
          <h2 id="tiers-heading" className="text-3xl font-heading font-semibold text-white mb-10 text-center">
            {t("tiers.heading")}
          </h2>
          <div className="grid md:grid-cols-4 gap-4">
            {PARTNER_TIERS.map((tier) => {
              const benefits = t.raw(`tiers.${tier.key}.benefits`) as string[];
              return (
                <div
                  key={tier.key}
                  className={`glass-card p-6 rounded-2xl border ${tier.border} ${tier.featured ? "ring-1 ring-amber-500/20" : ""}`}
                >
                  {tier.featured && (
                    <div className="text-2xs font-medium text-amber-400 uppercase tracking-wider mb-3">{t("tiers.mostPopular")}</div>
                  )}
                  <h3 className={`font-heading font-semibold text-xl mb-4 ${tier.color}`}>{t(`tiers.${tier.key}.name`)}</h3>
                  <ul className="space-y-2">
                    {benefits.map((b) => (
                      <li key={b} className="flex items-start gap-2 text-xs text-cy-gray-400">
                        <Check className="w-3.5 h-3.5 text-cy-orange flex-shrink-0 mt-0.5" aria-hidden="true" />
                        {b}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="benefits-heading">
        <div className="section-container">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 id="benefits-heading" className="text-3xl font-heading font-semibold text-white mb-4">
                {t("benefitsSection.heading")}
              </h2>
              <p className="text-cy-gray-400 mb-8">
                {t("benefitsSection.subheading")}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {(t.raw("benefitsSection.list") as string[]).map((b) => (
                  <div key={b} className="flex items-start gap-2 text-sm text-cy-gray-200">
                    <Check className="w-4 h-4 text-cy-orange flex-shrink-0 mt-0.5" aria-hidden="true" />
                    {b}
                  </div>
                ))}
              </div>
            </div>
            <div className="glass-card p-8 rounded-2xl">
              <h3 className="font-heading font-semibold text-white text-xl mb-4">{t("benefitsSection.readyHeading")}</h3>
              <p className="text-sm text-cy-gray-400 mb-6">
                {t("benefitsSection.readyDesc")}
              </p>
              <Link href={`/${locale}/contact`} className="btn-primary w-full justify-center py-3.5">
                {t("benefitsSection.applyNow")}
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <p className="text-2xs text-cy-gray-600 text-center mt-4">
                {t("benefitsSection.alreadyPartner")} <Link href={`/${locale}/demo`} className="text-cy-orange hover:underline">{t("benefitsSection.contactPortal")}</Link>
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
