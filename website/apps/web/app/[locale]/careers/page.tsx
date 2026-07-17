import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Code2, HeartPulse, BarChart3, Headphones, Users, Globe } from "lucide-react";

interface CareersPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: CareersPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("careersPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/careers",
    locale,
  });
}

const WHY_JOIN = [
  { key: "purpose", icon: HeartPulse },
  { key: "tech", icon: Code2 },
  { key: "impact", icon: Globe },
  { key: "team", icon: Users },
];

const DEPARTMENTS = [
  { key: "engineering", icon: Code2 },
  { key: "healthcare", icon: HeartPulse },
  { key: "product", icon: BarChart3 },
  { key: "success", icon: Headphones },
];

const VALUES = ["standards", "safety", "ownership", "transparency"];

export default async function CareersPage({ params }: CareersPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("careersPage");
  const perks = t.raw("perks") as string[];

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/6" />
        </div>
        <div className="section-container relative z-10 max-w-4xl">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            {t("badge")}
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight">
            {t("headingPrefix")}{" "}
            <span className="text-gradient">{t("headingHighlight")}</span>
          </h1>
          <p className="text-xl text-cy-gray-400 leading-relaxed max-w-3xl mb-8">
            {t("heroDesc")}
          </p>
          <Link
            href={`mailto:careers@cy-com.com`}
            className="btn-primary px-8 py-3 inline-flex"
          >
            {t("sendApplication")}
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </Link>
        </div>
      </div>

      {/* Why Join */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="why-heading">
        <div className="section-container">
          <h2 id="why-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            {t("whyHeading")}
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {WHY_JOIN.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.key} className="glass-card p-6 rounded-2xl flex gap-4">
                  <div className="w-10 h-10 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <h3 className="font-heading font-semibold text-white mb-2">{t(`whyJoin.${item.key}.title`)}</h3>
                    <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`whyJoin.${item.key}.desc`)}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Open Roles */}
      <section className="py-20" aria-labelledby="roles-heading">
        <div className="section-container">
          <h2 id="roles-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            {t("rolesHeading")}
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-2xl mx-auto">
            {t("rolesDesc")}
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            {DEPARTMENTS.map((dept) => {
              const Icon = dept.icon;
              const roles = t.raw(`departments.${dept.key}.roles`) as string[];
              return (
                <div key={dept.key} className="glass-card p-6 rounded-2xl">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-9 h-9 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center">
                      <Icon className="w-4.5 h-4.5 text-cy-orange" aria-hidden="true" />
                    </div>
                    <h3 className="font-heading font-semibold text-white">{t(`departments.${dept.key}.name`)}</h3>
                  </div>
                  <ul className="space-y-3">
                    {roles.map((role) => (
                      <li key={role} className="flex items-start justify-between gap-4 group">
                        <span className="text-sm text-cy-gray-200">{role}</span>
                        <a
                          href={`mailto:careers@cy-com.com?subject=Application: ${encodeURIComponent(role)}`}
                          className="text-xs text-cy-orange hover:text-cy-orange-light transition-colors whitespace-nowrap flex items-center gap-1 cursor-pointer"
                          aria-label={`${t("apply")} — ${role}`}
                        >
                          {t("apply")}
                          <ArrowRight className="w-3 h-3 rtl:rotate-180" aria-hidden="true" />
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

      {/* Values */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="values-heading">
        <div className="section-container">
          <h2 id="values-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            {t("howWeWorkHeading")}
          </h2>
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {VALUES.map((key) => (
              <div key={key} className="glass-card p-6 rounded-2xl flex gap-4">
                <div className="w-1 rounded-full bg-gradient-cy flex-shrink-0" aria-hidden="true" />
                <div>
                  <h3 className="font-heading font-semibold text-white mb-1">{t(`values.${key}.title`)}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed">{t(`values.${key}.desc`)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Perks */}
      <section className="py-20" aria-labelledby="perks-heading">
        <div className="section-container">
          <h2 id="perks-heading" className="text-3xl font-heading font-semibold text-white mb-12 text-center">
            {t("perksHeading")}
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 max-w-4xl mx-auto">
            {perks.map((perk) => (
              <div key={perk} className="glass-card px-4 py-3 rounded-xl flex items-center gap-2.5">
                <div className="w-2 h-2 rounded-full bg-cy-orange flex-shrink-0" aria-hidden="true" />
                <span className="text-sm text-cy-gray-200">{perk}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Apply CTA */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="careers-cta">
        <div className="section-container text-center max-w-2xl">
          <h2 id="careers-cta" className="text-3xl font-heading font-semibold text-white mb-4">
            {t("ctaHeading")}
          </h2>
          <p className="text-cy-gray-400 mb-8 leading-relaxed">
            {t("ctaDesc")}
          </p>
          <a
            href="mailto:careers@cy-com.com"
            className="btn-primary px-8 py-3 inline-flex"
          >
            careers@cy-com.com
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </a>
        </div>
      </section>
    </div>
  );
}
