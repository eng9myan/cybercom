import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight } from "lucide-react";

interface IndustriesPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: IndustriesPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Industries — Healthcare, Government, Enterprise Solutions",
    description: "CyberCom delivers specialized digital platforms for Healthcare, Government, Retail, Manufacturing, Education, Financial Services, Insurance, and Telecommunications.",
    path: "/industries",
    locale,
  });
}

const INDUSTRIES = [
  {
    slug: "healthcare",
    name: "Healthcare",
    desc: "End-to-end clinical platform for hospitals, clinics, laboratories, pharmacies, and patient engagement.",
    icon: "🏥",
    color: "emerald",
    products: ["CyMed Clinic", "CyMed Hospital", "CyMed Laboratory", "CyMed Imaging", "CyMed Pharmacy"],
    features: ["FHIR R4/R5 Native", "ICD-11 Coded", "AI Clinical Decision Support", "Population Health Analytics"],
    stats: { label: "9 healthcare modules", desc: "covering the full care continuum" },
  },
  {
    slug: "government",
    name: "Government",
    desc: "Citizen services, national registries, licensing, and digital government transformation.",
    icon: "🏛",
    color: "amber",
    products: ["CyGov", "CyCitizen", "CyIdentity"],
    features: ["Citizen Services Portal", "National Registries", "Digital Identity", "E-Licensing & Permits"],
    stats: { label: "Scalable to national scale", desc: "multi-ministry integration" },
  },
  {
    slug: "retail",
    name: "Retail & Commerce",
    desc: "Unified commerce, inventory, CRM, and customer experience management platforms.",
    icon: "🛒",
    color: "pink",
    products: ["CyCom ERP", "CyData"],
    features: ["Unified POS & E-commerce", "Inventory Management", "Customer Analytics", "Loyalty Programs"],
    stats: { label: "Omnichannel ready", desc: "in-store and online" },
  },
  {
    slug: "manufacturing",
    name: "Manufacturing",
    desc: "Production, quality, supply chain, and asset management platforms for modern manufacturing.",
    icon: "⚙️",
    color: "orange",
    products: ["CyCom ERP", "CyAI"],
    features: ["Production Planning", "Quality Control", "Supply Chain", "Predictive Maintenance"],
    stats: { label: "IoT & SCADA ready", desc: "industry 4.0 integration" },
  },
  {
    slug: "education",
    name: "Education",
    desc: "Learning management and institutional administration systems for educational organizations.",
    icon: "🎓",
    color: "sky",
    products: ["CyCom ERP", "CyConnect"],
    features: ["Student Information System", "Learning Management", "Online Exams", "Parent Portal"],
    stats: { label: "K-12 to University", desc: "all education levels" },
  },
  {
    slug: "financial",
    name: "Financial Services",
    desc: "Core banking, financial operations, compliance, and analytics platforms.",
    icon: "💰",
    color: "green",
    products: ["CyCom ERP", "CyData", "CyIdentity"],
    features: ["Core Financial Management", "Compliance Reporting", "Fraud Detection", "Multi-currency"],
    stats: { label: "IFRS & GAAP compliant", desc: "regulatory reporting built-in" },
  },
  {
    slug: "insurance",
    name: "Insurance",
    desc: "Policy management, claims processing, actuarial analytics, and customer service platforms.",
    icon: "🛡",
    color: "violet",
    products: ["CyCom ERP", "CyData"],
    features: ["Policy Management", "Claims Processing", "Actuarial Analytics", "Customer Portal"],
    stats: { label: "Full insurance lifecycle", desc: "from quote to claim" },
  },
  {
    slug: "telecom",
    name: "Telecommunications",
    desc: "BSS/OSS, billing, customer management, and network analytics platforms.",
    icon: "📡",
    color: "cyan",
    products: ["CyCom ERP", "CyConnect", "CyData"],
    features: ["Customer Management", "Billing & Rating", "Network Analytics", "Service Catalog"],
    stats: { label: "BSS/OSS ready", desc: "telco-grade operations" },
  },
];

const COLOR_VARIANTS: Record<string, string> = {
  emerald: "text-emerald-400 bg-emerald-500/5 border-emerald-500/20",
  amber: "text-amber-400 bg-amber-500/5 border-amber-500/20",
  pink: "text-pink-400 bg-pink-500/5 border-pink-500/20",
  orange: "text-orange-400 bg-orange-500/5 border-orange-500/20",
  sky: "text-sky-400 bg-sky-500/5 border-sky-500/20",
  green: "text-green-400 bg-green-500/5 border-green-500/20",
  violet: "text-violet-400 bg-violet-500/5 border-violet-500/20",
  cyan: "text-cyan-400 bg-cyan-500/5 border-cyan-500/20",
};

export default async function IndustriesPage({ params }: IndustriesPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Header */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[500px] h-[500px] -top-24 left-1/2 -translate-x-1/2 bg-cy-orange/8" />
        </div>
        <div className="section-container relative z-10 text-center">
          <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">Industries</p>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-4">
            Built for Your Industry
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto">
            Deep domain expertise backed by open standards. CyberCom platforms are purpose-built
            for the unique requirements of each sector.
          </p>
        </div>
      </div>

      {/* Industries grid */}
      <div className="section-container pb-24">
        <div className="grid md:grid-cols-2 gap-6">
          {INDUSTRIES.map((industry) => {
            const colorClass = (COLOR_VARIANTS[industry.color] ?? COLOR_VARIANTS.cyan) as string;
            return (
              <Link
                key={industry.slug}
                href={`/${l}/industries/${industry.slug}`}
                className="glass-card p-6 rounded-2xl border border-cy-glass-border hover:border-current/20 group transition-all duration-300 block"
                aria-label={`${industry.name} industry solutions`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl border ${colorClass}`}>
                    <span aria-hidden="true" role="img">{industry.icon}</span>
                  </div>
                  <ArrowRight
                    className="w-4 h-4 text-cy-gray-600 group-hover:text-white group-hover:translate-x-0.5 transition-all duration-200 rtl:rotate-180"
                    aria-hidden="true"
                  />
                </div>

                <h2 className={`text-xl font-heading font-semibold mb-2 group-hover:${colorClass.split(" ")[0]} transition-colors`}>
                  {industry.name}
                </h2>
                <p className="text-sm text-cy-gray-400 mb-4 leading-relaxed">{industry.desc}</p>

                {/* Features */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {industry.features.map((f) => (
                    <span key={f} className="text-2xs px-2 py-0.5 rounded-md bg-cy-glass-bg border border-cy-glass-border text-cy-gray-400">
                      {f}
                    </span>
                  ))}
                </div>

                {/* Products */}
                <div className="flex items-center gap-2 pt-3 border-t border-cy-glass-border">
                  <span className="text-xs text-cy-gray-600">Platforms:</span>
                  <div className="flex flex-wrap gap-1">
                    {industry.products.map((p) => (
                      <span key={p} className="text-xs text-cy-gray-400 font-medium">{p}</span>
                    ))}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
