"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Star, Quote } from "lucide-react";

const CUSTOMERS = [
  { name: "King Abdullah University Hospital", country: "Jordan", abbr: "KAUH", color: "#34d399" },
  { name: "Saudi German Hospital Group",       country: "KSA",    abbr: "SGH",  color: "#60a5fa" },
  { name: "Al Noor Specialist Clinics",        country: "UAE",    abbr: "ANS",  color: "#f472b6" },
  { name: "Gulf Diagnostic Imaging Center",    country: "Kuwait", abbr: "GDIC", color: "#fbbf24" },
  { name: "Jordan Medical Laboratory",         country: "Jordan", abbr: "JML",  color: "#a78bfa" },
  { name: "City Mall Retail Group",            country: "Jordan", abbr: "CMR",  color: "#ed6c00" },
  { name: "AlAmeen Pharmacy Network",          country: "UAE",    abbr: "APN",  color: "#59c3e1" },
  { name: "Riyadh Digital Health Initiative",  country: "KSA",    abbr: "RDHI", color: "#818cf8" },
];

const TESTIMONIALS = [
  {
    quote: "CyMed Hospital replaced three separate systems in one deployment. FHIR integration with our labs was live in under two weeks. The operational impact was immediate.",
    author: "Dr. Rania Khalil",
    title: "Chief Medical Officer",
    org: "King Abdullah University Hospital",
    product: "CyMed Hospital",
    color: "#34d399",
    stars: 5,
  },
  {
    quote: "The CyCom ERP payroll runs WPS-compliant payments across four countries without manual reconciliation. Our finance team went from 3 days to 4 hours per cycle.",
    author: "Mr. Faisal Al-Harbi",
    title: "CFO",
    org: "Saudi German Hospital Group",
    product: "CyCom ERP",
    color: "#60a5fa",
    stars: 5,
  },
  {
    quote: "CyShop handled our Ramadan peak — 8x normal volume — with zero downtime. The AI inventory forecasting prevented three stockouts we would never have caught.",
    author: "Mr. Khalid Nawas",
    title: "Operations Director",
    org: "City Mall Retail Group",
    product: "CyShop",
    color: "#ed6c00",
    stars: 5,
  },
];

export function SocialProof() {
  const shouldReduce = useReducedMotion();

  const fadeUp = (delay = 0) => ({
    initial: { opacity: 0, y: shouldReduce ? 0 : 24 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, amount: 0.2 },
    transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
  });

  return (
    <section className="py-24 relative overflow-hidden" aria-labelledby="social-proof-heading">
      {/* bg */}
      <div
        className="absolute inset-0 pointer-events-none"
        aria-hidden="true"
        style={{
          background: "radial-gradient(ellipse at 50% 100%, rgba(237,108,0,0.04) 0%, transparent 70%)",
        }}
      />

      <div className="section-container">
        {/* Header */}
        <motion.div {...fadeUp()} className="text-center mb-16">
          <p className="text-xs font-semibold uppercase tracking-widest text-cy-orange mb-3">
            Trusted by Leaders
          </p>
          <h2 id="social-proof-heading" className="text-3xl lg:text-4xl font-heading font-semibold text-white mb-4">
            Real outcomes, real organizations
          </h2>
          <p className="text-white/45 text-lg max-w-xl mx-auto leading-relaxed">
            Healthcare systems, retail groups, and enterprise teams across the GCC run on CyberCom.
          </p>
        </motion.div>

        {/* Customer logo grid */}
        <motion.div {...fadeUp(0.1)} className="mb-16">
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {CUSTOMERS.map((c) => (
              <motion.div
                key={c.abbr}
                whileHover={{ y: -2, scale: 1.03 }}
                transition={{ type: "spring", stiffness: 400, damping: 20 }}
                className="group rounded-xl p-4 text-center cursor-default"
                style={{
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.06)",
                }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold mx-auto mb-2 transition-all duration-300 group-hover:scale-110"
                  style={{
                    background: `${c.color}18`,
                    border: `1px solid ${c.color}30`,
                    color: c.color,
                  }}
                >
                  {c.abbr}
                </div>
                <p className="text-[10px] text-white/40 leading-tight">{c.country}</p>
              </motion.div>
            ))}
          </div>
          <p className="text-center text-xs text-white/25 mt-4">
            +30 organizations across Jordan, KSA, UAE, Kuwait, Qatar
          </p>
        </motion.div>

        {/* Section divider */}
        <div className="section-divider mb-16" />

        {/* Testimonials */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {TESTIMONIALS.map((t, i) => (
            <motion.div
              key={t.author}
              {...fadeUp(i * 0.1)}
              className="relative rounded-2xl p-7 flex flex-col"
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.07)",
              }}
            >
              {/* Accent top bar */}
              <div
                className="absolute top-0 inset-x-0 h-0.5 rounded-t-2xl opacity-60"
                style={{ background: `linear-gradient(to right, transparent, ${t.color}80, transparent)` }}
              />

              {/* Stars */}
              <div className="flex gap-1 mb-4">
                {Array.from({ length: t.stars }).map((_, si) => (
                  <Star key={si} className="w-3.5 h-3.5 fill-current" style={{ color: t.color }} />
                ))}
              </div>

              {/* Quote icon */}
              <Quote className="w-6 h-6 mb-3 opacity-20" style={{ color: t.color }} />

              {/* Text */}
              <blockquote className="text-white/65 text-sm leading-relaxed flex-1 mb-6">
                {t.quote}
              </blockquote>

              {/* Attribution */}
              <div className="flex items-center gap-3 pt-5 border-t border-white/[0.06]">
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style={{ background: `${t.color}20`, color: t.color }}
                >
                  {t.author.split(" ").map((n) => n[0]).slice(0, 2).join("")}
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-white truncate">{t.author}</div>
                  <div className="text-[11px] text-white/40 truncate">{t.title} · {t.org}</div>
                </div>
                <span
                  className="ml-auto text-[10px] font-medium px-2 py-0.5 rounded-full flex-shrink-0"
                  style={{ background: `${t.color}15`, color: t.color, border: `1px solid ${t.color}25` }}
                >
                  {t.product}
                </span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Trust badges */}
        <motion.div {...fadeUp(0.4)} className="mt-14 flex flex-wrap items-center justify-center gap-6">
          {[
            { label: "99.9% Uptime SLA", icon: "⬆" },
            { label: "14-Day Free Trial",  icon: "✓" },
            { label: "No lock-in contracts", icon: "◎" },
            { label: "Dedicated onboarding", icon: "★" },
            { label: "24/7 Arabic + English support", icon: "◈" },
          ].map((b) => (
            <div key={b.label} className="flex items-center gap-2 text-sm text-white/40">
              <span className="text-cy-orange text-xs">{b.icon}</span>
              {b.label}
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
