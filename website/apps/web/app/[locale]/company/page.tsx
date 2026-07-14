import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Users, Globe2, Target, Award, Shield, Zap, Heart } from "lucide-react";

interface CompanyPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: CompanyPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Company",
    description: "CyberCom Revolution is an enterprise software company delivering intelligent platforms for healthcare, retail, and enterprise. Founded to transform how organizations operate across the Middle East and beyond.",
    path: "/company",
    locale,
  });
}

const STATS = [
  { value: "3", label: "Enterprise Platforms", desc: "CyMed · CyShop · CyCom ERP" },
  { value: "9+", label: "Clinical Modules", desc: "From hospital to patient portal" },
  { value: "14", label: "ERP Modules", desc: "Finance to manufacturing" },
  { value: "FHIR R4", label: "Healthcare Standard", desc: "Native, not bolted-on" },
];

const VALUES = [
  { icon: Shield, title: "Security First", desc: "OAuth 2.1, Zero Trust, end-to-end encryption. Every product is built with security as an invariant, not an afterthought.", color: "text-violet-400", bg: "bg-violet-500/10 border-violet-500/20" },
  { icon: Heart, title: "Clinical Safety", desc: "Advisory-only AI, pharmacist-approved overrides, hash-chained audit trails. We never compromise on patient safety.", color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" },
  { icon: Globe2, title: "Regional by Design", desc: "Arabic and English natively. RTL/LTR, Jordan MOH, Saudi SFDA, UAE MOHAP frameworks built in from day one.", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: Zap, title: "One Ecosystem", desc: "CyMed, CyShop, and CyCom ERP share a single identity layer, audit trail, and integration hub. No silos.", color: "text-cy-orange", bg: "bg-cy-orange/10 border-cy-orange/20" },
  { icon: Target, title: "Enterprise Grade", desc: "Multi-tenant PostgreSQL RLS, Kubernetes-native, 99.9% SLA. Built to scale from 50-user clinic to national health authority.", color: "text-sky-400", bg: "bg-sky-500/10 border-sky-500/20" },
  { icon: Award, title: "Standards Compliant", desc: "ICD-11, FHIR R4/R5, HL7, DICOM, SNOMED CT, LOINC, IFRS, WPS (GCC). Standards are requirements, not marketing.", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
];

const PLATFORMS = [
  {
    name: "CyMed",
    tagline: "Intelligent Healthcare Platform",
    desc: "Nine integrated clinical modules — hospital, clinic, pharmacy, laboratory, imaging, patient portal, provider portal, revenue cycle, and population health — all on one FHIR R4 native platform.",
    color: "text-emerald-400",
    border: "border-emerald-500/20",
    bg: "bg-emerald-500/5",
    href: "/products/cymed",
    badge: "Healthcare",
  },
  {
    name: "CyShop",
    tagline: "Intelligent Retail & Commerce Platform",
    desc: "Cloud-native POS and commerce platform for restaurants, cafés, grocery stores, supermarkets, and convenience stores. AI forecasting, omnichannel POS, and full CyberCom Platform integration.",
    color: "text-cy-orange",
    border: "border-cy-orange/20",
    bg: "bg-cy-orange/5",
    href: "/products/cyshop",
    badge: "Retail",
  },
  {
    name: "CyCom ERP",
    tagline: "Unified Enterprise Resource Planning",
    desc: "Fourteen integrated modules — Finance, Accounting, Procurement, Inventory, Manufacturing, CRM, HR, Payroll, Assets, POS, and BI — on one enterprise platform compliant with IFRS and local regulations.",
    color: "text-blue-400",
    border: "border-blue-500/20",
    bg: "bg-blue-500/5",
    href: "/products/cycom",
    badge: "Enterprise",
  },
];

export default async function CompanyPage({ params }: CompanyPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <section className="relative py-24 overflow-hidden" aria-labelledby="company-heading">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/6" />
          <div className="glow-orb w-[400px] h-[400px] top-1/2 -right-32 bg-sky-500/5" />
        </div>
        <div className="section-container relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cy-orange/20 bg-cy-orange/5 mb-6">
              <div className="w-1.5 h-1.5 rounded-full bg-cy-orange animate-pulse" aria-hidden="true" />
              <span className="text-xs font-medium text-cy-orange tracking-wider uppercase">Enterprise Software Company</span>
            </div>
            <h1 id="company-heading" className="text-4xl sm:text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
              One Company.<br />
              <span className="text-gradient-orange">Three Platforms.</span><br />
              One Ecosystem.
            </h1>
            <p className="text-lg text-cy-gray-400 leading-relaxed max-w-2xl mx-auto mb-8">
              CyberCom Revolution is an enterprise software company building intelligent platforms for healthcare providers, retail businesses, and enterprises across the Middle East and globally. We believe software should be an accelerator — not a constraint.
            </p>
            <div className="flex flex-wrap gap-3 justify-center">
              <Link href={`/${l}/contact`} className="btn-primary px-6 py-3 text-sm inline-flex items-center gap-2">
                Contact Us
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${l}/about`} className="btn-secondary px-6 py-3 text-sm">
                About CyberCom
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 border-y border-cy-glass-border bg-cy-dark/30" aria-label="Company statistics">
        <div className="section-container">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {STATS.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-3xl sm:text-4xl font-heading font-bold text-gradient-orange mb-1">{s.value}</div>
                <div className="text-sm font-medium text-white mb-1">{s.label}</div>
                <div className="text-xs text-cy-gray-400">{s.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Our Platforms */}
      <section className="py-20" aria-labelledby="platforms-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="platforms-heading" className="text-3xl font-heading font-semibold text-white mb-4">Our Product Ecosystem</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">Three enterprise platforms. One shared identity, one audit trail, one integration layer. Built to work together from day one.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {PLATFORMS.map((p) => (
              <Link
                key={p.name}
                href={`/${l}${p.href}`}
                className={`glass-card rounded-2xl p-8 border ${p.border} ${p.bg} hover:scale-[1.01] transition-all duration-200 cursor-pointer group flex flex-col`}
                aria-label={`${p.name} — ${p.tagline}`}
              >
                <span className={`product-badge mb-4 ${p.color} ${p.border} ${p.bg} self-start`}>{p.badge}</span>
                <h3 className={`text-2xl font-heading font-bold ${p.color} mb-2`}>{p.name}</h3>
                <p className="text-sm font-medium text-white mb-3">{p.tagline}</p>
                <p className="text-sm text-cy-gray-400 leading-relaxed flex-1 mb-6">{p.desc}</p>
                <span className={`text-sm ${p.color} flex items-center gap-1 font-medium`}>
                  Explore {p.name}
                  <ArrowRight className="w-4 h-4 rtl:rotate-180 group-hover:translate-x-1 transition-transform" aria-hidden="true" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="values-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="values-heading" className="text-3xl font-heading font-semibold text-white mb-4">Our Principles</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">The non-negotiable principles that guide every product decision, architecture choice, and customer commitment.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {VALUES.map((v) => (
              <div key={v.title} className={`glass-card rounded-xl p-6 border ${v.bg}`}>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center border mb-4 ${v.bg}`}>
                  <v.icon className={`w-5 h-5 ${v.color}`} aria-hidden="true" />
                </div>
                <h3 className={`text-base font-heading font-semibold ${v.color} mb-2`}>{v.title}</h3>
                <p className="text-sm text-cy-gray-400 leading-relaxed">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-20" aria-labelledby="mission-heading">
        <div className="section-container max-w-4xl mx-auto text-center">
          <h2 id="mission-heading" className="text-3xl font-heading font-semibold text-white mb-6">Our Mission</h2>
          <blockquote className="text-xl text-cy-gray-200 leading-relaxed mb-8 italic">
            &ldquo;To transform how healthcare providers, retail businesses, and enterprises operate — by delivering intelligent, integrated, and standards-compliant software that scales from the smallest clinic to the largest health ministry.&rdquo;
          </blockquote>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link href={`/${l}/careers`} className="btn-primary px-6 py-3 text-sm inline-flex items-center gap-2">
              <Users className="w-4 h-4" aria-hidden="true" />
              Join Our Team
            </Link>
            <Link href={`/${l}/investors`} className="btn-secondary px-6 py-3 text-sm">
              Investor Relations
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
