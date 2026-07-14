import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, ExternalLink, Play, Calendar } from "lucide-react";

interface DemoCenterProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: DemoCenterProps): Promise<Metadata> {
  const { locale } = await params;
  return buildMetadata({
    title: "Demo Center — Try All CyberCom Products",
    description: "Launch live demos of CyMed Hospital, Clinic, Pharmacy, Lab, Imaging, CyShop, and CyCom ERP. Explore modules, test role workflows, and see real data.",
    path: "/demo-center",
    locale,
  });
}

interface DemoProduct {
  slug: string;
  name: string;
  subtitle: string;
  forWho: string;
  color: string;
  accentClass: string;
  pillClass: string;
  keyModules: string[];
  erpModules: string[];
  demoUrl: string;
  productSlug: string;
}

const DEMO_PRODUCTS: DemoProduct[] = [
  {
    slug: "hospital",
    name: "CyMed Hospital",
    subtitle: "Complete Hospital Information System",
    forWho: "Hospitals, Health Systems, MOH",
    color: "emerald",
    accentClass: "from-emerald-900/20 to-transparent",
    pillClass: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    keyModules: ["Admission & ADT", "EMR & CPOE", "Nurse Station", "OR Management", "ICU / Virtual ICU", "Pharmacy", "Lab / LIS", "Radiology / RIS", "Blood Bank", "AI Scribe", "Sepsis Alert"],
    erpModules: ["Finance & Revenue Cycle", "HR & Payroll", "Medical Inventory", "Procurement", "Fixed Assets", "Reports & Dashboards"],
    demoUrl: "https://cymed.cy-com.com/hospital",
    productSlug: "cymed-hospital",
  },
  {
    slug: "clinic",
    name: "CyMed Clinic",
    subtitle: "Intelligent Outpatient Management Platform",
    forWho: "Clinics, Polyclinics, Specialty Centers",
    color: "emerald",
    accentClass: "from-emerald-900/15 to-transparent",
    pillClass: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    keyModules: ["Patient Registration", "Appointment Scheduling", "EMR & E-Prescribing", "Clinical Decision Support", "Lab Results Viewer", "Referral Management", "Telemedicine", "AI Scribe"],
    erpModules: ["Finance & Billing", "HR & Payroll", "Attendance", "Clinical Inventory", "Procurement", "Reports"],
    demoUrl: "https://cymed.cy-com.com/clinic",
    productSlug: "cymed-clinic",
  },
  {
    slug: "pharmacy",
    name: "CyMed Pharmacy",
    subtitle: "Clinical Pharmacy Management System",
    forWho: "Hospital Pharmacies, Retail Chains, Independent Pharmacies",
    color: "emerald",
    accentClass: "from-teal-900/15 to-transparent",
    pillClass: "text-teal-400 bg-teal-500/10 border-teal-500/20",
    keyModules: ["POS & Dispensing", "Prescription Verification", "Drug Interaction Checking", "Narcotic Log", "E-Prescription Integration", "Clinical Review"],
    erpModules: ["Pharmacy Billing", "Drug Inventory", "Procurement", "HR & Payroll", "Finance", "Reports"],
    demoUrl: "https://cymed.cy-com.com/pharmacy",
    productSlug: "cymed-pharmacy",
  },
  {
    slug: "laboratory",
    name: "CyMed Laboratory",
    subtitle: "Laboratory Information System with Auto-Verification",
    forWho: "Clinical Labs, Reference Labs, Hospital LIS",
    color: "emerald",
    accentClass: "from-cyan-900/15 to-transparent",
    pillClass: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
    keyModules: ["Test Orders", "Sample Tracking", "LIS Core", "Auto-Verification", "QC Management", "Microbiology", "Blood Bank", "Analyzer Interface"],
    erpModules: ["Test Billing", "Reagent Inventory", "Procurement", "HR & Payroll", "Finance", "Reports"],
    demoUrl: "https://cymed.cy-com.com/laboratory",
    productSlug: "cymed-laboratory",
  },
  {
    slug: "imaging",
    name: "CyMed Imaging",
    subtitle: "Radiology Information System & PACS Integration",
    forWho: "Radiology Departments, Diagnostic Centers, Teleradiology",
    color: "indigo",
    accentClass: "from-indigo-900/15 to-transparent",
    pillClass: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
    keyModules: ["RIS Worklist", "Radiology Scheduling", "DICOM / PACS", "Structured Reporting", "AI Image Analysis", "Teleradiology", "3D Visualization"],
    erpModules: ["Imaging Billing", "Equipment Asset Registry", "Maintenance", "HR & Payroll", "Finance", "Reports"],
    demoUrl: "https://cymed.cy-com.com/imaging",
    productSlug: "cymed-imaging",
  },
  {
    slug: "cyshop",
    name: "CyShop",
    subtitle: "Retail & Commerce OS for Every Business",
    forWho: "Restaurants, Retail, Groceries, Cafés, Supermarkets, Franchises",
    color: "orange",
    accentClass: "from-orange-900/20 to-transparent",
    pillClass: "text-orange-400 bg-orange-500/10 border-orange-500/20",
    keyModules: ["POS", "KDS", "Online Ordering", "Delivery Management", "Table Management", "Loyalty & Rewards", "Menu Management", "Customer Portal"],
    erpModules: ["Finance & ZATCA", "Real-Time Inventory", "HR & Payroll", "Attendance", "Procurement", "CRM", "Reports & Dashboards"],
    demoUrl: "https://cyshop.cy-com.com",
    productSlug: "cyshop",
  },
  {
    slug: "erp",
    name: "CyCom ERP",
    subtitle: "Unified Enterprise Resource Planning",
    forWho: "Enterprises, SMBs, Healthcare Groups, Government Entities",
    color: "blue",
    accentClass: "from-blue-900/20 to-transparent",
    pillClass: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    keyModules: ["Accounting", "AP / AR", "HR Management", "Payroll", "Inventory", "Procurement", "Sales & CRM", "Project Management", "Fleet", "Maintenance", "PLM", "Quality"],
    erpModules: ["Finance & Banking", "Warehouses", "Manufacturing", "Recruitment", "Marketing Automation", "Helpdesk", "e-Signatures", "BI Reports"],
    demoUrl: "https://health.cy-com.com",
    productSlug: "cycom-erp",
  },
];

