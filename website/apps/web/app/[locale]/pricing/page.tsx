import { setRequestLocale } from "next-intl/server";
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
  return buildMetadata({
    title: "Pricing",
    description:
      "Transparent, scalable pricing for healthcare, government, and enterprise. Modular licensing — pay for what you deploy. Start with one product and expand across the ecosystem.",
    path: "/pricing",
    locale,
  });
}

const TIERS = [
  {
    name: "Starter",
    subtitle: "For small clinics & SMEs",
    tagline: "One product, one facility",
    features: [
      "1 CyberCom product module",
      "Up to 10 concurrent users",
      "SaaS cloud deployment",
      "Standard EN/AR interface",
      "Email support (48h SLA)",
      "Basic analytics & reports",
      "FHIR R4 API access",
    ],
    cta: "Get Started",
    ctaHref: "/demo",
    highlight: false,
    badge: null,
    color: "default",
  },
  {
    name: "Professional",
    subtitle: "For growing facilities",
    tagline: "Multi-module, multi-user",
    features: [
      "Up to 5 product modules",
      "Up to 100 concurrent users",
      "SaaS or private cloud",
      "Full EN/AR RTL/LTR support",
      "Priority support (24h SLA)",
      "Advanced analytics & BI",
      "Full FHIR R4/R5 API",
      "Integration hub (3 connectors)",
      "Audit trail & compliance reports",
    ],
    cta: "Request Pricing",
    ctaHref: "/contact",
    highlight: true,
    badge: "Most Popular",
    color: "orange",
  },
  {
    name: "Enterprise",
    subtitle: "For large organizations",
    tagline: "Full ecosystem, unlimited scale",
    features: [
      "Full CyberCom ecosystem access",
      "Unlimited users",
      "SaaS, private cloud, on-premise, or hybrid",
      "Custom branding & white label",
      "24/7 dedicated support (4h SLA)",
      "Custom analytics & BI dashboards",
      "Full integration hub (unlimited connectors)",
      "Custom workflows & automations",
      "Multi-facility & multi-tenant",
      "On-site training & implementation",
      "Dedicated customer success manager",
    ],
    cta: "Contact Sales",
    ctaHref: "/contact",
    highlight: false,
    badge: null,
    color: "default",
  },
  {
    name: "Government",
    subtitle: "For government agencies",
    tagline: "Sovereign, secure, compliant",
    features: [
      "Air-gapped deployment available",
      "Data sovereignty guarantee",
      "eIDAS & national ID integration",
      "Government cloud or on-premise",
      "Custom security certifications",
      "Dedicated implementation team",
      "SLA per government procurement",
      "National registry integration",
      "Citizen portal white label",
      "Full audit & compliance suite",
    ],
    cta: "Request Proposal",
    ctaHref: "/contact",
    highlight: false,
    badge: "Gov Edition",
    color: "amber",
  },
];

const MODULE_PRICING = [
  { category: "Healthcare", products: ["CyMed Hospital", "CyMed Clinic", "CyMed Laboratory", "CyMed Imaging", "CyMed Pharmacy", "Patient Portal", "Provider Portal", "Revenue Cycle", "Population Health"] },
  { category: "Enterprise", products: ["CyCom ERP (Finance, HR, Procurement, Inventory, CRM)", "CyAI — Advisory Intelligence", "CyData — Lakehouse & Analytics", "CyConnect — Unified Communications"] },
  { category: "Government", products: ["CyGov — Digital Government", "CyCitizen — Citizen Platform"] },
  { category: "Platform (included)", products: ["CyIdentity — IAM & Zero Trust", "CyIntegrationHub — Integration Middleware"] },
];

const FAQ = [
  {
    q: "How is CyberCom licensed?",
    a: "CyberCom uses a modular per-product licensing model. You pay for the specific product modules you deploy, with pricing based on the number of users, facility size, and deployment model. Contact sales for a customized quote.",
  },
  {
    q: "Is there a free trial?",
    a: "We offer a guided demonstration and a 30-day pilot program for qualified organizations. Contact us to schedule a demo and discuss a pilot deployment at your facility.",
  },
  {
    q: "Can I start with one product and expand?",
    a: "Yes. CyberCom is designed for phased adoption. Many customers start with a single product (e.g., CyMed Clinic) and expand to additional modules as their needs grow — without data migration.",
  },
  {
    q: "What deployment options are included?",
    a: "Starter includes SaaS cloud. Professional includes SaaS or private cloud. Enterprise and Government include all deployment options including on-premise and air-gapped.",
  },
  {
    q: "Does pricing include implementation?",
    a: "Starter and Professional include self-service onboarding and standard documentation. Enterprise includes on-site implementation support. Government pricing is custom per engagement.",
  },
  {
    q: "Is pricing the same for the Middle East region?",
    a: "CyberCom pricing is adapted for the GCC and MENA region. Contact our regional sales team for localized pricing in your currency.",
  },
];

