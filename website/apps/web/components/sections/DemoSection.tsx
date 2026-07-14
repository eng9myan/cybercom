"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { motion, useReducedMotion } from "framer-motion";
import { type Locale } from "@/lib/i18n";
import { demoApi, type DemoRequestPayload } from "@cybercom/api";
import { Check, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface DemoSectionProps {
  locale: Locale;
  asPageHero?: boolean;
}

const PRODUCTS_LIST = [
  "CyMed Clinic",
  "CyMed Hospital",
  "CyMed Laboratory",
  "CyMed Imaging",
  "CyMed Pharmacy",
  "CyMed Patient Portal",
  "CyMed Provider Portal",
  "CyMed Revenue Cycle",
  "CyMed Population Health",
  "CyShop",
  "CyCom ERP",
  "CyGov",
  "CyAI",
  "CyIdentity",
  "CyIntegrationHub",
  "CyData",
  "CyConnect",
  "CyCitizen",
];

const COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001+"] as const;

type FormState = {
  full_name: string;
  email: string;
  phone: string;
  job_title: string;
  company: string;
  company_size: typeof COMPANY_SIZES[number];
  country: string;
  product_interests: string[];
  message: string;
  gdpr_consent: boolean;
};

const INITIAL_FORM: FormState = {
  full_name: "",
  email: "",
  phone: "",
  job_title: "",
  company: "",
  company_size: "51-200",
  country: "",
  product_interests: [],
  message: "",
  gdpr_consent: false,
};

export function DemoSection({ locale: _locale, asPageHero = false }: DemoSectionProps) {
  const Heading = asPageHero ? "h1" : "h2";
  const t = useTranslations("demo");
  const shouldReduce = useReducedMotion();
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [referenceNumber, setReferenceNumber] = useState<string>("");

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }));
  }

  function toggleProduct(product: string) {
    setForm((prev) => ({
      ...prev,
      product_interests: prev.product_interests.includes(product)
        ? prev.product_interests.filter((p) => p !== product)
        : [...prev.product_interests, product],
    }));
    if (errors.product_interests) setErrors((prev) => ({ ...prev, product_interests: undefined }));
  }

  function validate(): boolean {
    const newErrors: Partial<Record<keyof FormState, string>> = {};
    if (!form.full_name.trim()) newErrors.full_name = "Full name is required";
    if (!form.email.trim() || !/\S+@\S+\.\S+/.test(form.email)) newErrors.email = "Valid work email is required";
    if (!form.job_title.trim()) newErrors.job_title = "Job title is required";
    if (!form.company.trim()) newErrors.company = "Company name is required";
    if (!form.country.trim()) newErrors.country = "Country is required";
    if (form.product_interests.length === 0) newErrors.product_interests = "Select at least one product";
    if (!form.gdpr_consent) newErrors.gdpr_consent = "You must agree to the privacy policy";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate() || status === "loading") return;
    setStatus("loading");
    try {
      const result = await demoApi.submit({
        ...form,
        gdpr_consent: true,
      } as DemoRequestPayload);
      setReferenceNumber(result.reference_number);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  return (
    <section className="py-32 relative" id="demo" aria-labelledby="demo-heading">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div className="glow-orb w-[800px] h-[800px] top-0 left-1/2 -translate-x-1/2 bg-cy-orange/5" />
      </div>

      <div className="section-container relative z-10">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 1, y: shouldReduce ? 0 : 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-12"
          >
            <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">Request Demo</p>
            <Heading id="demo-heading" className="text-4xl lg:text-5xl font-heading font-semibold text-white mb-4">
              {t("title")}
            </Heading>
            <p className="text-lg text-cy-gray-400">{t("subtitle")}</p>
          </motion.div>

          {/* Success state */}
          {status === "success" ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-card p-12 rounded-2xl text-center"
              role="status"
              aria-live="polite"
            >
              <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                <Check className="w-8 h-8 text-emerald-400" aria-hidden="true" />
              </div>
              <h3 className="text-2xl font-heading font-semibold text-white mb-3">{t("form.success")}</h3>
              <p className="text-cy-gray-400 mb-4">{t("form.reference")}</p>
              <p className="text-xl font-mono font-medium text-cy-orange">{referenceNumber}</p>
            </motion.div>
          ) : (
            <motion.form
              initial={{ opacity: 1, y: shouldReduce ? 0 : 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              onSubmit={handleSubmit}
              noValidate
              aria-label="Demo request form"
              className="glass-card p-8 rounded-2xl space-y-6"
            >
              {/* Error summary */}
              {status === "error" && (
                <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/5 flex items-start gap-3" role="alert">
                  <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" aria-hidden="true" />
                  <p className="text-sm text-destructive">
                    Something went wrong. Please try again or contact us at sales@cy-com.com.
                  </p>
                </div>
              )}

              {/* Row 1: Name + Email */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="demo-name" className="form-label">
                    {t("form.fullName")} <span aria-hidden="true" className="text-destructive">*</span>
                  </label>
                  <input
                    id="demo-name"
                    type="text"
                    autoComplete="name"
                    value={form.full_name}
                    onChange={(e) => setField("full_name", e.target.value)}
                    className={cn("form-input", errors.full_name && "border-destructive/50")}
                    aria-required="true"
                    aria-invalid={!!errors.full_name}
                    aria-describedby={errors.full_name ? "demo-name-error" : undefined}
                  />
                  {errors.full_name && (
                    <p id="demo-name-error" className="form-error" role="alert">
                      <AlertCircle className="w-3 h-3" aria-hidden="true" />
                      {errors.full_name}
                    </p>
                  )}
                </div>
                <div>
                  <label htmlFor="demo-email" className="form-label">
                    {t("form.email")} <span aria-hidden="true" className="text-destructive">*</span>
                  </label>
                  <input
                    id="demo-email"
                    type="email"
                    autoComplete="email"
                    value={form.email}
                    onChange={(e) => setField("email", e.target.value)}
                    className={cn("form-input", errors.email && "border-destructive/50")}
                    aria-required="true"
                    aria-invalid={!!errors.email}
                    aria-describedby={errors.email ? "demo-email-error" : undefined}
                  />
                  {errors.email && (
                    <p id="demo-email-error" className="form-error" role="alert">
                      <AlertCircle className="w-3 h-3" aria-hidden="true" />
                      {errors.email}
                    </p>
                  )}
                </div>
              </div>

              {/* Row 2: Job title + Company */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="demo-title" className="form-label">
                    {t("form.jobTitle")} <span aria-hidden="true" className="text-destructive">*</span>
                  </label>
                  <input
                    id="demo-title"
                    type="text"
                    autoComplete="organization-title"
                    value={form.job_title}
                    onChange={(e) => setField("job_title", e.target.value)}
                    className={cn("form-input", errors.job_title && "border-destructive/50")}
                    aria-required="true"
                    aria-invalid={!!errors.job_title}
                  />
                  {errors.job_title && (
                    <p className="form-error" role="alert">
                      <AlertCircle className="w-3 h-3" aria-hidden="true" />{errors.job_title}
                    </p>
                  )}
                </div>
                <div>
                  <label htmlFor="demo-company" className="form-label">
                    {t("form.company")} <span aria-hidden="true" className="text-destructive">*</span>
                  </label>
                  <input
                    id="demo-company"
                    type="text"
                    autoComplete="organization"
                    value={form.company}
                    onChange={(e) => setField("company", e.target.value)}
                    className={cn("form-input", errors.company && "border-destructive/50")}
                    aria-required="true"
                    aria-invalid={!!errors.company}
                  />
                  {errors.company && (
                    <p className="form-error" role="alert">
                      <AlertCircle className="w-3 h-3" aria-hidden="true" />{errors.company}
                    </p>
                  )}
                </div>
              </div>

              {/* Row 3: Country + Size */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="demo-country" className="form-label">
                    {t("form.country")} <span aria-hidden="true" className="text-destructive">*</span>
                  </label>
                  <input
                    id="demo-country"
                    type="text"
                    autoComplete="country-name"
                    value={form.country}
                    onChange={(e) => setField("country", e.target.value)}
                    className={cn("form-input", errors.country && "border-destructive/50")}
                    aria-required="true"
                    aria-invalid={!!errors.country}
                  />
                  {errors.country && (
                    <p className="form-error" role="alert">
                      <AlertCircle className="w-3 h-3" aria-hidden="true" />{errors.country}
                    </p>
                  )}
                </div>
                <div>
                  <label htmlFor="demo-size" className="form-label">{t("form.companySize")}</label>
                  <select
                    id="demo-size"
                    value={form.company_size}
                    onChange={(e) => setField("company_size", e.target.value as typeof COMPANY_SIZES[number])}
                    className="form-input"
                  >
                    {COMPANY_SIZES.map((s) => (
                      <option key={s} value={s}>{s} employees</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Phone */}
              <div>
                <label htmlFor="demo-phone" className="form-label">{t("form.phone")}</label>
                <input
                  id="demo-phone"
                  type="tel"
                  autoComplete="tel"
                  value={form.phone}
                  onChange={(e) => setField("phone", e.target.value)}
                  className="form-input"
                />
              </div>

              {/* Products */}
              <fieldset>
                <legend className="form-label mb-2">
                  {t("form.productInterests")} <span aria-hidden="true" className="text-destructive">*</span>
                </legend>
                <div
                  className="flex flex-wrap gap-2"
                  aria-invalid={!!errors.product_interests}
                  aria-describedby={errors.product_interests ? "products-error" : undefined}
                >
                  {PRODUCTS_LIST.map((product) => {
                    const selected = form.product_interests.includes(product);
                    return (
                      <button
                        key={product}
                        type="button"
                        onClick={() => toggleProduct(product)}
                        className={cn(
                          "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all duration-150 cursor-pointer",
                          selected
                            ? "bg-cy-orange/15 border-cy-orange/40 text-cy-orange"
                            : "bg-cy-glass-bg border-cy-glass-border text-cy-gray-400 hover:text-white hover:border-cy-glass-bg-hover"
                        )}
                        aria-pressed={selected}
                      >
                        {selected && <Check className="inline w-3 h-3 mr-1" aria-hidden="true" />}
                        {product}
                      </button>
                    );
                  })}
                </div>
                {errors.product_interests && (
                  <p id="products-error" className="form-error mt-2" role="alert">
                    <AlertCircle className="w-3 h-3" aria-hidden="true" />
                    {errors.product_interests}
                  </p>
                )}
              </fieldset>

              {/* Message */}
              <div>
                <label htmlFor="demo-message" className="form-label">{t("form.message")}</label>
                <textarea
                  id="demo-message"
                  rows={3}
                  value={form.message}
                  onChange={(e) => setField("message", e.target.value)}
                  className="form-input resize-none"
                  placeholder="Tell us about your organization and requirements..."
                />
              </div>

              {/* GDPR */}
              <div>
                <label className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={form.gdpr_consent}
                    onChange={(e) => setField("gdpr_consent", e.target.checked)}
                    className="mt-0.5 w-4 h-4 rounded border-cy-glass-border bg-cy-glass-bg text-cy-orange focus:ring-cy-orange focus:ring-offset-cy-black cursor-pointer"
                    aria-required="true"
                    aria-invalid={!!errors.gdpr_consent}
                    aria-describedby={errors.gdpr_consent ? "gdpr-error" : undefined}
                  />
                  <span className="text-xs text-cy-gray-400 group-hover:text-cy-gray-200 transition-colors">
                    {t("form.gdprConsent")}
                  </span>
                </label>
                {errors.gdpr_consent && (
                  <p id="gdpr-error" className="form-error mt-1" role="alert">
                    <AlertCircle className="w-3 h-3" aria-hidden="true" />
                    {errors.gdpr_consent}
                  </p>
                )}
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={status === "loading"}
                className="btn-primary w-full py-3.5 text-base justify-center disabled:opacity-60 disabled:cursor-not-allowed"
                aria-live="polite"
              >
                {status === "loading" ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                    {t("form.submitting")}
                  </>
                ) : (
                  t("form.submit")
                )}
              </button>
            </motion.form>
          )}
        </div>
      </div>
    </section>
  );
}
