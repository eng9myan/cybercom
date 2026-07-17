import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight } from "lucide-react";

interface AboutPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: AboutPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("aboutPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/about",
    locale,
  });
}

const MISSIONS = [
  { key: "healthcare", icon: "🏥" },
  { key: "government", icon: "🏛" },
  { key: "enterprise", icon: "⚡" },
];

const VALUES = ["standards", "safety", "integration", "scale"];

const PRODUCTS_BRIEF = ["cymed", "cycom", "cygov", "cyai", "cyidentity", "cyintegrationhub", "cydata", "cyconnect", "cycitizen"];
const PRODUCT_NAMES: Record<string, string> = { cymed: "CyMed", cycom: "CyCom", cygov: "CyGov", cyai: "CyAI", cyidentity: "CyIdentity", cyintegrationhub: "CyIntegrationHub", cydata: "CyData", cyconnect: "CyConnect", cycitizen: "CyCitizen" };

export default async function AboutPage({ params }: AboutPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("aboutPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/8" />
        </div>
        <div className="section-container relative z-10 max-w-4xl">
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
            {t("heroLine1")}{" "}
            <span className="text-gradient">{t("heroHighlight")}</span>{" "}
            {t("heroLine2")}
          </h1>
          <p className="text-xl text-cy-gray-400 leading-relaxed max-w-3xl">
            {t("heroDescription")}
          </p>
        </div>
      </div>

      {/* Mission */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="mission-heading">
        <div className="section-container">
          <h2 id="mission-heading" className="text-3xl font-heading font-semibold text-white mb-10 text-center">
            {t("mission.heading")}
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {MISSIONS.map((m) => (
              <div key={m.key} className="glass-card p-6 rounded-2xl">
                <div className="text-3xl mb-4" aria-hidden="true" role="img">{m.icon}</div>
                <h3 className="font-heading font-semibold text-white text-lg mb-2">{t(`mission.${m.key}.title`)}</h3>
                <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`mission.${m.key}.desc`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Products */}
      <section className="py-20" aria-labelledby="products-heading">
        <div className="section-container">
          <h2 id="products-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("products.heading")}
          </h2>
          <p className="text-center text-cy-gray-400 mb-10">{t("products.subheading")}</p>
          <div className="flex flex-wrap justify-center gap-3">
            {PRODUCTS_BRIEF.map((key) => (
              <div key={key} className="glass-card px-5 py-3 rounded-xl border border-cy-glass-border">
                <div className="text-sm font-heading font-semibold text-gradient-orange">{PRODUCT_NAMES[key]}</div>
                <div className="text-xs text-cy-gray-400">{t(`products.${key}`)}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="values-heading">
        <div className="section-container">
          <h2 id="values-heading" className="text-3xl font-heading font-semibold text-white mb-10 text-center">
            {t("values.heading")}
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {VALUES.map((key) => (
              <div key={key} className="glass-card p-6 rounded-2xl flex gap-4">
                <div className="w-1 rounded-full bg-gradient-cy flex-shrink-0" aria-hidden="true" />
                <div>
                  <h3 className="font-heading font-semibold text-white mb-1">{t(`values.${key}.name`)}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`values.${key}.desc`)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20" aria-labelledby="about-cta">
        <div className="section-container text-center">
          <h2 id="about-cta" className="text-3xl font-heading font-semibold text-white mb-4">
            {t("cta.heading")}
          </h2>
          <p className="text-cy-gray-400 mb-8">
            {t("cta.subheading")}
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
              {t("cta.requestDemo")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
              {t("cta.contactUs")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
