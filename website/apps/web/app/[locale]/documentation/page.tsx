import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, BookOpen, Code2, ShieldCheck, Stethoscope, ShoppingBag, Factory, Search, FileText, Video } from "lucide-react";

interface DocumentationPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: DocumentationPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Documentation",
    description: "Comprehensive documentation for CyMed, CyShop, CyCom ERP, and the CyberCom Platform. API references, integration guides, deployment runbooks, and clinical workflow documentation.",
    path: "/documentation",
    locale,
  });
}

const DOCS_URL = process.env.NEXT_PUBLIC_DOCS_URL ?? "https://docs.cy-com.com";

const DOC_SECTIONS = [
  {
    icon: Stethoscope,
    title: "CyMed Healthcare",
    desc: "Clinical workflow guides, FHIR API reference, HL7 integration, DICOM configuration, and deployment guides for all 9 CyMed modules.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
    links: [
      { label: "Getting Started with CyMed", href: `${DOCS_URL}/cymed/getting-started` },
      { label: "FHIR R4 API Reference", href: `${DOCS_URL}/cymed/fhir-api` },
      { label: "Hospital Deployment Guide", href: `${DOCS_URL}/cymed/hospital/deployment` },
      { label: "Drug Interaction Engine", href: `${DOCS_URL}/cymed/pharmacy/drug-interactions` },
      { label: "HL7 v2 Integration", href: `${DOCS_URL}/cymed/integration/hl7` },
    ],
  },
  {
    icon: ShoppingBag,
    title: "CyShop Retail",
    desc: "POS setup, inventory management, loyalty program configuration, and integration guides for all supported business types.",
    color: "text-cy-orange",
    bg: "bg-cy-orange/10 border-cy-orange/20",
    links: [
      { label: "CyShop Quick Start", href: `${DOCS_URL}/cyshop/getting-started` },
      { label: "POS Terminal Setup", href: `${DOCS_URL}/cyshop/pos/setup` },
      { label: "Restaurant & F&B Guide", href: `${DOCS_URL}/cyshop/restaurant` },
      { label: "Inventory Management", href: `${DOCS_URL}/cyshop/inventory` },
      { label: "Loyalty Program Config", href: `${DOCS_URL}/cyshop/loyalty` },
    ],
  },
  {
    icon: Factory,
    title: "CyCom ERP",
    desc: "Finance module configuration, chart of accounts setup, payroll processing, procurement workflows, and BI dashboard guides.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    links: [
      { label: "ERP Getting Started", href: `${DOCS_URL}/cycom/getting-started` },
      { label: "Chart of Accounts (IFRS)", href: `${DOCS_URL}/cycom/finance/chart-of-accounts` },
      { label: "Payroll & WPS Guide", href: `${DOCS_URL}/cycom/payroll/wps` },
      { label: "Procurement Workflow", href: `${DOCS_URL}/cycom/procurement` },
      { label: "BI Dashboard Setup", href: `${DOCS_URL}/cycom/bi` },
    ],
  },
  {
    icon: ShieldCheck,
    title: "CyberCom Platform",
    desc: "CyIdentity IAM, OAuth 2.1 setup, RBAC configuration, tenant provisioning, audit trail, and Zero Trust architecture guides.",
    color: "text-violet-400",
    bg: "bg-violet-500/10 border-violet-500/20",
    links: [
      { label: "Platform Architecture", href: `${DOCS_URL}/platform/architecture` },
      { label: "OAuth 2.1 & OIDC Setup", href: `${DOCS_URL}/platform/identity/oauth` },
      { label: "Tenant Provisioning", href: `${DOCS_URL}/platform/tenants` },
      { label: "RBAC Configuration", href: `${DOCS_URL}/platform/rbac` },
      { label: "Audit Trail Reference", href: `${DOCS_URL}/platform/audit` },
    ],
  },
  {
    icon: Code2,
    title: "API Reference",
    desc: "REST API documentation, authentication, pagination, error handling, and SDK guides for all CyberCom products.",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10 border-cyan-500/20",
    links: [
      { label: "REST API Overview", href: `${DOCS_URL}/api` },
      { label: "Authentication (OAuth 2.1)", href: `${DOCS_URL}/api/auth` },
      { label: "FHIR Endpoints", href: `${DOCS_URL}/api/fhir` },
      { label: "Webhooks & Events", href: `${DOCS_URL}/api/webhooks` },
      { label: "SDK & Client Libraries", href: `${DOCS_URL}/api/sdk` },
    ],
  },
  {
    icon: BookOpen,
    title: "Deployment & Operations",
    desc: "Kubernetes deployment, Docker configuration, Helm charts, backup procedures, monitoring, and disaster recovery runbooks.",
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
    links: [
      { label: "Kubernetes Deployment", href: `${DOCS_URL}/ops/kubernetes` },
      { label: "Helm Chart Reference", href: `${DOCS_URL}/ops/helm` },
      { label: "Backup & Restore", href: `${DOCS_URL}/ops/backup` },
      { label: "Monitoring Setup", href: `${DOCS_URL}/ops/monitoring` },
      { label: "Disaster Recovery", href: `${DOCS_URL}/ops/dr` },
    ],
  },
];

