import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Package, Star, Download, Filter, Zap, Shield, Globe, BarChart2 } from "lucide-react";

interface MarketplacePageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: MarketplacePageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Marketplace",
    description:
      "Discover certified modules, extensions, connectors, and AI packages for the CyberCom ecosystem. Published by CyberCom, verified partners, and community developers.",
    path: "/marketplace",
    locale,
  });
}

const CATEGORIES = [
  { label: "All", value: "all", icon: Package },
  { label: "Clinical Modules", value: "module", icon: Zap },
  { label: "Extensions", value: "extension", icon: Shield },
  { label: "AI Packages", value: "ai_package", icon: BarChart2 },
  { label: "Connectors", value: "connector", icon: Globe },
  { label: "Reports", value: "report", icon: Filter },
];

const FEATURED = [
  {
    name: "CyMed Advanced Analytics Pack",
    category: "AI Package",
    publisher: "CyberCom Official",
    publisherType: "official" as const,
    rating: 4.9,
    installs: 2400,
    description: "Pre-built clinical dashboards, KPI scorecards, and predictive readmission models for CyMed Hospital and Clinic.",
    tags: ["analytics", "ai", "clinical"],
    priceModel: "subscription" as const,
    priceAmount: 0,
  },
  {
    name: "MOH Data Exchange Connector",
    category: "Connector",
    publisher: "CyberCom Official",
    publisherType: "official" as const,
    rating: 4.8,
    installs: 1800,
    description: "Certified bi-directional data exchange with Ministry of Health national registries and e-health portals.",
    tags: ["moh", "fhir", "national"],
    priceModel: "free" as const,
    priceAmount: 0,
  },
  {
    name: "NABIDH FHIR Connector",
    category: "Connector",
    publisher: "CyberCom Official",
    publisherType: "official" as const,
    rating: 4.9,
    installs: 1200,
    description: "UAE NABIDH national health data network connector with certified FHIR R4 profile compliance.",
    tags: ["nabidh", "uae", "fhir", "national"],
    priceModel: "free" as const,
    priceAmount: 0,
  },
  {
    name: "Payroll Localization – GCC",
    category: "Extension",
    publisher: "TechBridge Arabia",
    publisherType: "partner" as const,
    rating: 4.7,
    installs: 950,
    description: "GCC-specific payroll rules for GOSI, WPS, end-of-service calculations, and multi-currency payslips.",
    tags: ["payroll", "gcc", "hr"],
    priceModel: "one_time" as const,
    priceAmount: 2400,
  },
  {
    name: "Clinical Template Library – Cardiology",
    category: "Clinical Template",
    publisher: "CyberCom Official",
    publisherType: "official" as const,
    rating: 4.8,
    installs: 760,
    description: "600+ validated cardiology clinical templates, order sets, care plans, and discharge summaries.",
    tags: ["cardiology", "templates", "clinical"],
    priceModel: "subscription" as const,
    priceAmount: 0,
  },
  {
    name: "WhatsApp Notifications Extension",
    category: "Extension",
    publisher: "NxBridge",
    publisherType: "partner" as const,
    rating: 4.6,
    installs: 1100,
    description: "Appointment reminders, lab result notifications, and prescription alerts via WhatsApp Business API.",
    tags: ["whatsapp", "notifications", "patient"],
    priceModel: "usage" as const,
    priceAmount: 0,
  },
];

const STATS = [
  { label: "Published Listings", value: "200+" },
  { label: "Verified Partners", value: "45" },
  { label: "Total Installs", value: "28K+" },
  { label: "Avg. Rating", value: "4.8★" },
];

function PublisherBadge({ type }: { type: "official" | "partner" | "community" }) {
  if (type === "official") return <span className="px-2 py-0.5 rounded-full text-2xs font-medium bg-cy-orange/10 text-cy-orange border border-cy-orange/20">Official</span>;
  if (type === "partner") return <span className="px-2 py-0.5 rounded-full text-2xs font-medium bg-cy-cyan/10 text-cy-cyan border border-cy-cyan/20">Verified Partner</span>;
  return <span className="px-2 py-0.5 rounded-full text-2xs font-medium bg-cy-glass-bg text-cy-gray-400 border border-cy-glass-border">Community</span>;
}

