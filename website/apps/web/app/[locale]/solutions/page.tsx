import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import {
  ArrowRight,
  Hospital,
  Building2,
  Landmark,
  FlaskConical,
  Pill,
  Scan,
  Users,
  BarChart3,
  Shield,
  Zap,
  Globe,
  CheckCircle2,
} from "lucide-react";

interface SolutionsPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: SolutionsPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("solutionsPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/solutions",
    locale,
  });
}

const INDUSTRY_SOLUTIONS = [
  {
    id: "healthcare",
    icon: Hospital,
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    iconClass: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
    gradientClass: "from-emerald-900/20 to-transparent",
    products: [
      { key: "hospital", slug: "cymed-hospital" },
      { key: "clinic", slug: "cymed-clinic" },
      { key: "laboratory", slug: "cymed-laboratory" },
      { key: "imaging", slug: "cymed-imaging" },
      { key: "pharmacy", slug: "cymed-pharmacy" },
      { key: "portal", slug: "cymed-patient-portal" },
    ],
    ctaHref: "/products/cymed-clinic",
  },
  {
    id: "government",
    icon: Landmark,
    color: "amber",
    accentClass: "text-amber-400 border-amber-500/20 bg-amber-500/5",
    iconClass: "bg-amber-500/10 border-amber-500/20 text-amber-400",
    gradientClass: "from-amber-900/20 to-transparent",
    products: [
      { key: "cygov", slug: "cygov" },
      { key: "cycitizen", slug: "cycitizen" },
      { key: "cyidentity", slug: "cyidentity" },
      { key: "cyintegrationhub", slug: "cyintegrationhub" },
    ],
    ctaHref: "/products/cygov",
  },
  {
    id: "enterprise",
    icon: Building2,
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
    iconClass: "bg-blue-500/10 border-blue-500/20 text-blue-400",
    gradientClass: "from-blue-900/20 to-transparent",
    products: [
      { key: "cycom", slug: "cycom" },
      { key: "cyai", slug: "cyai" },
      { key: "cydata", slug: "cydata" },
      { key: "cyconnect", slug: "cyconnect" },
    ],
    ctaHref: "/products/cycom",
  },
];

const DEPLOYMENT_MODELS = [
  { icon: Globe, key: "saas" },
  { icon: Shield, key: "private" },
  { icon: Building2, key: "onPremise" },
  { icon: Zap, key: "hybrid" },
];

const CROSS_CUTTING = [
  { icon: Shield, key: "cyidentity", slug: "cyidentity" },
  { icon: Globe, key: "cyintegrationhub", slug: "cyintegrationhub" },
  { icon: BarChart3, key: "cydata", slug: "cydata" },
  { icon: Users, key: "cyconnect", slug: "cyconnect" },
];

