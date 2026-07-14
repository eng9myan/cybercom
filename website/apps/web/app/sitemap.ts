import type { MetadataRoute } from "next";
import { siteConfig } from "@/lib/metadata";

const STATIC_ROUTES = [
  "",
  "/about",
  "/blog",
  "/careers",
  "/company",
  "/contact",
  "/customers",
  "/cyshop",
  "/demo",
  "/documentation",
  "/erp",
  "/industries",
  "/investors",
  "/legal/cookies",
  "/legal/privacy",
  "/legal/terms",
  "/marketplace",
  "/partners",
  "/partner",
  "/portal",
  "/pricing",
  "/products",
  "/solutions",
  "/tools/compare",
  "/tools/roi",
];

const PRODUCT_SLUGS = [
  "cymed",
  "cymed-clinic",
  "cymed-hospital",
  "cymed-laboratory",
  "cymed-imaging",
  "cymed-pharmacy",
  "cymed-patient-portal",
  "cymed-provider-portal",
  "cymed-revenue-cycle",
  "cymed-population-health",
  "cycom",
  "cycom-finance",
  "cycom-accounting",
  "cycom-procurement",
  "cycom-inventory",
  "cycom-hr",
  "cycom-payroll",
  "cycom-crm",
  "cycom-assets",
  "cycom-manufacturing",
  "cycom-retail",
  "cycom-bi",
  "cygov",
  "cyidentity",
  "cyintegrationhub",
  "cyai",
  "cydata",
  "cyconnect",
  "cyshop",
  "cyshop-retail",
  "cyshop-restaurant",
  "cyshop-bakery",
  "cyshop-coffee",
  "cyshop-fastfood",
  "cyshop-grocery",
  "cyshop-supermarket",
  "cyshop-convenience",
  "cycitizen",
];

const INDUSTRY_SLUGS = [
  "healthcare",
  "government",
  "retail",
  "manufacturing",
  "education",
  "financial",
  "insurance",
  "telecom",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const locales = ["en", "ar"];

  const staticEntries = locales.flatMap((locale) =>
    STATIC_ROUTES.map((route) => ({
      url: `${siteConfig.url}/${locale}${route}`,
      lastModified: now,
      changeFrequency: route === "" ? ("weekly" as const) : ("monthly" as const),
      priority: route === "" ? 1 : 0.7,
      alternates: {
        languages: {
          en: `${siteConfig.url}/en${route}`,
          ar: `${siteConfig.url}/ar${route}`,
        },
      },
    }))
  );

  const productEntries = locales.flatMap((locale) =>
    PRODUCT_SLUGS.map((slug) => ({
      url: `${siteConfig.url}/${locale}/products/${slug}`,
      lastModified: now,
      changeFrequency: "monthly" as const,
      priority: 0.8,
      alternates: {
        languages: {
          en: `${siteConfig.url}/en/products/${slug}`,
          ar: `${siteConfig.url}/ar/products/${slug}`,
        },
      },
    }))
  );

  const industryEntries = locales.flatMap((locale) =>
    INDUSTRY_SLUGS.map((slug) => ({
      url: `${siteConfig.url}/${locale}/industries/${slug}`,
      lastModified: now,
      changeFrequency: "monthly" as const,
      priority: 0.6,
      alternates: {
        languages: {
          en: `${siteConfig.url}/en/industries/${slug}`,
          ar: `${siteConfig.url}/ar/industries/${slug}`,
        },
      },
    }))
  );

  return [...staticEntries, ...productEntries, ...industryEntries];
}
