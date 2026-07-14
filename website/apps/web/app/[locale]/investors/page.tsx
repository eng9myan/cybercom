import { setRequestLocale } from "next-intl/server";
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
  return buildMetadata({
    title: "Investors",
    description:
      "CyberCom Revolution is building the next-generation enterprise platform for healthcare, government, and enterprise in the Middle East and beyond. Learn about our market opportunity and technology.",
    path: "/investors",
    locale,
  });
}

const METRICS = [
  { label: "Platform Products", value: "9", desc: "Integrated platforms across 3 verticals" },
  { label: "Clinical Standards", value: "5+", desc: "FHIR R4, ICD-11, SNOMED CT, LOINC, DICOM" },
  { label: "Deployment Models", value: "4", desc: "SaaS, Private Cloud, On-Premise, Hybrid" },
  { label: "Markets", value: "2", desc: "Healthcare, Government (Enterprise in progress)" },
  { label: "Languages", value: "2", desc: "English & Arabic (RTL/LTR native)" },
  { label: "Regulatory Coverage", value: "4+", desc: "HIPAA-ready, GDPR, eIDAS, ISO 27001 roadmap" },
];

const MARKET_SEGMENTS = [
  {
    icon: TrendingUp,
    title: "Healthcare IT — $XXX Billion Market",
    desc: "The MENA healthcare IT market is growing rapidly driven by government mandates for digital health, FHIR adoption, and national e-health strategies. CyberCom is positioned as a comprehensive native alternative to fragmented legacy systems.",
    highlight: "EMR, LIS, RIS, Pharmacy, RCM, Population Health",
  },
  {
    icon: Globe,
    title: "Government Digital Services",
    desc: "GCC governments are mandating digital transformation of citizen services, national registries, and inter-agency integration. CyberCom's CyGov and CyCitizen target this sovereign infrastructure layer.",
    highlight: "Citizen portals, National registries, e-Government",
  },
  {
    icon: BarChart3,
    title: "Enterprise ERP & Intelligence",
    desc: "SMEs and large enterprises in MENA need integrated ERP, AI, and analytics that understand local compliance (VAT, GAAP, IFRS), local language (Arabic), and local deployment requirements.",
    highlight: "ERP, BI, CRM, AI Advisory, Data Lakehouse",
  },
];

const DIFFERENTIATORS = [
  {
    icon: Layers,
    title: "9 Products, 1 Platform",
    desc: "Unlike competitors who sell point solutions, CyberCom delivers a unified ecosystem — one identity (CyIdentity), one integration layer (CyIntegrationHub), one data fabric (CyData) — across all 9 products.",
  },
  {
    icon: Shield,
    title: "Clinical Safety by Design",
    desc: "Drug interaction engine (5 interaction types), CyAI advisory-only enforcement, hash-chained audit trail, Break Glass access — clinical safety is a platform-level constraint, not a product feature.",
  },
  {
    icon: Cpu,
    title: "Open Standards Architecture",
    desc: "FHIR R4/R5, ICD-11, SNOMED CT, LOINC, DICOM, OAuth 2.1, OIDC, FIDO2 — CyberCom is built entirely on open international standards. No proprietary lock-in. Maximum interoperability.",
  },
  {
    icon: Globe,
    title: "MENA-Native Design",
    desc: "Arabic-first RTL/LTR interface, Arabic clinical terminology, GCC compliance readiness, local currency support, Islamic calendar — CyberCom is not translated from English; it is built for the region.",
  },
];

const PLATFORM_PRODUCTS = [
  { name: "CyMed", category: "Healthcare", status: "Production Ready", products: "Hospital, Clinic, Lab, Imaging, Pharmacy, Patient Portal, Provider Portal, RCM, Population Health" },
  { name: "CyCom", category: "Enterprise ERP", status: "Production Ready", products: "Finance, HR, Procurement, Inventory, CRM, BI" },
  { name: "CyGov", category: "Government", status: "Production Ready", products: "Citizen Services, Licensing, Registries, Workflows" },
  { name: "CyCitizen", category: "Citizen Experience", status: "Production Ready", products: "Citizen Portal, Digital Wallet, National ID" },
  { name: "CyIdentity", category: "Platform", status: "Production Ready", products: "OAuth 2.1, OIDC, MFA, SSO, Zero Trust, RBAC/ABAC" },
  { name: "CyIntegrationHub", category: "Platform", status: "Production Ready", products: "FHIR, HL7, DICOM, REST, Kafka, EDI, SOAP" },
  { name: "CyAI", category: "Intelligence", status: "Advisory Only", products: "Clinical AI, Government AI, Predictive Analytics, NLP" },
  { name: "CyData", category: "Data", status: "Production Ready", products: "Lakehouse, ETL, BI Dashboards, Data Governance" },
  { name: "CyConnect", category: "Communications", status: "Production Ready", products: "Messaging, Notifications, Video, Collaboration" },
];

