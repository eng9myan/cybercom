"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { type Locale } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { Menu, X, ChevronDown, Globe, Sun, Moon } from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";

interface NavbarProps {
  locale: Locale;
}

const PRODUCTS_MEGA_MENU = [
  {
    category: "Healthcare · CyMed",
    items: [
      { name: "CyMed", slug: "cymed", desc: "Complete healthcare platform" },
      { name: "CyMed Clinic", slug: "cymed-clinic", desc: "Outpatient clinical management" },
      { name: "CyMed Hospital", slug: "cymed-hospital", desc: "Complete hospital operations" },
      { name: "CyMed Laboratory", slug: "cymed-laboratory", desc: "LIS with auto-verification" },
      { name: "CyMed Imaging", slug: "cymed-imaging", desc: "RIS/DICOM PACS integration" },
      { name: "CyMed Pharmacy", slug: "cymed-pharmacy", desc: "Clinical pharmacy management" },
      { name: "CyMed Patient Portal", slug: "cymed-patient-portal", desc: "Patient self-service & records" },
      { name: "CyMed Provider Portal", slug: "cymed-provider-portal", desc: "Provider tools & scheduling" },
      { name: "CyMed Revenue Cycle", slug: "cymed-revenue-cycle", desc: "Billing, coding, collections" },
      { name: "CyMed Population Health", slug: "cymed-population-health", desc: "Analytics & care programs" },
    ],
  },
  {
    category: "Retail · CyShop",
    items: [
      { name: "CyShop", slug: "cyshop", desc: "Complete retail & commerce platform" },
      { name: "Restaurant & F&B", slug: "cyshop-restaurant", desc: "Dine-in, takeaway, delivery POS" },
      { name: "Grocery & Supermarket", slug: "cyshop-supermarket", desc: "Weighted items, loyalty, self-checkout" },
      { name: "Bakery & Coffee", slug: "cyshop-bakery", desc: "Recipe management, barista workflow" },
    ],
  },
  {
    category: "Enterprise · CyCom ERP",
    items: [
      { name: "CyCom ERP", slug: "cycom", desc: "Unified enterprise resource planning" },
      { name: "CyGov", slug: "cygov", desc: "Government digital transformation" },
      { name: "CyAI", slug: "cyai", desc: "AI & intelligence platform" },
      { name: "CyData", slug: "cydata", desc: "Data lakehouse & analytics" },
    ],
  },
  {
    category: "Platform",
    items: [
      { name: "CyIdentity", slug: "cyidentity", desc: "OAuth 2.1, OIDC, Zero Trust" },
      { name: "CyIntegrationHub", slug: "cyintegrationhub", desc: "FHIR, HL7, REST integration" },
      { name: "CyConnect", slug: "cyconnect", desc: "Unified communications" },
      { name: "CyCitizen", slug: "cycitizen", desc: "Citizen experience platform" },
    ],
  },
];

