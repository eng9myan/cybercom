import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Users, TrendingUp, BookOpen, Package, DollarSign, BarChart2, CheckCircle, Globe } from "lucide-react";

interface PartnerPortalPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: PartnerPortalPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("partnerPortalPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/partner",
    locale,
  });
}

const PORTAL_MODULES = [
  { key: "pipeline", icon: TrendingUp },
  { key: "dealReg", icon: DollarSign },
  { key: "revenue", icon: BarChart2 },
  { key: "assets", icon: Package },
  { key: "academy", icon: BookOpen },
  { key: "coMarketing", icon: Users },
];

const TIERS = [
  { key: "authorized", color: "text-cy-gray-400 border-cy-glass-border", featured: false },
  { key: "silver", color: "text-slate-300 border-slate-400/30", featured: false },
  { key: "gold", color: "text-amber-400 border-amber-500/40", featured: true },
  { key: "platinum", color: "text-cy-cyan border-cy-cyan/40", featured: false },
];

const REGIONS = [
  { key: "levant", contact: "levant@cy-com.com" },
  { key: "gulf", contact: "gulf@cy-com.com" },
  { key: "ksa", contact: "ksa@cy-com.com" },
  { key: "africa", contact: "africa@cy-com.com" },
  { key: "intl", contact: "intl@cy-com.com" },
];

export default async function PartnerPortalPage({ params }: PartnerPortalPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("partnerPortalPage");
  const portalUrl = process.env.NEXT_PUBLIC_PORTAL_URL ?? "https://portal.cy-com.com";

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[700px] h-[700px] -top-24 left-1/3 bg-cy-cyan/5" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-cyan border-cy-cyan/20 bg-cy-cyan/5 mb-6">
            {t("badge")}
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            {t("headingPrefix")}{" "}
            <span className="text-gradient">{t("headingHighlight")}</span>
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-10">
            {t("subheading")}
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <a href={`${portalUrl}/partner`} className="btn-primary px-8 py-3" target="_blank" rel="noreferrer">
              {t("signIn")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </a>
            <Link href={`/${l}/partners`} className="btn-secondary px-8 py-3">
              {t("applyForPartnership")}
            </Link>
          </div>
        </div>
      </div>

      {/* Portal modules */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="modules-heading">
        <div className="section-container">
          <h2 id="modules-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("modulesHeading")}
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-2xl mx-auto">
            {t("modulesDesc")}
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {PORTAL_MODULES.map((mod) => {
              const Icon = mod.icon;
              return (
                <div key={mod.key} className="glass-card p-6 rounded-2xl">
                  <div className="w-10 h-10 rounded-xl bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cy-cyan" aria-hidden="true" />
                  </div>
                  <h3 className="text-base font-heading font-semibold text-white mb-2">{t(`modules.${mod.key}.title`)}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`modules.${mod.key}.desc`)}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Partner tiers */}
      <section className="py-20" aria-labelledby="tiers-heading">
        <div className="section-container">
          <h2 id="tiers-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("tiersHeading")}
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-xl mx-auto">
            {t("tiersDesc")}
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {TIERS.map((tier) => {
              const requirements = t.raw(`tiers.${tier.key}.requirements`) as string[];
              const benefits = t.raw(`tiers.${tier.key}.benefits`) as string[];
              return (
                <div key={tier.key} className={`glass-card p-6 rounded-2xl border ${tier.featured ? "border-amber-500/40" : "border-cy-glass-border"}`}>
                  {tier.featured && (
                    <span className="text-2xs font-semibold text-amber-400 block mb-2">{t("mostPartners")}</span>
                  )}
                  <h3 className={`text-xl font-heading font-semibold mb-4 ${tier.color.split(" ")[0]}`}>{t(`tiers.${tier.key}.name`)}</h3>
                  <div className="mb-4">
                    <p className="text-2xs font-medium text-cy-gray-400 uppercase tracking-wider mb-2">{t("requirements")}</p>
                    <ul className="space-y-1">
                      {requirements.map((r) => (
                        <li key={r} className="text-xs text-cy-gray-300 flex items-start gap-1.5">
                          <span className="text-cy-gray-500 mt-0.5">–</span>
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-2xs font-medium text-cy-gray-400 uppercase tracking-wider mb-2">{t("benefits")}</p>
                    <ul className="space-y-1.5">
                      {benefits.map((b) => (
                        <li key={b} className="flex items-start gap-1.5 text-xs text-cy-gray-200">
                          <CheckCircle className="w-3 h-3 text-cy-orange mt-0.5 flex-shrink-0" aria-hidden="true" />
                          {b}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Regional contacts */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="regions-heading">
        <div className="section-container max-w-3xl">
          <h2 id="regions-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("regionsHeading")}
          </h2>
          <p className="text-cy-gray-400 text-center mb-10">
            {t("regionsDesc")}
          </p>
          <div className="grid sm:grid-cols-2 gap-4">
            {REGIONS.map((r) => (
              <div key={r.key} className="glass-card p-5 rounded-xl flex items-center gap-4">
                <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                  <Globe className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                </div>
                <div>
                  <div className="text-sm font-medium text-white">{t(`regions.${r.key}`)}</div>
                  <a href={`mailto:${r.contact}`} className="text-xs text-cy-gray-400 hover:text-cy-orange transition-colors">
                    {r.contact}
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Apply CTA */}
      <section className="py-20" aria-labelledby="apply-cta">
        <div className="section-container">
          <div className="glass-card p-10 lg:p-14 rounded-3xl text-center">
            <h2 id="apply-cta" className="text-3xl font-heading font-semibold text-white mb-4">
              {t("ctaHeading")}
            </h2>
            <p className="text-cy-gray-400 max-w-xl mx-auto mb-8">
              {t("ctaDesc")}
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <Link href={`/${l}/partners`} className="btn-primary px-8 py-3">
                {t("applyNow")}
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                {t("talkToPartnerships")}
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
