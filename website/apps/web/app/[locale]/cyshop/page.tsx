"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { useParams } from "next/navigation";
import {
  ArrowRight, ShoppingBag, Utensils, Coffee, Cake, ShoppingCart, Package, Zap,
  BarChart3, Wifi, WifiOff, CreditCard, Users, Star, Check, Play, ExternalLink, Brain
} from "lucide-react";

const CYSHOP_URL = process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com";

const BUSINESS_TYPES = [
  { icon: ShoppingBag, name: "Retail", desc: "Fashion, electronics, household, and general merchandise stores. Barcode scanning, stock management, and customer accounts.", color: "text-cy-orange", bg: "bg-cy-orange/10 border-cy-orange/20" },
  { icon: Utensils, name: "Restaurant", desc: "Full-service dine-in, takeaway, and delivery. Table management, KDS kitchen display, and integrated ordering.", color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" },
  { icon: Cake, name: "Bakery", desc: "Recipe management, production scheduling, fresh item expiry tracking, and daily waste reduction.", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
  { icon: Coffee, name: "Coffee Shop", desc: "Menu customization, modifier groups, barista workflow, and customer loyalty cards.", color: "text-brown-400 text-yellow-700", bg: "bg-yellow-500/10 border-yellow-500/20" },
  { icon: Zap, name: "Fast Food", desc: "Self-order kiosk, kitchen display, queue management, and drive-through timer integration.", color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/20" },
  { icon: Package, name: "Grocery", desc: "Weighted items, bulk pricing, scale integration, supplier purchase orders, and expiry management.", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: ShoppingCart, name: "Supermarket", desc: "Multi-department, self-checkout lanes, loyalty program, and promotional pricing engine.", color: "text-teal-400", bg: "bg-teal-500/10 border-teal-500/20" },
  { icon: Zap, name: "Convenience Store", desc: "Express checkout, tobacco and fuel management, prepaid cards, and 24/7 kiosk mode.", color: "text-sky-400", bg: "bg-sky-500/10 border-sky-500/20" },
];

const FEATURES = [
  { icon: BarChart3, title: "AI Sales Forecasting", desc: "Machine learning predicts demand by product, time of day, and season. Auto-generate purchase orders before stockouts happen.", color: "text-violet-400" },
  { icon: WifiOff, title: "Works Offline", desc: "POS continues processing sales without internet. All transactions sync automatically when connection restores. No data loss, ever.", color: "text-emerald-400" },
  { icon: CreditCard, title: "All Payment Methods", desc: "Card terminals, digital wallets, cash, credit, split bills, and QR pay. One integration, all methods.", color: "text-sky-400" },
  { icon: Users, title: "Loyalty & Rewards", desc: "Points program, tier levels, birthday offers, and personalized promotions. Keep customers coming back.", color: "text-rose-400" },
  { icon: Brain, title: "CyAI Intelligence", desc: "Waste reduction alerts, bestseller rankings, peak-hour staffing suggestions, and supplier performance scoring — powered by CyAI.", color: "text-pink-400" },
  { icon: Wifi, title: "Multi-Location", desc: "Manage unlimited branches from a single dashboard. Central menu management, consolidated reporting, and inter-branch inventory transfers.", color: "text-amber-400" },
];

const WORKFLOW_STEPS = [
  { step: 1, title: "Setup Your Business", desc: "Choose your business type, configure menu or product catalog, add locations, and connect payment terminals in minutes." },
  { step: 2, title: "Add Your Team", desc: "Staff sign in via CyIdentity SSO. Assign roles (cashier, manager, admin). Set shift schedules and access permissions." },
  { step: 3, title: "Launch POS", desc: "Open CyShop POS on tablet, touchscreen, or desktop. Scan items, take orders, and accept all payment methods." },
  { step: 4, title: "Manage Inventory", desc: "Stock tracked in real time. Auto-replenishment alerts when items run low. Receive deliveries via barcode scanning." },
  { step: 5, title: "Grow with Data", desc: "AI-powered dashboards show bestsellers, peak hours, customer trends, and growth opportunities. Export reports in one click." },
];

const EDITIONS = [
  { name: "Starter", price: "For single locations", features: ["1 location", "Up to 3 POS terminals", "Core inventory", "Basic reports", "Customer accounts", "Email support"] },
  { name: "Business", price: "For multi-location chains", popular: true, features: ["Unlimited locations", "Unlimited terminals", "Loyalty program", "Staff management", "Advanced analytics", "AI forecasting", "Priority support"] },
  { name: "Enterprise", price: "For franchises & groups", features: ["All Business features", "Franchise management", "Central kitchen integration", "Custom integrations", "API access", "Dedicated account manager", "24/7 SLA"] },
];

const AI_FEATURES = [
  { title: "Demand Forecasting", desc: "Predicts what you'll sell tomorrow, next week, and next month based on historical sales, weather, and local events." },
  { title: "Waste Prevention", desc: "Alerts when perishable items approach expiry. Suggests markdowns to sell before waste occurs." },
  { title: "Staff Optimization", desc: "Recommends optimal staffing levels by hour based on predicted footfall and transaction volume." },
  { title: "Supplier Intelligence", desc: "Scores suppliers by delivery reliability, quality, and pricing. Suggests best-value vendor per item." },
  { title: "Menu Engineering", desc: "Identifies high-margin items, low performers, and pricing opportunities. Maximizes profitability per menu category." },
  { title: "Customer Insights", desc: "Segments customers by purchase behavior, frequency, and lifetime value. Powers personalized loyalty campaigns." },
];

export default function CyShopPage() {
  const params = useParams();
  const locale = (params?.locale as string) ?? "en";
  const l = locale;
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
              <span className="text-xs font-medium text-cy-orange tracking-wider uppercase">CyShop · Intelligent Retail Platform</span>
            </motion.div>
            <motion.h1 id="cyshop-heading" variants={fadeUp} initial="hidden" animate="visible" custom={0.1} className="text-5xl sm:text-6xl lg:text-7xl font-heading font-semibold text-white mb-6 leading-tight">
              The Smartest POS{" "}<br />
              <span className="text-gradient-orange">for Every Business</span>
            </motion.h1>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.2} className="text-xl text-cy-gray-400 leading-relaxed mb-4 max-w-2xl">
              From restaurants and bakeries to supermarkets and convenience stores — CyShop is the cloud-native retail platform with AI intelligence built in.
            </motion.p>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.25} className="text-base text-cy-gray-400 mb-8 max-w-2xl">
              Part of the CyberCom Revolution ecosystem. Shares one identity layer, audit trail, and integration hub with CyMed and CyCom ERP.
            </motion.p>
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0.3} className="flex flex-wrap gap-3">
              <a href={CYSHOP_URL} target="_blank" rel="noreferrer" className="btn-primary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                <Play className="w-4 h-4" aria-hidden="true" />
                Launch Demo
                <ExternalLink className="w-3.5 h-3.5 opacity-70" aria-hidden="true" />
              </a>
              <Link href={`/${l}/demo?product=cyshop`} className="btn-secondary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                Request a Demo
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
            <h2 id="business-types-heading" className="text-3xl font-heading font-semibold text-white mb-4">Built for Every Business Type</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">One platform. Infinite configurations. CyShop adapts to how your business operates — not the other way around.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {BUSINESS_TYPES.map((bt, i) => (
              <motion.div
                key={bt.name}
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
                <h3 className={`text-sm font-heading font-semibold ${bt.color} mb-1.5`}>{bt.name}</h3>
                <p className="text-xs text-cy-gray-400 leading-relaxed">{bt.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20" aria-labelledby="features-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="features-heading" className="text-3xl font-heading font-semibold text-white mb-4">Platform Features</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">Everything you need to run and grow your retail or food service business, in one connected platform.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
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
                  <h3 className="text-sm font-heading font-semibold text-white mb-1.5">{f.title}</h3>
                  <p className="text-xs text-cy-gray-400 leading-relaxed">{f.desc}</p>
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
              <span className="text-xs font-medium text-pink-400 tracking-wider uppercase">Powered by CyAI</span>
            </div>
            <h2 id="ai-heading" className="text-3xl font-heading font-semibold text-white mb-4">AI Intelligence Built In</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">CyShop integrates CyAI for advisory intelligence across every dimension of your retail operation. AI assists — you decide.</p>
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

      {/* Workflow */}
      <section className="py-20" aria-labelledby="workflow-heading">
        <div className="section-container max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 id="workflow-heading" className="text-3xl font-heading font-semibold text-white mb-4">How CyShop Works</h2>
            <p className="text-cy-gray-400">From setup to first sale in hours, not weeks.</p>
          </div>
          <div className="space-y-4">
            {WORKFLOW_STEPS.map((step) => (
              <div key={step.step} className="glass-card rounded-xl p-6 flex gap-5 items-start">
                <div className="w-8 h-8 rounded-full bg-cy-orange/10 border border-cy-orange/30 flex items-center justify-center flex-shrink-0 text-sm font-bold text-cy-orange">{step.step}</div>
                <div>
                  <h3 className="text-sm font-heading font-semibold text-white mb-1.5">{step.title}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed">{step.desc}</p>
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
            <h2 id="editions-heading" className="text-3xl font-heading font-semibold text-white mb-4">Choose Your Edition</h2>
            <p className="text-cy-gray-400 max-w-xl mx-auto">Start with what you need. Upgrade as you grow. All plans include cloud hosting, updates, and core support.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {EDITIONS.map((ed) => (
              <div key={ed.name} className={`glass-card rounded-2xl p-7 flex flex-col ${ed.popular ? "border-cy-orange/40 ring-1 ring-cy-orange/20" : ""}`}>
                {ed.popular && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cy-orange/10 border border-cy-orange/30 text-xs font-medium text-cy-orange mb-4 self-start">
                    <Star className="w-3 h-3 fill-cy-orange" aria-hidden="true" />
                    Most Popular
                  </div>
                )}
                <h3 className="text-xl font-heading font-semibold text-white mb-1">{ed.name}</h3>
                <p className="text-xs text-cy-gray-400 mb-5">{ed.price}</p>
                <ul className="space-y-2.5 mb-7 flex-1" aria-label={`${ed.name} plan features`}>
                  {ed.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5">
                      <Check className="w-4 h-4 text-cy-orange flex-shrink-0 mt-0.5" aria-hidden="true" />
                      <span className="text-sm text-cy-gray-200">{f}</span>
                    </li>
                  ))}
                </ul>
                <Link href={`/${l}/demo?product=cyshop`} className={`w-full text-center py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${ed.popular ? "btn-primary" : "btn-secondary"}`}>
                  Get Started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20" aria-labelledby="cta-heading">
        <div className="section-container text-center max-w-3xl mx-auto">
          <h2 id="cta-heading" className="text-3xl font-heading font-semibold text-white mb-4">Ready to Modernize Your Business?</h2>
          <p className="text-cy-gray-400 mb-8">Join hundreds of retail and F&B businesses already running on CyShop. Start your demo today.</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a href={CYSHOP_URL} target="_blank" rel="noreferrer" className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2">
              <Play className="w-4 h-4" aria-hidden="true" />
              Launch CyShop Demo
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