export function Navbar({ locale }: NavbarProps) {
  const t = useTranslations("nav");
  const { theme, toggle: toggleTheme } = useTheme();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [productsOpen, setProductsOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  const altLocale = locale === "en" ? "ar" : "en";

  return (
    <header
      className={cn(
        "fixed top-0 inset-x-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-cy-black/90 backdrop-blur-xl border-b border-cy-glass-border shadow-glass"
          : "bg-transparent"
      )}
      role="banner"
    >
      <nav
        className="section-container flex items-center justify-between h-16"
        aria-label="Main navigation"
      >
        {/* Logo */}
        <Link
          href={`/${locale}`}
          className="flex items-center gap-2.5 focus-visible:ring-2 focus-visible:ring-cy-orange rounded-lg"
          aria-label="CyberCom Revolution — Home"
        >
          <div className="w-8 h-8 rounded-lg bg-gradient-cy flex items-center justify-center">
            <span className="text-white font-heading font-bold text-sm">Cy</span>
          </div>
          <span className="font-heading font-semibold text-white text-base hidden sm:block">
            CyberCom
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden lg:flex items-center gap-1">
          {/* Products mega menu */}
          <div className="relative">
            <button
              className="btn-ghost flex items-center gap-1"
              onMouseEnter={() => setProductsOpen(true)}
              onMouseLeave={() => setProductsOpen(false)}
              onClick={() => setProductsOpen((v) => !v)}
              aria-expanded={productsOpen}
              aria-haspopup="true"
            >
              {t("products")}
              <ChevronDown
                className={cn("w-3.5 h-3.5 transition-transform duration-200", productsOpen && "rotate-180")}
                aria-hidden="true"
              />
            </button>

            {productsOpen && (
              <div
                className="absolute top-full mt-1 left-0 w-[900px] p-6 glass-card rounded-2xl grid grid-cols-4 gap-5"
                onMouseEnter={() => setProductsOpen(true)}
                onMouseLeave={() => setProductsOpen(false)}
                role="menu"
              >
                {PRODUCTS_MEGA_MENU.map((group) => (
                  <div key={group.category}>
                    <p className="text-2xs font-medium text-cy-gray-400 uppercase tracking-wider mb-3">
                      {group.category}
                    </p>
                    <ul className="space-y-1">
                      {group.items.map((item) => (
                        <li key={item.slug}>
                          <Link
                            href={
                              item.slug === "cyshop" || item.slug.startsWith("cyshop-")
                                ? `/${locale}/cyshop`
                                : item.slug === "cycom"
                                ? `/${locale}/erp`
                                : item.slug === "cymed"
                                ? `/${locale}/cymed`
                                : `/${locale}/products/${item.slug}`
                            }
                            className="block px-2 py-1.5 rounded-lg text-sm text-cy-gray-200 hover:text-white hover:bg-cy-glass-bg transition-colors duration-150 focus-visible:ring-1 focus-visible:ring-cy-orange"
                            role="menuitem"
                          >
                            <span className="font-medium block">{item.name}</span>
                            <span className="text-2xs text-cy-gray-400">{item.desc}</span>
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Link href={`/${locale}/solutions`} className="btn-ghost">{t("solutions")}</Link>
          <Link href={`/${locale}/industries`} className="btn-ghost">{t("industries")}</Link>
          <Link href={`/${locale}/pricing`} className="btn-ghost">{t("pricing")}</Link>
          <Link href={`/${locale}/demo-center`} className="btn-ghost text-cy-orange font-medium border border-cy-orange/20 bg-cy-orange/5 hover:bg-cy-orange/10 rounded-lg px-3 py-1.5 transition-all duration-200">{t("demoCenter")}</Link>
          <Link href={`/${locale}/partners`} className="btn-ghost">{t("partners")}</Link>
          <Link href={`/${locale}/marketplace`} className="btn-ghost">{t("marketplace")}</Link>
          <Link href={`/${locale}/documentation`} className="btn-ghost">{t("docs")}</Link>
          <Link href={`/${locale}/about`} className="btn-ghost">{t("about")}</Link>
        </div>

        {/* Actions */}
        <div className="hidden lg:flex items-center gap-2">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="btn-ghost p-2 rounded-lg"
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              <Sun className="w-4 h-4 text-white/60 hover:text-cy-orange transition-colors" aria-hidden="true" />
            ) : (
              <Moon className="w-4 h-4 text-slate-500 hover:text-cy-orange transition-colors" aria-hidden="true" />
            )}
          </button>

          {/* Locale switcher */}
          <Link
            href={`/${altLocale}`}
            className="btn-ghost text-xs flex items-center gap-1.5"
            aria-label={`Switch to ${altLocale === "en" ? "English" : "العربية"}`}
          >
            <Globe className="w-3.5 h-3.5" aria-hidden="true" />
            {altLocale === "en" ? "EN" : "AR"}
          </Link>

          <Link
            href={process.env.NEXT_PUBLIC_PORTAL_URL ?? `/${locale}/portal`}
            className="btn-secondary text-sm py-2 px-4"
          >
            {t("portal")}
          </Link>

          <Link href={`/${locale}/demo`} className="btn-primary text-sm py-2 px-4">
            {t("requestDemo")}
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="lg:hidden btn-ghost p-2"
          onClick={() => setMobileOpen((v) => !v)}
          aria-expanded={mobileOpen}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
        >
          {mobileOpen ? (
            <X className="w-5 h-5" aria-hidden="true" />
          ) : (
            <Menu className="w-5 h-5" aria-hidden="true" />
          )}
        </button>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="lg:hidden bg-cy-dark/95 backdrop-blur-xl border-b border-cy-glass-border">
          <nav className="section-container py-4 space-y-1" aria-label="Mobile navigation">
            {PRODUCTS_MEGA_MENU.flatMap((g) =>
              g.items.map((item) => (
                <Link
                  key={item.slug}
                  href={
                    item.slug === "cyshop" || item.slug.startsWith("cyshop-")
                      ? `/${locale}/cyshop`
                      : item.slug === "cycom"
                      ? `/${locale}/erp`
                      : `/${locale}/products/${item.slug}`
                  }
                  className="block px-3 py-2.5 rounded-xl text-sm text-cy-gray-200 hover:text-white hover:bg-cy-glass-bg transition-colors"
                  onClick={() => setMobileOpen(false)}
                >
                  {item.name}
                </Link>
              ))
            )}
            <div className="h-px bg-cy-glass-border my-3" />
            <Link href={`/${locale}/solutions`} className="block px-3 py-2.5 rounded-xl text-sm text-cy-gray-200 hover:text-white hover:bg-cy-glass-bg transition-colors" onClick={() => setMobileOpen(false)}>{t("solutions")}</Link>
            <Link href={`/${locale}/industries`} className="block px-3 py-2.5 rounded-xl text-sm text-cy-gray-200 hover:text-white hover:bg-cy-glass-bg transition-colors" onClick={() => setMobileOpen(false)}>{t("industries")}</Link>
            <Link href={`/${locale}/pricing`} className="block px-3 py-2.5 rounded-xl text-sm text-cy-gray-200 hover:text-white hover:bg-cy-glass-bg transition-colors" onClick={() => setMobileOpen(false)}>{t("pricing")}</Link>
            <Link href={`/${locale}/partners`} className="block px-3 py-2.5 rounded-xl text-sm text-cy-gray-200 hover:text-white hover:bg-cy-glass-bg transition-colors" onClick={() => setMobileOpen(false)}>{t("partners")}</Link>
            <Link href={`/${locale}/marketplace`} className="block px-3 py-2.5 rounded-xl text-sm text-cy-gray-200 hover:text-white hover:bg-cy-glass-bg transition-colors" onClick={() => setMobileOpen(false)}>{t("marketplace")}</Link>
            <Link href={`/${locale}/about`} className="block px-3 py-2.5 rounded-xl text-sm text-cy-gray-200 hover:text-white hover:bg-cy-glass-bg transition-colors" onClick={() => setMobileOpen(false)}>{t("about")}</Link>
            <div className="h-px bg-cy-glass-border my-3" />
            <Link href={`/${locale}/demo`} className="btn-primary w-full justify-center" onClick={() => setMobileOpen(false)}>{t("requestDemo")}</Link>
            <Link href={`/${altLocale}`} className="btn-secondary w-full justify-center mt-2" onClick={() => setMobileOpen(false)}>
              <Globe className="w-4 h-4" aria-hidden="true" />
              {altLocale === "en" ? "English" : "العربية"}
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
