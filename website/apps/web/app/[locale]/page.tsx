import { setRequestLocale } from "next-intl/server";
import { getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import { Hero } from "@/components/sections/Hero";
import { StatsBand } from "@/components/sections/StatsBand";
import { ProductEcosystem } from "@/components/sections/ProductEcosystem";
import { SocialProof } from "@/components/sections/SocialProof";
import { IndustriesSection } from "@/components/sections/IndustriesSection";
import { CyMedSection } from "@/components/sections/CyMedSection";
import { GlobalReach } from "@/components/sections/GlobalReach";
import { DemoSection } from "@/components/sections/DemoSection";
import { buildMetadata, homepageSeoKeywords } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";

interface HomePageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: HomePageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const isAr = locale === "ar";

  const metadata = buildMetadata({
    title: isAr
      ? "سايبر كوم — منصات الرعاية الصحية والحكومة والمؤسسات"
      : "CyberCom Revolution — Healthcare, Government & Enterprise Platforms",
    description: isAr
      ? "تحويل الرعاية الصحية والحكومة والمؤسسات عبر المنصات الذكية. CyMed — نظام صحي FHIR وICD-11. CyGov — حوكمة رقمية. CyCom — تخطيط الموارد."
      : "Transforming Healthcare, Government and Enterprise through 9 integrated intelligent platforms. CyMed FHIR-native EHR, CyGov digital government, CyCom ERP, CyAI, CyIdentity and more.",
    path: "/",
    locale,
  });

  return {
    ...metadata,
    title: {
      absolute: isAr
        ? "سايبر كوم — منصات الرعاية الصحية والحكومة والمؤسسات"
        : "CyberCom Revolution — Healthcare, Government & Enterprise Platforms",
    },
    keywords: homepageSeoKeywords[locale as Locale] ?? homepageSeoKeywords.en,
    other: {
      "schema:type": "Organization",
      "schema:name": "CyberCom Revolution",
      "schema:url": "https://www.cy-com.com",
      "schema:description": "Enterprise software company delivering healthcare, government, and ERP platforms",
    },
  };
}

export default async function HomePage({ params }: HomePageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <>
      {/* JSON-LD structured data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Organization",
            name: "CyberCom Revolution",
            url: "https://www.cy-com.com",
            logo: "https://www.cy-com.com/opengraph-image",
            description:
              "Enterprise software company delivering integrated healthcare, government, and ERP platforms.",
            sameAs: [
              "https://linkedin.com/company/cybercom-revolution",
              "https://twitter.com/CyberComRev",
            ],
            contactPoint: {
              "@type": "ContactPoint",
              contactType: "sales",
              email: "sales@cy-com.com",
              availableLanguage: ["English", "Arabic"],
            },
            hasOfferCatalog: {
              "@type": "OfferCatalog",
              name: "CyberCom Platform Suite",
              itemListElement: [
                {
                  "@type": "SoftwareApplication",
                  name: "CyMed",
                  applicationCategory: "HealthApplication",
                  description: "FHIR-native, ICD-11 ready healthcare platform",
                },
                {
                  "@type": "SoftwareApplication",
                  name: "CyCom",
                  applicationCategory: "BusinessApplication",
                  description: "Enterprise ERP platform",
                },
                {
                  "@type": "SoftwareApplication",
                  name: "CyGov",
                  applicationCategory: "GovernmentApplication",
                  description: "Government digital transformation platform",
                },
              ],
            },
          }),
        }}
      />

      <Hero locale={l} />
      <StatsBand />
      <ProductEcosystem locale={l} />
      <SocialProof />
      <IndustriesSection locale={l} />
      <CyMedSection locale={l} />
      <GlobalReach locale={l} />
      <DemoSection locale={l} />
    </>
  );
}
