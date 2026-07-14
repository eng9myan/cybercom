import { setRequestLocale } from "next-intl/server";
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
  return buildMetadata({
    title: "Product Comparison",
    description:
      "Compare CyberCom product editions — Starter, Professional, Enterprise, and Government. See feature availability, deployment options, and SLA differences side by side.",
    path: "/tools/compare",
    locale,
  });
}

type Availability = true | false | string;

interface FeatureRow {
  category: string;
  features: { label: string; starter: Availability; professional: Availability; enterprise: Availability; government: Availability }[];
}

const COMPARISON: FeatureRow[] = [
  {
    category: "Core Platform",
    features: [
      { label: "CyIdentity (IAM & Zero Trust)", starter: true, professional: true, enterprise: true, government: true },
      { label: "CyIntegrationHub (FHIR, HL7, REST)", starter: "Basic", professional: "Full", enterprise: "Full", government: "Full" },
      { label: "Multi-language (EN/AR RTL/LTR)", starter: true, professional: true, enterprise: true, government: true },
      { label: "Audit trail", starter: "30 days", professional: "1 year", enterprise: "7 years", government: "10 years" },
    ],
  },
  {
    category: "Deployment",
    features: [
      { label: "SaaS (multi-tenant cloud)", starter: true, professional: true, enterprise: true, government: false },
      { label: "Private cloud / VPC", starter: false, professional: true, enterprise: true, government: true },
      { label: "On-premise", starter: false, professional: false, enterprise: true, government: true },
      { label: "Air-gapped", starter: false, professional: false, enterprise: false, government: true },
      { label: "Hybrid (cloud + on-premise)", starter: false, professional: false, enterprise: true, government: true },
    ],
  },
  {
    category: "Users & Capacity",
    features: [
      { label: "Concurrent users", starter: "Up to 10", professional: "Up to 100", enterprise: "Unlimited", government: "Unlimited" },
      { label: "Facilities", starter: "1", professional: "Up to 5", enterprise: "Unlimited", government: "Unlimited" },
      { label: "Product modules", starter: "1", professional: "Up to 5", enterprise: "Full ecosystem", government: "Full ecosystem" },
      { label: "Offline / disconnected mode", starter: false, professional: false, enterprise: true, government: true },
    ],
  },
  {
    category: "Clinical & Interoperability",
    features: [
      { label: "FHIR R4 API", starter: true, professional: true, enterprise: true, government: true },
      { label: "FHIR R5 API", starter: false, professional: true, enterprise: true, government: true },
      { label: "ICD-11 coding", starter: true, professional: true, enterprise: true, government: true },
      { label: "DICOM / PACS integration", starter: false, professional: true, enterprise: true, government: true },
      { label: "National MOH registry integration", starter: false, professional: "Optional", enterprise: true, government: true },
      { label: "eIDAS / national ID integration", starter: false, professional: false, enterprise: "Optional", government: true },
    ],
  },
  {
    category: "Security & Compliance",
    features: [
      { label: "MFA (TOTP, passkeys)", starter: true, professional: true, enterprise: true, government: true },
      { label: "SSO (SAML, OIDC)", starter: false, professional: true, enterprise: true, government: true },
      { label: "Data encryption at rest + in transit", starter: true, professional: true, enterprise: true, government: true },
      { label: "Data residency / sovereignty", starter: false, professional: false, enterprise: true, government: true },
      { label: "Custom security certifications", starter: false, professional: false, enterprise: "Optional", government: true },
    ],
  },
  {
    category: "White Label & Branding",
    features: [
      { label: "Custom logo", starter: false, professional: true, enterprise: true, government: true },
      { label: "Custom domain", starter: false, professional: false, enterprise: true, government: true },
      { label: "Full white label (UI, email, portal)", starter: false, professional: false, enterprise: true, government: true },
      { label: "Citizen portal white label", starter: false, professional: false, enterprise: false, government: true },
    ],
  },
  {
    category: "Support",
    features: [
      { label: "Support SLA", starter: "Email 48h", professional: "Priority 24h", enterprise: "24/7 4h", government: "Custom" },
      { label: "Dedicated support engineer", starter: false, professional: false, enterprise: true, government: true },
      { label: "On-site implementation", starter: false, professional: false, enterprise: true, government: true },
      { label: "Customer success manager", starter: false, professional: false, enterprise: true, government: true },
    ],
  },
];

