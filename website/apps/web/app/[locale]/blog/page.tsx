import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Calendar, Clock, Tag } from "lucide-react";

interface BlogPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: BlogPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("blogPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/blog",
    locale,
  });
}

type ArticleCategory = "Healthcare IT" | "Platform" | "Government" | "Enterprise" | "Clinical";

const ARTICLES: {
  slug: string;
  category: ArticleCategory;
  date: string;
  featured: boolean;
}[] = [
  { slug: "fhir-r4-interoperability-mena", category: "Healthcare IT", date: "2026-06-15", featured: true },
  { slug: "icd-11-clinical-coding-readiness", category: "Clinical", date: "2026-06-08", featured: false },
  { slug: "drug-interaction-engine-design", category: "Clinical", date: "2026-06-01", featured: false },
  { slug: "zero-trust-healthcare-identity", category: "Platform", date: "2026-05-25", featured: false },
  { slug: "government-digital-transformation-gcc", category: "Government", date: "2026-05-18", featured: false },
  { slug: "postgresql-rls-multi-tenancy", category: "Platform", date: "2026-05-10", featured: false },
  { slug: "healthcare-erp-integration-patterns", category: "Enterprise", date: "2026-05-02", featured: false },
  { slug: "cybercom-release-2-production-readiness", category: "Platform", date: "2026-04-28", featured: false },
];

const CATEGORY_COLORS: Record<ArticleCategory, string> = {
  "Healthcare IT": "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
  "Clinical": "text-pink-400 border-pink-500/20 bg-pink-500/5",
  "Platform": "text-blue-400 border-blue-500/20 bg-blue-500/5",
  "Government": "text-amber-400 border-amber-500/20 bg-amber-500/5",
  "Enterprise": "text-violet-400 border-violet-500/20 bg-violet-500/5",
};

const ALL_CATEGORIES: ArticleCategory[] = ["Healthcare IT", "Clinical", "Platform", "Government", "Enterprise"];

function formatDate(dateStr: string, locale: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString(locale === "ar" ? "ar-EG" : "en-US", { year: "numeric", month: "long", day: "numeric" });
}

