"use client";

import { motion, useReducedMotion } from "framer-motion";
import { type Locale } from "@/lib/i18n";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface GlobalReachProps {
  locale: Locale;
}

const STATS = [
  { value: "9", label: "Integrated Platforms", desc: "Covering healthcare through citizen services" },
  { value: "FHIR", label: "Native Standard", desc: "R4 & R5 — full compliance built-in" },
  { value: "ICD-11", label: "Clinical Coding", desc: "WHO standard, natively implemented" },
  { value: "OAuth 2.1", label: "Security Standard", desc: "PKCE, passkeys, Zero Trust architecture" },
  { value: "Multi-Tenant", label: "Architecture", desc: "Cloud, hybrid, on-premise deployment" },
  { value: "24/7", label: "Platform Availability", desc: "Enterprise SLA with dedicated support" },
];

const PLATFORMS = [
  { name: "AWS", category: "Cloud" },
  { name: "Azure", category: "Cloud" },
  { name: "GCP", category: "Cloud" },
  { name: "On-Premise", category: "Deployment" },
  { name: "Hybrid", category: "Deployment" },
  { name: "Air-Gapped", category: "Deployment" },
];

export function GlobalReach({ locale }: GlobalReachProps) {
  const shouldReduce = useReducedMotion();

  return (
    <section className="py-32 relative bg-cy-dark/20" aria-labelledby="reach-heading">
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div className="glow-orb w-[600px] h-[600px] -bottom-32 right-0 bg-cy-orange/5" />
      </div>

      <div className="section-container relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: shouldReduce ? 0 : 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">Platform Capabilities</p>
          <h2 id="reach-heading" className="text-4xl lg:text-5xl font-heading font-semibold text-white mb-4">
            Enterprise-Grade, Globally Ready
          </h2>
          <p className="text-lg text-cy-gray-400 max-w-2xl mx-auto">
            Built on open standards. Deployable on any cloud or on-premise infrastructure.
            Trusted for mission-critical healthcare and government operations.
          </p>
        </motion.div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-16">
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: shouldReduce ? 0 : 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.1 }}
              transition={{ duration: 0.4, delay: i * 0.06 }}
              className="glass-card p-6 rounded-2xl"
            >
              <div className="text-2xl font-heading font-bold text-gradient mb-1">{stat.value}</div>
              <div className="text-sm font-medium text-white mb-1">{stat.label}</div>
              <div className="text-xs text-cy-gray-400">{stat.desc}</div>
            </motion.div>
          ))}
        </div>

        {/* Deployment */}
        <div className="glass-card p-8 rounded-2xl mb-8">
          <h3 className="text-lg font-heading font-semibold text-white mb-4">Deployment Flexibility</h3>
          <div className="flex flex-wrap gap-3">
            {PLATFORMS.map((p) => (
              <div key={p.name} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cy-glass-bg border border-cy-glass-border">
                <div className="w-2 h-2 rounded-full bg-cy-orange" aria-hidden="true" />
                <span className="text-sm text-white font-medium">{p.name}</span>
                <span className="text-xs text-cy-gray-400">• {p.category}</span>
              </div>
            ))}
          </div>
        </div>

        {/* CTA strip */}
        <motion.div
          initial={{ opacity: 0, y: shouldReduce ? 0 : 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.6 }}
          className="bg-gradient-to-r from-cy-orange/10 via-cy-glass-bg to-cy-cyan/10 border border-cy-glass-border rounded-2xl p-8 flex flex-col sm:flex-row items-center justify-between gap-6"
        >
          <div>
            <h3 className="text-xl font-heading font-semibold text-white mb-1">
              Ready to transform your organization?
            </h3>
            <p className="text-sm text-cy-gray-400">
              Schedule a personalized demo with our platform specialists.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link href={`/${locale}/demo`} className="btn-primary whitespace-nowrap">
              Request Demo
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${locale}/contact`} className="btn-secondary whitespace-nowrap">
              Contact Sales
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
