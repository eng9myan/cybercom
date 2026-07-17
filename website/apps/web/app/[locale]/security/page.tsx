import { setRequestLocale, getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { Shield, Lock, Eye, CheckCircle2, Server, Globe, FileText } from "lucide-react";
import Link from "next/link";

interface SecurityPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: SecurityPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("securityPage");
  return buildMetadata({
    title: t("metaTitle"),
    description: t("metaDescription"),
    path: "/security",
    locale,
  });
}

const CERTS = [
  { key: "fhir", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  { key: "iso", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  { key: "soc2", color: "text-violet-400", bg: "bg-violet-500/10", border: "border-violet-500/20" },
  { key: "hipaa", color: "text-cyan-400", bg: "bg-cyan-500/10", border: "border-cyan-500/20" },
  { key: "gdpr", color: "text-teal-400", bg: "bg-teal-500/10", border: "border-teal-500/20" },
  { key: "pci", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  { key: "zatca", color: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/20" },
  { key: "oauth", color: "text-indigo-400", bg: "bg-indigo-500/10", border: "border-indigo-500/20" },
];

const PILLARS = [
  { key: "encryption", icon: Lock },
  { key: "access", icon: Eye },
  { key: "infrastructure", icon: Server },
  { key: "residency", icon: Globe },
  { key: "audit", icon: FileText },
  { key: "incident", icon: Shield },
];

export default async function SecurityPage({ params }: SecurityPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;
  const t = await getTranslations("securityPage");

  return (
    <main className="pt-24 pb-20">

      {/* Hero */}
      <section className="py-16 relative overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          aria-hidden="true"
          style={{ background: "radial-gradient(ellipse at 50% 0%, rgba(89,195,225,0.06) 0%, transparent 70%)" }}
        />
        <div className="section-container text-center relative z-10">
          <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-white/[0.09] bg-white/[0.04] mb-8">
            <Shield className="w-4 h-4 text-cy-cyan" />
            <span className="text-xs font-medium text-white/55 tracking-widest uppercase">
              {t("badge")}
            </span>
          </div>
          <h1 className="text-4xl lg:text-6xl font-heading font-semibold text-white mb-6 max-w-4xl mx-auto">
            {t("heroLine1")}<br />
            <span className="text-gradient-aurora">{t("heroLine2")}</span>
          </h1>
          <p className="text-lg text-white/45 max-w-2xl mx-auto leading-relaxed mb-10">
            {t("heroDescription")}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary-glow px-8 py-3.5">
              {t("requestReview")}
            </Link>
            <a href="mailto:security@cy-com.com" className="btn-secondary px-8 py-3.5">
              security@cy-com.com
            </a>
          </div>
        </div>
      </section>

      {/* Certifications */}
      <section className="py-16" aria-labelledby="cert-heading">
        <div className="section-container">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest text-cy-orange mb-3">{t("certifications.eyebrow")}</p>
            <h2 id="cert-heading" className="text-3xl font-heading font-semibold text-white">
              {t("certifications.heading")}
            </h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {CERTS.map((cert) => (
              <div key={cert.key} className="glass-card p-5 rounded-2xl">
                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold mb-4 border ${cert.bg} ${cert.border} ${cert.color}`}>
                  <CheckCircle2 className="w-3 h-3" />
                  {t(`certifications.${cert.key}.name`)}
                </div>
                <p className="text-xs text-cy-gray-400 mb-1">{t(`certifications.${cert.key}.category`)}</p>
                <p className="text-sm text-white/70 leading-relaxed">{t(`certifications.${cert.key}.desc`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security pillars */}
      <section className="py-16 bg-cy-dark/30" aria-labelledby="pillars-heading">
        <div className="section-container">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest text-cy-orange mb-3">{t("pillars.eyebrow")}</p>
            <h2 id="pillars-heading" className="text-3xl font-heading font-semibold text-white">
              {t("pillars.heading")}
            </h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {PILLARS.map((pillar) => {
              const Icon = pillar.icon;
              const items = t.raw(`pillars.${pillar.key}.items`) as string[];
              return (
                <div key={pillar.key} className="glass-card p-6 rounded-2xl">
                  <div className="w-10 h-10 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cy-orange" />
                  </div>
                  <h3 className="font-heading font-semibold text-white mb-4">{t(`pillars.${pillar.key}.title`)}</h3>
                  <ul className="space-y-2">
                    {items.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-sm text-cy-gray-400">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Responsible disclosure */}
      <section className="py-16" aria-labelledby="disclosure-heading">
        <div className="section-container max-w-3xl mx-auto text-center">
          <h2 id="disclosure-heading" className="text-2xl font-heading font-semibold text-white mb-4">
            {t("disclosure.heading")}
          </h2>
          <p className="text-white/50 mb-6 leading-relaxed">
            {t("disclosure.description")}
          </p>
          <a
            href="mailto:security@cy-com.com"
            className="btn-primary inline-flex items-center gap-2"
          >
            <Shield className="w-4 h-4" />
            {t("disclosure.reportButton")}
          </a>
          <p className="text-xs text-white/30 mt-4">
            {t("disclosure.footnote")}
          </p>
        </div>
      </section>

    </main>
  );
}
