"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { type Locale } from "@/lib/i18n";
import { cn } from "@/lib/utils";

interface IndustriesSectionProps {
  locale: Locale;
}

const INDUSTRIES = [
  {
    slug: "healthcare",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6" aria-hidden="true">
        <path d="M9 12h6m-3-3v6M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z" />
      </svg>
    ),
    color: "text-emerald-400",
    border: "hover:border-emerald-500/30",
    bg: "group-hover:bg-emerald-500/5",
  },
  {
    slug: "government",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6" aria-hidden="true">
        <path d="M3 21h18M5 21V7l7-4 7 4v14" />
      </svg>
    ),
    color: "text-amber-400",
    border: "hover:border-amber-500/30",
    bg: "group-hover:bg-amber-500/5",
  },
  {
    slug: "retail",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6" aria-hidden="true">
        <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2 5h14l-2-5M10 19a1 1 0 102 0 1 1 0 00-2 0zm7 0a1 1 0 102 0 1 1 0 00-2 0z" />
      </svg>
    ),
    color: "text-pink-400",
    border: "hover:border-pink-500/30",
    bg: "group-hover:bg-pink-500/5",
  },
  {
    slug: "manufacturing",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6" aria-hidden="true">
        <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
    color: "text-orange-400",
    border: "hover:border-orange-500/30",
    bg: "group-hover:bg-orange-500/5",
  },
  {
    slug: "education",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6" aria-hidden="true">
        <path d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
      </svg>
    ),
    color: "text-sky-400",
    border: "hover:border-sky-500/30",
    bg: "group-hover:bg-sky-500/5",
  },
  {
    slug: "financial",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6" aria-hidden="true">
        <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm0 0v20M2 12h20" />
      </svg>
    ),
    color: "text-green-400",
    border: "hover:border-green-500/30",
    bg: "group-hover:bg-green-500/5",
  },
  {
    slug: "insurance",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6" aria-hidden="true">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
    color: "text-violet-400",
    border: "hover:border-violet-500/30",
    bg: "group-hover:bg-violet-500/5",
  },
  {
    slug: "telecom",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6" aria-hidden="true">
        <path d="M1 6c0 9.941 8.059 18 18 18l3-6-6-3-2.029 2.029C11.179 15.237 8.763 12.821 7.029 9.971L9 8 6 2H3C1.895 2 1 2.895 1 4v2z" />
      </svg>
    ),
    color: "text-cyan-400",
    border: "hover:border-cyan-500/30",
    bg: "group-hover:bg-cyan-500/5",
  },
];

export function IndustriesSection({ locale }: IndustriesSectionProps) {
  const t = useTranslations("industries");
  const shouldReduce = useReducedMotion();

  return (
    <section className="py-24 bg-cy-dark/30" aria-labelledby="industries-heading">
      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: shouldReduce ? 0 : 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">Industries</p>
          <h2 id="industries-heading" className="text-4xl lg:text-5xl font-heading font-semibold text-white mb-4">
            {t("title")}
          </h2>
          <p className="text-lg text-cy-gray-400 max-w-2xl mx-auto">{t("subtitle")}</p>
        </motion.div>

        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {INDUSTRIES.map((industry, i) => (
            <motion.div
              key={industry.slug}
              initial={{ opacity: 0, y: shouldReduce ? 0 : 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.1 }}
              transition={{ duration: 0.5, delay: i * 0.06 }}
            >
              <Link
                href={`/${locale}/industries/${industry.slug}`}
                className={cn(
                  "glass-card group flex flex-col items-start p-5 rounded-2xl border border-cy-glass-border transition-all duration-300 cursor-pointer",
                  industry.border
                )}
                aria-label={`${t(`${industry.slug}.name`)} industry solutions`}
              >
                <div className={cn("mb-3 transition-colors duration-200", industry.color, industry.bg, "p-2 rounded-lg -ml-2")}>
                  {industry.icon}
                </div>
                <h3 className="font-heading font-semibold text-white text-sm mb-1">
                  {t(`${industry.slug}.name`)}
                </h3>
                <p className="text-xs text-cy-gray-400 leading-relaxed">
                  {t(`${industry.slug}.description`)}
                </p>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
