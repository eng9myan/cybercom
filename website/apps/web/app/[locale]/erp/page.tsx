"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { useParams } from "next/navigation";
import {
  ArrowRight, Play, ExternalLink, Check, Brain,
  BarChart3, DollarSign, Users, Package, ShoppingCart, Cpu,
  FileText, Building2, Cog, PieChart, CreditCard, Warehouse,
  Globe, Star
} from "lucide-react";

const MODULES = [
  {
    icon: DollarSign,
    name: "Finance",
    slug: "cycom-finance",
    desc: "General ledger, cash flow, multi-currency, IFRS-compliant financial statements and budgeting.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["General Ledger", "Accounts Receivable", "Accounts Payable"],
  },
  {
    icon: FileText,
    name: "Accounting",
    slug: "cycom-accounting",
    desc: "Automated AP/AR, VAT & tax calculations, bank reconciliation, and local tax authority integration.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["AP Matching", "AR Invoicing", "VAT Filing"],
  },
  {
    icon: ShoppingCart,
    name: "Procurement",
    slug: "cycom-procurement",
    desc: "Purchase requisitions, vendor bidding, PO automation, three-way invoice matching, and supplier scorecards.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["Requisitions", "PO Management", "Supplier Portal"],
  },
  {
    icon: Warehouse,
    name: "Inventory",
    slug: "cycom-inventory",
    desc: "Multi-warehouse stock tracking, batch/serial numbers, FIFO/FEFO costing, and auto-replenishment.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["Multi-Warehouse", "Barcode Scanning", "Stock Transfers"],
  },
  {
    icon: Cpu,
    name: "Manufacturing",
    slug: "cycom-manufacturing",
    desc: "Bill of materials, MRP planning, work order release, production tracking, and QA inspections.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["BOM", "MRP", "Work Orders"],
  },
  {
    icon: Building2,
    name: "CRM",
    slug: "cycom-crm",
    desc: "Lead pipeline, quotation drafting, contract management, and customer support ticketing.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["Lead Pipeline", "Quotations", "Support Tickets"],
  },
  {
    icon: Users,
    name: "HR",
    slug: "cycom-hr",
    desc: "Employee records, org hierarchy mapping, performance evaluations, and self-service ESS portal.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["Employee Records", "Performance", "ESS Portal"],
  },
  {
    icon: CreditCard,
    name: "Payroll",
    slug: "cycom-payroll",
    desc: "Bilingual payroll, WPS export (GCC), social security, end-of-service, and pay slip delivery.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["Salary Processing", "WPS Export", "Pay Slips"],
  },
  {
    icon: Cog,
    name: "Assets",
    slug: "cycom-assets",
    desc: "Fixed asset registry, depreciation runs, maintenance scheduling, and mobile asset auditing.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["Asset Registry", "Depreciation", "Maintenance"],
  },
  {
    icon: Package,
    name: "POS",
    slug: "cycom-retail",
    desc: "Retail checkout, barcode scanning, loyalty rewards, offline mode, and shift closing with GL posting.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["Checkout", "Offline Mode", "Shift Reports"],
  },
  {
    icon: BarChart3,
    name: "BI",
    slug: "cycom-bi",
    desc: "Drag-and-drop analytics dashboards, KPI tiles, geographical maps, and scheduled report delivery.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["Dashboards", "Reporting", "Data Export"],
  },
  {
    icon: Globe,
    name: "Multi-Entity",
    slug: "cycom",
    desc: "Multi-currency, multi-language, multi-entity consolidation for groups and holding companies.",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    subModules: ["Consolidation", "Multi-Currency", "Inter-Company"],
  },
];

const AI_FEATURES = [
  { title: "AI Financial Forecasting", desc: "Cash flow predictions, revenue forecasting, and variance analysis powered by CyAI — advisory, never autonomous." },
  { title: "Procurement Intelligence", desc: "Supplier performance scoring, optimal reorder quantities, and early payment discount recommendations." },
  { title: "HR Analytics", desc: "Turnover risk prediction, workforce cost optimization, and recruitment pipeline analytics." },
  { title: "Inventory Optimization", desc: "Demand-driven replenishment, dead-stock identification, and multi-warehouse allocation recommendations." },
  { title: "Financial Anomaly Detection", desc: "Flags unusual journal entries, duplicate invoices, and suspicious payment patterns for compliance review." },
  { title: "BI Natural Language Query", desc: "Ask your data questions in plain Arabic or English. CyAI generates the analysis and visualization automatically." },
];

