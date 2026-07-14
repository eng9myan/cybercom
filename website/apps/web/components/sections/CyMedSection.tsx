"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Check } from "lucide-react";

interface CyMedSectionProps {
  locale: Locale;
}

const CYMED_PRODUCTS = [
  { name: "CyMed Clinic", slug: "cymed-clinic", desc: "Outpatient management, scheduling, EMR" },
  { name: "CyMed Hospital", slug: "cymed-hospital", desc: "Complete inpatient & operations" },
  { name: "CyMed Laboratory", slug: "cymed-laboratory", desc: "LIS with auto-verification & QC" },
  { name: "CyMed Imaging", slug: "cymed-imaging", desc: "RIS/DICOM/PACS integration" },
  { name: "CyMed Pharmacy", slug: "cymed-pharmacy", desc: "Clinical dispensing & inventory" },
  { name: "CyMed Patient Portal", slug: "cymed-patient-portal", desc: "Patient engagement & scheduling" },
  { name: "CyMed Provider Portal", slug: "cymed-provider-portal", desc: "Clinical workforce tools" },
  { name: "CyMed Revenue Cycle", slug: "cymed-revenue-cycle", desc: "Billing, coding, collections" },
  { name: "CyMed Population Health", slug: "cymed-population-health", desc: "Analytics & care programs" },
];

const BADGES = [
  "ICD-11 Native",
  "FHIR R4/R5",
  "SNOMED Ready",
  "LOINC Ready",
  "AI Powered",
  "Multi-Tenant",
  "Cloud Native",
  "HL7 v2/v3",
];

export function CyMedSection({ locale }: CyMedSectionProps) {
  const shouldReduce = useReducedMotion();

  return (
    <section className="py-32 relative overflow-hidden" aria-labelledby="cymed-heading">
      {/* Background gradient */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div className="glow-orb w-[700px] h-[700px] -bottom-32 -left-32 bg-emerald-500/5" />
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/5 via-transparent to-transparent" />
      </div>

      <div className="section-container relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: Content */}
          <motion.div
            initial={{ opacity: 0, x: shouldReduce ? 0 : -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.1 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 mb-6">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
              <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">Healthcare Platform</span>
            </div>

            <h2 id="cymed-heading" className="text-4xl lg:text-5xl font-heading font-semibold text-white mb-4">
              CyMed — Intelligent{" "}
              <span className="text-gradient-orange">Healthcare</span>{" "}
              Platform
            </h2>

            <p className="text-lg text-cy-gray-400 mb-8 leading-relaxed">
              FHIR-native, ICD-11 ready clinical platform engineered for hospitals, clinics, laboratories, pharmacies,
              and patient engagement — with built-in AI and population health analytics.
            </p>

            {/* Compliance badges */}
            <div className="flex flex-wrap gap-2 mb-8" aria-label="Technical standards">
              {BADGES.map((badge) => (
                <span
                  key={badge}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-emerald-500/15 bg-emerald-500/5 text-xs text-emerald-300 font-medium"
                >
                  <Check className="w-3 h-3" aria-hidden="true" />
                  {badge}
                </span>
              ))}
            </div>

            <div className="flex flex-wrap gap-3">
              <Link href={`/${locale}/products/cymed-hospital`} className="btn-primary">
                Explore CyMed Hospital
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${locale}/demo?product=cymed`} className="btn-secondary">
                Request Demo
              </Link>
            </div>
          </motion.div>

          {/* Right: Product grid */}
          <motion.div
            initial={{ opacity: 0, x: shouldReduce ? 0 : 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.1 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1], delay: 0.1 }}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {CYMED_PRODUCTS.map((product, i) => (
                <motion.div
                  key={product.slug}
                  initial={{ opacity: 0, y: shouldReduce ? 0 : 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.1 }}
                  transition={{ duration: 0.35, delay: 0.1 + i * 0.04 }}
                >
                  <Link
                    href={`/${locale}/products/${product.slug}`}
                    className="glass-card block p-4 rounded-xl border border-cy-glass-border hover:border-emerald-500/25 group transition-all duration-300"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                        <div className="w-3 h-3 rounded-sm bg-emerald-400" aria-hidden="true" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-white group-hover:text-emerald-300 transition-colors duration-150">
                          {product.name}
                        </div>
                        <div className="text-xs text-cy-gray-400 mt-0.5 leading-relaxed">
                          {product.desc}
                        </div>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