const TIERS = ["Starter", "Professional", "Enterprise", "Government"] as const;
const TIER_SUBTITLES: Record<string, string> = {
  Starter: "Small clinics & SMEs",
  Professional: "Growing facilities",
  Enterprise: "Large organizations",
  Government: "Government agencies",
};
const HIGHLIGHTED_TIER = "Enterprise";

function Cell({ value }: { value: Availability }) {
  if (value === true) return <Check className="w-4 h-4 text-cy-orange mx-auto" aria-label="Included" />;
  if (value === false) return <Minus className="w-4 h-4 text-cy-gray-600 mx-auto" aria-label="Not included" />;
  return <span className="text-xs text-cy-gray-300 text-center block">{value}</span>;
}

export default async function ComparePage({ params }: ComparePageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/5" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            Edition Comparison
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            Choose the right{" "}
            <span className="text-gradient">CyberCom edition</span>
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto">
            Compare all four CyberCom editions side by side — deployment, users, compliance,
            and support across Starter, Professional, Enterprise, and Government.
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
                <th className="text-left p-4 text-sm font-medium text-cy-gray-400 w-1/3" scope="col">Feature</th>
                {TIERS.map((tier) => (
                  <th
                    key={tier}
                    scope="col"
                    className={`p-4 text-center rounded-t-xl ${tier === HIGHLIGHTED_TIER ? "bg-cy-orange/10 border-x border-t border-cy-orange/30" : ""}`}
                  >
                    <div className="text-base font-heading font-semibold text-white">{tier}</div>
                    <div className="text-xs text-cy-gray-400 mt-0.5">{TIER_SUBTITLES[tier]}</div>
                    {tier === HIGHLIGHTED_TIER && (
                      <div className="mt-1">
                        <span className="inline-flex items-center gap-1 text-2xs font-semibold text-cy-orange">
                          <Star className="w-3 h-3 fill-cy-orange" aria-hidden="true" />
                          Most Popular
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
                      {section.category}
                    </td>
                  </tr>

                  {/* Feature rows */}
                  {section.features.map((feature, fi) => {
                    const isLast = si === COMPARISON.length - 1 && fi === section.features.length - 1;
                    return (
                      <tr key={feature.label} className="group">
                        <td className={`px-4 py-3 text-sm text-cy-gray-300 border-t border-cy-glass-border group-hover:text-white transition-colors ${isLast ? "rounded-bl-xl" : ""}`}>
                          {feature.label}
                        </td>
                        {(["starter", "professional", "enterprise", "government"] as const).map((t) => {
                          const tierName = t.charAt(0).toUpperCase() + t.slice(1);
                          const highlighted = tierName === HIGHLIGHTED_TIER;
                          return (
                            <td
                              key={t}
                              className={`px-4 py-3 border-t border-cy-glass-border text-center ${highlighted ? "bg-cy-orange/5 border-x border-cy-orange/20" : ""} ${isLast && highlighted ? "rounded-b-xl" : ""}`}
                            >
                              <Cell value={feature[t]} />
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
                      {tier === "Government" ? "Request Proposal" : "Get Started"}
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
            Not sure which edition?
          </h2>
          <p className="text-cy-gray-400 mb-8">
            Our solutions team will recommend the right edition and modules for your organization — free, within one business day.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
              Talk to Sales
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/tools/roi`} className="btn-secondary px-8 py-3">
              Calculate ROI
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
