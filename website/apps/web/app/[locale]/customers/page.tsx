import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Star, Building2, FlaskConical, Microscope, ShoppingBag, Factory } from "lucide-react";

interface CustomersPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: CustomersPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("customersPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/customers",
    locale,
  });
}

const INDUSTRIES = [
  { key: "hospital", icon: Building2, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { key: "clinics", icon: FlaskConical, color: "text-teal-400", bg: "bg-teal-500/10 border-teal-500/20" },
  { key: "labs", icon: Microscope, color: "text-sky-400", bg: "bg-sky-500/10 border-sky-500/20" },
  { key: "retail", icon: ShoppingBag, color: "text-cy-orange", bg: "bg-cy-orange/10 border-cy-orange/20" },
  { key: "enterprise", icon: Factory, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
];

const TESTIMONIALS = [
  { key: "t1", product: "CyMed Hospital", color: "text-emerald-400" },
  { key: "t2", product: "CyShop", color: "text-cy-orange" },
  { key: "t3", product: "CyCom ERP", color: "text-blue-400" },
  { key: "t4", product: "CyMed Pharmacy", color: "text-violet-400" },
  { key: "t5", product: "CyMed Laboratory", color: "text-teal-400" },
  { key: "t6", product: "CyShop", color: "text-cy-orange" },
];

export default async function CustomersPage({ params }: CustomersPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("customersPage");

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <section className="relative py-24 overflow-hidden" aria-labelledby="customers-heading">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="glow-orb w-[600px] h-[600px] -top-32 right-0 bg-emerald-500/5" />
          <div className="glow-orb w-[400px] h-[400px] bottom-0 left-0 bg-cy-orange/5" />
        </div>
        <div className="section-container relative z-10 text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cy-orange/20 bg-cy-orange/5 mb-6">
            <div className="w-1.5 h-1.5 rounded-full bg-cy-orange animate-pulse" aria-hidden="true" />
            <span className="text-xs font-medium text-cy-orange tracking-wider uppercase">{t("badge")}</span>
          </div>
          <h1 id="customers-heading" className="text-4xl sm:text-5xl font-heading font-semibold text-white mb-6 leading-tight">
            {t("heroLine1")}<br />
            <span className="text-gradient-orange">{t("heroLine2")}</span>
          </h1>
          <p className="text-lg text-cy-gray-400 leading-relaxed max-w-2xl mx-auto mb-8">
            {t("heroDescription")}
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary px-6 py-3 text-sm inline-flex items-center gap-2">
              {t("requestDemo")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/contact`} className="btn-secondary px-6 py-3 text-sm">
              {t("contactSales")}
            </Link>
          </div>
        </div>
      </section>

      {/* Industries We Serve */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="industries-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="industries-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("industries.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("industries.subheading")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {INDUSTRIES.map((ind) => (
              <div key={ind.key} className={`glass-card rounded-xl p-6 border ${ind.bg}`}>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center border mb-4 ${ind.bg}`}>
                  <ind.icon className={`w-5 h-5 ${ind.color}`} aria-hidden="true" />
                </div>
                <h3 className={`text-sm font-heading font-semibold ${ind.color} mb-2`}>{t(`industries.${ind.key}.label`)}</h3>
                <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`industries.${ind.key}.desc`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20" aria-labelledby="testimonials-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="testimonials-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("testimonials.heading")}</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">{t("testimonials.subheading")}</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {TESTIMONIALS.map((item) => (
              <div key={item.key} className="glass-card rounded-2xl p-7 flex flex-col">
                <div className="flex items-center gap-1 mb-4" aria-label="5 stars">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star key={i} className="w-4 h-4 text-cy-orange fill-cy-orange" aria-hidden="true" />
                  ))}
                </div>
                <blockquote className="text-sm text-cy-gray-200 leading-relaxed flex-1 mb-6 italic">
                  &ldquo;{t(`testimonials.${item.key}.quote`)}&rdquo;
                </blockquote>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-white">{t(`testimonials.${item.key}.name`)}</div>
                    <div className="text-xs text-cy-gray-400">{t(`testimonials.${item.key}.role`)}</div>
                    <div className="text-xs text-cy-gray-400">{t(`testimonials.${item.key}.org`)} · {t(`testimonials.${item.key}.country`)}</div>
                  </div>
                  <span className={`product-badge text-xs ${item.color} border-current/20 bg-current/5 flex-shrink-0`}>{item.product}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="cta-heading">
        <div className="section-container text-center max-w-3xl mx-auto">
          <h2 id="cta-heading" className="text-3xl font-heading font-semibold text-white mb-4">{t("cta.heading")}</h2>
          <p className="text-cy-gray-400 mb-8">{t("cta.subheading")}</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2">
              {t("cta.bookDemo")}
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3 text-sm">
              {t("cta.contactSales")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