export default async function DemoCenterPage({ params }: DemoCenterProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[700px] h-[700px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/5" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            Demo Center
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-semibold text-white mb-4 leading-tight">
            Try Every Product — Live
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-8 leading-relaxed">
            Launch any flagship product with real data. Explore all modules, test role workflows,
            and see how each product connects to the ERP backbone — no sign-up required.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href={`/${l}/demo`} className="btn-primary-glow px-8 py-3.5 text-base">
              Request Guided Demo
              <Calendar className="w-4 h-4" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/products`} className="btn-secondary px-8 py-3.5 text-base">
              View All Products
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      {/* Demo product cards */}
      <section className="pb-32">
        <div className="section-container">
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
            {DEMO_PRODUCTS.map(product => (
              <div
                key={product.slug}
                className={`glass-card rounded-2xl overflow-hidden border border-cy-glass-border hover:border-cy-glass-bg-hover transition-all duration-300 group bg-gradient-to-br ${product.accentClass}`}
              >
                {/* Card header */}
                <div className="p-6 pb-4">
                  <span className={`product-badge mb-3 ${product.pillClass}`}>
                    {product.forWho.split(",")[0]?.trim() ?? product.forWho}
                  </span>
                  <h2 className="text-xl font-heading font-semibold text-white mb-1">{product.name}</h2>
                  <p className="text-sm text-cy-gray-400">{product.subtitle}</p>
                  <p className="text-xs text-cy-gray-500 mt-1">For: {product.forWho}</p>
                </div>

                {/* Key modules */}
                <div className="px-6 pb-4">
                  <p className="text-xs font-medium text-cy-gray-400 uppercase tracking-wider mb-2">Key Modules</p>
                  <div className="flex flex-wrap gap-1.5">
                    {product.keyModules.map(mod => (
                      <span key={mod} className="text-[10px] px-2 py-0.5 rounded-md bg-white/[0.04] text-cy-gray-300 border border-cy-glass-border">
                        {mod}
                      </span>
                    ))}
                  </div>
                </div>

                {/* ERP modules */}
                <div className="px-6 pb-4">
                  <p className="text-xs font-medium text-blue-400 uppercase tracking-wider mb-2">Embedded ERP</p>
                  <div className="flex flex-wrap gap-1.5">
                    {product.erpModules.map(mod => (
                      <span key={mod} className="text-[10px] px-2 py-0.5 rounded-md bg-blue-500/5 text-blue-300 border border-blue-500/15">
                        {mod}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="p-4 border-t border-cy-glass-border flex gap-2">
                  <a
                    href={product.demoUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 inline-flex items-center justify-center gap-2 bg-cy-orange hover:bg-cy-orange-light text-white text-sm font-medium px-4 py-2.5 rounded-xl transition-all duration-200"
                  >
                    <Play className="w-3.5 h-3.5" aria-hidden="true" />
                    Launch Demo
                    <ExternalLink className="w-3 h-3 opacity-60" aria-hidden="true" />
                  </a>
                  <Link
                    href={`/${l}/products/${product.productSlug}`}
                    className="inline-flex items-center justify-center gap-2 btn-secondary text-sm px-4 py-2.5 flex-1"
                  >
                    Learn More
                    <ArrowRight className="w-3.5 h-3.5 rtl:rotate-180" aria-hidden="true" />
                  </Link>
                </div>

                {/* Guided demo CTA */}
                <div className="px-4 pb-4">
                  <Link
                    href={`/${l}/demo?product=${product.productSlug}`}
                    className="w-full text-xs text-cy-gray-400 hover:text-white transition-colors text-center py-2 inline-block"
                  >
                    <Calendar className="w-3 h-3 inline mr-1" aria-hidden="true" />
                    Request a guided 1-on-1 demo
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="py-20 bg-cy-dark/40">
        <div className="section-container text-center">
          <h2 className="text-3xl font-heading font-semibold text-white mb-4">Need a guided walkthrough?</h2>
          <p className="text-lg text-cy-gray-400 max-w-xl mx-auto mb-8">
            Our platform specialists will walk you through every module relevant to your organization — with your own data setup.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href={`/${l}/demo`} className="btn-primary-glow px-8 py-3.5 text-base">
              Book a Demo
              <Calendar className="w-4 h-4" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3.5 text-base">
              Contact Sales
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