export default async function InvestorsPage({ params }: InvestorsPageProps) {
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
        <div className="section-container relative z-10 max-w-4xl">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            Investor Relations
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
            Building the intelligence layer for{" "}
            <span className="text-gradient">the next economy</span>
          </h1>
          <p className="text-xl text-cy-gray-400 leading-relaxed max-w-3xl mb-8">
            CyberCom Revolution is an enterprise software company engineering 9 integrated
            platforms for healthcare, government, and enterprise — all connected through a
            shared identity, data, and integration fabric. We are building the platform
            infrastructure of the digital MENA economy.
          </p>
          <a
            href="mailto:investors@cy-com.com"
            className="btn-primary px-8 py-3 inline-flex"
          >
            Contact Investor Relations
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </a>
        </div>
      </div>

      {/* Key Metrics */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="metrics-heading">
        <div className="section-container">
          <h2 id="metrics-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            Platform at a Glance
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {METRICS.map((m) => (
              <div key={m.label} className="glass-card p-6 rounded-2xl text-center">
                <div className="text-4xl font-heading font-bold text-gradient-orange mb-1">{m.value}</div>
                <div className="text-sm font-medium text-white mb-1">{m.label}</div>
                <div className="text-xs text-cy-gray-400">{m.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Market Opportunity */}
      <section className="py-20" aria-labelledby="market-heading">
        <div className="section-container">
          <h2 id="market-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            Market Opportunity
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Three large, underserved markets experiencing simultaneous digital transformation mandates.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {MARKET_SEGMENTS.map((seg) => {
              const Icon = seg.icon;
              return (
                <div key={seg.title} className="glass-card p-6 rounded-2xl">
                  <div className="w-10 h-10 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                  </div>
                  <h3 className="font-heading font-semibold text-white mb-2">{seg.title}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed mb-4">{seg.desc}</p>
                  <div className="text-xs text-cy-orange bg-cy-orange/5 border border-cy-orange/20 rounded-lg px-3 py-2">
                    {seg.highlight}
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
            Technology Differentiation
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {DIFFERENTIATORS.map((d) => {
              const Icon = d.icon;
              return (
                <div key={d.title} className="glass-card p-6 rounded-2xl flex gap-4">
                  <div className="w-10 h-10 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <h3 className="font-heading font-semibold text-white mb-2">{d.title}</h3>
                    <p className="text-sm text-cy-gray-400 leading-relaxed">{d.desc}</p>
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
            Product Portfolio Status
          </h2>
          <div className="overflow-x-auto rounded-2xl border border-cy-glass-border">
            <table className="w-full text-sm" role="table" aria-label="Product portfolio status">
              <thead>
                <tr className="border-b border-cy-glass-border bg-cy-dark/50">
                  <th scope="col" className="text-left px-5 py-3.5 text-xs font-semibold text-cy-gray-400 uppercase tracking-wider">Platform</th>
                  <th scope="col" className="text-left px-5 py-3.5 text-xs font-semibold text-cy-gray-400 uppercase tracking-wider">Category</th>
                  <th scope="col" className="text-left px-5 py-3.5 text-xs font-semibold text-cy-gray-400 uppercase tracking-wider hidden md:table-cell">Products</th>
                  <th scope="col" className="text-left px-5 py-3.5 text-xs font-semibold text-cy-gray-400 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody>
                {PLATFORM_PRODUCTS.map((p, i) => (
                  <tr key={p.name} className={`border-b border-cy-glass-border last:border-0 ${i % 2 === 0 ? "" : "bg-cy-dark/20"}`}>
                    <td className="px-5 py-4 font-heading font-semibold text-white">{p.name}</td>
                    <td className="px-5 py-4 text-cy-gray-400">{p.category}</td>
                    <td className="px-5 py-4 text-cy-gray-400 hidden md:table-cell text-xs leading-relaxed">{p.products}</td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${p.status === "Production Ready" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${p.status === "Production Ready" ? "bg-emerald-400" : "bg-amber-400"}`} aria-hidden="true" />
                        {p.status}
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
            Investor Inquiries
          </h2>
          <p className="text-cy-gray-400 mb-8 leading-relaxed">
            For investment inquiries, financial information requests, or partnership discussions,
            please contact our investor relations team directly.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="mailto:investors@cy-com.com" className="btn-primary px-8 py-3 inline-flex">
              investors@cy-com.com
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </a>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
              Contact Us
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
