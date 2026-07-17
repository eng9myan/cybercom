import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Package, Star, Download, Filter, Zap, Shield, Globe, BarChart2 } from "lucide-react";
import { useTranslations } from "next-intl";

interface MarketplacePageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: MarketplacePageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("marketplacePage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/marketplace",
    locale,
  });
}

const CATEGORIES = [
  { key: "all", icon: Package },
  { key: "module", icon: Zap },
  { key: "extension", icon: Shield },
  { key: "ai_package", icon: BarChart2 },
  { key: "connector", icon: Globe },
  { key: "report", icon: Filter },
];

const FEATURED = [
  { key: "analytics", publisherType: "official" as const, rating: 4.9, installs: 2400, priceModel: "subscription" as const, priceAmount: 0 },
  { key: "moh", publisherType: "official" as const, rating: 4.8, installs: 1800, priceModel: "free" as const, priceAmount: 0 },
  { key: "nabidh", publisherType: "official" as const, rating: 4.9, installs: 1200, priceModel: "free" as const, priceAmount: 0 },
  { key: "payroll", publisherType: "partner" as const, rating: 4.7, installs: 950, priceModel: "one_time" as const, priceAmount: 2400 },
  { key: "cardiology", publisherType: "official" as const, rating: 4.8, installs: 760, priceModel: "subscription" as const, priceAmount: 0 },
  { key: "whatsapp", publisherType: "partner" as const, rating: 4.6, installs: 1100, priceModel: "usage" as const, priceAmount: 0 },
];

function PublisherBadge({ type }: { type: "official" | "partner" | "community" }) {
  const t = useTranslations("marketplacePage.publisherBadges");
  if (type === "official") return <span className="px-2 py-0.5 rounded-full text-2xs font-medium bg-cy-orange/10 text-cy-orange border border-cy-orange/20">{t("official")}</span>;
  if (type === "partner") return <span className="px-2 py-0.5 rounded-full text-2xs font-medium bg-cy-cyan/10 text-cy-cyan border border-cy-cyan/20">{t("partner")}</span>;
  return <span className="px-2 py-0.5 rounded-full text-2xs font-medium bg-cy-glass-bg text-cy-gray-400 border border-cy-glass-border">{t("community")}</span>;
}

export default async function MarketplacePage({ params }: MarketplacePageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("marketplacePage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[700px] h-[700px] -top-32 left-1/4 bg-cy-orange/5" />
          <div className="glow-orb w-[500px] h-[500px] top-0 right-1/4 bg-cy-cyan/4" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            {t("badge")}
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            {t("headingPrefix")}{" "}
            <span className="text-gradient">{t("headingHighlight")}</span>
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-10">
            {t("subheading")}
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
              {t("getPlatformAccess")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/partner`} className="btn-secondary px-8 py-3">
              {t("publishExtension")}
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-cy-dark/30 border-y border-cy-glass-border py-10">
        <div className="section-container grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
          {(["listings", "partners", "installs", "rating"] as const).map((key) => (
            <div key={key}>
              <div className="text-3xl font-heading font-semibold text-cy-orange mb-1">{t(`stats.${key}.value`)}</div>
              <div className="text-sm text-cy-gray-400">{t(`stats.${key}.label`)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Categories */}
      <section className="py-12" aria-labelledby="categories-heading">
        <div className="section-container">
          <h2 id="categories-heading" className="sr-only">{t("browseCategories")}</h2>
          <div className="flex flex-wrap gap-2 justify-center">
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              const label = t(`categories.${cat.key}`);
              return (
                <button
                  key={cat.key}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border border-cy-glass-border bg-cy-glass-bg text-cy-gray-300 hover:text-white hover:border-cy-orange/40 transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-cy-orange"
                  aria-label={`${t("filterBy")} ${label}`}
                >
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Featured listings */}
      <section className="pb-20" aria-labelledby="featured-heading">
        <div className="section-container">
          <div className="flex items-center justify-between mb-8">
            <h2 id="featured-heading" className="text-2xl font-heading font-semibold text-white">
              {t("featuredHeading")}
            </h2>
            <span className="text-sm text-cy-gray-400">{t("showingCount")}</span>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURED.map((item) => {
              const tags = t.raw(`items.${item.key}.tags`) as string[];
              return (
                <article
                  key={item.key}
                  className="glass-card p-6 rounded-2xl flex flex-col hover:border-cy-glass-border/80 transition-colors duration-150"
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="w-10 h-10 rounded-xl bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                      <Package className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                    </div>
                    <PublisherBadge type={item.publisherType} />
                  </div>

                  <h3 className="text-sm font-heading font-semibold text-white mb-1">{t(`items.${item.key}.name`)}</h3>
                  <p className="text-xs text-cy-gray-400 mb-1">{t(`items.${item.key}.category`)} · {t(`items.${item.key}.publisher`)}</p>
                  <p className="text-xs text-cy-gray-400 leading-relaxed mb-4 flex-1">{t(`items.${item.key}.description`)}</p>

                  <div className="flex flex-wrap gap-1 mb-4">
                    {tags.map((tag) => (
                      <span key={tag} className="px-2 py-0.5 rounded-md text-2xs bg-cy-glass-bg border border-cy-glass-border text-cy-gray-400">
                        {tag}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 text-xs text-cy-gray-400">
                      <span className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-amber-400 fill-amber-400" aria-hidden="true" />
                        {item.rating}
                      </span>
                      <span className="flex items-center gap-1">
                        <Download className="w-3 h-3" aria-hidden="true" />
                        {item.installs.toLocaleString()}
                      </span>
                    </div>
                    <span className="text-xs font-medium text-cy-orange">
                      {item.priceModel === "free" ? t("free") : item.priceModel === "subscription" ? t("included") : `$${item.priceAmount.toLocaleString()}`}
                    </span>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      {/* Publish CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="publish-cta">
        <div className="section-container">
          <div className="glass-card p-10 lg:p-14 rounded-3xl grid lg:grid-cols-2 gap-10 items-center">
            <div>
              <h2 id="publish-cta" className="text-3xl font-heading font-semibold text-white mb-4">
                {t("publishCta.heading")}
              </h2>
              <p className="text-cy-gray-400 leading-relaxed mb-6">
                {t("publishCta.description")}
              </p>
              <div className="flex flex-wrap gap-4">
                <Link href={`/${l}/partner`} className="btn-primary px-8 py-3">
                  {t("publishCta.becomePublisher")}
                  <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
                </Link>
                <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3">
                  {t("publishCta.developerSupport")}
                </Link>
              </div>
            </div>
            <div className="space-y-4">
              {[
                { key: "certification", icon: Shield },
                { key: "distribution", icon: Globe },
                { key: "revenue", icon: BarChart2 },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.key} className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center flex-shrink-0">
                      <Icon className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">{t(`publishCta.${item.key}.title`)}</div>
                      <div className="text-xs text-cy-gray-400">{t(`publishCta.${item.key}.desc`)}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
