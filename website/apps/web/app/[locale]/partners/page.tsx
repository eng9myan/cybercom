import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Check } from "lucide-react";

interface PartnersPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: PartnersPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Partner Program",
    description: "Join the CyberCom Partner Program. Become an authorized implementation, reseller, or technology partner and access training, support, and co-selling resources.",
    path: "/partners",
    locale,
  });
}

const PARTNER_TIERS = [
  {
    name: "Authorized",
    color: "text-cy-gray-400",
    border: "border-cy-glass-border",
    benefits: ["Product training access", "Sales collateral", "Partner directory listing"],
  },
  {
    name: "Silver",
    color: "text-slate-300",
    border: "border-slate-400/30",
    benefits: ["All Authorized benefits", "Co-marketing funds", "Lead sharing", "Technical support"],
  },
  {
    name: "Gold",
    color: "text-amber-400",
    border: "border-amber-500/30",
    featured: true,
    benefits: ["All Silver benefits", "Dedicated partner manager", "Certified training program", "Demo environment access", "Priority support"],
  },
  {
    name: "Platinum",
    color: "text-cy-cyan",
    border: "border-cy-cyan/30",
    benefits: ["All Gold benefits", "Joint GTM planning", "Executive alignment sessions", "Custom integrations support", "Revenue share uplift"],
  },
];

const PARTNER_TYPES = [
  { type: "Implementation", desc: "Deploy and configure CyberCom platforms for end customers", icon: "⚙️" },
  { type: "Reseller", desc: "Resell CyberCom licenses and services in your market", icon: "🤝" },
  { type: "Technology", desc: "Integrate your product with the CyberCom platform ecosystem", icon: "🔗" },
  { type: "Consulting", desc: "Advise organizations on CyberCom-based digital transformation", icon: "💡" },
];

const BENEFITS = [
  "Access to CyberCom Academy training",
  "Sales and technical certification programs",
  "Co-branded marketing materials",
  "Sandbox & demo environments",
  "Partner revenue share program",
  "Joint business planning support",
  "Priority technical support channel",
  "Partner directory listing on cy-com.com",
];

export default async function PartnersPage({ params }: PartnersPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/8" />
        </div>
        <div className="section-container relative z-10 text-center">
          <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">Partner Program</p>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-4">
            Grow with CyberCom
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-8">
            Join a growing network of implementation, reseller, technology, and consulting partners
            delivering digital transformation across the Middle East and beyond.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href={`/${locale}/contact`} className="btn-primary px-8 py-3">
              Apply to Become a Partner
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${locale}/demo`} className="btn-secondary px-8 py-3">
              Partner Login
            </Link>
          </div>
        </div>
      </div>

      {/* Partner types */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="types-heading">
        <div className="section-container">
          <h2 id="types-heading" className="text-3xl font-heading font-semibold text-white mb-10 text-center">
            Partner Types
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {PARTNER_TYPES.map((pt) => (
              <div key={pt.type} className="glass-card p-6 rounded-2xl text-center">
                <div className="text-3xl mb-4" aria-hidden="true" role="img">{pt.icon}</div>
                <h3 className="font-heading font-semibold text-white mb-2">{pt.type}</h3>
                <p className="text-xs text-cy-gray-400 leading-relaxed">{pt.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tiers */}
      <section className="py-20" aria-labelledby="tiers-heading">
        <div className="section-container">
          <h2 id="tiers-heading" className="text-3xl font-heading font-semibold text-white mb-10 text-center">
            Partner Tiers
          </h2>
          <div className="grid md:grid-cols-4 gap-4">
            {PARTNER_TIERS.map((tier) => (
              <div
                key={tier.name}
                className={`glass-card p-6 rounded-2xl border ${tier.border} ${tier.featured ? "ring-1 ring-amber-500/20" : ""}`}
              >
                {tier.featured && (
                  <div className="text-2xs font-medium text-amber-400 uppercase tracking-wider mb-3">Most Popular</div>
                )}
                <h3 className={`font-heading font-semibold text-xl mb-4 ${tier.color}`}>{tier.name}</h3>
                <ul className="space-y-2">
                  {tier.benefits.map((b) => (
                    <li key={b} className="flex items-start gap-2 text-xs text-cy-gray-400">
                      <Check className="w-3.5 h-3.5 text-cy-orange flex-shrink-0 mt-0.5" aria-hidden="true" />
                      {b}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="benefits-heading">
        <div className="section-container">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 id="benefits-heading" className="text-3xl font-heading font-semibold text-white mb-4">
                Everything You Need to Succeed
              </h2>
              <p className="text-cy-gray-400 mb-8">
                CyberCom partners get the training, tools, and support to confidently deliver
                digital transformation projects for their customers.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {BENEFITS.map((b) => (
                  <div key={b} className="flex items-start gap-2 text-sm text-cy-gray-200">
                    <Check className="w-4 h-4 text-cy-orange flex-shrink-0 mt-0.5" aria-hidden="true" />
                    {b}
                  </div>
                ))}
              </div>
            </div>
            <div className="glass-card p-8 rounded-2xl">
              <h3 className="font-heading font-semibold text-white text-xl mb-4">Ready to join?</h3>
              <p className="text-sm text-cy-gray-400 mb-6">
                Complete our partner application form. Our team reviews all applications within 5 business days.
              </p>
              <Link href={`/${locale}/contact`} className="btn-primary w-full justify-center py-3.5">
                Apply Now
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <p className="text-2xs text-cy-gray-600 text-center mt-4">
                Already a partner? <Link href={`/${locale}/demo`} className="text-cy-orange hover:underline">Contact us to access Partner Portal</Link>
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
