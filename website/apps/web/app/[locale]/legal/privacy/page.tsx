import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";

interface LegalPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: LegalPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Privacy Policy",
    description: "Privacy policy and health data protection guidelines for CyberCom platforms.",
    path: "/legal/privacy",
    locale,
  });
}

export default async function PrivacyPage({ params }: LegalPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const isAr = locale === "ar";

  return (
    <div className="min-h-dvh pt-24 pb-16">
      <div className="section-container max-w-4xl">
        <h1 className="text-4xl font-heading font-semibold text-white mb-8 border-b border-cy-glass-border pb-4">
          {isAr ? "سياسة الخصوصية" : "Privacy Policy"}
        </h1>
        <div className="space-y-6 text-cy-gray-300 leading-relaxed">
          <p className="text-xs text-cy-gray-500">
            {isAr ? "آخر تحديث: 28 يونيو 2026" : "Last updated: June 28, 2026"}
          </p>
          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "1. نظرة عامة" : "1. Introduction"}
            </h2>
            <p>
              {isAr
                ? "في سايبر كوم ريفولوشن، نلتزم بحماية خصوصية وأمان معلوماتك الشخصية والصحية. توضح سياسة الخصوصية هذه كيفية جمع واستخدام وحماية البيانات عبر موقعنا الإلكتروني ومنصاتنا."
                : "At CyberCom Revolution, we are committed to protecting the privacy and security of your personal and health information. This Privacy Policy explains how we collect, use, and safeguard data across our website and platforms."}
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "2. حماية البيانات الصحية (FHIR & HIPAA)" : "2. Health Data Protection (FHIR & HIPAA)"}
            </h2>
            <p>
              {isAr
                ? "تتوافق منصاتنا الصحية تمامًا مع معايير HIPAA و GDPR الإقليمية. يتم تخزين جميع السجلات الصحية الإلكترونية ونقلها باستخدام تنسيقات موارد FHIR المشفرة ومعايير التشفير TLS 1.3."
                : "Our health platforms are fully compliant with HIPAA and regional GDPR guidelines. All Electronic Health Records (EHR) are stored and transmitted using encrypted FHIR resource formats and TLS 1.3 encryption standards."}
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "3. مشاركة البيانات" : "3. Data Sharing & Third-Parties"}
            </h2>
            <p>
              {isAr
                ? "نحن لا نبيع أو نؤجر معلوماتك الشخصية لأطراف ثالثة. تتم مشاركة البيانات فقط مع مزودي الخدمة المعتمدين لتسهيل تشغيل الأنظمة أو بناءً على متطلبات قانونية."
                : "We do not sell or rent your personal information to third parties. Data is shared only with authorized service providers to facilitate systems operations or as required by law."}
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "4. حقوقك" : "4. Your Rights"}
            </h2>
            <p>
              {isAr
                ? "لديك الحق في طلب الوصول إلى بياناتك الشخصية وتصحيحها أو مسحها. يمكنك الاتصال بمسؤول حماية البيانات لدينا عبر البريد الإلكتروني: security@cy-com.com."
                : "You have the right to request access to, correction of, or erasure of your personal data. You may contact our Data Protection Officer at: security@cy-com.com."}
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
