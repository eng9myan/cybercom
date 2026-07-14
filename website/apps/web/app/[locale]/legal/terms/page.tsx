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
    title: "Terms of Service",
    description: "Terms of service and usage conditions for CyberCom platforms.",
    path: "/legal/terms",
    locale,
  });
}

export default async function TermsPage({ params }: LegalPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const isAr = locale === "ar";

  return (
    <div className="min-h-dvh pt-24 pb-16">
      <div className="section-container max-w-4xl">
        <h1 className="text-4xl font-heading font-semibold text-white mb-8 border-b border-cy-glass-border pb-4">
          {isAr ? "شروط الخدمة" : "Terms of Service"}
        </h1>
        <div className="space-y-6 text-cy-gray-300 leading-relaxed">
          <p className="text-xs text-cy-gray-500">
            {isAr ? "آخر تحديث: 28 يونيو 2026" : "Last updated: June 28, 2026"}
          </p>
          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "1. قبول الشروط" : "1. Acceptance of Terms"}
            </h2>
            <p>
              {isAr
                ? "باستخدامك لموقعنا الإلكتروني أو خدماتنا، فإنك توافق على الالتزام بشروط الخدمة هذه. إذا كنت لا توافق عليها، يرجى عدم استخدام المنصة."
                : "By accessing or using our website or platforms, you agree to be bound by these Terms of Service. If you do not agree, please do not use the platforms."}
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "2. ترخيص الاستخدام" : "2. License & Access"}
            </h2>
            <p>
              {isAr
                ? "نحن نمنحك ترخيصًا محدودًا غير حصري وغير قابل للتحويل للوصول إلى المنصة واستخدامها للأغراض التجارية أو المهنية المصرح بها، وفقًا لخطة الاشتراك والترخيص النشط للشركة."
                : "We grant you a limited, non-exclusive, non-transferable license to access and use the platforms for authorized business or professional purposes, subject to your subscription plan and active licensing keys."}
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "3. المسؤوليات" : "3. User Conduct & Responsibilities"}
            </h2>
            <p>
              {isAr
                ? "يتحمل المستخدمون كامل المسؤولية عن البيانات المدخلة وضمان صحة السجلات الطبية والمالية. يمنع استخدام الأنظمة لأي نشاط غير قانوني أو انتهاك لسلامة البنية التحتية."
                : "Users are fully responsible for the data inputted into EMR/ERP systems. Any unauthorized access, attempts to compromise infrastructure integrity, or use for unlawful activities is strictly prohibited."}
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "4. القانون المعمول به" : "4. Governing Law"}
            </h2>
            <p>
              {isAr
                ? "تخضع هذه الشروط وتفسر وفقًا للقوانين المحلية المعمول بها في مكان التأسيس وتخضع النزاعات للاختصاص القضائي للمحاكم المحلية."
                : "These terms shall be governed by and construed in accordance with the laws of the operating jurisdiction, and any disputes shall be subject to the exclusive jurisdiction of the local courts."}
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