export default async function MarketplacePage({ params }: MarketplacePageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[700px] h-[700px] -top-32 left-1/4 bg-cy-orange/5" />
          <div className="glow-orb w-[500px] h-[500px] top-0 right-1/4 bg-cy-cyan/4" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            CyberCom Marketplace
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            Extend your{" "}
            <span className="text-gradient">CyberCom platform</span>
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-10">
            Certified modules, AI packages, connectors, and clinical templates.
            Published by CyberCom and verified partners — installable in one click.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
              Get Platform Access
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/partner`} className="btn-secondary px-8 py-3">
              Publish an Extension
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-cy-dark/30 border-y border-cy-glass-border py-10">
        <div className="section-container grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
          {STATS.map((s) => (
            <div key={s.label}>
              <div className="text-3xl font-heading font-semibold text-cy-orange mb-1">{s.value}</div>
              <div className="text-sm text-cy-gray-400">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Categories */}
      <section className="py-12" aria-labelledby="categories-heading">
        <div className="section-container">
          <h2 id="categories-heading" className="sr-only">Browse Categories</h2>
          <div className="flex flex-wrap gap-2 justify-center">
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <button
                  key={cat.value}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border border-cy-glass-border bg-cy-glass-bg text-cy-gray-300 hover:text-white hover:border-cy-orange/40 transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-cy-orange"
                  aria-label={`Filter by ${cat.label}`}
                >
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  {cat.label}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Featured listings */}
      <section className="pb-20" aria-labelledby="featured-heading">
        <div className="section-container">
          <div className="flex items-center justify-between mb-8">
            <h2 id="featured-heading" className="text-2xl font-heading font-semibold text-white">
              Featured Listings
            </h2>
            <span className="text-sm text-cy-gray-400">Showing 6 of 200+</span>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURED.map((item) => (
              <article
                key={item.name}
                className="glass-card p-6 rounded-2xl flex flex-col hover:border-cy-glass-border/80 transition-colors duration-150"
              >
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                    <Package className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                  </div>
                  <PublisherBadge type={item.publisherType} />
                </div>

                <h3 className="text-sm font-heading font-semibold text-white mb-1">{item.name}</h3>
                <p className="text-xs text-cy-gray-400 mb-1">{item.category} · {item.publisher}</p>
                <p className="text-xs text-cy-gray-400 leading-relaxed mb-4 flex-1">{item.description}</p>

                <div className="flex flex-wrap gap-1 mb-4">
                  {item.tags.map((tag) => (
                    <span key={tag} className="px-2 py-0.5 rounded-md text-2xs bg-cy-glass-bg border border-cy-glass-border text-cy-gray-400">
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 text-xs text-cy-gray-400">
                    <span className="flex items-center gap-1">
                      <Star className="w-3 h-3 text-amber-400 fill-amber-400" aria-hidden="true" />
                      {item.rating}
                    </span>
                    <span className="flex items-center gap-1">
                      <Download className="w-3 h-3" aria-hidden="true" />
                      {item.installs.toLocaleString()}
                    </span>
                  </div>
                  <span className="text-xs font-medium text-cy-orange">
                    {item.priceModel === "free" ? "Free" : item.priceModel === "subscription" ? "Included" : `$${item.priceAmount.toLocaleString()}`}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Publish CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="publish-cta">
        <div className="section-container">
          <div className="glass-card p-10 lg:p-14 rounded-3xl grid lg:grid-cols-2 gap-10 items-center">
            <div>
              <h2 id="publish-cta" className="text-3xl font-heading font-semibold text-white mb-4">
                Publish your extension
              </h2>
              <p className="text-cy-gray-400 leading-relaxed mb-6">
                Join the CyberCom developer ecosystem. Build certified modules, connectors,
                and AI packages that reach thousands of healthcare, government, and enterprise customers
                across the MENA region and beyond.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link href={`/${l}/partner`} className="btn-primary px-8 py-3">
                  Become a Publisher
                  <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
                </Link>
                <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                  Developer Support
                </Link>
              </div>
            </div>
            <div className="space-y-4">
              {[
                { icon: Shield, title: "Certification program", desc: "Pass our technical review and earn a verified publisher badge" },
                { icon: Globe, title: "Global distribution", desc: "Reach all CyberCom customers via the in-platform marketplace" },
                { icon: BarChart2, title: "Revenue sharing", desc: "Earn revenue on paid listings through the partner program" },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                      <Icon className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">{item.title}</div>
                      <div className="text-xs text-cy-gray-400">{item.desc}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
