"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  ArrowRight, ShoppingBag, Utensils, Coffee, Cake, ShoppingCart, Package, Zap,
  BarChart3, Wifi, WifiOff, CreditCard, Users, Star, Check, Play, ExternalLink, Brain
} from "lucide-react";

const CYSHOP_URL = process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com";

const BUSINESS_TYPES = [
  { icon: ShoppingBag, key: "retail", color: "text-cy-orange", bg: "bg-cy-orange/10 border-cy-orange/20" },
  { icon: Utensils, key: "restaurant", color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" },
  { icon: Cake, key: "bakery", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
  { icon: Coffee, key: "coffeeShop", color: "text-brown-400 text-yellow-700", bg: "bg-yellow-500/10 border-yellow-500/20" },
  { icon: Zap, key: "fastFood", color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/20" },
  { icon: Package, key: "grocery", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: ShoppingCart, key: "supermarket", color: "text-teal-400", bg: "bg-teal-500/10 border-teal-500/20" },
  { icon: Zap, key: "convenienceStore", color: "text-sky-400", bg: "bg-sky-500/10 border-sky-500/20" },
];

const FEATURES = [
  { icon: BarChart3, key: "forecasting", color: "text-violet-400" },
  { icon: WifiOff, key: "offline", color: "text-emerald-400" },
  { icon: CreditCard, key: "payments", color: "text-sky-400" },
  { icon: Users, key: "loyalty", color: "text-rose-400" },
  { icon: Brain, key: "ai", color: "text-pink-400" },
  { icon: Wifi, key: "multiLocation", color: "text-amber-400" },
];

const WORKFLOW_STEPS = [
  { step: 1, key: "step1" },
  { step: 2, key: "step2" },
  { step: 3, key: "step3" },
  { step: 4, key: "step4" },
  { step: 5, key: "step5" },
];

const EDITIONS = [
  { key: "starter" },
  { key: "business", popular: true },
  { key: "enterprise" },
];

const AI_FEATURES = [
  { key: "demand" },
  { key: "waste" },
  { key: "staffing" },
  { key: "supplier" },
  { key: "menu" },
  { key: "customer" },
];

export default function CyShopPage() {
  const params = useParams();
  const locale = (params?.locale as string) ?? "en";
  const l = locale;
  const t = useTranslations("cyshop");
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
      <section className="relative min-h-[85vh] flex items-center overflow-hidden" aria-labelledby="cyshop-heading">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="glow-orb w-[800px] h-[800px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/8 animate-glow-pulse" />
          <div className="glow-orb w-[500px] h-[500px] bottom-0 -right-32 bg-amber-500/6" />
          <div className="absolute inset-0 opacity-[0.025]" style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)`, backgroundSize: "64px 64px" }} />
        </div>
        <div className="section-container relative z-10">
          <div className="max-w-4xl">
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cy-orange/20 bg-cy-orange/5 mb-8">
              <ShoppingBag className="w-3.5 h-3.5 text-cy-orange" aria-hidden="true" />
              <span className="text-xs font-medium text-cy-orange tracking-wider uppercase">{t("badge")}</span>
            </motion.div>
            <motion.h1 id="cyshop-heading" variants={fadeUp} initial="hidden" animate="visible" custom={0.1} className="text-5xl sm:text-6xl lg:text-7xl font-heading font-semibold text-white mb-6 leading-tight">
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
              <a href={CYSHOP_URL} target="_blank" rel="noreferrer" className="btn-primary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                <Play className="w-4 h-4" aria-hidden="true" />
                {t("hero.launchDemo")}
                <ExternalLink className="w-3.5 h-3.5 opacity-70" aria-hidden="true" />
              </a>
              <Link href={`/${l}/demo?product=cyshop`} className="btn-secondary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                {t("hero.requestDemo")}
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Business Types */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="business-types-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="business-types-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("businessTypes.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("businessTypes.subheading")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {BUSINESS_TYPES.map((bt, i) => (
              <motion.div
                key={bt.key}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i * 0.05}
                className={`glass-card rounded-xl p-5 border ${bt.bg} hover:scale-[1.01] transition-all duration-200`}
              >
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center border mb-3 ${bt.bg}`}>
                  <bt.icon className={`w-4.5 h-4.5 ${bt.color}`} aria-hidden="true" />
                </div>
                <h3 className={`text-sm font-heading font-semibold ${bt.color} mb-1.5`}>{t(`businessTypes.${bt.key}.name`)}</h3>
                <p className="text-xs text-cy-gray-400 leading-relaxed">{t(`businessTypes.${bt.key}.desc`)}</p>
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

      {/* AI Features */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="ai-heading">
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

      {/* Workflow */}
      <section className="py-20" aria-labelledby="workflow-heading">
        <div className="section-container max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 id="workflow-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("workflow.heading")}</h2>
            <p className="text-cy-gray-400">{t("workflow.subheading")}</p>
          </div>
          <div className="space-y-4">
            {WORKFLOW_STEPS.map((step) => (
              <div key={step.step} className="glass-card rounded-xl p-6 flex gap-5 items-start">
                <div className="w-8 h-8 rounded-full bg-cy-orange/10 border border-cy-orange/30 flex items-center justify-center flex-shrink-0 text-sm font-bold text-cy-orange">{step.step}</div>
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
      <section className="py-20 bg-cy-dark/30" aria-labelledby="editions-heading">
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
                <div key={ed.key} className={`glass-card rounded-2xl p-7 flex flex-col ${ed.popular ? "border-cy-orange/40 ring-1 ring-cy-orange/20" : ""}`}>
                  {ed.popular && (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cy-orange/10 border border-cy-orange/30 text-xs font-medium text-cy-orange mb-4 self-start">
                      <Star className="w-3 h-3 fill-cy-orange" aria-hidden="true" />
                      {t("editions.mostPopular")}
                    </div>
                  )}
                  <h3 className="text-xl font-heading font-semibold text-white mb-1">{name}</h3>
                  <p className="text-xs text-cy-gray-400 mb-5">{t(`editions.${ed.key}.price`)}</p>
                  <ul className="space-y-2.5 mb-7 flex-1" aria-label={`${name} plan features`}>
                    {features.map((f) => (
                      <li key={f} className="flex items-start gap-2.5">
                        <Check className="w-4 h-4 text-cy-orange flex-shrink-0 mt-0.5" aria-hidden="true" />
                        <span className="text-sm text-cy-gray-200">{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Link href={`/${l}/demo?product=cyshop`} className={`w-full text-center py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${ed.popular ? "btn-primary" : "btn-secondary"}`}>
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
            <a href={CYSHOP_URL} target="_blank" rel="noreferrer" className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2">
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
