"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  TrendingUp,
  Users,
  BookOpen,
  Megaphone,
  Star,
  Globe,
  Award,
  Shield,
  Zap,
  ChevronRight,
  Search,
  MapPin,
  Building2,
  CheckCircle2,
} from "lucide-react";
import { motion } from "framer-motion";
import { clsx } from "clsx";

// ─── Data ──────────────────────────────────────────────────────────────────────

const BENEFITS = [
  {
    icon: TrendingUp,
    title: "Revenue Share",
    description:
      "Earn competitive commissions on every deal. Our tiered structure rewards growth — the more you sell, the more you earn.",
    color: "cy-orange",
    colorClass: "text-cy-orange bg-cy-orange/10 border-cy-orange/20",
  },
  {
    icon: Users,
    title: "Sales Support",
    description:
      "Dedicated partner success managers, pre-sales technical experts and joint go-to-market execution for every major opportunity.",
    color: "cy-cyan",
    colorClass: "text-cy-cyan bg-cy-cyan/10 border-cy-cyan/20",
  },
  {
    icon: BookOpen,
    title: "Training & Certification",
    description:
      "Access to the CyberCom Academy — product training, certification tracks and hands-on labs to sharpen your expertise.",
    color: "cy-orange",
    colorClass: "text-cy-orange bg-cy-orange/10 border-cy-orange/20",
  },
  {
    icon: Megaphone,
    title: "Marketing Co-op",
    description:
      "Co-branded assets, market development funds and joint campaign support to help you reach more customers, faster.",
    color: "cy-cyan",
    colorClass: "text-cy-cyan bg-cy-cyan/10 border-cy-cyan/20",
  },
];

const TIERS = [
  {
    name: "Authorized",
    icon: Shield,
    revenue: "< $50K ARR",
    commission: "10%",
    perks: [
      "Partner portal access",
      "Sales kit library",
      "Online training",
      "Email support",
    ],
    highlight: false,
    badgeClass: "border-cy-gray-600/40 text-cy-gray-400",
  },
  {
    name: "Silver",
    icon: Star,
    revenue: "$50K–$200K ARR",
    commission: "15%",
    perks: [
      "All Authorized benefits",
      "Dedicated partner manager",
      "Deal registration",
      "Co-marketing funds",
      "Priority support",
    ],
    highlight: false,
    badgeClass: "border-slate-400/40 text-slate-300",
  },
  {
    name: "Gold",
    icon: Award,
    revenue: "$200K–$500K ARR",
    commission: "20%",
    perks: [
      "All Silver benefits",
      "Joint business plan",
      "MDF top-up",
      "Executive sponsorship",
      "Demo environment",
      "Certification bonuses",
    ],
    highlight: true,
    badgeClass: "border-yellow-500/50 text-yellow-400",
  },
  {
    name: "Platinum",
    icon: Zap,
    revenue: "$500K+ ARR",
    commission: "25%",
    perks: [
      "All Gold benefits",
      "Custom SLAs",
      "Co-sell motions",
      "Product roadmap input",
      "Dedicated SE",
      "Global expansion support",
    ],
    highlight: false,
    badgeClass: "border-cy-cyan/40 text-cy-cyan",
  },
];

const WHY_ITEMS = [
  {
    icon: Globe,
    title: "Massive Market Opportunity",
    description:
      "Healthcare digitization, e-government modernization and enterprise transformation represent a $2T+ global opportunity. Get there first.",
  },
  {
    icon: Shield,
    title: "Proven Platforms",
    description:
      "CyberCom products are deployed in 18 countries. Battle-tested, compliant and enterprise-grade — your reputation stays protected.",
  },
  {
    icon: Award,
    title: "Industry Certifications",
    description:
      "Earn recognized CyberCom certifications that differentiate your team and validate expertise to enterprise buyers.",
  },
  {
    icon: Users,
    title: "Partner-First Culture",
    description:
      "We win only when you win. No channel conflict, transparent deal registration and sales team alignment from day one.",
  },
];

