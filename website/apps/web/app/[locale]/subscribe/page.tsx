"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Check, ChevronRight, Building2, ShoppingCart, BarChart3,
  FlaskConical, Scan, Pill, Stethoscope, ArrowRight, ArrowLeft,
  Zap, Shield, Clock, CreditCard, Phone, Globe, Users,
  Star, Info, CheckCircle2, Calendar,
} from "lucide-react";

/* ─────────────────────────────────────────────
   PRODUCT CATALOGUE
───────────────────────────────────────────── */
type BillingCycle = "monthly" | "annual";

interface Edition {
  name: string;
  monthlyPrice: number | null; // null = custom
  desc: string;
  highlights: string[];
}

interface Product {
  id: string;
  name: string;
  tagline: string;
  icon: React.ElementType;
  color: string;
  border: string;
  bg: string;
  category: "healthcare" | "retail" | "erp";
  editions: Edition[];
  demoUrl: string;
}

const PRODUCTS: Product[] = [
  {
    id: "cymed-hospital",
    name: "CyMed Hospital",
    tagline: "Complete Hospital Information System",
    icon: Building2,
    color: "text-emerald-400",
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/10",
    category: "healthcare",
    demoUrl: "https://cymed.cy-com.com/hospital",
    editions: [
      { name: "Hospital Core", monthlyPrice: 2500, desc: "Up to 200 beds", highlights: ["ADT", "EMR", "Nursing", "Billing", "Lab integration"] },
      { name: "Hospital Advanced", monthlyPrice: 4500, desc: "200–500 beds", highlights: ["All Core", "OR Management", "ICU", "Blood Bank", "PACS"] },
      { name: "Hospital Enterprise", monthlyPrice: null, desc: "500+ beds / multi-facility", highlights: ["All Advanced", "Multi-facility", "Population health", "AI CDS", "24/7 SLA"] },
    ],
  },
  {
    id: "cymed-clinic",
    name: "CyMed Clinic",
    tagline: "Intelligent Outpatient Management",
    icon: Stethoscope,
    color: "text-teal-400",
    border: "border-teal-500/30",
    bg: "bg-teal-500/10",
    category: "healthcare",
    demoUrl: "https://cymed.cy-com.com/clinic",
    editions: [
      { name: "Clinic Starter", monthlyPrice: 299, desc: "Up to 5 providers", highlights: ["Core EMR", "Scheduling", "Billing", "Patient records"] },
      { name: "Clinic Professional", monthlyPrice: 599, desc: "Multi-specialty practice", highlights: ["All Starter", "Multi-specialty", "Lab/Pharmacy", "Analytics"] },
      { name: "Clinic Enterprise", monthlyPrice: null, desc: "Clinic chains & networks", highlights: ["All Professional", "Multi-branch", "API access", "24/7 SLA"] },
    ],
  },
  {
    id: "cymed-pharmacy",
    name: "CyMed Pharmacy",
    tagline: "Clinical Pharmacy Management",
    icon: Pill,
    color: "text-violet-400",
    border: "border-violet-500/30",
    bg: "bg-violet-500/10",
    category: "healthcare",
    demoUrl: "https://cymed.cy-com.com/pharmacy",
    editions: [
      { name: "Pharmacy Core", monthlyPrice: 199, desc: "Dispensing & inventory", highlights: ["Dispensing", "Inventory", "Drug interactions", "Reporting"] },
      { name: "Pharmacy Clinical", monthlyPrice: 399, desc: "Full clinical pharmacy", highlights: ["All Core", "Clinical review", "IV admixture", "Narcotic tracking"] },
    ],
  },
  {
    id: "cymed-laboratory",
    name: "CyMed Laboratory",
    tagline: "LIS with Auto-Verification",
    icon: FlaskConical,
    color: "text-cyan-400",
    border: "border-cyan-500/30",
    bg: "bg-cyan-500/10",
    category: "healthcare",
    demoUrl: "https://cymed.cy-com.com/laboratory",
    editions: [
      { name: "Lab Core", monthlyPrice: 299, desc: "Chemistry & hematology", highlights: ["Core catalog", "QC", "Analyzer interface", "FHIR results"] },
      { name: "Lab Full", monthlyPrice: 549, desc: "Full-service laboratory", highlights: ["All Core", "Microbiology", "Blood bank", "Auto-verification"] },
    ],
  },
  {
    id: "cymed-imaging",
    name: "CyMed Imaging",
    tagline: "Radiology & PACS Integration",
    icon: Scan,
    color: "text-sky-400",
    border: "border-sky-500/30",
    bg: "bg-sky-500/10",
    category: "healthcare",
    demoUrl: "https://cymed.cy-com.com/imaging",
    editions: [
      { name: "Imaging Core", monthlyPrice: 399, desc: "RIS + PACS connectivity", highlights: ["RIS workflow", "DICOM viewer", "Basic reporting"] },
      { name: "Imaging Advanced", monthlyPrice: 799, desc: "Full RIS + AI analysis", highlights: ["All Core", "AI analysis", "3D visualization", "Teleradiology"] },
    ],
  },
  {
    id: "cyshop",
    name: "CyShop",
    tagline: "Retail & Commerce Platform",
    icon: ShoppingCart,
    color: "text-orange-400",
    border: "border-orange-500/30",
    bg: "bg-orange-500/10",
    category: "retail",
    demoUrl: "https://cyshop.cy-com.com",
    editions: [
      { name: "Starter", monthlyPrice: 99, desc: "Single location, 3 terminals", highlights: ["Core POS", "Inventory", "Sales reports", "Customer accounts"] },
      { name: "Business", monthlyPrice: 299, desc: "Multi-location", highlights: ["All Starter", "Multi-branch", "Loyalty", "Staff management", "Analytics"] },
      { name: "Enterprise", monthlyPrice: null, desc: "Franchise & chain", highlights: ["All Business", "Franchise mgmt", "Central kitchen", "AI forecasting", "API"] },
    ],
  },
  {
    id: "cycom-erp",
    name: "CyCom ERP",
    tagline: "Unified Enterprise Resource Planning",
    icon: BarChart3,
    color: "text-blue-400",
    border: "border-blue-500/30",
    bg: "bg-blue-500/10",
    category: "erp",
    demoUrl: "https://health.cy-com.com",
    editions: [
      { name: "Business", monthlyPrice: 999, desc: "SME operations", highlights: ["Finance", "HR", "Inventory", "CRM", "Payroll"] },
      { name: "Enterprise", monthlyPrice: 2499, desc: "Large organization", highlights: ["All Business", "Manufacturing", "BI", "Advanced analytics", "API"] },
      { name: "Healthcare ERP", monthlyPrice: null, desc: "Bundled with CyMed", highlights: ["All Enterprise", "Clinical finance", "Medical inventory", "Healthcare HR"] },
    ],
  },
];

