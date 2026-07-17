import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight } from "lucide-react";

interface IndustriesPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: IndustriesPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("industriesPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/industries",
    locale,
  });
}

const INDUSTRIES = [
  { key: "healthcare", icon: "🏥", color: "emerald", products: ["CyMed Clinic", "CyMed Hospital", "CyMed Laboratory", "CyMed Imaging", "CyMed Pharmacy"] },
  { key: "government", icon: "🏛", color: "amber", products: ["CyGov", "CyCitizen", "CyIdentity"] },
  { key: "retail", icon: "🛒", color: "pink", products: ["CyCom ERP", "CyData"] },
  { key: "manufacturing", icon: "⚙️", color: "orange", products: ["CyCom ERP", "CyAI"] },
  { key: "education", icon: "🎓", color: "sky", products: ["CyCom ERP", "CyConnect"] },
  { key: "financial", icon: "💰", color: "green", products: ["CyCom ERP", "CyData", "CyIdentity"] },
  { key: "insurance", icon: "🛡", color: "violet", products: ["CyCom ERP", "CyData"] },
  { key: "telecom", icon: "📡", color: "cyan", products: ["CyCom ERP", "CyConnect", "CyData"] },
];

const COLOR_VARIANTS: Record<string, string> = {
  emerald: "text-emerald-400 bg-emerald-500/5 border-emerald-500/20",
  amber: "text-amber-400 bg-amber-500/5 border-amber-500/20",
  pink: "text-pink-400 bg-pink-500/5 border-pink-500/20",
  orange: "text-orange-400 bg-orange-500/5 border-orange-500/20",
  sky: "text-sky-400 bg-sky-500/5 border-sky-500/20",
  green: "text-green-400 bg-green-500/5 border-green-500/20",
  violet: "text-violet-400 bg-violet-500/5 border-violet-500/20",
  cyan: "text-cyan-400 bg-cyan-500/5 border-cyan-500/20",
};

export default async function IndustriesPage({ params }: IndustriesPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("industriesPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Header */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[500px] h-[500px] -top-24 left-1/2 -translate-x-1/2 bg-cy-orange/8" />
        </div>
        <div className="section-container relative z-10 text-center">
          <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">{t("badge")}</p>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-4">
            {t("heading")}
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto">
            {t("subheading")}
          </p>
        </div>
      </div>

      {/* Industries grid */}
      <div className="section-container pb-24">
        <div className="grid md:grid-cols-2 gap-6">
          {INDUSTRIES.map((industry) => {
            const colorClass = (COLOR_VARIANTS[industry.color] ?? COLOR_VARIANTS.cyan) as string;
            const name = t(`list.${industry.key}.name`);
            const features = t.raw(`list.${industry.key}.features`) as string[];
            return (
              <Link
                key={industry.key}
                href={`/${l}/industries/${industry.key}`}
                className="glass-card p-6 rounded-2xl border border-cy-glass-border hover:border-current/20 group transition-all duration-300 block"
                aria-label={`${name} industry solutions`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl border ${colorClass}`}>
                    <span aria-hidden="true" role="img">{industry.icon}</span>
                  </div>
                  <ArrowRight
                    className="w-4 h-4 text-cy-gray-600 group-hover:text-white group-hover:translate-x-0.5 transition-all duration-200 rtl:rotate-180"
                    aria-hidden="true"
                  />
                </div>

                <h2 className={`text-xl font-heading font-semibold mb-2 group-hover:${colorClass.split(" ")[0]} transition-colors`}>
                  {name}
                </h2>
                <p className="text-sm text-cy-gray-400 mb-4 leading-relaxed">{t(`list.${industry.key}.desc`)}</p>

                {/* Features */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {features.map((f) => (
                    <span key={f} className="text-2xs px-2 py-0.5 rounded-md bg-cy-glass-bg border border-cy-glass-border text-cy-gray-400">
                      {f}
                    </span>
                  ))}
                </div>

                {/* Products */}
                <div className="flex items-center gap-2 pt-3 border-t border-cy-glass-border">
                  <span className="text-xs text-cy-gray-600">{t("platformsLabel")}</span>
                  <div className="flex flex-wrap gap-1">
                    {industry.products.map((p) => (
                      <span key={p} className="text-xs text-cy-gray-400 font-medium">{p}</span>
                    ))}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
