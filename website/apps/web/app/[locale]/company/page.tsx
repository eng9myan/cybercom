import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Users, Globe2, Target, Award, Shield, Zap, Heart } from "lucide-react";

interface CompanyPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: CompanyPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("companyPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/company",
    locale,
  });
}

const STATS_KEYS = ["platforms", "clinical", "erp", "standard"];

const VALUES = [
  { key: "security", icon: Shield, color: "text-violet-400", bg: "bg-violet-500/10 border-violet-500/20" },
  { key: "safety", icon: Heart, color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" },
  { key: "regional", icon: Globe2, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { key: "ecosystem", icon: Zap, color: "text-cy-orange", bg: "bg-cy-orange/10 border-cy-orange/20" },
  { key: "enterprise", icon: Target, color: "text-sky-400", bg: "bg-sky-500/10 border-sky-500/20" },
  { key: "standards", icon: Award, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
];

const PLATFORMS = [
  { key: "cymed", name: "CyMed", color: "text-emerald-400", border: "border-emerald-500/20", bg: "bg-emerald-500/5", href: "/products/cymed" },
  { key: "cyshop", name: "CyShop", color: "text-cy-orange", border: "border-cy-orange/20", bg: "bg-cy-orange/5", href: "/products/cyshop" },
  { key: "cycom", name: "CyCom ERP", color: "text-blue-400", border: "border-blue-500/20", bg: "bg-blue-500/5", href: "/products/cycom" },
];

export default async function CompanyPage({ params }: CompanyPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("companyPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <section className="relative py-24 overflow-hidden" aria-labelledby="company-heading">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/6" />
          <div className="glow-orb w-[400px] h-[400px] top-1/2 -right-32 bg-sky-500/5" />
        </div>
        <div className="section-container relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cy-orange/20 bg-cy-orange/5 mb-6">
              <div className="w-1.5 h-1.5 rounded-full bg-cy-orange animate-pulse" aria-hidden="true" />
              <span className="text-xs font-medium text-cy-orange tracking-wider uppercase">{t("badge")}</span>
            </div>
            <h1 id="company-heading" className="text-4xl sm:text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
              {t("heroLine1")}<br />
              <span className="text-gradient-orange">{t("heroLine2")}</span><br />
              {t("heroLine3")}
            </h1>
            <p className="text-lg text-cy-gray-400 leading-relaxed max-w-2xl mx-auto mb-8">
              {t("heroDescription")}
            </p>
            <div className="flex flex-wrap gap-3 justify-center">
              <Link href={`/${l}/contact`} className="btn-primary px-6 py-3 text-sm inline-flex items-center gap-2">
                {t("contactUs")}
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${l}/about`} className="btn-secondary px-6 py-3 text-sm">
                {t("aboutCybercom")}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 border-y border-cy-glass-border bg-cy-dark/30" aria-label="Company statistics">
        <div className="section-container">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {STATS_KEYS.map((key) => (
              <div key={key} className="text-center">
                <div className="text-3xl sm:text-4xl font-heading font-bold text-gradient-orange mb-1">{t(`stats.${key}.value`)}</div>
                <div className="text-sm font-medium text-white mb-1">{t(`stats.${key}.label`)}</div>
                <div className="text-xs text-cy-gray-400">{t(`stats.${key}.desc`)}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Our Platforms */}
      <section className="py-20" aria-labelledby="platforms-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="platforms-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("platforms.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("platforms.subheading")}</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {PLATFORMS.map((p) => {
              const tagline = t(`platforms.${p.key}.tagline`);
              return (
                <Link
                  key={p.key}
                  href={`/${l}${p.href}`}
                  className={`glass-card rounded-2xl p-8 border ${p.border} ${p.bg} hover:scale-[1.01] transition-all duration-200 cursor-pointer group flex flex-col`}
                  aria-label={`${p.name} — ${tagline}`}
                >
                  <span className={`product-badge mb-4 ${p.color} ${p.border} ${p.bg} self-start`}>{t(`platforms.${p.key}.badge`)}</span>
                  <h3 className={`text-2xl font-heading font-bold ${p.color} mb-2`}>{p.name}</h3>
                  <p className="text-sm font-medium text-white mb-3">{tagline}</p>
                  <p className="text-sm text-cy-gray-400 leading-relaxed flex-1 mb-6">{t(`platforms.${p.key}.desc`)}</p>
                  <span className={`text-sm ${p.color} flex items-center gap-1 font-medium`}>
                    {t("platforms.explore")} {p.name}
                    <ArrowRight className="w-4 h-4 rtl:rotate-180 group-hover:translate-x-1 transition-transform" aria-hidden="true" />
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="values-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="values-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("values.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("values.subheading")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {VALUES.map((v) => (
              <div key={v.key} className={`glass-card rounded-xl p-6 border ${v.bg}`}>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center border mb-4 ${v.bg}`}>
                  <v.icon className={`w-5 h-5 ${v.color}`} aria-hidden="true" />
                </div>
                <h3 className={`text-base font-heading font-semibold ${v.color} mb-2`}>{t(`values.${v.key}.title`)}</h3>
                <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`values.${v.key}.desc`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-20" aria-labelledby="mission-heading">
        <div className="section-container max-w-4xl mx-auto text-center">
          <h2 id="mission-heading" className="text-3xl font-heading font-semibold text-white mb-6">{t("mission.heading")}</h2>
          <blockquote className="text-xl text-cy-gray-200 leading-relaxed mb-8 italic">
            &ldquo;{t("mission.quote")}&rdquo;
          </blockquote>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link href={`/${l}/careers`} className="btn-primary px-6 py-3 text-sm inline-flex items-center gap-2">
              <Users className="w-4 h-4" aria-hidden="true" />
              {t("mission.joinTeam")}
            </Link>
            <Link href={`/${l}/investors`} className="btn-secondary px-6 py-3 text-sm">
              {t("mission.investorRelations")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
