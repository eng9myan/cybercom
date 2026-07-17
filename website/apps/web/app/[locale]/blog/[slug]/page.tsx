import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowLeft, Calendar, Clock, Tag, User } from "lucide-react";

interface ArticlePageProps {
  params: Promise<{ locale: string; slug: string }>;
}

const ARTICLES_META: Record<string, { category: string; date: string; readTime: string }> = {
  "fhir-r4-interoperability-mena": { category: "Healthcare IT", date: "2026-06-15", readTime: "8 min read" },
  "icd-11-clinical-coding-readiness": { category: "Clinical", date: "2026-06-08", readTime: "6 min read" },
  "drug-interaction-engine-design": { category: "Clinical", date: "2026-06-01", readTime: "10 min read" },
  "zero-trust-healthcare-identity": { category: "Platform", date: "2026-05-25", readTime: "7 min read" },
  "government-digital-transformation-gcc": { category: "Government", date: "2026-05-18", readTime: "9 min read" },
  "postgresql-rls-multi-tenancy": { category: "Platform", date: "2026-05-10", readTime: "12 min read" },
  "healthcare-erp-integration-patterns": { category: "Enterprise", date: "2026-05-02", readTime: "7 min read" },
  "cybercom-release-2-production-readiness": { category: "Platform", date: "2026-04-28", readTime: "5 min read" },
};

export async function generateStaticParams() {
  return Object.keys(ARTICLES_META).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: ArticlePageProps): Promise<Metadata> {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const meta = ARTICLES_META[slug];
  if (!meta) return {};
  const t = await getTranslations("blogPage");
  const title = t(`articles.${slug}.title`);
  const excerpt = t(`articles.${slug}.excerpt`);

  return buildMetadata({
    title: `${title} — ${t("badge")}`,
    description: excerpt,
    path: `/blog/${slug}`,
    locale,
  });
}

export default async function ArticleDetailPage({ params }: ArticlePageProps) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const meta = ARTICLES_META[slug];

  if (!meta) notFound();

  const t = await getTranslations("blogPage");
  const ta = await getTranslations("blogArticles");
  const isAr = locale === "ar";
  const formattedDate = new Date(meta.date).toLocaleDateString(isAr ? "ar-EG" : "en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const paragraphs = ta.raw(`articles.${slug}.paragraphs`) as string[];

  return (
    <div className="min-h-dvh pt-24 pb-16">
      <div className="section-container max-w-3xl">
        {/* Back Link */}
        <Link
          href={`/${locale}/blog`}
          className="inline-flex items-center gap-2 text-sm text-cy-gray-400 hover:text-white transition-colors mb-8 group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform rtl:rotate-180" />
          {ta("backToBlog")}
        </Link>

        {/* Article Header */}
        <article className="space-y-6">
          <div className="space-y-3">
            <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5">
              <Tag className="w-3 h-3" aria-hidden="true" />
              {t(`categories.${meta.category}`)}
            </span>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-heading font-semibold text-white leading-tight">
              {t(`articles.${slug}.title`)}
            </h1>
          </div>

          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-6 py-4 border-y border-cy-glass-border text-xs text-cy-gray-400">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center">
                <User className="w-3.5 h-3.5 text-cy-gray-400" />
              </div>
              <div>
                <p className="font-medium text-white">{ta(`articles.${slug}.author`)}</p>
                <p className="text-2xs text-cy-gray-500">{ta(`articles.${slug}.authorRole`)}</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              <time dateTime={meta.date}>{formattedDate}</time>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              <span>{t(`articles.${slug}.readTime`)}</span>
            </div>
          </div>

          {/* Body Paragraphs */}
          <div className="space-y-6 text-cy-gray-300 leading-relaxed text-base pt-4">
            {paragraphs.map((para, index) => (
              <p key={index}>{para}</p>
            ))}
          </div>
        </article>
      </div>
    </div>
  );
}
