import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Users, TrendingUp, BookOpen, Package, DollarSign, BarChart2, CheckCircle, Globe } from "lucide-react";

interface PartnerPortalPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: PartnerPortalPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Partner Portal",
    description:
      "CyberCom Partner Portal — manage opportunities, deal registrations, revenue share, partner assets, and certifications. For authorized CyberCom implementation, reseller, and technology partners.",
    path: "/partner",
    locale,
  });
}

const PORTAL_MODULES = [
  {
    icon: TrendingUp,
    title: "Pipeline & Opportunities",
    desc: "Track your sales pipeline, register customer opportunities, and get co-selling support from the CyberCom regional team.",
  },
  {
    icon: DollarSign,
    title: "Deal Registration",
    desc: "Register qualified deals for protection and uplift. Approved deals are locked to your partner account for 90 days.",
  },
  {
    icon: BarChart2,
    title: "Revenue & Payouts",
    desc: "View your commission statements, revenue share calculations, and payout history by product and period.",
  },
  {
    icon: Package,
    title: "Partner Assets",
    desc: "Access certified sales decks, brochures, case studies, demo environments, and product videos — tiered by your partner level.",
  },
  {
    icon: BookOpen,
    title: "CyberCom Academy",
    desc: "Enroll in product certifications, watch training modules, and schedule technical workshops with CyberCom engineers.",
  },
  {
    icon: Users,
    title: "Co-Marketing Hub",
    desc: "Submit joint marketing activities, request co-marketing funds, and access approved campaign templates and brand assets.",
  },
];

const TIERS = [
  {
    name: "Authorized",
    requirements: ["Complete partner onboarding", "1 trained staff member", "Min. 1 closed deal/year"],
    benefits: ["Partner directory listing", "Basic sales assets", "Product training access"],
    color: "text-cy-gray-400 border-cy-glass-border",
  },
  {
    name: "Silver",
    requirements: ["2 certified staff members", "Min. $50K ARR", "6 months active"],
    benefits: ["All Authorized benefits", "Co-marketing budget", "Lead sharing program", "Technical pre-sales support"],
    color: "text-slate-300 border-slate-400/30",
  },
  {
    name: "Gold",
    featured: true,
    requirements: ["4 certified staff members", "Min. $200K ARR", "12 months active"],
    benefits: ["All Silver benefits", "Dedicated partner manager", "Demo environment license", "Priority support SLA", "Co-selling engagements"],
    color: "text-amber-400 border-amber-500/40",
  },
  {
    name: "Platinum",
    requirements: ["6 certified staff members", "Min. $500K ARR", "Executive alignment"],
    benefits: ["All Gold benefits", "Joint GTM planning", "Revenue share uplift (5%)", "Executive sponsor", "Custom integration support"],
    color: "text-cy-cyan border-cy-cyan/40",
  },
];

const REGIONS = [
  { name: "Jordan & Levant", contact: "levant@cy-com.com" },
  { name: "UAE & Gulf", contact: "gulf@cy-com.com" },
  { name: "Saudi Arabia", contact: "ksa@cy-com.com" },
  { name: "Egypt & North Africa", contact: "africa@cy-com.com" },
  { name: "Europe & International", contact: "intl@cy-com.com" },
];

export default async function PartnerPortalPage({ params }: PartnerPortalPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const portalUrl = process.env.NEXT_PUBLIC_PORTAL_URL ?? "https://portal.cy-com.com";

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[700px] h-[700px] -top-24 left-1/3 bg-cy-cyan/5" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-cyan border-cy-cyan/20 bg-cy-cyan/5 mb-6">
            Partner Portal
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            Grow your business with{" "}
            <span className="text-gradient">CyberCom</span>
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-10">
            Manage your partnership from one portal — pipeline, deals, revenue, certifications, and assets.
            Built for implementation, reseller, and technology partners.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <a href={`${portalUrl}/partner`} className="btn-primary px-8 py-3" target="_blank" rel="noreferrer">
              Partner Sign In
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </a>
            <Link href={`/${l}/partners`} className="btn-secondary px-8 py-3">
              Apply for Partnership
            </Link>
          </div>
        </div>
      </div>

      {/* Portal modules */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="modules-heading">
        <div className="section-container">
          <h2 id="modules-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            Partner portal modules
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Everything your team needs to manage the full partner lifecycle in one place.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {PORTAL_MODULES.map((mod) => {
              const Icon = mod.icon;
              return (
                <div key={mod.title} className="glass-card p-6 rounded-2xl">
                  <div className="w-10 h-10 rounded-xl bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cy-cyan" aria-hidden="true" />
                  </div>
                  <h3 className="text-base font-heading font-semibold text-white mb-2">{mod.title}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed">{mod.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Partner tiers */}
      <section className="py-20" aria-labelledby="tiers-heading">
        <div className="section-container">
          <h2 id="tiers-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            Partner tiers
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-xl mx-auto">
            Progress through tiers as your partnership grows — unlocking more resources, support, and revenue share.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {TIERS.map((tier) => (
              <div key={tier.name} className={`glass-card p-6 rounded-2xl border ${tier.featured ? "border-amber-500/40" : "border-cy-glass-border"}`}>
                {tier.featured && (
                  <span className="text-2xs font-semibold text-amber-400 block mb-2">Most Partners</span>
                )}
                <h3 className={`text-xl font-heading font-semibold mb-4 ${tier.color.split(" ")[0]}`}>{tier.name}</h3>
                <div className="mb-4">
                  <p className="text-2xs font-medium text-cy-gray-400 uppercase tracking-wider mb-2">Requirements</p>
                  <ul className="space-y-1">
                    {tier.requirements.map((r) => (
                      <li key={r} className="text-xs text-cy-gray-300 flex items-start gap-1.5">
                        <span className="text-cy-gray-500 mt-0.5">–</span>
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-2xs font-medium text-cy-gray-400 uppercase tracking-wider mb-2">Benefits</p>
                  <ul className="space-y-1.5">
                    {tier.benefits.map((b) => (
                      <li key={b} className="flex items-start gap-1.5 text-xs text-cy-gray-200">
                        <CheckCircle className="w-3 h-3 text-cy-orange mt-0.5 flex-shrink-0" aria-hidden="true" />
                        {b}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Regional contacts */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="regions-heading">
        <div className="section-container max-w-3xl">
          <h2 id="regions-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            Regional partner teams
          </h2>
          <p className="text-cy-gray-400 text-center mb-10">
            Each region has a dedicated partner team for co-selling, deal registration, and escalations.
          </p>
          <div className="grid sm:grid-cols-2 gap-4">
            {REGIONS.map((r) => (
              <div key={r.name} className="glass-card p-5 rounded-xl flex items-center gap-4">
                <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                  <Globe className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                </div>
                <div>
                  <div className="text-sm font-medium text-white">{r.name}</div>
                  <a href={`mailto:${r.contact}`} className="text-xs text-cy-gray-400 hover:text-cy-orange transition-colors">
                    {r.contact}
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Apply CTA */}
      <section className="py-20" aria-labelledby="apply-cta">
        <div className="section-container">
          <div className="glass-card p-10 lg:p-14 rounded-3xl text-center">
            <h2 id="apply-cta" className="text-3xl font-heading font-semibold text-white mb-4">
              Not yet a partner?
            </h2>
            <p className="text-cy-gray-400 max-w-xl mx-auto mb-8">
              Apply to join the CyberCom Partner Program and start building your practice around the
              fastest-growing healthcare and enterprise platform in the MENA region.
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <Link href={`/${l}/partners`} className="btn-primary px-8 py-3">
                Apply Now
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                Talk to Partnerships
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
