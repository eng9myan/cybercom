"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { useTranslations } from "next-intl";
import { type Locale } from "@/lib/i18n";
import { demoProvisionApi, DemoProvisionApiError, type DemoProvisionResponse, type DemoProvisionError } from "@cybercom/api";
import { Check, AlertCircle, Loader2, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface TryFreeSectionProps {
  locale: Locale;
  productCode: string;
  productName: string;
}

export function TryFreeSection({ locale, productCode, productName }: TryFreeSectionProps) {
  const t = useTranslations("tryPage");
  const shouldReduce = useReducedMotion();
  const [email, setEmail] = useState("");
  const [orgName, setOrgName] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [error, setError] = useState<DemoProvisionError | null>(null);
  const [result, setResult] = useState<DemoProvisionResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("submitting");
    setError(null);
    try {
      const res = await demoProvisionApi.provision({
        product_code: productCode,
        email,
        org_name: orgName,
        locale: (locale as "en" | "ar") ?? "en",
      });
      setResult(res);
      setStatus("success");
    } catch (err) {
      if (err instanceof DemoProvisionApiError) {
        setError(err.body);
      } else {
        setError({ detail: t("genericError") });
      }
      setStatus("error");
    }
  };

  if (error?.contact_required) {
    return (
      <section className="py-24 max-w-lg mx-auto px-4 text-center">
        <h1 className="text-2xl font-semibold mb-3">{productName} {t("salesAssistedHeading")}</h1>
        <p className="text-cy-gray-400 mb-6">{error.detail}</p>
        <Link href={`/${locale}/contact`} className="btn-primary px-6 py-3 text-sm inline-block">
          {t("contactSales")}
        </Link>
      </section>
    );
  }

  if (status === "success" && result) {
    return (
      <section className="py-24 max-w-lg mx-auto px-4 text-center">
        <div className="w-12 h-12 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mx-auto mb-4">
          <Check className="w-6 h-6 text-emerald-400" aria-hidden="true" />
        </div>
        <h1 className="text-2xl font-semibold mb-3">{t("successHeading")}</h1>
        <div className="glass-card rounded-lg p-4 mb-4 text-left inline-block">
          {result.cyshop_subdomain && (
            <p className="text-cy-gray-400 text-sm mb-1">{t("workspace")}: <span className="text-white font-mono">{result.cyshop_subdomain}</span></p>
          )}
          <p className="text-cy-gray-400 text-sm mb-1">{t("login")}: <span className="text-white font-mono">{result.username}</span></p>
          <p className="text-cy-gray-400 text-sm">{t("password")}: <span className="text-white font-mono">{result.password}</span></p>
        </div>
        <p className="text-cy-gray-400 mb-6 flex items-center justify-center gap-1.5">
          <Clock className="w-3.5 h-3.5" aria-hidden="true" />
          {t("expires")} {new Date(result.trial_ends_at).toLocaleString(locale === "ar" ? "ar-EG" : "en-US")}
        </p>
        <p className="text-xs text-cy-gray-500">
          {t("checkEmailPrefix")}{email}{t("checkEmailSuffix")}
        </p>
        <p className="text-xs text-cy-gray-500 mt-2">
          {t("savePasswordNote")}
        </p>
        {(() => {
          const loginUrl = result.cyshop_subdomain
            ? (process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com")
            : productCode === "cycom"
              ? (process.env.NEXT_PUBLIC_CYCOM_URL ?? "https://erp.cy-com.com")
              : productCode.startsWith("cymed")
                ? (process.env.NEXT_PUBLIC_CYMED_URL ?? "https://cymed.cy-com.com")
                : null;
          if (!loginUrl) return null;
          return (
            <a
              href={loginUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary mt-6 px-6 py-3 text-sm inline-block"
            >
              {t("goToLogin")}
            </a>
          );
        })()}
      </section>
    );
  }

  return (
    <section className="py-24 max-w-lg mx-auto px-4">
      <motion.div
        initial={{ opacity: 0, y: shouldReduce ? 0 : 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-2xl font-semibold mb-2">{t("heroHeadingPrefix")} {productName} {t("heroHeadingSuffix")}</h1>
        <p className="text-cy-gray-400 mb-8">
          {t("heroDesc")}
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="try-org" className="form-label">{t("orgName")}</label>
            <input
              id="try-org"
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              className="form-input"
            />
          </div>
          <div>
            <label htmlFor="try-email" className="form-label">
              {t("workEmail")} <span aria-hidden="true" className="text-destructive">*</span>
            </label>
            <input
              id="try-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={cn("form-input", error?.detail && "border-destructive/50")}
              aria-invalid={!!error?.detail}
            />
            {error?.detail && (
              <p className="form-error" role="alert">
                <AlertCircle className="w-3 h-3" aria-hidden="true" />
                {error.detail}
              </p>
            )}
          </div>
          <button
            type="submit"
            disabled={status === "submitting"}
            className="btn-primary w-full py-3.5 text-sm inline-flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {status === "submitting" && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
            {t("startTrial")}
          </button>
        </form>
      </motion.div>
    </section>
  );
}
