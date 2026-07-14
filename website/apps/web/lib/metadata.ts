import type { Metadata } from "next";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://www.cy-com.com";

export const siteConfig = {
  name: "CyberCom Revolution",
  url: siteUrl,
  description:
    "Transforming Healthcare, Government and Enterprise through intelligent platforms — CyMed, CyCom, CyGov, CyAI, CyIdentity, CyIntegrationHub, CyData, CyConnect, CyCitizen.",
  twitterHandle: "@CyberComRev",
  ogImage: `${siteUrl}/opengraph-image`,
};

export function buildMetadata({
  title,
  description,
  path = "/",
  locale = "en",
  ogImage,
  noIndex = false,
}: {
  title: string;
  description: string;
  path?: string;
  locale?: string;
  ogImage?: string;
  noIndex?: boolean;
}): Metadata {
  const fullTitle = `${title} | ${siteConfig.name}`;
  const canonical = `${siteUrl}/${locale}${path}`;

  return {
    title,
    description,
    metadataBase: new URL(siteUrl),
    alternates: {
      canonical,
      languages: {
        en: `${siteUrl}/en${path}`,
        ar: `${siteUrl}/ar${path}`,
      },
    },
    openGraph: {
      title: fullTitle,
      description,
      url: canonical,
      siteName: siteConfig.name,
      images: [{ url: ogImage ?? siteConfig.ogImage, width: 1200, height: 630, alt: title }],
      locale: locale === "ar" ? "ar_SA" : "en_US",
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: fullTitle,
      description,
      images: [ogImage ?? siteConfig.ogImage],
      creator: siteConfig.twitterHandle,
    },
    robots: noIndex ? { index: false, follow: false } : { index: true, follow: true },
  };
}

export const homepageSeoKeywords = {
  en: [
    "healthcare platform",
    "FHIR EMR",
    "ICD-11 EHR",
    "government digital transformation",
    "ERP system",
    "AI healthcare",
    "CyMed",
    "CyberCom",
    "hospital management system",
    "government software",
    "enterprise software Middle East",
  ],
  ar: [
    "نظام صحي",
    "السجل الطبي الإلكتروني",
    "نظام المستشفيات",
    "التحول الرقمي الحكومي",
    "نظام تخطيط موارد المؤسسات",
    "الذكاء الاصطناعي في الرعاية الصحية",
    "CyMed",
    "سايبر كوم",
  ],
};
