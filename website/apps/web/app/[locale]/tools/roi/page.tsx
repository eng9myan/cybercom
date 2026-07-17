import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, TrendingUp, Clock, Users, DollarSign, CheckCircle, BarChart2 } from "lucide-react";

interface ROIPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: ROIPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("roiPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/tools/roi",
    locale,
  });
}

const ROI_SCENARIOS = [
  { key: "clinic", highlight: false },
  { key: "hospital", highlight: true },
  { key: "government", highlight: false },
];

const KEY_DRIVERS = [
  { key: "time", icon: Clock },
  { key: "revenue", icon: DollarSign },
  { key: "staff", icon: Users },
  { key: "risk", icon: BarChart2 },
];

const TREND_ROWS = [
  { yearNum: 1, investment: 120, returns: 280, net: "+$160K" },
  { yearNum: 2, investment: 120, returns: 420, net: "+$300K" },
  { yearNum: 3, investment: 120, returns: 420, net: "+$300K" },
];

export default async function ROIPage({ params }: ROIPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("roiPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-24 right-0 bg-cy-orange/5" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            {t("badge")}
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            {t("headingPrefix")}{" "}
            <span className="text-gradient">{t("headingHighlight")}</span>
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-10">
            {t("subheading")}
          </p>
          <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
            {t("getReport")}
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </Link>
        </div>
      </div>

      {/* Scenarios */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="scenarios-heading">
        <div className="section-container">
          <h2 id="scenarios-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("scenariosHeading")}
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-xl mx-auto">
            {t("scenariosDesc")}
          </p>
          <div className="grid lg:grid-cols-3 gap-5">
            {ROI_SCENARIOS.map((sc) => {
              const savingsKeys = ["s1", "s2", "s3", "s4"];
              return (
                <div
                  key={sc.key}
                  className={`glass-card p-8 rounded-2xl flex flex-col ${sc.highlight ? "border-cy-orange/40" : "border-cy-glass-border"}`}
                >
                  {sc.highlight && (
                    <span className="text-2xs font-semibold text-cy-orange mb-3">{t("mostCommon")}</span>
                  )}
                  <h3 className="text-lg font-heading font-semibold text-white mb-1">{t(`scenarios.${sc.key}.segment`)}</h3>
                  <p className="text-sm text-cy-gray-400 mb-6">{t("investment")}: {t(`scenarios.${sc.key}.investment`)}</p>

                  <div className="space-y-3 mb-6 flex-1">
                    {savingsKeys.map((sk) => (
                      <div key={sk} className="flex items-center justify-between gap-2">
                        <span className="text-xs text-cy-gray-400 flex-1">{t(`scenarios.${sc.key}.savings.${sk}.label`)}</span>
                        <span className="text-xs font-semibold text-white whitespace-nowrap">{t(`scenarios.${sc.key}.savings.${sk}.amount`)}</span>
                      </div>
                    ))}
                  </div>

                  <div className="h-px bg-cy-glass-border mb-5" />

                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div>
                      <div className="text-xl font-heading font-bold text-cy-orange">{t(`scenarios.${sc.key}.roi`)}</div>
                      <div className="text-2xs text-cy-gray-400">{t("threeYearRoi")}</div>
                    </div>
                    <div>
                      <div className="text-xl font-heading font-bold text-white">{t(`scenarios.${sc.key}.totalSavings`)}</div>
                      <div className="text-2xs text-cy-gray-400">{t("totalSavings")}</div>
                    </div>
                    <div>
                      <div className="text-xl font-heading font-bold text-white">{t(`scenarios.${sc.key}.payback`)}</div>
                      <div className="text-2xs text-cy-gray-400">{t("payback")}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-cy-gray-500 text-center mt-6">
            {t("scenariosFootnote")}
          </p>
        </div>
      </section>

      {/* Key drivers */}
      <section className="py-20" aria-labelledby="drivers-heading">
        <div className="section-container">
          <h2 id="drivers-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("driversHeading")}
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-xl mx-auto">
            {t("driversDesc")}
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            {KEY_DRIVERS.map((driver) => {
              const Icon = driver.icon;
              const items = t.raw(`drivers.${driver.key}.items`) as string[];
              return (
                <div key={driver.key} className="glass-card p-8 rounded-2xl">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 rounded-xl bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center">
                      <Icon className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                    </div>
                    <h3 className="text-lg font-heading font-semibold text-white">{t(`drivers.${driver.key}.title`)}</h3>
                  </div>
                  <ul className="space-y-2.5">
                    {items.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-sm text-cy-gray-300">
                        <CheckCircle className="w-4 h-4 text-cy-orange flex-shrink-0 mt-0.5" aria-hidden="true" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ROI trend visual */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="trend-heading">
        <div className="section-container max-w-3xl">
          <h2 id="trend-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("trendHeading")}
          </h2>
          <p className="text-cy-gray-400 text-center mb-10">{t("trendSubheading")}</p>
          <div className="glass-card p-8 rounded-2xl space-y-4" aria-label="3-year ROI chart for 500-staff hospital">
            {TREND_ROWS.map((row) => (
              <div key={row.yearNum}>
                <div className="flex items-center justify-between text-xs text-cy-gray-400 mb-1.5">
                  <span>{t("year")} {row.yearNum}</span>
                  <span className="text-cy-orange font-semibold">{row.net}</span>
                </div>
                <div className="relative h-6 rounded-lg overflow-hidden bg-cy-glass-bg">
                  <div
                    className="absolute inset-y-0 left-0 bg-cy-orange/20 rounded-lg"
                    style={{ width: `${(row.investment / 420) * 100}%` }}
                    aria-label={`Investment $${row.investment}K`}
                  />
                  <div
                    className="absolute inset-y-0 left-0 bg-cy-orange rounded-lg"
                    style={{ width: `${(row.returns / 420) * 100}%`, opacity: 0.7 }}
                    aria-label={`Returns $${row.returns}K`}
                  />
                </div>
                <div className="flex gap-4 mt-1 text-2xs text-cy-gray-500">
                  <span>{t("investmentLabel")}: ${row.investment}K</span>
                  <span>{t("returnsLabel")}: ${row.returns}K</span>
                </div>
              </div>
            ))}
            <div className="flex items-center gap-4 pt-2">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-sm bg-cy-orange/20" aria-hidden="true" />
                <span className="text-2xs text-cy-gray-400">{t("investmentLabel")}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-sm bg-cy-orange/70" aria-hidden="true" />
                <span className="text-2xs text-cy-gray-400">{t("cumulativeReturns")}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20" aria-labelledby="roi-cta">
        <div className="section-container max-w-2xl text-center">
          <TrendingUp className="w-10 h-10 text-cy-orange mx-auto mb-6" aria-hidden="true" />
          <h2 id="roi-cta" className="text-3xl font-heading font-semibold text-white mb-4">
            {t("ctaHeading")}
          </h2>
          <p className="text-cy-gray-400 mb-8">
            {t("ctaDesc")}
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
              {t("requestAnalysis")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/tools/compare`} className="btn-secondary px-8 py-3">
              {t("compareProducts")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
