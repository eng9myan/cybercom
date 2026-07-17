import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Check, Minus, Star } from "lucide-react";

interface ComparePageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: ComparePageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("comparePage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/tools/compare",
    locale,
  });
}

type Availability = true | false | string;

interface FeatureRow {
  category: string;
  features: { key: string; starter: Availability; professional: Availability; enterprise: Availability; government: Availability }[];
}

const COMPARISON: FeatureRow[] = [
  {
    category: "Core Platform",
    features: [
      { key: "identity", starter: true, professional: true, enterprise: true, government: true },
      { key: "integrationHub", starter: "Basic", professional: "Full", enterprise: "Full", government: "Full" },
      { key: "multiLanguage", starter: true, professional: true, enterprise: true, government: true },
      { key: "auditTrail", starter: "30 days", professional: "1 year", enterprise: "7 years", government: "10 years" },
    ],
  },
  {
    category: "Deployment",
    features: [
      { key: "saas", starter: true, professional: true, enterprise: true, government: false },
      { key: "privateCloud", starter: false, professional: true, enterprise: true, government: true },
      { key: "onPremise", starter: false, professional: false, enterprise: true, government: true },
      { key: "airGapped", starter: false, professional: false, enterprise: false, government: true },
      { key: "hybrid", starter: false, professional: false, enterprise: true, government: true },
    ],
  },
  {
    category: "Users & Capacity",
    features: [
      { key: "concurrentUsers", starter: "Up to 10", professional: "Up to 100", enterprise: "Unlimited", government: "Unlimited" },
      { key: "facilities", starter: "1", professional: "Up to 5", enterprise: "Unlimited", government: "Unlimited" },
      { key: "productModules", starter: "1", professional: "Up to 5", enterprise: "Full ecosystem", government: "Full ecosystem" },
      { key: "offlineMode", starter: false, professional: false, enterprise: true, government: true },
    ],
  },
  {
    category: "Clinical & Interoperability",
    features: [
      { key: "fhirR4", starter: true, professional: true, enterprise: true, government: true },
      { key: "fhirR5", starter: false, professional: true, enterprise: true, government: true },
      { key: "icd11", starter: true, professional: true, enterprise: true, government: true },
      { key: "dicom", starter: false, professional: true, enterprise: true, government: true },
      { key: "mohRegistry", starter: false, professional: "Optional", enterprise: true, government: true },
      { key: "eidas", starter: false, professional: false, enterprise: "Optional", government: true },
    ],
  },
  {
    category: "Security & Compliance",
    features: [
      { key: "mfa", starter: true, professional: true, enterprise: true, government: true },
      { key: "sso", starter: false, professional: true, enterprise: true, government: true },
      { key: "encryption", starter: true, professional: true, enterprise: true, government: true },
      { key: "residency", starter: false, professional: false, enterprise: true, government: true },
      { key: "customCerts", starter: false, professional: false, enterprise: "Optional", government: true },
    ],
  },
  {
    category: "White Label & Branding",
    features: [
      { key: "customLogo", starter: false, professional: true, enterprise: true, government: true },
      { key: "customDomain", starter: false, professional: false, enterprise: true, government: true },
      { key: "fullWhiteLabel", starter: false, professional: false, enterprise: true, government: true },
      { key: "citizenWhiteLabel", starter: false, professional: false, enterprise: false, government: true },
    ],
  },
  {
    category: "Support",
    features: [
      { key: "supportSla", starter: "Email 48h", professional: "Priority 24h", enterprise: "24/7 4h", government: "Custom" },
      { key: "dedicatedEngineer", starter: false, professional: false, enterprise: true, government: true },
      { key: "onSiteImplementation", starter: false, professional: false, enterprise: true, government: true },
      { key: "csm", starter: false, professional: false, enterprise: true, government: true },
    ],
  },
];

const TIERS = ["Starter", "Professional", "Enterprise", "Government"] as const;
const HIGHLIGHTED_TIER = "Enterprise";

function Cell({ value, t }: { value: Availability; t: (key: string) => string }) {
  if (value === true) return <Check className="w-4 h-4 text-cy-orange mx-auto" aria-label="Included" />;
  if (value === false) return <Minus className="w-4 h-4 text-cy-gray-600 mx-auto" aria-label="Not included" />;
  const label = /^\d+$/.test(value) ? value : t(`availabilityValues.${value}`);
  return <span className="text-xs text-cy-gray-300 text-center block">{label}</span>;
}