export default async function PricingPage({ params }: PricingPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/6" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            Pricing
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            Transparent, modular pricing
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-4">
            Pay for the products you deploy. Start with one module, expand as you grow.
            All tiers include the CyIdentity and CyIntegrationHub platform foundation.
          </p>
          <p className="text-sm text-cy-gray-500">
            All pricing is custom — contact sales for a quote tailored to your organization.
          </p>
        </div>
      </div>

      {/* Pricing Tiers */}
      <section className="py-8 pb-20" aria-labelledby="tiers-heading">
        <h2 id="tiers-heading" className="sr-only">Pricing Tiers</h2>
        <div className="section-container">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {TIERS.map((tier) => (
              <div
                key={tier.name}
                className={`relative glass-card p-6 rounded-2xl flex flex-col ${tier.highlight ? "border-cy-orange/40 shadow-orange-glow" : "border-cy-glass-border"}`}
              >
                {tier.badge && (
                  <div className={`absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-2xs font-semibold whitespace-nowrap ${tier.color === "orange" ? "bg-cy-orange text-white" : tier.color === "amber" ? "bg-amber-500 text-white" : "bg-cy-glass-bg border border-cy-glass-border text-cy-gray-200"}`}>
                    {tier.badge}
                  </div>
                )}

                <div className="mb-4">
                  <h3 className="text-lg font-heading font-semibold text-white mb-0.5">{tier.name}</h3>
                  <p className="text-xs text-cy-gray-400">{tier.subtitle}</p>
                </div>

                <div className="mb-6">
                  <span className="text-2xl font-heading font-semibold text-white">Custom pricing</span>
                  <p className="text-xs text-cy-gray-500 mt-1">{tier.tagline}</p>
                </div>

                <ul className="space-y-2.5 flex-1 mb-8">
                  {tier.features.map((f) => (
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
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Module Pricing */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="modules-heading">
        <div className="section-container">
          <h2 id="modules-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            Modular Product Catalog
          </h2>
          <p className="text-cy-gray-400 text-center mb-12">
            Choose the products your organization needs. Each module includes its platform services.
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            {MODULE_PRICING.map((cat) => (
              <div key={cat.category} className="glass-card p-6 rounded-2xl">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <span className="w-1.5 h-4 rounded-full bg-cy-orange" aria-hidden="true" />
                  {cat.category}
                </h3>
                <ul className="space-y-2">
                  {cat.products.map((p) => (
                    <li key={p} className="flex items-center gap-2 text-sm text-cy-gray-300">
                      <Check className="w-3.5 h-3.5 text-cy-orange flex-shrink-0" aria-hidden="true" />
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20" aria-labelledby="faq-heading">
        <div className="section-container max-w-3xl">
          <h2 id="faq-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6">
            {FAQ.map((item) => (
              <div key={item.q} className="glass-card p-6 rounded-2xl">
                <h3 className="font-heading font-semibold text-white mb-2">{item.q}</h3>
                <p className="text-sm text-cy-gray-400 leading-relaxed">{item.a}</p>
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
                  Ready to get a quote?
                </h2>
                <p className="text-cy-gray-400 leading-relaxed mb-6">
                  Our sales team will build a custom pricing proposal for your specific organization,
                  deployment model, and product selection — usually within 2 business days.
                </p>
                <div className="flex flex-wrap gap-4">
                  <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
                    Request a Demo
                    <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
                  </Link>
                  <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                    Contact Sales
                  </Link>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                    <Phone className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">Sales Team</div>
                    <div className="text-xs text-cy-gray-400">Available Sunday–Thursday, 9am–6pm GST</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                    <Building2 className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">Enterprise & Government</div>
                    <div className="text-xs text-cy-gray-400">Custom proposals within 2 business days</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                    <Globe className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">GCC & MENA Region</div>
                    <div className="text-xs text-cy-gray-400">Localized pricing in AED, SAR, JOD, USD</div>
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
