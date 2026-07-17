"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { motion, useReducedMotion } from "framer-motion";
import { contactApi, type ContactPayload, type Department } from "@cybercom/api";
import { Check, AlertCircle, Loader2, Mail, Phone, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";

const DEPARTMENT_KEYS: Department[] = ["sales", "support", "partnerships", "press", "careers", "general"];

const OFFICE_KEYS = [
  { key: "riyadh", phone: "+962 79 644 4994" },
  { key: "dubai", phone: "+962 79 644 4994" },
  { key: "amman", phone: "+962 79 644 4994" },
];

type FormState = {
  full_name: string;
  email: string;
  company: string;
  subject: string;
  message: string;
  department: Department;
  gdpr_consent: boolean;
};

export default function ContactPage() {
  const t = useTranslations("contact");
  const shouldReduce = useReducedMotion();
  const [form, setForm] = useState<FormState>({
    full_name: "",
    email: "",
    company: "",
    subject: "",
    message: "",
    department: "general",
    gdpr_consent: false,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [ticketNumber, setTicketNumber] = useState("");

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }));
  }

  function validate(): boolean {
    const errs: Partial<Record<keyof FormState, string>> = {};
    if (!form.full_name.trim()) errs.full_name = t("form.errors.name");
    if (!form.email.trim() || !/\S+@\S+\.\S+/.test(form.email)) errs.email = t("form.errors.email");
    if (!form.subject.trim()) errs.subject = t("form.errors.subject");
    if (!form.message.trim() || form.message.length < 10) errs.message = t("form.errors.message");
    if (!form.gdpr_consent) errs.gdpr_consent = t("form.errors.consent");
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate() || status === "loading") return;
    setStatus("loading");
    try {
      const result = await contactApi.send({ ...form, gdpr_consent: true } as ContactPayload);
      setTicketNumber(result.ticket_number);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="min-h-dvh pt-16">
      {/* Header */}
      <div className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[500px] h-[500px] -top-24 right-0 bg-cy-cyan/6" />
        </div>
        <div className="section-container relative z-10 text-center">
          <p className="text-sm font-medium text-cy-orange mb-3 uppercase tracking-wider">{t("badge")}</p>
          <h1 className="text-5xl font-heading font-semibold text-white mb-4">{t("title")}</h1>
          <p className="text-xl text-cy-gray-400 max-w-xl mx-auto">{t("subtitle")}</p>
        </div>
      </div>

      <div className="section-container pb-24">
        <div className="grid lg:grid-cols-2 gap-12">
          {/* Contact Form */}
          <motion.div
            initial={{ opacity: 0, y: shouldReduce ? 0 : 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {status === "success" ? (
              <div className="glass-card p-10 rounded-2xl text-center" role="status" aria-live="polite">
                <div className="w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-5">
                  <Check className="w-7 h-7 text-emerald-400" aria-hidden="true" />
                </div>
                <h2 className="text-xl font-heading font-semibold text-white mb-2">{t("success.heading")}</h2>
                <p className="text-cy-gray-400 mb-3">{t("success.desc")}</p>
                <p className="text-sm text-cy-gray-400">{t("success.ticket")} <span className="font-mono text-cy-orange">{ticketNumber}</span></p>
              </div>
            ) : (
              <form
                onSubmit={handleSubmit}
                noValidate
                aria-label="Contact form"
                className="glass-card p-8 rounded-2xl space-y-5"
              >
                <h2 className="text-lg font-heading font-semibold text-white mb-1">{t("form.sendMessage")}</h2>

                {status === "error" && (
                  <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/5 flex items-start gap-3" role="alert">
                    <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <p className="text-sm text-destructive">{t("form.genericError")}</p>
                  </div>
                )}

                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="c-name" className="form-label">
                      {t("form.name")} <span aria-hidden="true" className="text-destructive">*</span>
                    </label>
                    <input
                      id="c-name"
                      type="text"
                      autoComplete="name"
                      value={form.full_name}
                      onChange={(e) => setField("full_name", e.target.value)}
                      className={cn("form-input", errors.full_name && "border-destructive/50")}
                      aria-required="true"
                      aria-invalid={!!errors.full_name}
                    />
                    {errors.full_name && <p className="form-error" role="alert"><AlertCircle className="w-3 h-3" aria-hidden="true" />{errors.full_name}</p>}
                  </div>
                  <div>
                    <label htmlFor="c-email" className="form-label">
                      {t("form.email")} <span aria-hidden="true" className="text-destructive">*</span>
                    </label>
                    <input
                      id="c-email"
                      type="email"
                      autoComplete="email"
                      value={form.email}
                      onChange={(e) => setField("email", e.target.value)}
                      className={cn("form-input", errors.email && "border-destructive/50")}
                      aria-required="true"
                      aria-invalid={!!errors.email}
                    />
                    {errors.email && <p className="form-error" role="alert"><AlertCircle className="w-3 h-3" aria-hidden="true" />{errors.email}</p>}
                  </div>
                </div>

                <div>
                  <label htmlFor="c-company" className="form-label">{t("form.company")}</label>
                  <input
                    id="c-company"
                    type="text"
                    autoComplete="organization"
                    value={form.company}
                    onChange={(e) => setField("company", e.target.value)}
                    className="form-input"
                  />
                </div>

                <div>
                  <label htmlFor="c-dept" className="form-label">{t("form.department")}</label>
                  <select
                    id="c-dept"
                    value={form.department}
                    onChange={(e) => setField("department", e.target.value as Department)}
                    className="form-input"
                  >
                    {DEPARTMENT_KEYS.map((d) => (
                      <option key={d} value={d}>{t(`departments.${d}`)}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="c-subject" className="form-label">
                    {t("form.subject")} <span aria-hidden="true" className="text-destructive">*</span>
                  </label>
                  <input
                    id="c-subject"
                    type="text"
                    value={form.subject}
                    onChange={(e) => setField("subject", e.target.value)}
                    className={cn("form-input", errors.subject && "border-destructive/50")}
                    aria-required="true"
                    aria-invalid={!!errors.subject}
                  />
                  {errors.subject && <p className="form-error" role="alert"><AlertCircle className="w-3 h-3" aria-hidden="true" />{errors.subject}</p>}
                </div>

                <div>
                  <label htmlFor="c-message" className="form-label">
                    {t("form.message")} <span aria-hidden="true" className="text-destructive">*</span>
                  </label>
                  <textarea
                    id="c-message"
                    rows={5}
                    value={form.message}
                    onChange={(e) => setField("message", e.target.value)}
                    className={cn("form-input resize-none", errors.message && "border-destructive/50")}
                    aria-required="true"
                    aria-invalid={!!errors.message}
                    placeholder={t("form.messagePlaceholder")}
                  />
                  {errors.message && <p className="form-error" role="alert"><AlertCircle className="w-3 h-3" aria-hidden="true" />{errors.message}</p>}
                </div>

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.gdpr_consent}
                    onChange={(e) => setField("gdpr_consent", e.target.checked)}
                    className="mt-0.5 w-4 h-4 rounded border-cy-glass-border bg-cy-glass-bg text-cy-orange focus:ring-cy-orange focus:ring-offset-cy-black cursor-pointer"
                    aria-required="true"
                    aria-invalid={!!errors.gdpr_consent}
                  />
                  <span className="text-xs text-cy-gray-400">
                    {t("form.consent")}
                  </span>
                </label>
                {errors.gdpr_consent && <p className="form-error -mt-3" role="alert"><AlertCircle className="w-3 h-3" aria-hidden="true" />{errors.gdpr_consent}</p>}

                <button
                  type="submit"
                  disabled={status === "loading"}
                  className="btn-primary w-full justify-center py-3.5 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {status === "loading" ? (
                    <><Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />{t("form.sending")}</>
                  ) : t("form.send")}
                </button>
              </form>
            )}
          </motion.div>

          {/* Info panel */}
          <motion.div
            initial={{ opacity: 0, y: shouldReduce ? 0 : 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="space-y-6"
          >
            {/* Quick contact cards */}
            <div className="glass-card p-6 rounded-2xl">
              <h3 className="font-heading font-semibold text-white mb-4">{t("quickContact.heading")}</h3>
              <div className="space-y-3">
                <a href="mailto:sales@cy-com.com" className="flex items-center gap-3 text-sm text-cy-gray-400 hover:text-white transition-colors group">
                  <div className="w-9 h-9 rounded-lg bg-cy-orange/10 flex items-center justify-center flex-shrink-0 group-hover:bg-cy-orange/20 transition-colors">
                    <Mail className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="font-medium text-white">{t("quickContact.sales")}</div>
                    <div>sales@cy-com.com</div>
                  </div>
                </a>
                <a href="mailto:support@cy-com.com" className="flex items-center gap-3 text-sm text-cy-gray-400 hover:text-white transition-colors group">
                  <div className="w-9 h-9 rounded-lg bg-cy-cyan/10 flex items-center justify-center flex-shrink-0 group-hover:bg-cy-cyan/20 transition-colors">
                    <Mail className="w-4 h-4 text-cy-cyan" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="font-medium text-white">{t("quickContact.support")}</div>
                    <div>support@cy-com.com</div>
                  </div>
                </a>
                <a href="mailto:partners@cy-com.com" className="flex items-center gap-3 text-sm text-cy-gray-400 hover:text-white transition-colors group">
                  <div className="w-9 h-9 rounded-lg bg-violet-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-violet-500/20 transition-colors">
                    <Mail className="w-4 h-4 text-violet-400" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="font-medium text-white">{t("quickContact.partnerships")}</div>
                    <div>partners@cy-com.com</div>
                  </div>
                </a>
              </div>
            </div>

            {/* Office locations */}
            <div className="glass-card p-6 rounded-2xl">
              <h3 className="font-heading font-semibold text-white mb-4">{t("offices.heading")}</h3>
              <div className="space-y-4">
                {OFFICE_KEYS.map((office) => (
                  <div key={office.key} className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-lg bg-cy-glass-bg flex items-center justify-center flex-shrink-0">
                      <MapPin className="w-4 h-4 text-cy-orange" aria-hidden="true" />
                    </div>
                    <div className="text-sm">
                      <div className="font-medium text-white">{t(`offices.${office.key}.city`)}, {t(`offices.${office.key}.country`)}</div>
                      <div className="text-cy-gray-400">{t(`offices.${office.key}.address`)}</div>
                      <div className="text-cy-gray-400">{office.phone}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
