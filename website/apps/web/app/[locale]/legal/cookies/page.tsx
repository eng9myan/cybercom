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
    title: "Cookies Policy",
    description: "Cookies policy and tracking management for CyberCom platforms.",
    path: "/legal/cookies",
    locale,
  });
}

export default async function CookiesPage({ params }: LegalPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const isAr = locale === "ar";

  return (
    <div className="min-h-dvh pt-24 pb-16">
      <div className="section-container max-w-4xl">
        <h1 className="text-4xl font-heading font-semibold text-white mb-8 border-b border-cy-glass-border pb-4">
          {isAr ? "سياسة ملفات الارتباط" : "Cookies Policy"}
        </h1>
        <div className="space-y-6 text-cy-gray-300 leading-relaxed">
          <p className="text-xs text-cy-gray-500">
            {isAr ? "آخر تحديث: 28 يونيو 2026" : "Last updated: June 28, 2026"}
          </p>
          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "1. ما هي ملفات تعريف الارتباط؟" : "1. What Are Cookies?"}
            </h2>
            <p>
              {isAr
                ? "ملفات تعريف الارتباط هي ملفات نصية صغيرة يتم وضعها على جهازك عند زيارة موقعنا لمساعدتنا في تذكر تفضيلاتك وتوفير تجربة مستخدم مخصصة وآمنة."
                : "Cookies are small text files placed on your device to help us recognize your session, remember your preferences, and provide a secure, tailored user experience."}
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "2. أنواع ملفات تعريف الارتباط التي نستخدمها" : "2. Types of Cookies We Use"}
            </h2>
            <ul className="list-disc list-inside space-y-2">
              <li>
                <strong>{isAr ? "الملفات الضرورية:" : "Strictly Necessary Cookies:"}</strong>{" "}
                {isAr
                  ? "مهمة لتأمين تسجيل الدخول، والمصادقة على الجلسة، والتحقق من الهوية."
                  : "Critical for secure login, multi-tenant session validation, and JWT auth tokens."}
              </li>
              <li>
                <strong>{isAr ? "ملفات التفضيلات:" : "Preferences Cookies:"}</strong>{" "}
                {isAr
                  ? "تذكر تفضيلات اللغة (العربية/الإنجليزية) وتخطيط الشاشة (RTL/LTR)."
                  : "Remembering language selections (AR/EN) and layout styles (RTL/LTR)."}
              </li>
              <li>
                <strong>{isAr ? "ملفات التحليل:" : "Analytical/Performance Cookies:"}</strong>{" "}
                {isAr
                  ? "جمع بيانات مجهولة الهوية لتحليل سرعة التحميل واكتشاف أخطاء واجهات البرمجة."
                  : "Collecting anonymous metrics to monitor page performance, load times, and API responsiveness."}
              </li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">
              {isAr ? "3. إدارة التفضيلات" : "3. Managing Cookie Preferences"}
            </h2>
            <p>
              {isAr
                ? "يمكنك تعديل إعدادات متصفحك لرفض ملفات تعريف الارتباط أو تنبيهك عند إرسالها. يرجى العلم بأن تعطيل الملفات الضرورية قد يؤثر على عمل وظائف المنصة الأساسية."
                : "You can configure your browser to reject cookies or alert you when they are set. Note that disabling strictly necessary cookies will impact platform login and session operations."}
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
