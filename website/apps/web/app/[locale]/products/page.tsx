import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight } from "lucide-react";

interface ProductsPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: ProductsPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "All Products",
    description: "Explore all 9 CyberCom platforms: CyMed healthcare, CyCom ERP, CyGov government, CyAI, CyIdentity, CyIntegrationHub, CyData, CyConnect, CyCitizen.",
    path: "/products",
    locale,
  });
}

const PLATFORM_CATEGORIES = [
  {
    name: "Healthcare",
    desc: "FHIR-native, ICD-11 ready clinical platforms",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/5",
    borderColor: "border-emerald-500/20",
    products: [
      { name: "CyMed Clinic", slug: "cymed-clinic", desc: "Outpatient clinical management" },
      { name: "CyMed Hospital", slug: "cymed-hospital", desc: "Complete hospital operations" },
      { name: "CyMed Laboratory", slug: "cymed-laboratory", desc: "LIS with auto-verification" },
      { name: "CyMed Imaging", slug: "cymed-imaging", desc: "RIS/DICOM PACS" },
      { name: "CyMed Pharmacy", slug: "cymed-pharmacy", desc: "Clinical dispensing" },
      { name: "CyMed Patient Portal", slug: "cymed-patient-portal", desc: "Patient engagement" },
      { name: "CyMed Provider Portal", slug: "cymed-provider-portal", desc: "Clinical workforce" },
      { name: "CyMed Revenue Cycle", slug: "cymed-revenue-cycle", desc: "RCM & billing" },
      { name: "CyMed Population Health", slug: "cymed-population-health", desc: "Analytics & programs" },
    ],
  },
  {
    name: "Retail",
    desc: "Intelligent retail & commerce platform",
    color: "text-cy-orange",
    bgColor: "bg-cy-orange/5",
    borderColor: "border-cy-orange/20",
    products: [
      { name: "CyShop", slug: "cyshop", desc: "Complete retail & commerce platform" },
    ],
  },
  {
    name: "Enterprise",
    desc: "ERP, government, and citizen platforms",
    color: "text-blue-400",
    bgColor: "bg-blue-500/5",
    borderColor: "border-blue-500/20",
    products: [
      { name: "CyCom ERP", slug: "cycom", desc: "Unified enterprise ERP" },
      { name: "CyCom Finance", slug: "cycom-finance", desc: "Financial management & budgeting" },
      { name: "CyCom Accounting", slug: "cycom-accounting", desc: "AP, AR, & tax compliance" },
      { name: "CyCom Procurement", slug: "cycom-procurement", desc: "Sourcing & supplier relations" },
      { name: "CyCom Inventory", slug: "cycom-inventory", desc: "Multi-warehouse stock control" },
      { name: "CyCom HR", slug: "cycom-hr", desc: "Human resource & talent" },
      { name: "CyCom Payroll", slug: "cycom-payroll", desc: "Bilingual salary & WPS processing" },
      { name: "CyCom CRM", slug: "cycom-crm", desc: "Lead pipeline & customer management" },
      { name: "CyCom Assets", slug: "cycom-assets", desc: "Fixed asset & depreciation registry" },
      { name: "CyCom Manufacturing", slug: "cycom-manufacturing", desc: "Production & Bill of Materials" },
      { name: "CyCom Retail", slug: "cycom-retail", desc: "Point of Sale & checkout retail" },
      { name: "CyCom BI", slug: "cycom-bi", desc: "Drag-and-drop dashboards & BI" },
      { name: "CyGov", slug: "cygov", desc: "Digital government platform" },
      { name: "CyCitizen", slug: "cycitizen", desc: "Citizen experience" },
    ],
  },
  {
    name: "Intelligence & Data",
    desc: "AI, analytics, and integration platforms",
    color: "text-pink-400",
    bgColor: "bg-pink-500/5",
    borderColor: "border-pink-500/20",
    products: [
      { name: "CyAI", slug: "cyai", desc: "Artificial intelligence platform" },
      { name: "CyData", slug: "cydata", desc: "Data lakehouse & analytics" },
    ],
  },
  {
    name: "Infrastructure",
    desc: "Identity, integration, and communications",
    color: "text-violet-400",
    bgColor: "bg-violet-500/5",
    borderColor: "border-violet-500/20",
    products: [
      { name: "CyIdentity", slug: "cyidentity", desc: "OAuth 2.1, OIDC, Zero Trust" },
      { name: "CyIntegrationHub", slug: "cyintegrationhub", desc: "FHIR, HL7, REST, Kafka" },
      { name: "CyConnect", slug: "cyconnect", desc: "Unified communications" },
    ],
  },
  {
    name: "Developer",
    desc: "APIs, SDKs, and integration tools",
    color: "text-violet-300",
    bgColor: "bg-violet-400/5",
    borderColor: "border-violet-400/20",
    products: [
      { name: "CyDeveloper", slug: "cydeveloper", desc: "REST APIs, SDKs, webhooks, sandbox" },
    ],
  },
];

export default async function ProductsPage({ params }: ProductsPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Header */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/8" />
        </div>
        <div className="section-container relative z-10 text-center">
          <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">Platform Suite</p>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-4">
            The CyberCom Ecosystem
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto">
            Three enterprise platforms — CyMed, CyShop, and CyCom ERP — built on open standards, sharing one identity layer, one audit trail, and one integration hub.
          </p>
        </div>
      </div>

      {/* Categories */}
      <div className="section-container pb-24">
        <div className="space-y-16">
          {PLATFORM_CATEGORIES.map((category) => (
            <section key={category.name} aria-labelledby={`cat-${category.name}`}>
              <div className="flex items-center gap-3 mb-6">
                <div className={`w-2 h-6 rounded-full ${category.bgColor} border ${category.borderColor}`} aria-hidden="true" />
                <div>
                  <h2 id={`cat-${category.name}`} className={`text-xl font-heading font-semibold ${category.color}`}>
                    {category.name}
                  </h2>
                  <p className="text-sm text-cy-gray-400">{category.desc}</p>
                </div>
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {category.products.map((product) => (
                  <Link
                    key={product.slug}
                    href={`/${l}/products/${product.slug}`}
                    className="glass-card block p-5 rounded-xl border border-cy-glass-border hover:border-current/20 group transition-all duration-300"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className={`font-medium text-sm mb-0.5 group-hover:${category.color} transition-colors`}>
                          {product.name}
                        </div>
                        <div className="text-xs text-cy-gray-400">{product.desc}</div>
                      </div>
                      <ArrowRight
                        className="w-4 h-4 text-cy-gray-600 group-hover:text-white group-hover:translate-x-0.5 transition-all duration-200 flex-shrink-0 rtl:rotate-180"
                        aria-hidden="true"
                      />
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>

        {/* Demo CTA */}
        <div className="mt-16 glass-card p-8 rounded-2xl text-center">
          <h2 className="text-2xl font-heading font-semibold text-white mb-3">
            Not sure which platform fits your needs?
          </h2>
          <p className="text-cy-gray-400 mb-6">
            Our platform specialists will guide you to the right solution for your industry and scale.
          </p>
          <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
            Schedule a Consultation
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </div>
  );
}