const ANNUAL_DISCOUNT = 0.20;
const TRIAL_DAYS = 14;

/* ─────────────────────────────────────────────
   TYPES
───────────────────────────────────────────── */
interface Selection {
  productId: string;
  editionIndex: number;
}

interface ContactInfo {
  fullName: string;
  workEmail: string;
  company: string;
  phone: string;
  country: string;
  companySize: string;
  intent: "trial" | "buy";
}

/* ─────────────────────────────────────────────
   STEP COMPONENTS
───────────────────────────────────────────── */
function StepBadge({ n, active, done }: { n: number; active: boolean; done: boolean }) {
  if (done) return (
    <span className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
      <Check className="w-4 h-4 text-white" />
    </span>
  );
  return (
    <span className={`w-8 h-8 rounded-full border-2 flex items-center justify-center flex-shrink-0 text-sm font-bold transition-colors ${active ? "border-cy-orange bg-cy-orange text-white" : "border-cy-glass-border text-cy-gray-400"}`}>
      {n}
    </span>
  );
}

/* ─────────────────────────────────────────────
   MAIN COMPONENT
───────────────────────────────────────────── */
export default function SubscribePage() {
  const [step, setStep] = useState(1);
  const [selections, setSelections] = useState<Selection[]>([]);
  const [billing, setBilling] = useState<BillingCycle>("annual");
  const [contact, setContact] = useState<ContactInfo>({
    fullName: "", workEmail: "", company: "", phone: "",
    country: "", companySize: "51-200", intent: "trial",
  });
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  /* helpers */
  const isSelected = (id: string) => selections.some((s) => s.productId === id);

  function toggleProduct(id: string) {
    setSelections((prev) =>
      prev.some((s) => s.productId === id)
        ? prev.filter((s) => s.productId !== id)
        : [...prev, { productId: id, editionIndex: 0 }]
    );
  }

  function setEdition(productId: string, idx: number) {
    setSelections((prev) => prev.map((s) => s.productId === productId ? { ...s, editionIndex: idx } : s));
  }

  function calcPrice(edition: Edition): number | null {
    if (edition.monthlyPrice === null) return null;
    return billing === "annual"
      ? Math.round(edition.monthlyPrice * (1 - ANNUAL_DISCOUNT))
      : edition.monthlyPrice;
  }

  function totalMonthly(): number | null {
    let total = 0;
    for (const sel of selections) {
      const product = PRODUCTS.find((p) => p.id === sel.productId)!;
      const edition = product.editions[sel.editionIndex]!;
      const price = calcPrice(edition);
      if (price === null) return null; // has custom pricing
      total += price;
    }
    return total;
  }

  const total = totalMonthly();
  const annualTotal = total !== null ? total * 12 : null;

  async function handleSubmit() {
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 1500));
    setSubmitted(true);
    setSubmitting(false);
  }

  const STEPS = ["Choose Products", "Select Editions", "Billing Cycle", "Review & Subscribe"];

  /* ── STEP 1: Product picker ── */
  const step1 = (
    <div>
      <h2 className="text-2xl font-heading font-semibold text-white mb-2">Which products do you need?</h2>
      <p className="text-cy-gray-400 mb-8">Select one or more. You can add more later from your portal.</p>

      {/* Healthcare */}
      <div className="mb-8">
        <p className="text-xs font-medium text-cy-gray-500 uppercase tracking-wider mb-3">Healthcare — CyMed</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {PRODUCTS.filter((p) => p.category === "healthcare").map((p) => {
            const Icon = p.icon;
            const sel = isSelected(p.id);
            return (
              <button
                key={p.id}
                onClick={() => toggleProduct(p.id)}
                className={`relative text-left p-4 rounded-xl border transition-all duration-200 ${sel ? `${p.border} ${p.bg}` : "border-cy-glass-border bg-cy-dark/40 hover:border-cy-glass-bg-hover"}`}
              >
                {sel && (
                  <span className="absolute top-3 right-3 w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center">
                    <Check className="w-3 h-3 text-white" />
                  </span>
                )}
                <div className={`w-8 h-8 rounded-lg ${p.bg} border ${p.border} flex items-center justify-center mb-3`}>
                  <Icon className={`w-4 h-4 ${p.color}`} />
                </div>
                <div className="font-heading font-semibold text-sm text-white mb-0.5">{p.name}</div>
                <div className="text-xs text-cy-gray-400">{p.tagline}</div>
                <div className="mt-3 text-xs text-cy-gray-500">
                  From <span className={`font-semibold ${p.color}`}>${p.editions[0]!.monthlyPrice?.toLocaleString() ?? "Custom"}/mo</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Retail */}
      <div className="mb-8">
        <p className="text-xs font-medium text-cy-gray-500 uppercase tracking-wider mb-3">Retail & Commerce</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {PRODUCTS.filter((p) => p.category === "retail").map((p) => {
            const Icon = p.icon;
            const sel = isSelected(p.id);
            return (
              <button
                key={p.id}
                onClick={() => toggleProduct(p.id)}
                className={`relative text-left p-4 rounded-xl border transition-all duration-200 ${sel ? `${p.border} ${p.bg}` : "border-cy-glass-border bg-cy-dark/40 hover:border-cy-glass-bg-hover"}`}
              >
                {sel && (
                  <span className="absolute top-3 right-3 w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center">
                    <Check className="w-3 h-3 text-white" />
                  </span>
                )}
                <div className={`w-8 h-8 rounded-lg ${p.bg} border ${p.border} flex items-center justify-center mb-3`}>
                  <Icon className={`w-4 h-4 ${p.color}`} />
                </div>
                <div className="font-heading font-semibold text-sm text-white mb-0.5">{p.name}</div>
                <div className="text-xs text-cy-gray-400">{p.tagline}</div>
                <div className="mt-3 text-xs text-cy-gray-500">
                  From <span className={`font-semibold ${p.color}`}>${p.editions[0]!.monthlyPrice?.toLocaleString() ?? "Custom"}/mo</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ERP */}
      <div className="mb-8">
        <p className="text-xs font-medium text-cy-gray-500 uppercase tracking-wider mb-3">Enterprise ERP</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {PRODUCTS.filter((p) => p.category === "erp").map((p) => {
            const Icon = p.icon;
            const sel = isSelected(p.id);
            return (
              <button
                key={p.id}
                onClick={() => toggleProduct(p.id)}
                className={`relative text-left p-4 rounded-xl border transition-all duration-200 ${sel ? `${p.border} ${p.bg}` : "border-cy-glass-border bg-cy-dark/40 hover:border-cy-glass-bg-hover"}`}
              >
                {sel && (
                  <span className="absolute top-3 right-3 w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center">
                    <Check className="w-3 h-3 text-white" />
                  </span>
                )}
                <div className={`w-8 h-8 rounded-lg ${p.bg} border ${p.border} flex items-center justify-center mb-3`}>
                  <Icon className={`w-4 h-4 ${p.color}`} />
                </div>
                <div className="font-heading font-semibold text-sm text-white mb-0.5">{p.name}</div>
                <div className="text-xs text-cy-gray-400">{p.tagline}</div>
                <div className="mt-3 text-xs text-cy-gray-500">
                  From <span className={`font-semibold ${p.color}`}>${p.editions[0]!.monthlyPrice?.toLocaleString() ?? "Custom"}/mo</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {selections.length > 0 && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <span className="text-sm text-emerald-300">
            {selections.length} product{selections.length > 1 ? "s" : ""} selected — {selections.map((s) => PRODUCTS.find((p) => p.id === s.productId)?.name).join(", ")}
          </span>
        </div>
      )}
    </div>
  );

  /* ── STEP 2: Edition picker ── */
  const step2 = (
    <div>
      <h2 className="text-2xl font-heading font-semibold text-white mb-2">Choose your edition</h2>
      <p className="text-cy-gray-400 mb-8">Pick the tier that fits your scale. Upgrade anytime from your portal.</p>
      <div className="space-y-8">
        {selections.map((sel) => {
          const product = PRODUCTS.find((p) => p.id === sel.productId)!;
          const Icon = product.icon;
          return (
            <div key={sel.productId}>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-7 h-7 rounded-lg ${product.bg} border ${product.border} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${product.color}`} />
                </div>
                <span className="font-heading font-semibold text-white">{product.name}</span>
              </div>
              <div className="grid sm:grid-cols-3 gap-3">
                {product.editions.map((edition, idx) => {
                  const price = edition.monthlyPrice !== null
                    ? (billing === "annual" ? Math.round(edition.monthlyPrice * (1 - ANNUAL_DISCOUNT)) : edition.monthlyPrice)
                    : null;
                  const chosen = sel.editionIndex === idx;
                  return (
                    <button
                      key={edition.name}
                      onClick={() => setEdition(sel.productId, idx)}
                      className={`text-left p-4 rounded-xl border transition-all duration-200 ${chosen ? `${product.border} ${product.bg}` : "border-cy-glass-border bg-cy-dark/40 hover:border-cy-glass-bg-hover"}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="font-heading font-semibold text-sm text-white">{edition.name}</span>
                        {chosen && <Check className={`w-4 h-4 ${product.color} flex-shrink-0`} />}
                      </div>
                      <div className="text-xs text-cy-gray-400 mb-3">{edition.desc}</div>
                      <div className={`text-lg font-heading font-bold ${product.color} mb-3`}>
                        {price !== null ? `$${price.toLocaleString()}/mo` : "Custom"}
                      </div>
                      <ul className="space-y-1">
                        {edition.highlights.map((h) => (
                          <li key={h} className="flex items-center gap-1.5 text-xs text-cy-gray-300">
                            <Check className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                            {h}
                          </li>
                        ))}
                      </ul>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  /* ── STEP 3: Billing cycle ── */
  const step3 = (
    <div>
      <h2 className="text-2xl font-heading font-semibold text-white mb-2">Billing cycle</h2>
      <p className="text-cy-gray-400 mb-8">Annual billing saves 20% across all products.</p>
      <div className="grid sm:grid-cols-2 gap-4 max-w-xl">
        {(["annual", "monthly"] as BillingCycle[]).map((cycle) => (
          <button
            key={cycle}
            onClick={() => setBilling(cycle)}
            className={`text-left p-6 rounded-xl border transition-all duration-200 ${billing === cycle ? "border-cy-orange bg-cy-orange/10" : "border-cy-glass-border bg-cy-dark/40 hover:border-cy-glass-bg-hover"}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="font-heading font-semibold text-white capitalize">{cycle}</div>
                {cycle === "annual" && (
                  <span className="inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    Save 20%
                  </span>
                )}
              </div>
              {billing === cycle && <Check className="w-5 h-5 text-cy-orange" />}
            </div>
            <div className="text-sm text-cy-gray-400">
              {cycle === "annual"
                ? "Billed once per year. Best value for long-term deployments."
                : "Billed each month. Flexible, cancel anytime."}
            </div>
          </button>
        ))}
      </div>

      {total !== null && (
        <div className="mt-8 p-5 rounded-xl glass-card max-w-xl">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-cy-gray-400">Monthly equivalent</span>
            <span className="text-white font-semibold">${total.toLocaleString()}/mo</span>
          </div>
          {billing === "annual" && (
            <>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-cy-gray-400">Annual total</span>
                <span className="text-white font-semibold">${(total * 12).toLocaleString()}/yr</span>
              </div>
              <div className="flex justify-between text-sm pt-2 border-t border-cy-glass-border">
                <span className="text-emerald-400">Annual saving vs monthly</span>
                <span className="text-emerald-400 font-semibold">
                  ${Math.round(total / (1 - ANNUAL_DISCOUNT) * 12 - total * 12).toLocaleString()}/yr
                </span>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );

  /* ── STEP 4: Review & subscribe ── */
  const step4 = (
    <div className="grid lg:grid-cols-5 gap-8">
      {/* Summary */}
      <div className="lg:col-span-3">
        <h2 className="text-2xl font-heading font-semibold text-white mb-6">Review & subscribe</h2>
        <div className="space-y-3 mb-6">
          {selections.map((sel) => {
            const product = PRODUCTS.find((p) => p.id === sel.productId)!;
            const edition = product.editions[sel.editionIndex]!;
            const price = calcPrice(edition);
            const Icon = product.icon;
            return (
              <div key={sel.productId} className="flex items-center gap-4 p-4 glass-card rounded-xl">
                <div className={`w-9 h-9 rounded-lg ${product.bg} border ${product.border} flex items-center justify-center flex-shrink-0`}>
                  <Icon className={`w-5 h-5 ${product.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-heading font-semibold text-sm text-white">{product.name}</div>
                  <div className="text-xs text-cy-gray-400">{edition.name}</div>
                </div>
                <div className="text-right flex-shrink-0">
                  {price !== null
                    ? <div className="font-semibold text-white">${price.toLocaleString()}<span className="text-xs text-cy-gray-400">/mo</span></div>
                    : <div className="text-cy-orange text-sm font-medium">Custom</div>}
                </div>
              </div>
            );
          })}
        </div>

        {total !== null ? (
          <div className="p-4 glass-card rounded-xl mb-6">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-cy-gray-400">Subtotal ({billing})</span>
              <span className="text-white">${total.toLocaleString()}/mo</span>
            </div>
            {billing === "annual" && annualTotal !== null && (
              <div className="flex justify-between text-sm pt-2 border-t border-cy-glass-border mt-2">
                <span className="text-white font-semibold">Annual total</span>
                <span className="text-white font-bold">${annualTotal.toLocaleString()}/yr</span>
              </div>
            )}
          </div>
        ) : (
          <div className="p-4 glass-card rounded-xl mb-6 border border-cy-orange/20">
            <div className="flex items-center gap-2 text-sm text-cy-orange">
              <Info className="w-4 h-4" />
              One or more products requires custom pricing. Our team will contact you with a quote.
            </div>
          </div>
        )}

        {/* Intent toggle */}
        <div className="mb-6">
          <p className="text-sm text-cy-gray-400 mb-3">How would you like to start?</p>
          <div className="grid grid-cols-2 gap-3">
            {(["trial", "buy"] as const).map((intent) => (
              <button
                key={intent}
                onClick={() => setContact((c) => ({ ...c, intent }))}
                className={`p-4 rounded-xl border text-left transition-all ${contact.intent === intent ? "border-cy-orange bg-cy-orange/10" : "border-cy-glass-border hover:border-cy-glass-bg-hover"}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {intent === "trial" ? <Clock className="w-4 h-4 text-emerald-400" /> : <CreditCard className="w-4 h-4 text-cy-orange" />}
                  <span className="font-semibold text-sm text-white">
                    {intent === "trial" ? `${TRIAL_DAYS}-Day Free Trial` : "Subscribe Now"}
                  </span>
                </div>
                <p className="text-xs text-cy-gray-400">
                  {intent === "trial" ? "Full access, no credit card required. Convert anytime." : "Start your subscription immediately with full production access."}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Contact form */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-cy-gray-400 mb-1.5">Full Name *</label>
              <input
                className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
                placeholder="Mohammad Al-Nsour"
                value={contact.fullName}
                onChange={(e) => setContact((c) => ({ ...c, fullName: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-cy-gray-400 mb-1.5">Work Email *</label>
              <input
                type="email"
                className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
                placeholder="you@company.com"
                value={contact.workEmail}
                onChange={(e) => setContact((c) => ({ ...c, workEmail: e.target.value }))}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-cy-gray-400 mb-1.5">Company *</label>
              <input
                className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
                placeholder="Your Organization"
                value={contact.company}
                onChange={(e) => setContact((c) => ({ ...c, company: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-cy-gray-400 mb-1.5">Phone</label>
              <input
                className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
                placeholder="+962 XX XXX XXXX"
                value={contact.phone}
                onChange={(e) => setContact((c) => ({ ...c, phone: e.target.value }))}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-cy-gray-400 mb-1.5">Country *</label>
              <select
                className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white outline-none focus:border-cy-orange border border-cy-glass-border transition-colors bg-cy-dark"
                value={contact.country}
                onChange={(e) => setContact((c) => ({ ...c, country: e.target.value }))}
              >
                <option value="">Select country</option>
                {["Jordan", "Saudi Arabia", "UAE", "Kuwait", "Qatar", "Bahrain", "Oman", "Egypt", "Iraq", "Lebanon", "Other"].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-cy-gray-400 mb-1.5">Company Size</label>
              <select
                className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white outline-none focus:border-cy-orange border border-cy-glass-border transition-colors bg-cy-dark"
                value={contact.companySize}
                onChange={(e) => setContact((c) => ({ ...c, companySize: e.target.value }))}
              >
                {["1-10", "11-50", "51-200", "201-500", "500+"].map((s) => (
                  <option key={s} value={s}>{s} employees</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!contact.fullName || !contact.workEmail || !contact.company || !contact.country || submitting}
          className="mt-6 w-full inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-sm bg-cy-orange hover:bg-cy-orange-light text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? (
            <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />{contact.intent === "trial" ? "Activating trial..." : "Processing..."}</>
          ) : (
            <>{contact.intent === "trial" ? `Start ${TRIAL_DAYS}-Day Free Trial` : "Subscribe & Get Started"}<ArrowRight className="w-4 h-4" /></>
          )}
        </button>

        <p className="text-xs text-cy-gray-500 mt-3 text-center">
          By subscribing you agree to our <Link href="/en/legal/terms" className="text-cy-orange hover:text-cy-orange-light">Terms of Service</Link> and <Link href="/en/legal/privacy" className="text-cy-orange hover:text-cy-orange-light">Privacy Policy</Link>.
        </p>
      </div>

      {/* Right panel — trust signals */}
      <div className="lg:col-span-2 space-y-4">
        <div className="glass-card p-5 rounded-xl">
          <h3 className="font-heading font-semibold text-white text-sm mb-4">What you get</h3>
          <ul className="space-y-3">
            {[
              { icon: Zap, text: "Instant trial activation" },
              { icon: Shield, text: "FHIR R4, ISO 27001, SOC 2" },
              { icon: Users, text: "Dedicated onboarding specialist" },
              { icon: Globe, text: "Arabic + English interface" },
              { icon: Clock, text: "99.9% uptime SLA (Enterprise)" },
              { icon: Phone, text: "24/7 support (Enterprise)" },
            ].map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm text-cy-gray-300">
                <Icon className="w-4 h-4 text-cy-orange flex-shrink-0" />
                {text}
              </li>
            ))}
          </ul>
        </div>

        <div className="glass-card p-5 rounded-xl">
          <h3 className="font-heading font-semibold text-white text-sm mb-4">Try before you buy</h3>
          <div className="space-y-3">
            {selections.map((sel) => {
              const product = PRODUCTS.find((p) => p.id === sel.productId)!;
              return (
                <a
                  key={sel.productId}
                  href={product.demoUrl}
                  target="_blank"
                  rel="noreferrer"
                  className={`flex items-center gap-2 text-xs ${product.color} hover:opacity-80 transition-opacity`}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-current flex-shrink-0" />
                  Try {product.name} live demo →
                </a>
              );
            })}
          </div>
        </div>

        <div className="glass-card p-5 rounded-xl">
          <div className="flex items-center gap-2 mb-3">
            {[...Array(5)].map((_, i) => <Star key={i} className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />)}
          </div>
          <p className="text-xs text-cy-gray-300 italic mb-3">
            &ldquo;CyberCom reduced our pharmacy dispensing errors by 94% in the first month. The FHIR integration with our EMR was seamless.&rdquo;
          </p>
          <div className="text-xs text-cy-gray-500">— Clinical Director, 350-bed hospital, Jordan</div>
        </div>

        <div className="glass-card p-5 rounded-xl border border-cy-orange/20">
          <div className="text-sm font-semibold text-white mb-1">Need a custom quote?</div>
          <p className="text-xs text-cy-gray-400 mb-3">Enterprise pricing, volume discounts, and healthcare bundle pricing available.</p>
          <Link href="/en/contact?interest=enterprise-sales" className="inline-flex items-center gap-1.5 text-xs text-cy-orange hover:text-cy-orange-light transition-colors">
            <Phone className="w-3.5 h-3.5" />
            Talk to sales
          </Link>
        </div>
      </div>
    </div>
  );

  /* ── SUCCESS STATE ── */
  if (submitted) {
    return (
      <div className="min-h-dvh pt-16 flex items-center justify-center">
        <div className="text-center max-w-lg px-4">
          <div className="w-20 h-20 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-10 h-10 text-emerald-400" />
          </div>
          <h1 className="text-3xl font-heading font-semibold text-white mb-3">
            {contact.intent === "trial" ? "Trial activated!" : "Subscription confirmed!"}
          </h1>
          <p className="text-cy-gray-400 mb-2">
            Check <span className="text-white font-medium">{contact.workEmail}</span> for your access credentials.
          </p>
          <p className="text-cy-gray-400 mb-8">
            Your onboarding specialist will contact you within 2 hours.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/en/portal" className="btn-primary px-6 py-3">
              Go to Customer Portal <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/en" className="btn-secondary px-6 py-3">Back to Home</Link>
          </div>
          <div className="mt-8 flex items-center justify-center gap-2 text-sm text-cy-gray-400">
            <Calendar className="w-4 h-4" />
            {contact.intent === "trial" ? `${TRIAL_DAYS}-day trial ends automatically — no charge unless you subscribe.` : "Your subscription is now active."}
          </div>
        </div>
      </div>
    );
  }

  const stepContent = [step1, step2, step3, step4];
  const canProceed = [
    selections.length > 0,
    true,
    true,
    !!(contact.fullName && contact.workEmail && contact.company && contact.country),
  ];

  return (
    <div className="min-h-dvh pt-16">
      {/* Header */}
      <div className="border-b border-cy-glass-border bg-cy-dark/60 sticky top-16 z-40 backdrop-blur-md">
        <div className="section-container py-4">
          <div className="flex items-center gap-2 sm:gap-4 overflow-x-auto">
            {STEPS.map((label, i) => {
              const n = i + 1;
              const active = step === n;
              const done = step > n;
              return (
                <div key={label} className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => done && setStep(n)}
                    className={`flex items-center gap-2 ${done ? "cursor-pointer opacity-100" : "cursor-default"} ${active ? "opacity-100" : "opacity-50"}`}
                  >
                    <StepBadge n={n} active={active} done={done} />
                    <span className={`text-sm font-medium hidden sm:block ${active ? "text-white" : "text-cy-gray-400"}`}>{label}</span>
                  </button>
                  {i < STEPS.length - 1 && <ChevronRight className="w-4 h-4 text-cy-gray-600 flex-shrink-0" />}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Step content */}
      <div className="section-container py-12">
        {stepContent[step - 1]}

        {/* Navigation */}
        {step < 4 && (
          <div className="flex items-center justify-between mt-10 pt-6 border-t border-cy-glass-border">
            <button
              onClick={() => setStep((s) => Math.max(1, s - 1))}
              disabled={step === 1}
              className="inline-flex items-center gap-2 btn-ghost px-5 py-2.5 text-sm disabled:opacity-30"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <button
              onClick={() => setStep((s) => s + 1)}
              disabled={!canProceed[step - 1]}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-sm bg-cy-orange hover:bg-cy-orange-light text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Continue <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
