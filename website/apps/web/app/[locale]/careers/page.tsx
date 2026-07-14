import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Code2, HeartPulse, BarChart3, Headphones, Users, Globe } from "lucide-react";

interface CareersPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: CareersPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Careers",
    description:
      "Build the intelligent platforms transforming healthcare, government, and enterprise across the Middle East and beyond. Join CyberCom Revolution.",
    path: "/careers",
    locale,
  });
}

const WHY_JOIN = [
  {
    icon: HeartPulse,
    title: "Purpose-driven work",
    desc: "Every line of code contributes to better patient care, more efficient government, and stronger enterprise operations across the Middle East.",
  },
  {
    icon: Code2,
    title: "Cutting-edge technology",
    desc: "Work with FHIR R4, Kafka, PostgreSQL RLS multi-tenancy, Next.js 15, Keycloak 24, and AI clinical decision systems built to production grade.",
  },
  {
    icon: Globe,
    title: "Regional & global impact",
    desc: "Based in the MENA region with a product designed to scale globally — English, Arabic, RTL/LTR, ICD-11, SNOMED CT, and international compliance built in.",
  },
  {
    icon: Users,
    title: "Small team, large scope",
    desc: "We're a lean, high-ownership engineering culture. You'll work across the full stack, influence architecture, and ship features that matter from day one.",
  },
];

const DEPARTMENTS = [
  {
    icon: Code2,
    name: "Engineering",
    roles: [
      "Senior Backend Engineer (Django / PostgreSQL)",
      "Senior Frontend Engineer (Next.js / TypeScript)",
      "Platform Engineer (Kubernetes / Terraform)",
      "Clinical Informatics Engineer (FHIR / HL7)",
    ],
  },
  {
    icon: HeartPulse,
    name: "Healthcare & Clinical",
    roles: [
      "Clinical Implementation Specialist",
      "Healthcare Data Analyst",
      "Clinical Terminology Specialist (ICD-11 / SNOMED CT)",
    ],
  },
  {
    icon: BarChart3,
    name: "Product & Sales",
    roles: [
      "Product Manager — CyMed Healthcare",
      "Enterprise Account Executive",
      "Pre-Sales Solution Architect",
    ],
  },
  {
    icon: Headphones,
    name: "Customer Success",
    roles: [
      "Customer Success Manager",
      "Implementation Project Manager",
      "Technical Support Engineer",
    ],
  },
];

const VALUES = [
  { title: "Open standards, always", desc: "We build on FHIR, ICD-11, OAuth 2.1 — not proprietary lock-in. Standards ensure longevity and interoperability." },
  { title: "Clinical safety first", desc: "Every healthcare feature is designed with patient safety as a non-negotiable constraint, not an afterthought." },
  { title: "Deep ownership", desc: "Small teams with large scope. Engineers own their modules end-to-end — from schema design to production monitoring." },
  { title: "Radical transparency", desc: "We document decisions, publish ADRs, and share technical context openly across the team." },
];

const PERKS = [
  "Competitive salary (market-benchmarked)",
  "Flexible remote / hybrid work",
  "30 days annual leave",
  "Learning & conference budget",
  "Healthcare coverage",
  "Stock options (senior roles)",
  "Home office setup stipend",
  "Arabic & English working environment",
];

export default async function CareersPage({ params }: CareersPageProps) {
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
        <div className="section-container relative z-10 max-w-4xl">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            Careers
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
            Build what matters.{" "}
            <span className="text-gradient">Serve millions.</span>
          </h1>
          <p className="text-xl text-cy-gray-400 leading-relaxed max-w-3xl mb-8">
            CyberCom Revolution is building the intelligence layer for healthcare, government, and
            enterprise across the Middle East and beyond. We&apos;re looking for engineers, clinical
            specialists, and builders who want their work to mean something.
          </p>
          <Link
            href={`mailto:careers@cy-com.com`}
            className="btn-primary px-8 py-3 inline-flex"
          >
            Send Your Application
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </Link>
        </div>
      </div>

      {/* Why Join */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="why-heading">
        <div className="section-container">
          <h2 id="why-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            Why CyberCom?
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {WHY_JOIN.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="glass-card p-6 rounded-2xl flex gap-4">
                  <div className="w-10 h-10 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <h3 className="font-heading font-semibold text-white mb-2">{item.title}</h3>
                    <p className="text-sm text-cy-gray-400 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Open Roles */}
      <section className="py-20" aria-labelledby="roles-heading">
        <div className="section-container">
          <h2 id="roles-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            Open Positions
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-2xl mx-auto">
            We&apos;re building across all disciplines. If you don&apos;t see your exact role but believe
            you&apos;re a strong fit, send us a message — we review all applications.
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            {DEPARTMENTS.map((dept) => {
              const Icon = dept.icon;
              return (
                <div key={dept.name} className="glass-card p-6 rounded-2xl">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-9 h-9 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center">
                      <Icon className="w-4.5 h-4.5 text-cy-orange" aria-hidden="true" />
                    </div>
                    <h3 className="font-heading font-semibold text-white">{dept.name}</h3>
                  </div>
                  <ul className="space-y-3">
                    {dept.roles.map((role) => (
                      <li key={role} className="flex items-start justify-between gap-4 group">
                        <span className="text-sm text-cy-gray-200">{role}</span>
                        <a
                          href={`mailto:careers@cy-com.com?subject=Application: ${encodeURIComponent(role)}`}
                          className="text-xs text-cy-orange hover:text-cy-orange-light transition-colors whitespace-nowrap flex items-center gap-1 cursor-pointer"
                          aria-label={`Apply for ${role}`}
                        >
                          Apply
                          <ArrowRight className="w-3 h-3 rtl:rotate-180" aria-hidden="true" />
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="values-heading">
        <div className="section-container">
          <h2 id="values-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            How We Work
          </h2>
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {VALUES.map((v) => (
              <div key={v.title} className="glass-card p-6 rounded-2xl flex gap-4">
                <div className="w-1 rounded-full bg-gradient-cy flex-shrink-0" aria-hidden="true" />
                <div>
                  <h3 className="font-heading font-semibold text-white mb-1">{v.title}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed">{v.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Perks */}
      <section className="py-20" aria-labelledby="perks-heading">
        <div className="section-container">
          <h2 id="perks-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            Benefits & Perks
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 max-w-4xl mx-auto">
            {PERKS.map((perk) => (
              <div key={perk} className="glass-card px-4 py-3 rounded-xl flex items-center gap-2.5">
                <div className="w-2 h-2 rounded-full bg-cy-orange flex-shrink-0" aria-hidden="true" />
                <span className="text-sm text-cy-gray-200">{perk}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Apply CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="careers-cta">
        <div className="section-container text-center max-w-2xl">
          <h2 id="careers-cta" className="text-3xl font-heading font-semibold text-white mb-4">
            Don&apos;t see the right role?
          </h2>
          <p className="text-cy-gray-400 mb-8 leading-relaxed">
            We&apos;re always open to meeting exceptional people. Send us your CV and a short note about
            what you&apos;d like to build.
          </p>
          <a
            href="mailto:careers@cy-com.com"
            className="btn-primary px-8 py-3 inline-flex"
          >
            careers@cy-com.com
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </a>
        </div>
      </section>
    </div>
  );
}
