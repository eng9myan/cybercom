"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  ArrowRight, Play, ExternalLink, Check, Brain,
  BarChart3, DollarSign, Users, Package, ShoppingCart, Cpu,
  FileText, Building2, Cog, PieChart, CreditCard, Warehouse,
  Globe, Star
} from "lucide-react";

const MODULES = [
  { icon: DollarSign, key: "finance", slug: "cycom-finance", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: FileText, key: "accounting", slug: "cycom-accounting", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: ShoppingCart, key: "procurement", slug: "cycom-procurement", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: Warehouse, key: "inventory", slug: "cycom-inventory", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: Cpu, key: "manufacturing", slug: "cycom-manufacturing", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: Building2, key: "crm", slug: "cycom-crm", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: Users, key: "hr", slug: "cycom-hr", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: CreditCard, key: "payroll", slug: "cycom-payroll", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: Cog, key: "assets", slug: "cycom-assets", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: Package, key: "pos", slug: "cycom-retail", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: BarChart3, key: "bi", slug: "cycom-bi", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { icon: Globe, key: "multiEntity", slug: "cycom", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
];

const AI_FEATURES = [
  { key: "forecasting" },
  { key: "procurement" },
  { key: "hr" },
  { key: "inventory" },
  { key: "anomaly" },
  { key: "biQuery" },
];

const EDITIONS = [
  { key: "business" },
  { key: "enterprise", popular: true },
  { key: "healthcareErp" },
];

export default function ErpPage() {
  const params = useParams();
  const locale = (params?.locale as string) ?? "en";
  const l = locale;
  const t = useTranslations("erp");
  const ERP_URL = process.env.NEXT_PUBLIC_CYCOM_URL ?? "https://erp.cy-com.com";
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
              <span className="text-xs font-medium text-blue-400 tracking-wider uppercase">{t("badge")}</span>
            </motion.div>
            <motion.h1 id="erp-heading" variants={fadeUp} initial="hidden" animate="visible" custom={0.1} className="text-5xl sm:text-6xl lg:text-7xl font-heading font-semibold text-white mb-6 leading-tight">
              {t("hero.titleLine1")}{" "}<br />
              <span className="text-blue-400">{t("hero.titleLine2")}</span>{" "}<br />
              <span className="text-gradient-orange">{t("hero.titleLine3")}</span>
            </motion.h1>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.2} className="text-xl text-cy-gray-400 leading-relaxed mb-4 max-w-2xl">
              {t("hero.description")}
            </motion.p>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.25} className="text-sm text-cy-gray-400 mb-8 max-w-2xl">
              {t("hero.tagline")}
            </motion.p>
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0.3} className="flex flex-wrap gap-3">
              <Link href={`/${l}/try/cycom`} className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl font-medium text-sm bg-blue-500 hover:bg-blue-400 text-white transition-all duration-200 cursor-pointer">
                <Play className="w-4 h-4" aria-hidden="true" />
                {t("hero.launchDashboard")}
              </Link>
              <Link href={`/${l}/demo?product=cycom`} className="btn-secondary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                {t("hero.requestDemo")}
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
            <h2 id="modules-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("modules.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("modules.subheading")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {MODULES.map((mod, i) => {
              const subModules = t.raw(`modules.${mod.key}.subModules`) as string[];
              return (
                <motion.div
                  key={mod.key}
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
                    <h3 className={`text-sm font-heading font-semibold ${mod.color} mb-1.5 group-hover:underline`}>{t(`modules.${mod.key}.name`)}</h3>
                    <p className="text-xs text-cy-gray-400 leading-relaxed mb-3 flex-1">{t(`modules.${mod.key}.desc`)}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {subModules.map((sm) => (
                        <span key={sm} className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/20">{sm}</span>
                      ))}
                    </div>
                    <span className={`text-xs ${mod.color} flex items-center gap-1 mt-3 font-medium`}>
                      {t("modules.exploreModule")}
                      <ArrowRight className="w-3 h-3 rtl:rotate-180 group-hover:translate-x-1 transition-transform" aria-hidden="true" />
                    </span>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* AI Intelligence */}
      <section className="py-20" aria-labelledby="ai-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-pink-500/20 bg-pink-500/5 mb-4">
              <Brain className="w-3.5 h-3.5 text-pink-400" aria-hidden="true" />
              <span className="text-xs font-medium text-pink-400 tracking-wider uppercase">{t("aiSection.badge")}</span>
            </div>
            <h2 id="ai-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("aiSection.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("aiSection.subheading")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {AI_FEATURES.map((f, i) => (
              <motion.div
                key={f.key}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i * 0.05}
                className="glass-card rounded-xl p-6 border border-pink-500/10 bg-pink-500/3"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="w-4 h-4 text-pink-400 flex-shrink-0" aria-hidden="true" />
                  <h3 className="text-sm font-heading font-semibold text-pink-400">{t(`aiSection.${f.key}.title`)}</h3>
                </div>
                <p className="text-xs text-cy-gray-400 leading-relaxed">{t(`aiSection.${f.key}.desc`)}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="compliance-heading">
        <div className="section-container">
          <div className="text-center mb-12">
            <h2 id="compliance-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("compliance.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("compliance.subheading")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-4xl mx-auto">
            {(t.raw("compliance.items") as string[]).map((c) => (
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
            <h2 id="editions-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("editions.heading")}</h2>
            <p className="text-cy-gray-400 max-w-xl mx-auto">{t("editions.subheading")}</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {EDITIONS.map((ed) => {
              const name = t(`editions.${ed.key}.name`);
              const features = t.raw(`editions.${ed.key}.features`) as string[];
              return (
                <div key={ed.key} className={`glass-card rounded-2xl p-7 flex flex-col ${ed.popular ? "border-blue-500/40 ring-1 ring-blue-500/20" : ""}`}>
                  {ed.popular && (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-xs font-medium text-blue-400 mb-4 self-start">
                      <Star className="w-3 h-3 fill-blue-400" aria-hidden="true" />
                      {t("editions.mostPopular")}
                    </div>
                  )}
                  <h3 className="text-xl font-heading font-semibold text-white mb-1">{name}</h3>
                  <p className="text-xs text-cy-gray-400 mb-5">{t(`editions.${ed.key}.tagline`)}</p>
                  <ul className="space-y-2.5 mb-7 flex-1" aria-label={`${name} plan features`}>
                    {features.map((f) => (
                      <li key={f} className="flex items-start gap-2.5">
                        <Check className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                        <span className="text-sm text-cy-gray-200">{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Link href={`/${l}/demo?product=cycom`} className={`w-full text-center py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${ed.popular ? "bg-blue-500 hover:bg-blue-400 text-white" : "btn-secondary"}`}>
                    {t("editions.getStarted")}
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="erp-cta-heading">
        <div className="section-container text-center max-w-3xl mx-auto">
          <h2 id="erp-cta-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("cta.heading")}</h2>
          <p className="text-cy-gray-400 mb-8">{t("cta.subheading")}</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a href={ERP_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 px-8 py-3 rounded-xl font-medium text-sm bg-blue-500 hover:bg-blue-400 text-white transition-all duration-200 cursor-pointer">
              <Play className="w-4 h-4" aria-hidden="true" />
              {t("cta.launchDashboard")}
              <ExternalLink className="w-3.5 h-3.5 opacity-70" aria-hidden="true" />
            </a>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3 text-sm">
              {t("cta.contactSales")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
