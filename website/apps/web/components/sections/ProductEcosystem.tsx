"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Zap, Shield, Globe, Database, Cpu, Users, ShoppingCart, Activity } from "lucide-react";

interface ProductEcosystemProps {
  locale: Locale;
}

const PRIMARY_PRODUCTS = [
  {
    id: "cymed",
    name: "CyMed",
    slug: "cymed-clinic",
    category: "Healthcare",
    tagline: "FHIR-native clinical platform for hospitals, clinics, labs, and pharmacies",
    accent: "#34d399",
    accentBg: "rgba(52,211,153,0.08)",
    accentBorder: "rgba(52,211,153,0.2)",
    icon: Activity,
    stats: [
      { value: "9", label: "Clinical Modules" },
      { value: "FHIR R4", label: "Native Standard" },
      { value: "ICD-11", label: "Coding" },
    ],
    products: ["Hospital", "Clinic", "Laboratory", "Imaging", "Pharmacy", "Patient Portal", "Provider Portal", "Revenue Cycle", "Population Health"],
    badge: "Most Popular",
    size: "large",
  },
  {
    id: "cyshop",
    name: "CyShop",
    slug: "cyshop",
    category: "Retail & Commerce",
    tagline: "Omnichannel POS and commerce platform for restaurants, retail, grocery, and F&B",
    accent: "#ed6c00",
    accentBg: "rgba(237,108,0,0.08)",
    accentBorder: "rgba(237,108,0,0.2)",
    icon: ShoppingCart,
    stats: [
      { value: "8", label: "Business Types" },
      { value: "AI", label: "Forecasting" },
      { value: "PCI-DSS", label: "Compliance" },
    ],
    products: ["Retail POS", "Restaurant", "Bakery", "Coffee Shop", "Fast Food", "Grocery", "Supermarket", "Convenience"],
    size: "medium",
  },
  {
    id: "cycom",
    name: "CyCom ERP",
    slug: "cycom",
    category: "Enterprise ERP",
    tagline: "Complete ERP with finance, HR, procurement, manufacturing, and BI — built for the Arab world",
    accent: "#60a5fa",
    accentBg: "rgba(96,165,250,0.08)",
    accentBorder: "rgba(96,165,250,0.2)",
    icon: Database,
    stats: [
      { value: "14+", label: "ERP Modules" },
      { value: "IFRS", label: "+ GAAP + WPS" },
      { value: "ZATCA", label: "e-Invoice" },
    ],
    products: ["Finance", "Accounting", "Procurement", "Inventory", "HR", "Payroll", "CRM", "Manufacturing", "Assets", "POS", "BI", "Projects"],
    size: "medium",
  },
] as const;

const PLATFORM_PRODUCTS = [
  {
    id: "cyidentity",
    name: "CyIdentity",
    slug: "cyidentity",
    tagline: "Zero Trust SSO · OAuth 2.1 · Passkeys · RBAC",
    accent: "#a78bfa",
    icon: Shield,
  },
  {
    id: "cyai",
    name: "CyAI",
    slug: "cyai",
    tagline: "Clinical AI · NLP · Predictive Analytics · Computer Vision",
    accent: "#f472b6",
    icon: Cpu,
  },
  {
    id: "cyintegrationhub",
    name: "CyIntegrationHub",
    slug: "cyintegrationhub",
    tagline: "FHIR · HL7 v2/v3 · DICOM · REST · SOAP · Kafka",
    accent: "#59c3e1",
    icon: Zap,
  },
  {
    id: "cydata",
    name: "CyData",
    slug: "cydata",
    tagline: "Lakehouse · BI Dashboards · Population Health · Data Governance",
    accent: "#34d399",
    icon: Database,
  },
  {
    id: "cygov",
    name: "CyGov",
    slug: "cygov",
    tagline: "Citizen Services · National Registries · E-Permits · Digital ID",
    accent: "#fbbf24",
    icon: Globe,
  },
  {
    id: "cycitizen",
    name: "CyCitizen",
    slug: "cycitizen",
    tagline: "Citizen Portal · Digital Wallet · National Identity · Gov Services",
    accent: "#818cf8",
    icon: Users,
  },
];