const COMPLIANCE = [
  "IFRS compliant financial reporting",
  "GAAP (US) support",
  "VAT & tax authority integration",
  "WPS (Wage Protection System — GCC)",
  "Jordan Social Security (SSC)",
  "Saudi ZATCA e-invoicing",
  "UAE FTA VAT reporting",
  "Multi-currency (50+ currencies)",
  "Bilingual (Arabic / English)",
  "RTL + LTR interface",
  "ISO 27001-ready security",
  "GDPR data privacy controls",
];

const EDITIONS = [
  { name: "Business", tagline: "For SMEs", features: ["Finance & Accounting", "HR & Payroll", "Inventory", "CRM", "Basic BI", "Standard support"] },
  { name: "Enterprise", tagline: "For large organizations", popular: true, features: ["All Business features", "Manufacturing & BOM", "Advanced analytics", "Multi-entity consolidation", "API access & webhooks", "CyAI intelligence", "Priority support"] },
  { name: "Healthcare ERP", tagline: "CyCom + CyMed integration", features: ["All Enterprise features", "CyMed billing integration", "Revenue cycle module", "Clinical supply chain", "ICD-11 & CPT coding", "FHIR financial data", "Dedicated CMIO support"] },
];

export default function ErpPage() {
  const params = useParams();
  const locale = (params?.locale as string) ?? "en";
  const l = locale;
  const ERP_URL = process.env.NEXT_PUBLIC_CYCOM_URL ?? "https://health.cy-com.com";
  const shouldReduce = useReducedMotion();

  const fadeUp = {
    hidden: { opacity: 0, y: shouldReduce ? 0 : 24 },
    visible: (delay: number) => ({
      opacity: 1, y: 0,
      transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] },
    }),
  };

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <section className="relative min-h-[85vh] flex items-center overflow-hidden" aria-labelledby="erp-heading">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="glow-orb w-[700px] h-[700px] -top-32 left-1/2 -translate-x-1/2 bg-blue-500/8 animate-glow-pulse" />
          <div className="glow-orb w-[500px] h-[500px] bottom-0 -left-32 bg-violet-500/5" />
          <div className="absolute inset-0 opacity-[0.025]" style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)`, backgroundSize: "64px 64px" }} />
        </div>
        <div className="section-container relative z-10">
          <div className="max-w-4xl">
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-blue-500/20 bg-blue-500/5 mb-8">
              <PieChart className="w-3.5 h-3.5 text-blue-400" aria-hidden="true" />
              <span className="text-xs font-medium text-blue-400 tracking-wider uppercase">CyCom ERP · Enterprise Resource Planning</span>
            </motion.div>
            <motion.h1 id="erp-heading" variants={fadeUp} initial="hidden" animate="visible" custom={0.1} className="text-5xl sm:text-6xl lg:text-7xl font-heading font-semibold text-white mb-6 leading-tight">
              One ERP.{" "}<br />
              <span className="text-blue-400">Every Module.</span>{" "}<br />
              <span className="text-gradient-orange">One Truth.</span>
            </motion.h1>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.2} className="text-xl text-cy-gray-400 leading-relaxed mb-4 max-w-2xl">
              CyCom ERP unifies Finance, Procurement, Inventory, Manufacturing, CRM, HR, Payroll, Assets, POS, and BI in a single IFRS-compliant, bilingual enterprise platform.
            </motion.p>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.25} className="text-sm text-cy-gray-400 mb-8 max-w-2xl">
              Integrated with CyMed for healthcare revenue cycle and CyShop for retail operations through the CyberCom Platform.
            </motion.p>
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0.3} className="flex flex-wrap gap-3">
              <a href={ERP_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl font-medium text-sm bg-blue-500 hover:bg-blue-400 text-white transition-all duration-200 cursor-pointer">
                <Play className="w-4 h-4" aria-hidden="true" />
                Launch ERP Dashboard
                <ExternalLink className="w-3.5 h-3.5 opacity-70" aria-hidden="true" />
              </a>
              <Link href={`/${l}/demo?product=cycom`} className="btn-secondary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                Request a Demo
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Modules Grid */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="modules-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="modules-heading" className="text-3xl font-heading font-semibold text-white mb-4">12 Integrated Modules</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">Every module shares the same database, chart of accounts, and user management. No integrations. No data silos. No duplicate entry.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {MODULES.map((mod, i) => (
              <motion.div
                key={mod.name}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i * 0.04}
              >
                <Link
                  href={`/${l}/products/${mod.slug}`}
                  className={`glass-card rounded-xl p-5 border ${mod.bg} flex flex-col hover:scale-[1.01] transition-all duration-200 cursor-pointer group h-full`}
                >
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center border mb-3 ${mod.bg}`}>
                    <mod.icon className={`w-4.5 h-4.5 ${mod.color}`} aria-hidden="true" />
                  </div>
                  <h3 className={`text-sm font-heading font-semibold ${mod.color} mb-1.5 group-hover:underline`}>{mod.name}</h3>
                  <p className="text-xs text-cy-gray-400 leading-relaxed mb-3 flex-1">{mod.desc}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {mod.subModules.map((sm) => (
                      <span key={sm} className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/20">{sm}</span>
                    ))}
                  </div>
                  <span className={`text-xs ${mod.color} flex items-center gap-1 mt-3 font-medium`}>
                    Explore module
                    <ArrowRight className="w-3 h-3 rtl:rotate-180 group-hover:translate-x-1 transition-transform" aria-hidden="true" />
                  </span>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Intelligence */}
      <section className="py-20" aria-labelledby="ai-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-pink-500/20 bg-pink-500/5 mb-4">
              <Brain className="w-3.5 h-3.5 text-pink-400" aria-hidden="true" />
              <span className="text-xs font-medium text-pink-400 tracking-wider uppercase">Powered by CyAI</span>
            </div>
            <h2 id="ai-heading" className="text-3xl font-heading font-semibold text-white mb-4">AI-Powered Enterprise Intelligence</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">CyCom ERP integrates CyAI for advisory intelligence across finance, procurement, HR, and operations. Advisory-only — human approval always required.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {AI_FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i * 0.05}
                className="glass-card rounded-xl p-6 border border-pink-500/10 bg-pink-500/3"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="w-4 h-4 text-pink-400 flex-shrink-0" aria-hidden="true" />
                  <h3 className="text-sm font-heading font-semibold text-pink-400">{f.title}</h3>
                </div>
                <p className="text-xs text-cy-gray-400 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="compliance-heading">
        <div className="section-container">
          <div className="text-center mb-12">
            <h2 id="compliance-heading" className="text-3xl font-heading font-semibold text-white mb-4">Compliance & Standards</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">Built for the Middle East and global markets from the ground up. Compliance is an invariant, not a checkbox.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-4xl mx-auto">
            {COMPLIANCE.map((c) => (
              <div key={c} className="flex items-center gap-3 glass-card rounded-lg p-4">
                <div className="w-5 h-5 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
                  <Check className="w-3 h-3 text-blue-400" aria-hidden="true" />
                </div>
                <span className="text-sm text-cy-gray-200">{c}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Editions */}
      <section className="py-20" aria-labelledby="editions-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="editions-heading" className="text-3xl font-heading font-semibold text-white mb-4">Choose Your Edition</h2>
            <p className="text-cy-gray-400 max-w-xl mx-auto">Start with the modules you need. Activate more as you grow. All editions share the same core platform.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {EDITIONS.map((ed) => (
              <div key={ed.name} className={`glass-card rounded-2xl p-7 flex flex-col ${ed.popular ? "border-blue-500/40 ring-1 ring-blue-500/20" : ""}`}>
                {ed.popular && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-xs font-medium text-blue-400 mb-4 self-start">
                    <Star className="w-3 h-3 fill-blue-400" aria-hidden="true" />
                    Most Popular
                  </div>
                )}
                <h3 className="text-xl font-heading font-semibold text-white mb-1">{ed.name}</h3>
                <p className="text-xs text-cy-gray-400 mb-5">{ed.tagline}</p>
                <ul className="space-y-2.5 mb-7 flex-1" aria-label={`${ed.name} plan features`}>
                  {ed.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5">
                      <Check className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                      <span className="text-sm text-cy-gray-200">{f}</span>
                    </li>
                  ))}
                </ul>
                <Link href={`/${l}/demo?product=cycom`} className={`w-full text-center py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${ed.popular ? "bg-blue-500 hover:bg-blue-400 text-white" : "btn-secondary"}`}>
                  Get Started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="erp-cta-heading">
        <div className="section-container text-center max-w-3xl mx-auto">
          <h2 id="erp-cta-heading" className="text-3xl font-heading font-semibold text-white mb-4">Ready to Unify Your Enterprise?</h2>
          <p className="text-cy-gray-400 mb-8">See the full CyCom ERP platform in action. Our team will configure a demo to match your industry and business size.</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a href={ERP_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 px-8 py-3 rounded-xl font-medium text-sm bg-blue-500 hover:bg-blue-400 text-white transition-all duration-200 cursor-pointer">
              <Play className="w-4 h-4" aria-hidden="true" />
              Launch ERP Dashboard
              <ExternalLink className="w-3.5 h-3.5 opacity-70" aria-hidden="true" />
            </a>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3 text-sm">
              Contact Sales
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