const QUICK_LINKS = [
  { icon: Search, label: "Search All Docs", href: `${DOCS_URL}/search`, desc: "Find anything across all documentation" },
  { icon: Video, label: "Video Tutorials", href: `${DOCS_URL}/videos`, desc: "Step-by-step video guides for all products" },
  { icon: FileText, label: "Release Notes", href: `${DOCS_URL}/releases`, desc: "Latest updates and changelog" },
  { icon: Code2, label: "API Playground", href: `${DOCS_URL}/playground`, desc: "Interactive API explorer and testing" },
];

export default async function DocumentationPage({ params }: DocumentationPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <section className="relative py-24 overflow-hidden" aria-labelledby="docs-heading">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="glow-orb w-[500px] h-[500px] -top-16 left-1/4 bg-violet-500/5" />
          <div className="glow-orb w-[400px] h-[400px] bottom-0 right-0 bg-cyan-500/5" />
        </div>
        <div className="section-container relative z-10 text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-violet-500/20 bg-violet-500/5 mb-6">
            <BookOpen className="w-3.5 h-3.5 text-violet-400" aria-hidden="true" />
            <span className="text-xs font-medium text-violet-400 tracking-wider uppercase">Documentation</span>
          </div>
          <h1 id="docs-heading" className="text-4xl sm:text-5xl font-heading font-semibold text-white mb-6 leading-tight">
            Everything You Need to{" "}<br />
            <span className="text-gradient-orange">Build, Deploy & Scale</span>
          </h1>
          <p className="text-lg text-cy-gray-400 leading-relaxed mb-8">
            Comprehensive guides, API references, integration tutorials, and deployment runbooks for CyMed, CyShop, CyCom ERP, and the CyberCom Platform.
          </p>
          <a
            href={DOCS_URL}
            target="_blank"
            rel="noreferrer"
            className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2"
          >
            Open Full Documentation
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </a>
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12 border-y border-cy-glass-border bg-cy-dark/30" aria-label="Quick access links">
        <div className="section-container">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {QUICK_LINKS.map((q) => (
              <a
                key={q.label}
                href={q.href}
                target="_blank"
                rel="noreferrer"
                className="glass-card rounded-xl p-5 flex items-start gap-4 hover:border-cy-glass-bg-hover transition-all duration-150 cursor-pointer group"
              >
                <div className="w-9 h-9 rounded-lg bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center flex-shrink-0">
                  <q.icon className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                </div>
                <div>
                  <div className="text-sm font-medium text-white group-hover:text-cy-orange transition-colors">{q.label}</div>
                  <div className="text-xs text-cy-gray-400 mt-0.5">{q.desc}</div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Documentation Sections */}
      <section className="py-20" aria-labelledby="doc-sections-heading">
        <div className="section-container">
          <h2 id="doc-sections-heading" className="sr-only">Documentation sections</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {DOC_SECTIONS.map((section) => (
              <div key={section.title} className={`glass-card rounded-2xl p-7 border ${section.bg} flex flex-col`}>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center border mb-4 ${section.bg}`}>
                  <section.icon className={`w-5 h-5 ${section.color}`} aria-hidden="true" />
                </div>
                <h3 className={`text-base font-heading font-semibold ${section.color} mb-2`}>{section.title}</h3>
                <p className="text-sm text-cy-gray-400 leading-relaxed mb-5 flex-1">{section.desc}</p>
                <ul className="space-y-2" aria-label={`${section.title} documentation links`}>
                  {section.links.map((link) => (
                    <li key={link.label}>
                      <a
                        href={link.href}
                        target="_blank"
                        rel="noreferrer"
                        className={`text-sm ${section.color} hover:underline flex items-center gap-1.5`}
                      >
                        <ArrowRight className="w-3 h-3 rtl:rotate-180 flex-shrink-0" aria-hidden="true" />
                        {link.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Support CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="support-cta-heading">
        <div className="section-container text-center max-w-3xl mx-auto">
          <h2 id="support-cta-heading" className="text-3xl font-heading font-semibold text-white mb-4">Can&apos;t Find What You Need?</h2>
          <p className="text-cy-gray-400 mb-8">Our support team is here to help. Contact us for technical assistance, implementation guidance, or integration support.</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link href={`/${l}/contact`} className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2">
              Contact Support
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <a href={`${DOCS_URL}/community`} target="_blank" rel="noreferrer" className="btn-secondary px-8 py-3 text-sm">
              Community Forum
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