const PARTNER_DIRECTORY = [
  {
    name: "Medtech Gulf Solutions",
    country: "Saudi Arabia",
    type: "Implementation",
    products: ["CyMed", "CyIdentity"],
    tier: "Gold",
  },
  {
    name: "Digital Gov Partners",
    country: "UAE",
    type: "Reseller",
    products: ["CyGov", "CyIntegrationHub"],
    tier: "Platinum",
  },
  {
    name: "Innovatech Egypt",
    country: "Egypt",
    type: "Consulting",
    products: ["CyCom", "CyAI"],
    tier: "Silver",
  },
  {
    name: "NordicCare Systems",
    country: "Sweden",
    type: "Technology",
    products: ["CyMed", "CyAI"],
    tier: "Gold",
  },
  {
    name: "AfricaHealth IT",
    country: "Kenya",
    type: "Implementation",
    products: ["CyMed", "CyCom"],
    tier: "Authorized",
  },
  {
    name: "SingaporeTech Gov",
    country: "Singapore",
    type: "Reseller",
    products: ["CyGov", "CyIdentity"],
    tier: "Silver",
  },
];

const COUNTRIES = ["All Countries", "Saudi Arabia", "UAE", "Egypt", "Sweden", "Kenya", "Singapore"];
const TYPES = ["All Types", "Implementation", "Reseller", "Technology", "Consulting"];

const TIER_BADGE: Record<string, string> = {
  Authorized: "border-cy-gray-600/40 text-cy-gray-400 bg-cy-gray-600/10",
  Silver: "border-slate-400/40 text-slate-300 bg-slate-400/10",
  Gold: "border-yellow-500/40 text-yellow-400 bg-yellow-500/10",
  Platinum: "border-cy-cyan/40 text-cy-cyan bg-cy-cyan/10",
};

// ─── Sub-components ─────────────────────────────────────────────────────────

