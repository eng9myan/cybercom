import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, BookOpen, Code2, ShieldCheck, Stethoscope, ShoppingBag, Factory, Search, FileText, Video } from "lucide-react";

interface DocumentationPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: DocumentationPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("documentationPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/documentation",
    locale,
  });
}

const DOCS_URL = process.env.NEXT_PUBLIC_DOCS_URL ?? "https://docs.cy-com.com";

const DOC_SECTIONS = [
  { key: "cymed", icon: Stethoscope, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", hrefs: [`${DOCS_URL}/cymed/getting-started`, `${DOCS_URL}/cymed/fhir-api`, `${DOCS_URL}/cymed/hospital/deployment`, `${DOCS_URL}/cymed/pharmacy/drug-interactions`, `${DOCS_URL}/cymed/integration/hl7`] },
  { key: "cyshop", icon: ShoppingBag, color: "text-cy-orange", bg: "bg-cy-orange/10 border-cy-orange/20", hrefs: [`${DOCS_URL}/cyshop/getting-started`, `${DOCS_URL}/cyshop/pos/setup`, `${DOCS_URL}/cyshop/restaurant`, `${DOCS_URL}/cyshop/inventory`, `${DOCS_URL}/cyshop/loyalty`] },
  { key: "cycom", icon: Factory, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20", hrefs: [`${DOCS_URL}/cycom/getting-started`, `${DOCS_URL}/cycom/finance/chart-of-accounts`, `${DOCS_URL}/cycom/payroll/wps`, `${DOCS_URL}/cycom/procurement`, `${DOCS_URL}/cycom/bi`] },
  { key: "platform", icon: ShieldCheck, color: "text-violet-400", bg: "bg-violet-500/10 border-violet-500/20", hrefs: [`${DOCS_URL}/platform/architecture`, `${DOCS_URL}/platform/identity/oauth`, `${DOCS_URL}/platform/tenants`, `${DOCS_URL}/platform/rbac`, `${DOCS_URL}/platform/audit`] },
  { key: "api", icon: Code2, color: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/20", hrefs: [`${DOCS_URL}/api`, `${DOCS_URL}/api/auth`, `${DOCS_URL}/api/fhir`, `${DOCS_URL}/api/webhooks`, `${DOCS_URL}/api/sdk`] },
  { key: "ops", icon: BookOpen, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20", hrefs: [`${DOCS_URL}/ops/kubernetes`, `${DOCS_URL}/ops/helm`, `${DOCS_URL}/ops/backup`, `${DOCS_URL}/ops/monitoring`, `${DOCS_URL}/ops/dr`] },
];

const QUICK_LINKS = [
  { key: "search", icon: Search, href: `${DOCS_URL}/search` },
  { key: "videos", icon: Video, href: `${DOCS_URL}/videos` },
  { key: "releases", icon: FileText, href: `${DOCS_URL}/releases` },
  { key: "playground", icon: Code2, href: `${DOCS_URL}/playground` },
];

export default async function DocumentationPage({ params }: DocumentationPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("documentationPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <section className="relative py-24 overflow-hidden" aria-labelledby="docs-heading">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="glow-orb w-[500px] h-[500px] -top-16 left-1/4 bg-violet-500/5" />
          <div className="glow-orb w-[400px] h-[400px] bottom-0 right-0 bg-cyan-500/5" />
        </div>
        <div className="section-container relative z-10 text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-violet-500/20 bg-violet-500/5 mb-6">
            <BookOpen className="w-3.5 h-3.5 text-violet-400" aria-hidden="true" />
            <span className="text-xs font-medium text-violet-400 tracking-wider uppercase">{t("badge")}</span>
          </div>
          <h1 id="docs-heading" className="text-4xl sm:text-5xl font-heading font-semibold text-white mb-6 leading-tight">
            {t("headingLine1")}{" "}<br />
            <span className="text-gradient-orange">{t("headingLine2")}</span>
          </h1>
          <p className="text-lg text-cy-gray-400 leading-relaxed mb-8">
            {t("description")}
          </p>
          <a
            href={DOCS_URL}
            target="_blank"
            rel="noreferrer"
            className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2"
          >
            {t("openFullDocs")}
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </a>
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12 border-y border-cy-glass-border bg-cy-dark/30" aria-label="Quick access links">
        <div className="section-container">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {QUICK_LINKS.map((q) => (
              <a
                key={q.key}
                href={q.href}
                target="_blank"
                rel="noreferrer"
                className="glass-card rounded-xl p-5 flex items-start gap-4 hover:border-cy-glass-bg-hover transition-all duration-150 cursor-pointer group"
              >
                <div className="w-9 h-9 rounded-lg bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center flex-shrink-0">
                  <q.icon className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                </div>
                <div>
                  <div className="text-sm font-medium text-white group-hover:text-cy-orange transition-colors">{t(`quickLinks.${q.key}.label`)}</div>
                  <div className="text-xs text-cy-gray-400 mt-0.5">{t(`quickLinks.${q.key}.desc`)}</div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Documentation Sections */}
      <section className="py-20" aria-labelledby="doc-sections-heading">
        <div className="section-container">
          <h2 id="doc-sections-heading" className="sr-only">{t("badge")}</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {DOC_SECTIONS.map((section) => {
              const title = t(`sections.${section.key}.title`);
              const links = t.raw(`sections.${section.key}.links`) as string[];
              return (
                <div key={section.key} className={`glass-card rounded-2xl p-7 border ${section.bg} flex flex-col`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center border mb-4 ${section.bg}`}>
                    <section.icon className={`w-5 h-5 ${section.color}`} aria-hidden="true" />
                  </div>
                  <h3 className={`text-base font-heading font-semibold ${section.color} mb-2`}>{title}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed mb-5 flex-1">{t(`sections.${section.key}.desc`)}</p>
                  <ul className="space-y-2" aria-label={`${title} documentation links`}>
                    {links.map((label, i) => (
                      <li key={label}>
                        <a
                          href={section.hrefs[i]}
                          target="_blank"
                          rel="noreferrer"
                          className={`text-sm ${section.color} hover:underline flex items-center gap-1.5`}
                        >
                          <ArrowRight className="w-3 h-3 rtl:rotate-180 flex-shrink-0" aria-hidden="true" />
                          {label}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Support CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="support-cta-heading">
        <div className="section-container text-center max-w-3xl mx-auto">
          <h2 id="support-cta-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("cantFind")}</h2>
          <p className="text-cy-gray-400 mb-8">{t("supportDesc")}</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link href={`/${l}/contact`} className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2">
              {t("contactSupport")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <a href={`${DOCS_URL}/community`} target="_blank" rel="noreferrer" className="btn-secondary px-8 py-3 text-sm">
              {t("communityForum")}
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
