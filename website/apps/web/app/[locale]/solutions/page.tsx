import { setRequestLocale } from "next-intl/server";
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
  return buildMetadata({
    title: "Solutions — Healthcare, Government & Enterprise",
    description:
      "CyberCom delivers complete digital transformation solutions for hospitals, clinics, government agencies, and enterprises. FHIR-native, ICD-11 coded, cloud-ready.",
    path: "/solutions",
    locale,
  });
}

const INDUSTRY_SOLUTIONS = [
  {
    id: "healthcare",
    icon: Hospital,
    title: "Healthcare",
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    iconClass: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
    gradientClass: "from-emerald-900/20 to-transparent",
    tagline: "End-to-end clinical digital transformation",
    description:
      "A complete FHIR-native healthcare platform covering hospitals, clinics, labs, pharmacies, and patient engagement — all connected through a unified clinical data model.",
    products: [
      { name: "CyMed Hospital", slug: "cymed-hospital", desc: "Inpatient care, OR, ICU, bed management" },
      { name: "CyMed Clinic", slug: "cymed-clinic", desc: "Outpatient EMR, scheduling, revenue cycle" },
      { name: "CyMed Laboratory", slug: "cymed-laboratory", desc: "LIS with auto-verification, LOINC coding" },
      { name: "CyMed Imaging", slug: "cymed-imaging", desc: "RIS/PACS, DICOM, structured reporting" },
      { name: "CyMed Pharmacy", slug: "cymed-pharmacy", desc: "Clinical pharmacy, drug interactions, inventory" },
      { name: "CyMed Patient Portal", slug: "cymed-patient-portal", desc: "Patient engagement and self-service" },
    ],
    outcomes: [
      "ICD-11 & FHIR R4 clinical coding",
      "Drug interaction prevention engine",
      "Break Glass emergency access",
      "Hash-chained audit trail",
    ],
    cta: { label: "Explore Healthcare", href: "/products/cymed-clinic" },
  },
  {
    id: "government",
    icon: Landmark,
    title: "Government",
    color: "amber",
    accentClass: "text-amber-400 border-amber-500/20 bg-amber-500/5",
    iconClass: "bg-amber-500/10 border-amber-500/20 text-amber-400",
    gradientClass: "from-amber-900/20 to-transparent",
    tagline: "Citizen-first digital government platform",
    description:
      "Transform citizen services, national registries, licensing, and government operations through a secure, scalable digital government platform with eIDAS-compliant digital identity.",
    products: [
      { name: "CyGov", slug: "cygov", desc: "Citizen services, licensing, national registries" },
      { name: "CyCitizen", slug: "cycitizen", desc: "Citizen portal, digital wallet, national ID" },
      { name: "CyIdentity", slug: "cyidentity", desc: "OAuth 2.1, SSO, Zero Trust IAM" },
      { name: "CyIntegrationHub", slug: "cyintegrationhub", desc: "Inter-agency integration fabric" },
    ],
    outcomes: [
      "eIDAS & GDPR compliant",
      "Air-gapped deployment support",
      "WCAG 2.1 AA accessible",
      "Multilingual EN/AR citizen UI",
    ],
    cta: { label: "Explore Government", href: "/products/cygov" },
  },
  {
    id: "enterprise",
    icon: Building2,
    title: "Enterprise",
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
    iconClass: "bg-blue-500/10 border-blue-500/20 text-blue-400",
    gradientClass: "from-blue-900/20 to-transparent",
    tagline: "Unified ERP, AI, and analytics for modern enterprises",
    description:
      "A full-suite enterprise platform unifying finance, HR, procurement, manufacturing, CRM, BI, and AI — deployed on cloud or on-premise, integrated through a single identity and event fabric.",
    products: [
      { name: "CyCom ERP", slug: "cycom", desc: "Finance, HR, procurement, inventory, CRM" },
      { name: "CyAI", slug: "cyai", desc: "AI advisory, predictive analytics, automation" },
      { name: "CyData", slug: "cydata", desc: "Lakehouse, BI dashboards, data governance" },
      { name: "CyConnect", slug: "cyconnect", desc: "Unified communications and notifications" },
    ],
    outcomes: [
      "IFRS & GAAP compliant accounting",
      "Real-time BI with 50+ report types",
      "AI advisory-only (non-autonomous)",
      "Multi-currency & multi-language",
    ],
    cta: { label: "Explore Enterprise", href: "/products/cycom" },
  },
];