function PartnerNav() {
  return (
    <header className="fixed top-0 inset-x-0 z-50 border-b border-cy-glass-border bg-cy-black/80 backdrop-blur-md">
      <div className="section-container flex items-center justify-between h-16">
        <Link href="/" className="flex items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cy-orange rounded-lg">
          <span className="text-xl font-heading font-bold text-gradient-orange">
            CyberCom
          </span>
          <span className="text-sm text-cy-gray-400 font-body">Partners</span>
        </Link>
        <nav aria-label="Partner portal navigation" className="hidden md:flex items-center gap-6">
          <a href="#benefits" className="text-sm text-cy-gray-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cy-orange rounded">
            Benefits
          </a>
          <a href="#tiers" className="text-sm text-cy-gray-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cy-orange rounded">
            Partner Tiers
          </a>
          <a href="#directory" className="text-sm text-cy-gray-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cy-orange rounded">
            Directory
          </a>
          <Link href="/apply" className="btn-primary text-xs px-4 py-2 min-h-[36px]">
            Become a Partner
          </Link>
        </nav>
        <Link href="/apply" className="md:hidden btn-primary text-xs px-4 py-2 min-h-[36px]">
          Apply
        </Link>
      </div>
    </header>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function PartnersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("All Countries");
  const [selectedType, setSelectedType] = useState("All Types");

  const filtered = PARTNER_DIRECTORY.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.country.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCountry =
      selectedCountry === "All Countries" || p.country === selectedCountry;
    const matchesType =
      selectedType === "All Types" || p.type === selectedType;
    return matchesSearch && matchesCountry && matchesType;
  });

  return (
    <>
      <PartnerNav />

      <main id="main-content" className="pt-16">
        {/* ── Hero ─────────────────────────────────────────────────────────── */}
        <section
          aria-labelledby="hero-heading"
          className="relative overflow-hidden py-24 md:py-36"
        >
          {/* Background glows */}
          <div
            aria-hidden="true"
            className="glow-orb w-[600px] h-[600px] bg-cy-orange/10 -top-40 -left-40"
          />
          <div
            aria-hidden="true"
            className="glow-orb w-[500px] h-[500px] bg-cy-cyan/8 -bottom-20 -right-20"
          />

          <div className="section-container relative z-10 text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cy-orange/30 bg-cy-orange/10 text-cy-orange text-xs font-medium mb-6">
                <Star className="w-3.5 h-3.5" aria-hidden="true" />
                CyberCom Partner Program
              </span>
            </motion.div>

            <motion.h1
              id="hero-heading"
              className="text-4xl md:text-6xl lg:text-7xl font-heading font-bold text-white mb-6"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.05 }}
            >
              Grow Your Business{" "}
              <span className="text-gradient-orange">with CyberCom</span>
            </motion.h1>

            <motion.p
              className="text-lg md:text-xl text-cy-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              Join 200+ partners across 35 countries delivering next-generation
              healthcare, government and enterprise platforms. Together we
              transform industries.
            </motion.p>

            <motion.div
              className="flex flex-col sm:flex-row items-center justify-center gap-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.15 }}
            >
              <Link href="/apply" className="btn-primary text-base px-8 py-3.5">
                Become a Partner
                <ArrowRight className="w-4 h-4" aria-hidden="true" />
              </Link>
              <a href="#tiers" className="btn-secondary text-base px-8 py-3.5">
                View Partner Tiers
              </a>
            </motion.div>

            {/* Stats row */}
            <motion.div
              className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-3xl mx-auto"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.25 }}
              aria-label="Partner program statistics"
            >
              {[
                { value: "200+", label: "Active Partners" },
                { value: "35", label: "Countries" },
                { value: "25%", label: "Max Commission" },
                { value: "$2B+", label: "Market Opportunity" },
              ].map((stat) => (
                <div key={stat.label} className="glass-card p-5 text-center">
                  <p className="text-2xl md:text-3xl font-heading font-bold text-gradient-orange">
                    {stat.value}
                  </p>
                  <p className="text-xs text-cy-gray-400 mt-1">{stat.label}</p>
                </div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── Benefits ──────────────────────────────────────────────────────── */}
        <section
          id="benefits"
          aria-labelledby="benefits-heading"
          className="py-24 relative"
        >
          <div className="section-container">
            <div className="text-center mb-16">
              <h2
                id="benefits-heading"
                className="text-3xl md:text-4xl font-heading font-bold text-white mb-4"
              >
                Everything You Need to{" "}
                <span className="text-gradient-orange">Succeed</span>
              </h2>
              <p className="text-cy-gray-400 text-lg max-w-2xl mx-auto">
                Our partner program is designed to accelerate your growth with
                the resources, support and incentives that matter most.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {BENEFITS.map((benefit, i) => {
                const Icon = benefit.icon;
                return (
                  <motion.article
                    key={benefit.title}
                    className="glass-card p-8 flex gap-6"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.45, delay: i * 0.08 }}
                  >
                    <div
                      className={clsx(
                        "flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center border",
                        benefit.colorClass
                      )}
                      aria-hidden="true"
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-lg font-heading font-semibold text-white mb-2">
                        {benefit.title}
                      </h3>
                      <p className="text-cy-gray-400 text-sm leading-relaxed">
                        {benefit.description}
                      </p>
                    </div>
                  </motion.article>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── Partner Tiers ────────────────────────────────────────────────── */}
        <section
          id="tiers"
          aria-labelledby="tiers-heading"
          className="py-24 relative"
        >
          <div
            aria-hidden="true"
            className="glow-orb w-[400px] h-[400px] bg-cy-cyan/6 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
          />
          <div className="section-container relative z-10">
            <div className="text-center mb-16">
              <h2
                id="tiers-heading"
                className="text-3xl md:text-4xl font-heading font-bold text-white mb-4"
              >
                Partner Tiers &amp;{" "}
                <span className="text-gradient-orange">Commissions</span>
              </h2>
              <p className="text-cy-gray-400 text-lg max-w-2xl mx-auto">
                Start as an Authorized partner and unlock greater rewards as
                your revenue grows.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {TIERS.map((tier, i) => {
                const Icon = tier.icon;
                return (
                  <motion.article
                    key={tier.name}
                    className={clsx(
                      "glass-card p-6 flex flex-col",
                      tier.highlight &&
                        "border-yellow-500/30 ring-1 ring-yellow-500/20"
                    )}
                    initial={{ opacity: 0, y: 24 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.45, delay: i * 0.07 }}
                    aria-label={`${tier.name} partner tier`}
                  >
                    {tier.highlight && (
                      <span className="inline-block text-xs font-semibold text-yellow-400 bg-yellow-500/10 border border-yellow-500/30 rounded-full px-3 py-0.5 mb-4 self-start">
                        Most Popular
                      </span>
                    )}
                    <div className="flex items-center gap-3 mb-4">
                      <div
                        className={clsx(
                          "w-10 h-10 rounded-xl flex items-center justify-center border",
                          tier.badgeClass,
                          "bg-white/5"
                        )}
                        aria-hidden="true"
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-heading font-bold text-white text-lg">
                          {tier.name}
                        </h3>
                        <p className="text-xs text-cy-gray-400">{tier.revenue}</p>
                      </div>
                    </div>

                    <div className="mb-5">
                      <span className="text-3xl font-heading font-bold text-gradient-orange">
                        {tier.commission}
                      </span>
                      <span className="text-cy-gray-400 text-sm ml-1">
                        commission
                      </span>
                    </div>

                    <ul className="space-y-2 flex-1" aria-label={`${tier.name} tier benefits`}>
                      {tier.perks.map((perk) => (
                        <li
                          key={perk}
                          className="flex items-center gap-2 text-sm text-cy-gray-400"
                        >
                          <CheckCircle2
                            className="w-4 h-4 text-cy-orange flex-shrink-0"
                            aria-hidden="true"
                          />
                          {perk}
                        </li>
                      ))}
                    </ul>

                    <Link
                      href="/apply"
                      className={clsx(
                        "mt-6 btn-secondary text-xs w-full",
                        tier.highlight && "btn-primary"
                      )}
                    >
                      Get Started
                      <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
                    </Link>
                  </motion.article>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── Why Become a Partner ──────────────────────────────────────────── */}
        <section aria-labelledby="why-heading" className="py-24">
          <div className="section-container">
            <div className="text-center mb-16">
              <h2
                id="why-heading"
                className="text-3xl md:text-4xl font-heading font-bold text-white mb-4"
              >
                Why Partner with{" "}
                <span className="text-gradient-orange">CyberCom</span>?
              </h2>
              <p className="text-cy-gray-400 text-lg max-w-2xl mx-auto">
                We provide the technology, support and market access. You bring
                the local expertise and customer relationships.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              {WHY_ITEMS.map((item, i) => {
                const Icon = item.icon;
                return (
                  <motion.div
                    key={item.title}
                    className="flex gap-5 p-6 glass-card"
                    initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.45, delay: i * 0.08 }}
                  >
                    <div
                      className="flex-shrink-0 w-11 h-11 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center"
                      aria-hidden="true"
                    >
                      <Icon className="w-5 h-5 text-cy-orange" />
                    </div>
                    <div>
                      <h3 className="text-base font-heading font-semibold text-white mb-1.5">
                        {item.title}
                      </h3>
                      <p className="text-sm text-cy-gray-400 leading-relaxed">
                        {item.description}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── Partner Directory ─────────────────────────────────────────────── */}
        <section
          id="directory"
          aria-labelledby="directory-heading"
          className="py-24 relative"
        >
          <div className="section-container">
            <div className="text-center mb-12">
              <h2
                id="directory-heading"
                className="text-3xl md:text-4xl font-heading font-bold text-white mb-4"
              >
                Partner{" "}
                <span className="text-gradient-orange">Directory</span>
              </h2>
              <p className="text-cy-gray-400 text-lg max-w-xl mx-auto">
                Find a certified CyberCom partner near you.
              </p>
            </div>

            {/* Filters */}
            <div className="glass-card p-4 mb-8 flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <Search
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cy-gray-400 pointer-events-none"
                  aria-hidden="true"
                />
                <input
                  type="search"
                  placeholder="Search partners…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="form-input pl-9"
                  aria-label="Search partners by name or country"
                />
              </div>
              <div className="relative md:w-48">
                <MapPin
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cy-gray-400 pointer-events-none"
                  aria-hidden="true"
                />
                <select
                  value={selectedCountry}
                  onChange={(e) => setSelectedCountry(e.target.value)}
                  className="form-select pl-9"
                  aria-label="Filter by country"
                >
                  {COUNTRIES.map((c) => (
                    <option key={c} value={c} className="bg-cy-dark">
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div className="relative md:w-48">
                <Building2
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cy-gray-400 pointer-events-none"
                  aria-hidden="true"
                />
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="form-select pl-9"
                  aria-label="Filter by partner type"
                >
                  {TYPES.map((t) => (
                    <option key={t} value={t} className="bg-cy-dark">
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Directory grid */}
            {filtered.length === 0 ? (
              <div
                className="glass-card p-16 text-center text-cy-gray-400"
                role="status"
                aria-live="polite"
              >
                <Search className="w-10 h-10 mx-auto mb-4 opacity-40" aria-hidden="true" />
                <p className="text-lg font-medium text-white mb-2">
                  No partners found
                </p>
                <p className="text-sm">Try adjusting your search filters.</p>
              </div>
            ) : (
              <div
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                aria-live="polite"
                aria-label={`${filtered.length} partners found`}
              >
                {filtered.map((partner) => (
                  <article
                    key={partner.name}
                    className="glass-card p-6"
                    aria-label={partner.name}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-base font-heading font-semibold text-white leading-snug">
                        {partner.name}
                      </h3>
                      <span
                        className={clsx(
                          "tier-badge flex-shrink-0 ml-3",
                          TIER_BADGE[partner.tier]
                        )}
                      >
                        {partner.tier}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 text-sm text-cy-gray-400 mb-1">
                      <MapPin className="w-3.5 h-3.5 flex-shrink-0" aria-hidden="true" />
                      {partner.country}
                    </div>
                    <div className="flex items-center gap-1.5 text-sm text-cy-gray-400 mb-4">
                      <Building2 className="w-3.5 h-3.5 flex-shrink-0" aria-hidden="true" />
                      {partner.type} Partner
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {partner.products.map((prod) => (
                        <span
                          key={prod}
                          className="px-2 py-0.5 rounded text-xs border border-cy-glass-border text-cy-gray-400 bg-cy-glass-bg"
                        >
                          {prod}
                        </span>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* ── CTA ──────────────────────────────────────────────────────────── */}
        <section aria-labelledby="cta-heading" className="py-24 relative overflow-hidden">
          <div
            aria-hidden="true"
            className="glow-orb w-[500px] h-[500px] bg-cy-orange/12 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
          />
          <div className="section-container relative z-10">
            <div className="glass-card p-12 md:p-20 text-center max-w-3xl mx-auto">
              <h2
                id="cta-heading"
                className="text-3xl md:text-5xl font-heading font-bold text-white mb-6"
              >
                Ready to{" "}
                <span className="text-gradient-orange">Get Started</span>?
              </h2>
              <p className="text-lg text-cy-gray-400 mb-10 max-w-lg mx-auto leading-relaxed">
                Applications are reviewed within 5 business days. Once
                approved, you get immediate access to the partner portal and
                all resources.
              </p>
              <Link href="/apply" className="btn-primary text-base px-10 py-4">
                Apply to Become a Partner
                <ArrowRight className="w-5 h-5" aria-hidden="true" />
              </Link>
              <p className="mt-6 text-sm text-cy-gray-400">
                Already a partner?{" "}
                <Link
                  href="/dashboard"
                  className="text-cy-orange hover:text-cy-orange-light underline underline-offset-2 transition-colors"
                >
                  Sign in to the portal
                </Link>
              </p>
            </div>
          </div>
        </section>

        {/* ── Footer ───────────────────────────────────────────────────────── */}
        <footer className="border-t border-cy-glass-border py-10">
          <div className="section-container flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-cy-gray-400">
            <span>
              &copy; {new Date().getFullYear()} CyberCom Revolution. All rights
              reserved.
            </span>
            <nav aria-label="Footer links" className="flex items-center gap-6">
              <a
                href="https://cy-com.com/privacy"
                className="hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cy-orange rounded"
              >
                Privacy
              </a>
              <a
                href="https://cy-com.com/terms"
                className="hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cy-orange rounded"
              >
                Terms
              </a>
              <a
                href="mailto:partners@cy-com.com"
                className="hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cy-orange rounded"
              >
                Contact Partners Team
              </a>
            </nav>
          </div>
        </footer>
      </main>
    </>
  );
}
