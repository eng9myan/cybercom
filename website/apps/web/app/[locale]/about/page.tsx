import { setRequestLocale } from "next-intl/server";
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
  return buildMetadata({
    title: "About",
    description: "CyberCom Revolution builds the world's most integrated intelligent platforms for healthcare, government, and enterprise — unifying 9 domains in one connected ecosystem.",
    path: "/about",
    locale,
  });
}

const MISSIONS = [
  {
    title: "Healthcare Transformation",
    desc: "We believe every patient deserves care delivered through intelligent, standards-based systems that eliminate friction and reduce errors.",
    icon: "🏥",
  },
  {
    title: "Government Modernization",
    desc: "We build digital government infrastructure that makes public services accessible, efficient, and transparent for every citizen.",
    icon: "🏛",
  },
  {
    title: "Enterprise Intelligence",
    desc: "We connect ERP, AI, and analytics to give enterprises the real-time insight they need to operate at the speed of modern business.",
    icon: "⚡",
  },
];

const VALUES = [
  { name: "Open Standards First", desc: "FHIR, ICD-11, OAuth 2.1 — we build on open standards, not proprietary lock-in." },
  { name: "Clinical Safety", desc: "Every healthcare feature is designed with clinical safety, drug interaction prevention, and patient privacy at its core." },
  { name: "Radical Integration", desc: "9 platforms that actually talk to each other — through real APIs, shared identity, and unified data." },
  { name: "Global Scale", desc: "Multi-language, multi-currency, multi-regulatory — designed for the Middle East and beyond." },
];

const PRODUCTS_BRIEF = [
  { name: "CyMed", desc: "Healthcare" },
  { name: "CyCom", desc: "ERP" },
  { name: "CyGov", desc: "Government" },
  { name: "CyAI", desc: "Intelligence" },
  { name: "CyIdentity", desc: "Identity" },
  { name: "CyIntegrationHub", desc: "Integration" },
  { name: "CyData", desc: "Data" },
  { name: "CyConnect", desc: "Communications" },
  { name: "CyCitizen", desc: "Citizens" },
];

export default async function AboutPage({ params }: AboutPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/8" />
        </div>
        <div className="section-container relative z-10 max-w-4xl">
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
            We&apos;re building the{" "}
            <span className="text-gradient">intelligence layer</span>{" "}
            for healthcare, government, and enterprise.
          </h1>
          <p className="text-xl text-cy-gray-400 leading-relaxed max-w-3xl">
            CyberCom Revolution is an enterprise software company engineering a unified ecosystem
            of 9 platforms — from FHIR-native clinical systems to AI-powered government services —
            all connected through a shared identity, integration, and data fabric.
          </p>
        </div>
      </div>

      {/* Mission */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="mission-heading">
        <div className="section-container">
          <h2 id="mission-heading" className="text-3xl font-heading font-semibold text-white mb-10 text-center">
            Our Mission
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {MISSIONS.map((m) => (
              <div key={m.title} className="glass-card p-6 rounded-2xl">
                <div className="text-3xl mb-4" aria-hidden="true" role="img">{m.icon}</div>
                <h3 className="font-heading font-semibold text-white text-lg mb-2">{m.title}</h3>
                <p className="text-sm text-cy-gray-400 leading-relaxed">{m.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Products */}
      <section className="py-20" aria-labelledby="products-heading">
        <div className="section-container">
          <h2 id="products-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            The CyberCom Ecosystem
          </h2>
          <p className="text-center text-cy-gray-400 mb-10">Nine platforms. One unified identity. One integration fabric.</p>
          <div className="flex flex-wrap justify-center gap-3">
            {PRODUCTS_BRIEF.map((p) => (
              <div key={p.name} className="glass-card px-5 py-3 rounded-xl border border-cy-glass-border">
                <div className="text-sm font-heading font-semibold text-gradient-orange">{p.name}</div>
                <div className="text-xs text-cy-gray-400">{p.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="values-heading">
        <div className="section-container">
          <h2 id="values-heading" className="text-3xl font-heading font-semibold text-white mb-10 text-center">
            What We Believe
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {VALUES.map((v) => (
              <div key={v.name} className="glass-card p-6 rounded-2xl flex gap-4">
                <div className="w-1 rounded-full bg-gradient-cy flex-shrink-0" aria-hidden="true" />
                <div>
                  <h3 className="font-heading font-semibold text-white mb-1">{v.name}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed">{v.desc}</p>
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
            Ready to work with us?
          </h2>
          <p className="text-cy-gray-400 mb-8">
            Whether you are a healthcare organization, government agency, or enterprise — let&apos;s talk.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
              Request a Demo
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
              Contact Us
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
