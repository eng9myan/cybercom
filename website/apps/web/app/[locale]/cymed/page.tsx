"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  ArrowRight, Building2, Stethoscope, FlaskConical, Pill, ScanLine, ShieldCheck,
  FileCheck2, Brain, Lock, Globe2, Check, Play, ExternalLink, Activity
} from "lucide-react";

const CYMED_URL = process.env.NEXT_PUBLIC_CYMED_URL ?? "https://cymed.cy-com.com";

const VERTICALS = [
  { icon: Stethoscope, slug: "cymed-clinic", key: "clinic", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: Building2, slug: "cymed-hospital", key: "hospital", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: FlaskConical, slug: "cymed-laboratory", key: "laboratory", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: ScanLine, slug: "cymed-imaging", key: "imaging", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: Pill, slug: "cymed-pharmacy", key: "pharmacy", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
];

const FEATURES = [
  { icon: FileCheck2, key: "fhir", color: "text-emerald-400" },
  { icon: ShieldCheck, key: "terminology", color: "text-teal-400" },
  { icon: Lock, key: "consent", color: "text-sky-400" },
  { icon: Activity, key: "audit", color: "text-amber-400" },
  { icon: Brain, key: "ai", color: "text-pink-400" },
  { icon: Globe2, key: "bilingual", color: "text-violet-400" },
];

const WORKFLOW_STEPS = [
  { step: 1, key: "step1" },
  { step: 2, key: "step2" },
  { step: 3, key: "step3" },
  { step: 4, key: "step4" },
  { step: 5, key: "step5" },
];

const EDITIONS = [
  { key: "clinic" },
  { key: "hospital", popular: true },
  { key: "enterprise" },
];

export default function CyMedPage() {
  const params = useParams();
  const locale = (params?.locale as string) ?? "en";
  const l = locale;
  const t = useTranslations("cymed");
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
      <section className="relative min-h-[85vh] flex items-center overflow-hidden" aria-labelledby="cymed-heading">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="glow-orb w-[800px] h-[800px] -top-32 left-1/2 -translate-x-1/2 bg-emerald-500/8 animate-glow-pulse" />
          <div className="glow-orb w-[500px] h-[500px] bottom-0 -right-32 bg-teal-500/6" />
          <div className="absolute inset-0 opacity-[0.025]" style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)`, backgroundSize: "64px 64px" }} />
        </div>
        <div className="section-container relative z-10">
          <div className="max-w-4xl">
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 mb-8">
              <Stethoscope className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
              <span className="text-xs font-medium text-emerald-400 tracking-wider uppercase">{t("badge")}</span>
            </motion.div>
            <motion.h1 id="cymed-heading" variants={fadeUp} initial="hidden" animate="visible" custom={0.1} className="text-5xl sm:text-6xl lg:text-7xl font-heading font-semibold text-white mb-6 leading-tight">
              {t("hero.titleLine1")}{" "}<br />
              <span className="text-gradient-orange">{t("hero.titleLine2")}</span>
            </motion.h1>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.2} className="text-xl text-cy-gray-400 leading-relaxed mb-4 max-w-2xl">
              {t("hero.description")}
            </motion.p>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.25} className="text-base text-cy-gray-400 mb-8 max-w-2xl">
              {t("hero.tagline")}
            </motion.p>
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0.3} className="flex flex-wrap gap-3">
              <Link href={`/${l}/try/cymed-clinic`} className="btn-primary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                <Play className="w-4 h-4" aria-hidden="true" />
                {t("hero.tryFree")}
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${l}/demo?product=cymed`} className="btn-secondary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                {t("hero.requestDemo")}
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Verticals */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="verticals-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="verticals-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("verticals.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("verticals.subheading")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {VERTICALS.map((v, i) => (
              <motion.div
                key={v.slug}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i * 0.05}
              >
                <Link
                  href={`/${l}/products/${v.slug}`}
                  className={`glass-card block rounded-xl p-5 border h-full ${v.bg} hover:scale-[1.01] transition-all duration-200`}
                >
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center border mb-3 ${v.bg}`}>
                    <v.icon className={`w-4.5 h-4.5 ${v.color}`} aria-hidden="true" />
                  </div>
                  <h3 className={`text-sm font-heading font-semibold ${v.color} mb-1.5`}>{t(`verticals.${v.key}.name`)}</h3>
                  <p className="text-xs text-cy-gray-400 leading-relaxed">{t(`verticals.${v.key}.desc`)}</p>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20" aria-labelledby="features-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="features-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("features.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("features.subheading")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.key}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i * 0.05}
                className="glass-card rounded-xl p-6 flex gap-4"
              >
                <div className={`w-10 h-10 rounded-xl bg-cy-dark border border-cy-glass-border flex items-center justify-center flex-shrink-0`}>
                  <f.icon className={`w-5 h-5 ${f.color}`} aria-hidden="true" />
                </div>
                <div>
                  <h3 className="text-sm font-heading font-semibold text-white mb-1.5">{t(`features.${f.key}.title`)}</h3>
                  <p className="text-xs text-cy-gray-400 leading-relaxed">{t(`features.${f.key}.desc`)}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="workflow-heading">
        <div className="section-container max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 id="workflow-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("workflow.heading")}</h2>
            <p className="text-cy-gray-400">{t("workflow.subheading")}</p>
          </div>
          <div className="space-y-4">
            {WORKFLOW_STEPS.map((step) => (
              <div key={step.step} className="glass-card rounded-xl p-6 flex gap-5 items-start">
                <div className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center flex-shrink-0 text-sm font-bold text-emerald-400">{step.step}</div>
                <div>
                  <h3 className="text-sm font-heading font-semibold text-white mb-1.5">{t(`workflow.${step.key}.title`)}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`workflow.${step.key}.desc`)}</p>
                </div>
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
                <div key={ed.key} className={`glass-card rounded-2xl p-7 flex flex-col ${ed.popular ? "border-emerald-500/40 ring-1 ring-emerald-500/20" : ""}`}>
                  {ed.popular && (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-xs font-medium text-emerald-400 mb-4 self-start">
                      <Check className="w-3 h-3 fill-emerald-400" aria-hidden="true" />
                      {t("editions.mostCommon")}
                    </div>
                  )}
                  <h3 className="text-xl font-heading font-semibold text-white mb-1">{name}</h3>
                  <p className="text-xs text-cy-gray-400 mb-5">{t(`editions.${ed.key}.price`)}</p>
                  <ul className="space-y-2.5 mb-7 flex-1" aria-label={`${name} plan features`}>
                    {features.map((f) => (
                      <li key={f} className="flex items-start gap-2.5">
                        <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                        <span className="text-sm text-cy-gray-200">{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Link href={`/${l}/demo?product=cymed`} className={`w-full text-center py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${ed.popular ? "btn-primary" : "btn-secondary"}`}>
                    {t("editions.getStarted")}
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20" aria-labelledby="cta-heading">
        <div className="section-container text-center max-w-3xl mx-auto">
          <h2 id="cta-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("cta.heading")}</h2>
          <p className="text-cy-gray-400 mb-8">{t("cta.subheading")}</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a href={CYMED_URL} target="_blank" rel="noreferrer" className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2">
              <Play className="w-4 h-4" aria-hidden="true" />
              {t("cta.launchDemo")}
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