export default async function SolutionsPage({ params }: SolutionsPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("solutionsPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[700px] h-[700px] -top-40 left-1/2 -translate-x-1/2 bg-cy-orange/6" />
        </div>
        <div className="section-container relative z-10">
          <div className="max-w-4xl">
            <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
              {t("badge")}
            </span>
            <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
              {t("headingPrefix")}{" "}
              <span className="text-gradient">{t("headingHighlight")}</span>
            </h1>
            <p className="text-xl text-cy-gray-400 leading-relaxed max-w-3xl mb-8">
              {t("description")}
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
                {t("requestDemo")}
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                {t("talkSpecialist")}
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Industry Solutions */}
      <section className="py-20" aria-labelledby="industries-heading">
        <div className="section-container">
          <h2 id="industries-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("industries.heading")}
          </h2>
          <p className="text-center text-cy-gray-400 mb-16 max-w-2xl mx-auto">
            {t("industries.subheading")}
          </p>

          <div className="space-y-16">
            {INDUSTRY_SOLUTIONS.map((industry, idx) => {
              const Icon = industry.icon;
              const outcomes = t.raw(`industries.${industry.id}.outcomes`) as string[];
              return (
                <div
                  key={industry.id}
                  className={`rounded-3xl border border-cy-glass-border overflow-hidden bg-gradient-to-br ${industry.gradientClass} p-8 lg:p-12`}
                >
                  <div className="grid lg:grid-cols-2 gap-10 items-start">
                    {/* Left */}
                    <div className={idx % 2 === 1 ? "lg:order-2" : ""}>
                      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border mb-4 text-xs font-medium ${industry.accentClass}`}>
                        <Icon className="w-3.5 h-3.5" aria-hidden="true" />
                        {t(`industries.${industry.id}.title`)}
                      </div>
                      <h3 className="text-2xl font-heading font-semibold text-white mb-3">
                        {t(`industries.${industry.id}.tagline`)}
                      </h3>
                      <p className="text-cy-gray-400 leading-relaxed mb-6">
                        {t(`industries.${industry.id}.description`)}
                      </p>

                      {/* Outcomes */}
                      <ul className="space-y-2 mb-8" aria-label="Key outcomes">
                        {outcomes.map((o) => (
                          <li key={o} className="flex items-center gap-2.5 text-sm text-cy-gray-200">
                            <CheckCircle2 className={`w-4 h-4 flex-shrink-0 ${industry.accentClass.split(" ")[0]}`} aria-hidden="true" />
                            {o}
                          </li>
                        ))}
                      </ul>

                      <Link href={`/${l}${industry.ctaHref}`} className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium border transition-colors duration-150 ${industry.accentClass} hover:bg-opacity-20`}>
                        {t(`industries.${industry.id}.ctaLabel`)}
                        <ArrowRight className="w-3.5 h-3.5 rtl:rotate-180" aria-hidden="true" />
                      </Link>
                    </div>

                    {/* Right — Products Grid */}
                    <div className={`grid sm:grid-cols-2 gap-3 ${idx % 2 === 1 ? "lg:order-1" : ""}`}>
                      {industry.products.map((p) => (
                        <Link
                          key={p.slug}
                          href={`/${l}/products/${p.slug}`}
                          className="glass-card p-4 rounded-xl hover:border-cy-glass-bg-hover transition-all duration-150 cursor-pointer group"
                        >
                          <div className="text-sm font-medium text-white group-hover:text-gradient-orange mb-1 transition-colors">
                            {t(`industries.${industry.id}.products.${p.key}.name`)}
                          </div>
                          <div className="text-xs text-cy-gray-400 leading-relaxed">{t(`industries.${industry.id}.products.${p.key}.desc`)}</div>
                        </Link>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Platform Foundation */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="platform-heading">
        <div className="section-container">
          <div className="text-center mb-12">
            <h2 id="platform-heading" className="text-3xl font-heading font-semibold text-white mb-4">
              {t("platform.heading")}
            </h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">
              {t("platform.subheading")}
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {CROSS_CUTTING.map((c) => {
              const Icon = c.icon;
              return (
                <Link
                  key={c.slug}
                  href={`/${l}/products/${c.slug}`}
                  className="glass-card p-5 rounded-2xl hover:border-cy-glass-bg-hover transition-all duration-150 cursor-pointer group"
                >
                  <div className="w-10 h-10 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div className="text-sm font-heading font-semibold text-white mb-1 group-hover:text-gradient-orange transition-colors">
                    {t(`platform.${c.key}.title`)}
                  </div>
                  <div className="text-xs text-cy-gray-400 leading-relaxed">{t(`platform.${c.key}.desc`)}</div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* Deployment Models */}
      <section className="py-20" aria-labelledby="deployment-heading">
        <div className="section-container">
          <h2 id="deployment-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("deployment.heading")}
          </h2>
          <p className="text-center text-cy-gray-400 mb-12">
            {t("deployment.subheading")}
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {DEPLOYMENT_MODELS.map((d) => {
              const Icon = d.icon;
              return (
                <div key={d.key} className="glass-card p-6 rounded-2xl">
                  <div className="w-10 h-10 rounded-xl bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cy-gray-200" aria-hidden="true" />
                  </div>
                  <h3 className="font-heading font-semibold text-white mb-1">{t(`deployment.${d.key}.title`)}</h3>
                  <p className="text-xs text-cy-gray-400 leading-relaxed mb-3">{t(`deployment.${d.key}.desc`)}</p>
                  <p className="text-2xs text-cy-gray-600 uppercase tracking-wider">{t("deployment.bestFor")}</p>
                  <p className="text-xs text-cy-gray-400">{t(`deployment.${d.key}.fit`)}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="solutions-cta">
        <div className="section-container">
          <div className="glass-card p-10 lg:p-14 rounded-3xl text-center max-w-3xl mx-auto">
            <h2 id="solutions-cta" className="text-3xl font-heading font-semibold text-white mb-4">
              {t("cta.heading")}
            </h2>
            <p className="text-cy-gray-400 mb-8 leading-relaxed">
              {t("cta.subheading")}
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
                {t("cta.requestDemo")}
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                {t("cta.talkSales")}
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