export default async function ComparePage({ params }: ComparePageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("comparePage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/5" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            {t("badge")}
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            {t("headingPrefix")}{" "}
            <span className="text-gradient">{t("headingHighlight")}</span>
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto">
            {t("subheading")}
          </p>
        </div>
      </div>

      {/* Comparison table */}
      <section className="pb-20" aria-label="Feature comparison table">
        <div className="section-container overflow-x-auto">
          <table className="w-full min-w-[700px] border-separate border-spacing-0">
            {/* Header */}
            <thead>
              <tr>
                <th className="text-left p-4 text-sm font-medium text-cy-gray-400 w-1/3" scope="col">{t("featureCol")}</th>
                {TIERS.map((tier) => (
                  <th
                    key={tier}
                    scope="col"
                    className={`p-4 text-center rounded-t-xl ${tier === HIGHLIGHTED_TIER ? "bg-cy-orange/10 border-x border-t border-cy-orange/30" : ""}`}
                  >
                    <div className="text-base font-heading font-semibold text-white">{t(`tiers.${tier}.name`)}</div>
                    <div className="text-xs text-cy-gray-400 mt-0.5">{t(`tiers.${tier}.subtitle`)}</div>
                    {tier === HIGHLIGHTED_TIER && (
                      <div className="mt-1">
                        <span className="inline-flex items-center gap-1 text-2xs font-semibold text-cy-orange">
                          <Star className="w-3 h-3 fill-cy-orange" aria-hidden="true" />
                          {t("mostPopular")}
                        </span>
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {COMPARISON.map((section, si) => (
                <>
                  {/* Category row */}
                  <tr key={`cat-${section.category}`}>
                    <td
                      colSpan={5}
                      className={`px-4 py-3 text-2xs font-semibold text-cy-gray-400 uppercase tracking-wider bg-cy-dark/40 ${si === 0 ? "rounded-tl-xl" : ""}`}
                    >
                      {t(`categories.${section.category}`)}
                    </td>
                  </tr>

                  {/* Feature rows */}
                  {section.features.map((feature, fi) => {
                    const isLast = si === COMPARISON.length - 1 && fi === section.features.length - 1;
                    return (
                      <tr key={feature.key} className="group">
                        <td className={`px-4 py-3 text-sm text-cy-gray-300 border-t border-cy-glass-border group-hover:text-white transition-colors ${isLast ? "rounded-bl-xl" : ""}`}>
                          {t(`features.${feature.key}`)}
                        </td>
                        {(["starter", "professional", "enterprise", "government"] as const).map((tk) => {
                          const tierName = tk.charAt(0).toUpperCase() + tk.slice(1);
                          const highlighted = tierName === HIGHLIGHTED_TIER;
                          return (
                            <td
                              key={tk}
                              className={`px-4 py-3 border-t border-cy-glass-border text-center ${highlighted ? "bg-cy-orange/5 border-x border-cy-orange/20" : ""} ${isLast && highlighted ? "rounded-b-xl" : ""}`}
                            >
                              <Cell value={feature[tk]} t={t} />
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </>
              ))}

              {/* CTA row */}
              <tr>
                <td className="p-4" />
                {TIERS.map((tier) => (
                  <td
                    key={tier}
                    className={`p-4 text-center rounded-b-xl ${tier === HIGHLIGHTED_TIER ? "bg-cy-orange/10 border-x border-b border-cy-orange/30" : ""}`}
                  >
                    <Link
                      href={`/${l}/${tier === "Government" ? "contact" : "demo"}`}
                      className={`block text-sm py-2 px-4 rounded-lg ${tier === HIGHLIGHTED_TIER ? "btn-primary" : "btn-secondary"}`}
                    >
                      {tier === "Government" ? t("requestProposal") : t("getStarted")}
                    </Link>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="compare-cta">
        <div className="section-container max-w-2xl text-center">
          <h2 id="compare-cta" className="text-3xl font-heading font-semibold text-white mb-4">
            {t("ctaHeading")}
          </h2>
          <p className="text-cy-gray-400 mb-8">
            {t("ctaDesc")}
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
              {t("talkToSales")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/tools/roi`} className="btn-secondary px-8 py-3">
              {t("calculateRoi")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
