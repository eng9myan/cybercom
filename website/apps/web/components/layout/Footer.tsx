"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { type Locale } from "@/lib/i18n";
import { Mail, ArrowRight, Check, Linkedin, Twitter, Github } from "lucide-react";
import { contactApi } from "@cybercom/api";

interface FooterProps {
  locale: Locale;
}

const PRODUCTS = [
  { name: "CyMed", slug: "cymed" },
  { name: "CyShop", slug: "cyshop" },
  { name: "CyCom ERP", slug: "cycom" },
  { name: "CyGov", slug: "cygov" },
  { name: "CyAI", slug: "cyai" },
  { name: "CyIdentity", slug: "cyidentity" },
  { name: "CyIntegrationHub", slug: "cyintegrationhub" },
  { name: "CyData", slug: "cydata" },
  { name: "CyConnect", slug: "cyconnect" },
  { name: "CyCitizen", slug: "cycitizen" },
];

const COMPANY_LINKS = [
  { key: "about", href: "/about" },
  { key: "solutions", href: "/solutions" },
  { key: "pricing", href: "/pricing" },
  { key: "blog", href: "/blog" },
  { key: "careers", href: "/careers" },
  { key: "investors", href: "/investors" },
  { key: "partners", href: "/partners" },
  { key: "contact", href: "/contact" },
];

export function Footer({ locale }: FooterProps) {
  const t = useTranslations("footer");
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  async function handleSubscribe(e: React.FormEvent) {
    e.preventDefault();
    if (!email || status === "loading") return;
    setStatus("loading");
    try {
      await contactApi.subscribeNewsletter({ email, source: "footer", gdpr_consent: true });
      setStatus("success");
      setEmail("");
    } catch {
      setStatus("error");
      setTimeout(() => setStatus("idle"), 4000);
    }
  }

  return (
    <footer className="border-t border-cy-glass-border bg-cy-dark/50 mt-auto" role="contentinfo">
      <div className="section-container py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          {/* Brand */}
          <div className="lg:col-span-1">
            <Link href={`/${locale}`} className="flex items-center gap-2.5 mb-4 group" aria-label="CyberCom Revolution">
              <div className="w-9 h-9 rounded-xl bg-gradient-cy flex items-center justify-center group-hover:shadow-orange-glow transition-shadow duration-300">
                <span className="text-white font-heading font-bold text-sm">Cy</span>
              </div>
              <span className="font-heading font-semibold text-white text-lg">CyberCom</span>
            </Link>
            <p className="text-sm text-cy-gray-400 leading-relaxed mb-6 max-w-xs">
              {t("tagline")}
            </p>
            <div className="flex items-center gap-3">
              <a href="https://linkedin.com/company/cybercom-revolution" target="_blank" rel="noreferrer" aria-label="LinkedIn" className="w-9 h-9 rounded-lg border border-cy-glass-border flex items-center justify-center text-cy-gray-400 hover:text-white hover:border-cy-glass-bg-hover transition-colors cursor-pointer">
                <Linkedin className="w-4 h-4" aria-hidden="true" />
              </a>
              <a href="https://twitter.com/CyberComRev" target="_blank" rel="noreferrer" aria-label="Twitter / X" className="w-9 h-9 rounded-lg border border-cy-glass-border flex items-center justify-center text-cy-gray-400 hover:text-white hover:border-cy-glass-bg-hover transition-colors cursor-pointer">
                <Twitter className="w-4 h-4" aria-hidden="true" />
              </a>
              <a href="https://github.com/eng9myan" target="_blank" rel="noreferrer" aria-label="GitHub" className="w-9 h-9 rounded-lg border border-cy-glass-border flex items-center justify-center text-cy-gray-400 hover:text-white hover:border-cy-glass-bg-hover transition-colors cursor-pointer">
                <Github className="w-4 h-4" aria-hidden="true" />
              </a>
            </div>
          </div>

          {/* Products */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-4">{t("productsHeading")}</h3>
            <ul className="space-y-2.5">
              {PRODUCTS.map((p) => (
                <li key={p.slug}>
                  <Link
                    href={
                      p.slug === "cyshop"
                        ? `/${locale}/cyshop`
                        : p.slug === "cycom"
                        ? `/${locale}/erp`
                        : p.slug === "cymed"
                        ? `/${locale}/cymed`
                        : `/${locale}/products/${p.slug}`
                    }
                    className="text-sm text-cy-gray-400 hover:text-white transition-colors duration-150"
                  >
                    {p.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-4">{t("companyHeading")}</h3>
            <ul className="space-y-2.5">
              {COMPANY_LINKS.map((link) => (
                <li key={link.key}>
                  <Link
                    href={`/${locale}${link.href}`}
                    className="text-sm text-cy-gray-400 hover:text-white transition-colors duration-150"
                  >
                    {link.key.charAt(0).toUpperCase() + link.key.slice(1)}
                  </Link>
                </li>
              ))}
              <li>
                <Link href={`/${locale}/documentation`} className="text-sm text-cy-gray-400 hover:text-white transition-colors duration-150">
                  Documentation
                </Link>
              </li>
              <li>
                <Link href={`/${locale}/partner`} className="text-sm text-cy-gray-400 hover:text-white transition-colors duration-150">
                  Partner Portal
                </Link>
              </li>
            </ul>
          </div>

          {/* Newsletter */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">{t("newsletter.title")}</h3>
            <p className="text-xs text-cy-gray-400 mb-4">{t("newsletterDesc")}</p>
            <form onSubmit={handleSubscribe} noValidate aria-label="Newsletter subscription">
              <div className="relative">
                <label htmlFor="footer-email" className="sr-only">
                  {t("newsletter.placeholder")}
                </label>
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cy-gray-600 pointer-events-none" aria-hidden="true" />
                <input
                  id="footer-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t("newsletter.placeholder")}
                  className="form-input pl-9 pr-10 text-sm"
                  disabled={status === "loading" || status === "success"}
                  required
                  aria-required="true"
                />
                <button
                  type="submit"
                  disabled={status === "loading" || status === "success" || !email}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-7 h-7 rounded-lg bg-cy-orange flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed hover:bg-cy-orange-light transition-colors cursor-pointer"
                  aria-label={t("newsletter.subscribe")}
                >
                  {status === "success" ? (
                    <Check className="w-3.5 h-3.5 text-white" aria-hidden="true" />
                  ) : (
                    <ArrowRight className="w-3.5 h-3.5 text-white" aria-hidden="true" />
                  )}
                </button>
              </div>
              {status === "success" && (
                <p className="mt-2 text-xs text-cy-cyan" role="status" aria-live="polite">
                  {t("newsletter.success")}
                </p>
              )}
              {status === "error" && (
                <p className="mt-2 text-xs text-destructive" role="alert">
                  Something went wrong. Please try again.
                </p>
              )}
            </form>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-cy-glass-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-cy-gray-600">{t("copyright")}</p>
          <div className="flex items-center gap-6">
            <Link href={`/${locale}/legal/privacy`} className="text-xs text-cy-gray-600 hover:text-white transition-colors">
              {t("legal.privacy")}
            </Link>
            <Link href={`/${locale}/legal/terms`} className="text-xs text-cy-gray-600 hover:text-white transition-colors">
              {t("legal.terms")}
            </Link>
            <Link href={`/${locale}/legal/cookies`} className="text-xs text-cy-gray-600 hover:text-white transition-colors">
              {t("legal.cookies")}
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