const DEPLOYMENT_MODELS = [
  {
    icon: Globe,
    title: "SaaS Cloud",
    desc: "Fully managed, auto-scaling, 99.9% SLA. Fastest time to value.",
    fit: "Clinics, SMEs, Government portals",
  },
  {
    icon: Shield,
    title: "Private Cloud",
    desc: "Dedicated infrastructure in the customer's cloud account (AWS, Azure, GCP).",
    fit: "Large hospitals, enterprise chains",
  },
  {
    icon: Building2,
    title: "On-Premise",
    desc: "Deployed in the customer's own data center. Full data sovereignty.",
    fit: "Government agencies, regulated industries",
  },
  {
    icon: Zap,
    title: "Hybrid",
    desc: "Core on-premise with cloud burst capacity and SaaS modules.",
    fit: "Hospital networks, multi-facility operators",
  },
];

const CROSS_CUTTING = [
  { icon: Shield, title: "CyIdentity", desc: "OAuth 2.1, OIDC, Zero Trust across all platforms", slug: "cyidentity" },
  { icon: Globe, title: "CyIntegrationHub", desc: "FHIR, HL7, DICOM, REST, Kafka integration fabric", slug: "cyintegrationhub" },
  { icon: BarChart3, title: "CyData", desc: "Unified data lakehouse and analytics across all products", slug: "cydata" },
  { icon: Users, title: "CyConnect", desc: "Secure communications and notifications across all platforms", slug: "cyconnect" },
];

export default async function SolutionsPage({ params }: SolutionsPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

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
              Solutions
            </span>
            <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
              Complete solutions for{" "}
              <span className="text-gradient">every challenge</span>
            </h1>
            <p className="text-xl text-cy-gray-400 leading-relaxed max-w-3xl mb-8">
              Whether you operate a single clinic or a national health ministry, CyberCom delivers
              purpose-built digital platforms that integrate seamlessly across healthcare, government,
              and enterprise — all through one unified ecosystem.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
                Request a Demo
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                Talk to a Specialist
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Industry Solutions */}
      <section className="py-20" aria-labelledby="industries-heading">
        <div className="section-container">
          <h2 id="industries-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            Solutions by Industry
          </h2>
          <p className="text-center text-cy-gray-400 mb-16 max-w-2xl mx-auto">
            Deep domain expertise across the sectors that need digital transformation most.
          </p>

          <div className="space-y-16">
            {INDUSTRY_SOLUTIONS.map((industry, idx) => {
              const Icon = industry.icon;
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
                        {industry.title}
                      </div>
                      <h3 className="text-2xl font-heading font-semibold text-white mb-3">
                        {industry.tagline}
                      </h3>
                      <p className="text-cy-gray-400 leading-relaxed mb-6">
                        {industry.description}
                      </p>

                      {/* Outcomes */}
                      <ul className="space-y-2 mb-8" aria-label="Key outcomes">
                        {industry.outcomes.map((o) => (
                          <li key={o} className="flex items-center gap-2.5 text-sm text-cy-gray-200">
                            <CheckCircle2 className={`w-4 h-4 flex-shrink-0 ${industry.accentClass.split(" ")[0]}`} aria-hidden="true" />
                            {o}
                          </li>
                        ))}
                      </ul>

                      <Link href={`/${l}${industry.cta.href}`} className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium border transition-colors duration-150 ${industry.accentClass} hover:bg-opacity-20`}>
                        {industry.cta.label}
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
                            {p.name}
                          </div>
                          <div className="text-xs text-cy-gray-400 leading-relaxed">{p.desc}</div>
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
              One Platform Foundation
            </h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">
              Every CyberCom solution runs on shared infrastructure — one identity, one integration
              layer, one data fabric — so every product works together from day one.
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
                    {c.title}
                  </div>
                  <div className="text-xs text-cy-gray-400 leading-relaxed">{c.desc}</div>
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
            Deployment Models
          </h2>
          <p className="text-center text-cy-gray-400 mb-12">
            Deploy where your data must live.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {DEPLOYMENT_MODELS.map((d) => {
              const Icon = d.icon;
              return (
                <div key={d.title} className="glass-card p-6 rounded-2xl">
                  <div className="w-10 h-10 rounded-xl bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cy-gray-200" aria-hidden="true" />
                  </div>
                  <h3 className="font-heading font-semibold text-white mb-1">{d.title}</h3>
                  <p className="text-xs text-cy-gray-400 leading-relaxed mb-3">{d.desc}</p>
                  <p className="text-2xs text-cy-gray-600 uppercase tracking-wider">Best for</p>
                  <p className="text-xs text-cy-gray-400">{d.fit}</p>
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
              Not sure which solution fits?
            </h2>
            <p className="text-cy-gray-400 mb-8 leading-relaxed">
              Our specialists will map your organization&apos;s needs to the right CyberCom products,
              deployment model, and implementation path — at no cost.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
                Request a Demo
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                Talk to Sales
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