export default async function BlogPage({ params }: BlogPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("blogPage");
  const featured = ARTICLES.find((a) => a.featured);
  const rest = ARTICLES.filter((a) => !a.featured);

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[500px] h-[500px] -top-24 left-1/2 -translate-x-1/2 bg-cy-orange/5" />
        </div>
        <div className="section-container relative z-10">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            {t("badge")}
          </span>
          <h1 className="text-5xl font-heading font-semibold text-white mb-4 leading-tight">
            {t("heading")}
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl">
            {t("subheading")}
          </p>
        </div>
      </div>

      {/* Categories */}
      <div className="section-container pb-8">
        <div className="flex flex-wrap gap-2" role="list" aria-label="Article categories">
          <span className="product-badge text-white border-cy-glass-border bg-cy-orange/10 cursor-default" role="listitem">
            {t("all")}
          </span>
          {ALL_CATEGORIES.map((cat) => (
            <span
              key={cat}
              className={`product-badge cursor-default ${CATEGORY_COLORS[cat]}`}
              role="listitem"
            >
              <Tag className="w-3 h-3" aria-hidden="true" />
              {t(`categories.${cat}`)}
            </span>
          ))}
        </div>
      </div>

      {/* Featured Article */}
      {featured && (
        <section className="pb-16" aria-labelledby="featured-heading">
          <div className="section-container">
            <h2 id="featured-heading" className="text-xs font-semibold text-cy-gray-500 uppercase tracking-wider mb-4">
              {t("featured")}
            </h2>
            <article className="glass-card p-8 lg:p-10 rounded-3xl border-cy-glass-border hover:border-cy-glass-bg-hover transition-colors duration-200">
              <div className="grid lg:grid-cols-2 gap-8 items-center">
                <div>
                  <span className={`product-badge mb-4 ${CATEGORY_COLORS[featured.category]}`}>
                    <Tag className="w-3 h-3" aria-hidden="true" />
                    {t(`categories.${featured.category}`)}
                  </span>
                  <h3 className="text-2xl font-heading font-semibold text-white mb-3 leading-snug">
                    {t(`articles.${featured.slug}.title`)}
                  </h3>
                  <p className="text-cy-gray-400 leading-relaxed mb-6">{t(`articles.${featured.slug}.excerpt`)}</p>
                  <div className="flex items-center gap-4 text-xs text-cy-gray-500 mb-6">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5" aria-hidden="true" />
                      <time dateTime={featured.date}>{formatDate(featured.date, locale)}</time>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" aria-hidden="true" />
                      {t(`articles.${featured.slug}.readTime`)}
                    </span>
                  </div>
                  <Link href={`/${l}/blog/${featured.slug}`} className="btn-primary inline-flex text-sm py-2.5 px-5">
                    {t("readArticle")}
                    <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
                  </Link>
                </div>
                {/* Visual placeholder — article preview */}
                <div className="hidden lg:block relative h-64 rounded-2xl bg-cy-dark/40 border border-cy-glass-border overflow-hidden">
                  <div className="absolute inset-0 flex flex-col gap-2 p-6 opacity-40">
                    {[...Array(8)].map((_, i) => (
                      <div key={i} className="h-2.5 rounded-full bg-cy-gray-600" style={{ width: `${60 + ((i * 17) % 35)}%` }} />
                    ))}
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-4xl font-heading font-bold text-gradient-orange opacity-30">
                      {t(`categories.${featured.category}`)}
                    </span>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </section>
      )}

      {/* Article Grid */}
      <section className="pb-20" aria-labelledby="articles-heading">
        <div className="section-container">
          <h2 id="articles-heading" className="text-xs font-semibold text-cy-gray-500 uppercase tracking-wider mb-6">
            {t("allArticles")}
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {rest.map((article) => (
              <article key={article.slug} className="glass-card p-6 rounded-2xl flex flex-col hover:border-cy-glass-bg-hover transition-colors duration-150">
                <span className={`product-badge mb-3 self-start ${CATEGORY_COLORS[article.category]}`}>
                  <Tag className="w-3 h-3" aria-hidden="true" />
                  {t(`categories.${article.category}`)}
                </span>
                <h3 className="font-heading font-semibold text-white mb-2 leading-snug flex-1">
                  {t(`articles.${article.slug}.title`)}
                </h3>
                <p className="text-sm text-cy-gray-400 leading-relaxed mb-4 line-clamp-3">
                  {t(`articles.${article.slug}.excerpt`)}
                </p>
                <div className="flex items-center justify-between mt-auto pt-4 border-t border-cy-glass-border">
                  <div className="flex items-center gap-3 text-xs text-cy-gray-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" aria-hidden="true" />
                      <time dateTime={article.date}>{formatDate(article.date, locale)}</time>
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" aria-hidden="true" />
                      {t(`articles.${article.slug}.readTime`)}
                    </span>
                  </div>
                  <Link
                    href={`/${l}/blog/${article.slug}`}
                    className="text-xs text-cy-orange hover:text-cy-orange-light transition-colors flex items-center gap-1 cursor-pointer"
                    aria-label={`${t("read")} ${t(`articles.${article.slug}.title`)}`}
                  >
                    {t("read")}
                    <ArrowRight className="w-3 h-3 rtl:rotate-180" aria-hidden="true" />
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="blog-newsletter">
        <div className="section-container text-center max-w-2xl">
          <h2 id="blog-newsletter" className="text-3xl font-heading font-semibold text-white mb-4">
            {t("newsletterHeading")}
          </h2>
          <p className="text-cy-gray-400 mb-8">
            {t("newsletterDesc")}
          </p>
          <Link href={`/${l}/contact`} className="btn-primary px-8 py-3 inline-flex">
            {t("subscribeButton")}
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </Link>
        </div>
      </section>
    </div>
  );
}