export function ProductEcosystem({ locale }: ProductEcosystemProps) {
  const shouldReduce = useReducedMotion();

  const fadeUp = (delay: number) => ({
    initial: { opacity: 0, y: shouldReduce ? 0 : 20 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, amount: 0.1 },
    transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
  });

  return (
    <section className="py-32 relative" aria-labelledby="ecosystem-heading">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div
          className="absolute top-0 right-0 w-[50vw] h-[60vh] rounded-full"
          style={{
            background: "radial-gradient(ellipse, rgba(89,195,225,0.05) 0%, transparent 70%)",
            filter: "blur(80px)",
          }}
        />
        <div
          className="absolute bottom-0 left-0 w-[40vw] h-[50vh] rounded-full"
          style={{
            background: "radial-gradient(ellipse, rgba(237,108,0,0.04) 0%, transparent 70%)",
            filter: "blur(80px)",
          }}
        />
      </div>

      <div className="section-container relative z-10">

        {/* ── Section header ── */}
        <motion.div {...fadeUp(0)} className="text-center mb-16">
          <p className="text-sm font-semibold text-cy-orange mb-3 uppercase tracking-widest">Platform Suite</p>
          <h2 id="ecosystem-heading" className="text-4xl lg:text-5xl font-heading font-semibold text-white mb-5">
            Three Platforms.<br />
            <span className="text-gradient-aurora">One Ecosystem.</span>
          </h2>
          <p className="text-lg text-white/45 max-w-2xl mx-auto leading-relaxed">
            CyMed, CyShop, and CyCom ERP share one identity layer, one integration hub,
            and one audit trail — with purpose-built AI for every vertical.
          </p>
        </motion.div>

        {/* ── Primary bento grid ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">

          {/* CyMed — large card */}
          {PRIMARY_PRODUCTS.map((p, i) => {
            const Icon = p.icon;
            return (
              <motion.div
                key={p.id}
                {...fadeUp(i * 0.1)}
                className={p.size === "large" ? "lg:col-span-1 lg:row-span-1" : ""}
              >
                <Link
                  href={p.slug === "cyshop" ? `/${locale}/cyshop` : p.slug === "cycom" ? `/${locale}/erp` : `/${locale}/products/${p.slug}`}
                  className="bento-card block p-8 h-full group"
                  style={{ borderColor: p.accentBorder }}
                  aria-label={`${p.name} — ${p.category}`}
                >
                  {/* Top row */}
                  <div className="flex items-start justify-between mb-6">
                    <div
                      className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0"
                      style={{ background: p.accentBg, border: `1px solid ${p.accentBorder}` }}
                    >
                      <Icon className="w-7 h-7" style={{ color: p.accent }} aria-hidden="true" />
                    </div>
                    {"badge" in p && (
                      <span
                        className="text-xs font-semibold px-2.5 py-1 rounded-full"
                        style={{ color: p.accent, background: p.accentBg, border: `1px solid ${p.accentBorder}` }}
                      >
                        {p.badge}
                      </span>
                    )}
                  </div>

                  {/* Category label */}
                  <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: p.accent }}>
                    {p.category}
                  </p>

                  {/* Name */}
                  <h3 className="text-2xl font-heading font-bold text-white mb-3">
                    {p.name}
                  </h3>

                  {/* Tagline */}
                  <p className="text-sm text-white/50 leading-relaxed mb-6">
                    {p.tagline}
                  </p>

                  {/* Stats row */}
                  <div className="grid grid-cols-3 gap-3 mb-6">
                    {p.stats.map(s => (
                      <div
                        key={s.label}
                        className="rounded-xl p-2.5 text-center"
                        style={{ background: p.accentBg, border: `1px solid ${p.accentBorder}` }}
                      >
                        <div className="font-heading font-bold text-sm" style={{ color: p.accent }}>{s.value}</div>
                        <div className="text-[10px] text-white/40 mt-0.5">{s.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Module pills */}
                  <div className="flex flex-wrap gap-1.5">
                    {p.products.slice(0, 6).map(mod => (
                      <span
                        key={mod}
                        className="text-xs px-2.5 py-1 rounded-lg text-white/50"
                        style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
                      >
                        {mod}
                      </span>
                    ))}
                    {p.products.length > 6 && (
                      <span className="text-xs px-2.5 py-1 rounded-lg text-white/30" style={{ background: "rgba(255,255,255,0.02)" }}>
                        +{p.products.length - 6} more
                      </span>
                    )}
                  </div>

                  {/* Explore CTA */}
                  <div className="flex items-center gap-2 mt-6 pt-5 border-t border-white/[0.07]">
                    <span className="text-sm font-medium" style={{ color: p.accent }}>Explore {p.name}</span>
                    <ArrowRight
                      className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1 rtl:rotate-180"
                      style={{ color: p.accent }}
                      aria-hidden="true"
                    />
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>

        {/* ── Section divider with label ── */}
        <motion.div {...fadeUp(0.4)} className="relative my-12 flex items-center gap-6">
          <div className="section-divider flex-1" />
          <span className="text-xs font-semibold uppercase tracking-widest text-white/30 flex-shrink-0">
            Platform Infrastructure
          </span>
          <div className="section-divider flex-1" />
        </motion.div>

        {/* ── Platform grid ── */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {PLATFORM_PRODUCTS.map((p, i) => {
            const Icon = p.icon;
            return (
              <motion.div key={p.id} {...fadeUp(0.45 + i * 0.05)}>
                <Link
                  href={`/${locale}/products/${p.slug}`}
                  className="group block rounded-2xl p-4 transition-all duration-300 hover:-translate-y-1"
                  style={{
                    background: "rgba(255,255,255,0.03)",
                    border: "1px solid rgba(255,255,255,0.06)",
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = `${p.accent}33`;
                    (e.currentTarget as HTMLElement).style.boxShadow = `0 0 24px ${p.accent}10`;
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.06)";
                    (e.currentTarget as HTMLElement).style.boxShadow = "none";
                  }}
                  aria-label={`${p.name} — ${p.tagline}`}
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                    style={{ background: `${p.accent}15` }}
                  >
                    <Icon className="w-4 h-4" style={{ color: p.accent }} aria-hidden="true" />
                  </div>
                  <div className="text-sm font-semibold text-white mb-1.5">{p.name}</div>
                  <p className="text-[11px] text-white/35 leading-relaxed">{p.tagline.split(" · ")[0]}</p>
                </Link>
              </motion.div>
            );
          })}
        </div>

        {/* ── Bottom CTA ── */}
        <motion.div {...fadeUp(0.7)} className="text-center mt-14">
          <Link href={`/${locale}/products`} className="btn-secondary px-8 py-3">
            View all Products
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
