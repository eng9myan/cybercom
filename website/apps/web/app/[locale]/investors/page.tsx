import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, TrendingUp, Globe, Shield, Layers, BarChart3, Cpu } from "lucide-react";

interface InvestorsPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: InvestorsPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("investorsPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/investors",
    locale,
  });
}

const METRICS = ["products", "standards", "deployment", "markets", "languages", "regulatory"];

const MARKET_SEGMENTS = [
  { key: "healthcare", icon: TrendingUp },
  { key: "government", icon: Globe },
  { key: "enterprise", icon: BarChart3 },
];

const DIFFERENTIATORS = [
  { key: "unified", icon: Layers },
  { key: "safety", icon: Shield },
  { key: "standards", icon: Cpu },
  { key: "regional", icon: Globe },
];

const PLATFORM_PRODUCTS = [
  { key: "cymed", name: "CyMed", status: "Production Ready" as const },
  { key: "cycom", name: "CyCom", status: "Production Ready" as const },
  { key: "cygov", name: "CyGov", status: "Production Ready" as const },
  { key: "cycitizen", name: "CyCitizen", status: "Production Ready" as const },
  { key: "cyidentity", name: "CyIdentity", status: "Production Ready" as const },
  { key: "cyintegrationhub", name: "CyIntegrationHub", status: "Production Ready" as const },
  { key: "cyai", name: "CyAI", status: "Advisory Only" as const },
  { key: "cydata", name: "CyData", status: "Production Ready" as const },
  { key: "cyconnect", name: "CyConnect", status: "Production Ready" as const },
];

export default async function InvestorsPage({ params }: InvestorsPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("investorsPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[700px] h-[700px] -top-40 left-1/2 -translate-x-1/2 bg-cy-orange/6" />
        </div>
        <div className="section-container relative z-10 max-w-4xl">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            {t("badge")}
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
            {t("headingPrefix")}{" "}
            <span className="text-gradient">{t("headingHighlight")}</span>
          </h1>
          <p className="text-xl text-cy-gray-400 leading-relaxed max-w-3xl mb-8">
            {t("heroDesc")}
          </p>
          <a
            href="mailto:investors@cy-com.com"
            className="btn-primary px-8 py-3 inline-flex"
          >
            {t("contactIR")}
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </a>
        </div>
      </div>

      {/* Key Metrics */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="metrics-heading">
        <div className="section-container">
          <h2 id="metrics-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            {t("metricsHeading")}
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {METRICS.map((key) => (
              <div key={key} className="glass-card p-6 rounded-2xl text-center">
                <div className="text-4xl font-heading font-bold text-gradient-orange mb-1">{t(`metrics.${key}.value`)}</div>
                <div className="text-sm font-medium text-white mb-1">{t(`metrics.${key}.label`)}</div>
                <div className="text-xs text-cy-gray-400">{t(`metrics.${key}.desc`)}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Market Opportunity */}
      <section className="py-20" aria-labelledby="market-heading">
        <div className="section-container">
          <h2 id="market-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("marketHeading")}
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-2xl mx-auto">
            {t("marketDesc")}
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {MARKET_SEGMENTS.map((seg) => {
              const Icon = seg.icon;
              return (
                <div key={seg.key} className="glass-card p-6 rounded-2xl">
                  <div className="w-10 h-10 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                  </div>
                  <h3 className="font-heading font-semibold text-white mb-2">{t(`marketSegments.${seg.key}.title`)}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed mb-4">{t(`marketSegments.${seg.key}.desc`)}</p>
                  <div className="text-xs text-cy-orange bg-cy-orange/5 border border-cy-orange/20 rounded-lg px-3 py-2">
                    {t(`marketSegments.${seg.key}.highlight`)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Differentiation */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="diff-heading">
        <div className="section-container">
          <h2 id="diff-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            {t("diffHeading")}
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {DIFFERENTIATORS.map((d) => {
              const Icon = d.icon;
              return (
                <div key={d.key} className="glass-card p-6 rounded-2xl flex gap-4">
                  <div className="w-10 h-10 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <h3 className="font-heading font-semibold text-white mb-2">{t(`differentiators.${d.key}.title`)}</h3>
                    <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`differentiators.${d.key}.desc`)}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Product Portfolio */}
      <section className="py-20" aria-labelledby="portfolio-heading">
        <div className="section-container">
          <h2 id="portfolio-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            {t("portfolioHeading")}
          </h2>
          <div className="overflow-x-auto rounded-2xl border border-cy-glass-border">
            <table className="w-full text-sm" role="table" aria-label="Product portfolio status">
              <thead>
                <tr className="border-b border-cy-glass-border bg-cy-dark/50">
                  <th scope="col" className="text-left px-5 py-3.5 text-xs font-semibold text-cy-gray-400 uppercase tracking-wider">{t("platform")}</th>
                  <th scope="col" className="text-left px-5 py-3.5 text-xs font-semibold text-cy-gray-400 uppercase tracking-wider">{t("category")}</th>
                  <th scope="col" className="text-left px-5 py-3.5 text-xs font-semibold text-cy-gray-400 uppercase tracking-wider hidden md:table-cell">{t("products")}</th>
                  <th scope="col" className="text-left px-5 py-3.5 text-xs font-semibold text-cy-gray-400 uppercase tracking-wider">{t("status")}</th>
                </tr>
              </thead>
              <tbody>
                {PLATFORM_PRODUCTS.map((p, i) => (
                  <tr key={p.key} className={`border-b border-cy-glass-border last:border-0 ${i % 2 === 0 ? "" : "bg-cy-dark/20"}`}>
                    <td className="px-5 py-4 font-heading font-semibold text-white">{p.name}</td>
                    <td className="px-5 py-4 text-cy-gray-400">{t(`portfolio.${p.key}.category`)}</td>
                    <td className="px-5 py-4 text-cy-gray-400 hidden md:table-cell text-xs leading-relaxed">{t(`portfolio.${p.key}.products`)}</td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${p.status === "Production Ready" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${p.status === "Production Ready" ? "bg-emerald-400" : "bg-amber-400"}`} aria-hidden="true" />
                        {t(`statusLabels.${p.status}`)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="investors-cta">
        <div className="section-container text-center max-w-2xl">
          <h2 id="investors-cta" className="text-3xl font-heading font-semibold text-white mb-4">
            {t("ctaHeading")}
          </h2>
          <p className="text-cy-gray-400 mb-8 leading-relaxed">
            {t("ctaDesc")}
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="mailto:investors@cy-com.com" className="btn-primary px-8 py-3 inline-flex">
              investors@cy-com.com
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </a>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
              {t("contactUs")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
