"use client";

import { useState, useId } from "react";
import Link from "next/link";
import {
  Building2,
  Globe,
  Users,
  ChevronRight,
  ChevronLeft,
  CheckCircle2,
  AlertCircle,
  Loader2,
  PartyPopper,
  ArrowLeft,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { clsx } from "clsx";

// ─── Types ────────────────────────────────────────────────────────────────────

interface FormData {
  // Step 1 — Company Info
  companyName: string;
  website: string;
  country: string;
  companySize: string;

  // Step 2 — Expertise
  partnerType: string;
  expertiseAreas: string[];
  yearsInBusiness: string;

  // Step 3 — Contact & Agreement
  contactName: string;
  email: string;
  phone: string;
  message: string;
  gdprConsent: boolean;
}

interface FieldErrors {
  [key: string]: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const PARTNER_TYPES = [
  { value: "implementation", label: "Implementation Partner" },
  { value: "reseller", label: "Reseller Partner" },
  { value: "technology", label: "Technology Partner" },
  { value: "consulting", label: "Consulting Partner" },
];

const EXPERTISE_AREAS = [
  { value: "CyMed", label: "CyMed — Healthcare Platform" },
  { value: "CyCom", label: "CyCom — Communications" },
  { value: "CyGov", label: "CyGov — Government Solutions" },
  { value: "CyAI", label: "CyAI — Artificial Intelligence" },
  { value: "CyIdentity", label: "CyIdentity — Identity & Access" },
  { value: "CyIntegrationHub", label: "CyIntegrationHub — Integrations" },
];

const COMPANY_SIZES = [
  { value: "1-10", label: "1–10 employees" },
  { value: "11-50", label: "11–50 employees" },
  { value: "51-200", label: "51–200 employees" },
  { value: "201-1000", label: "201–1,000 employees" },
  { value: "1000+", label: "1,000+ employees" },
];

const YEARS_OPTIONS = [
  { value: "0-1", label: "Less than 1 year" },
  { value: "1-3", label: "1–3 years" },
  { value: "3-5", label: "3–5 years" },
  { value: "5-10", label: "5–10 years" },
  { value: "10+", label: "10+ years" },
];

const COUNTRIES = [
  "Afghanistan", "Albania", "Algeria", "Argentina", "Australia", "Austria",
  "Bahrain", "Belgium", "Brazil", "Canada", "Chile", "China", "Colombia",
  "Denmark", "Egypt", "Finland", "France", "Germany", "Ghana", "Greece",
  "India", "Indonesia", "Iraq", "Ireland", "Italy", "Japan", "Jordan",
  "Kenya", "Kuwait", "Lebanon", "Libya", "Malaysia", "Mexico", "Morocco",
  "Netherlands", "New Zealand", "Nigeria", "Norway", "Oman", "Pakistan",
  "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia",
  "Saudi Arabia", "Singapore", "South Africa", "South Korea", "Spain",
  "Sweden", "Switzerland", "Thailand", "Tunisia", "Turkey", "UAE",
  "United Kingdom", "United States", "Vietnam", "Yemen",
].sort();

const STEPS = [
  { id: 1, label: "Company Info", icon: Building2 },
  { id: 2, label: "Expertise", icon: Users },
  { id: 3, label: "Contact", icon: Globe },
];

const INITIAL_FORM: FormData = {
  companyName: "",
  website: "",
  country: "",
  companySize: "",
  partnerType: "",
  expertiseAreas: [],
  yearsInBusiness: "",
  contactName: "",
  email: "",
  phone: "",
  message: "",
  gdprConsent: false,
};

// ─── Validation ───────────────────────────────────────────────────────────────

function validateStep(step: number, data: FormData): FieldErrors {
  const errors: FieldErrors = {};

  if (step === 1) {
    if (!data.companyName.trim())
      errors.companyName = "Company name is required.";
    if (data.website && !/^https?:\/\/.+/.test(data.website))
      errors.website = "Enter a valid URL (e.g. https://example.com).";
    if (!data.country) errors.country = "Please select your country.";
    if (!data.companySize) errors.companySize = "Please select company size.";
  }

  if (step === 2) {
    if (!data.partnerType) errors.partnerType = "Please select a partner type.";
    if (data.expertiseAreas.length === 0)
      errors.expertiseAreas = "Select at least one expertise area.";
    if (!data.yearsInBusiness)
      errors.yearsInBusiness = "Please select years in business.";
  }

  if (step === 3) {
    if (!data.contactName.trim()) errors.contactName = "Full name is required.";
    if (!data.email.trim()) errors.email = "Email address is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email))
      errors.email = "Enter a valid email address.";
    if (data.phone && !/^\+?[\d\s\-()]{7,20}$/.test(data.phone))
      errors.phone = "Enter a valid phone number.";
    if (!data.gdprConsent)
      errors.gdprConsent =
        "You must consent to the processing of your data to proceed.";
  }

  return errors;
}

// ─── Field Components ─────────────────────────────────────────────────────────

function Field({
  label,
  required,
  error,
  children,
  htmlFor,
  hint,
}: {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
  htmlFor: string;
  hint?: string;
}) {
  return (
    <div className="flex flex-col gap-0">
      <label htmlFor={htmlFor} className="form-label">
        {label}
        {required && (
          <span className="text-cy-orange ml-1" aria-label="required">
            *
          </span>
        )}
      </label>
      {hint && <p className="text-xs text-cy-gray-400 mb-1.5">{hint}</p>}
      {children}
      {error && (
        <p className="form-error" role="alert" id={`${htmlFor}-error`}>
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" aria-hidden="true" />
          {error}
        </p>
      )}
    </div>
  );
}

// ─── Step 1: Company Info ─────────────────────────────────────────────────────

function Step1({
  data,
  errors,
  onChange,
}: {
  data: FormData;
  errors: FieldErrors;
  onChange: (field: keyof FormData, value: string) => void;
}) {
  const id = useId();
  return (
    <div className="space-y-5">
      <Field
        label="Company Name"
        required
        error={errors.companyName}
        htmlFor={`${id}-companyName`}
      >
        <input
          id={`${id}-companyName`}
          type="text"
          value={data.companyName}
          onChange={(e) => onChange("companyName", e.target.value)}
          className={clsx(
            "form-input",
            errors.companyName && "border-red-500/50 focus:border-red-500/70"
          )}
          placeholder="Acme Technologies Ltd."
          autoComplete="organization"
          aria-describedby={errors.companyName ? `${id}-companyName-error` : undefined}
          aria-invalid={!!errors.companyName}
        />
      </Field>

      <Field
        label="Company Website"
        error={errors.website}
        htmlFor={`${id}-website`}
        hint="Optional — helps us understand your business."
      >
        <input
          id={`${id}-website`}
          type="url"
          value={data.website}
          onChange={(e) => onChange("website", e.target.value)}
          className={clsx(
            "form-input",
            errors.website && "border-red-500/50 focus:border-red-500/70"
          )}
          placeholder="https://example.com"
          autoComplete="url"
          aria-describedby={errors.website ? `${id}-website-error` : undefined}
          aria-invalid={!!errors.website}
        />
      </Field>

      <Field
        label="Country"
        required
        error={errors.country}
        htmlFor={`${id}-country`}
      >
        <select
          id={`${id}-country`}
          value={data.country}
          onChange={(e) => onChange("country", e.target.value)}
          className={clsx(
            "form-select",
            errors.country && "border-red-500/50 focus:border-red-500/70"
          )}
          aria-describedby={errors.country ? `${id}-country-error` : undefined}
          aria-invalid={!!errors.country}
        >
          <option value="" disabled className="bg-cy-dark">
            Select your country
          </option>
          {COUNTRIES.map((c) => (
            <option key={c} value={c} className="bg-cy-dark">
              {c}
            </option>
          ))}
        </select>
      </Field>

      <Field
        label="Company Size"
        required
        error={errors.companySize}
        htmlFor={`${id}-companySize`}
      >
        <select
          id={`${id}-companySize`}
          value={data.companySize}
          onChange={(e) => onChange("companySize", e.target.value)}
          className={clsx(
            "form-select",
            errors.companySize && "border-red-500/50 focus:border-red-500/70"
          )}
          aria-describedby={errors.companySize ? `${id}-companySize-error` : undefined}
          aria-invalid={!!errors.companySize}
        >
          <option value="" disabled className="bg-cy-dark">
            Select company size
          </option>
          {COMPANY_SIZES.map((s) => (
            <option key={s.value} value={s.value} className="bg-cy-dark">
              {s.label}
            </option>
          ))}
        </select>
      </Field>
    </div>
  );
}

// ─── Step 2: Expertise ────────────────────────────────────────────────────────

function Step2({
  data,
  errors,
  onChange,
  onToggleExpertise,
}: {
  data: FormData;
  errors: FieldErrors;
  onChange: (field: keyof FormData, value: string) => void;
  onToggleExpertise: (value: string) => void;
}) {
  const id = useId();
  return (
    <div className="space-y-5">
      <Field
        label="Partner Type"
        required
        error={errors.partnerType}
        htmlFor={`${id}-partnerType`}
      >
        <select
          id={`${id}-partnerType`}
          value={data.partnerType}
          onChange={(e) => onChange("partnerType", e.target.value)}
          className={clsx(
            "form-select",
            errors.partnerType && "border-red-500/50 focus:border-red-500/70"
          )}
          aria-describedby={errors.partnerType ? `${id}-partnerType-error` : undefined}
          aria-invalid={!!errors.partnerType}
        >
          <option value="" disabled className="bg-cy-dark">
            Select partner type
          </option>
          {PARTNER_TYPES.map((t) => (
            <option key={t.value} value={t.value} className="bg-cy-dark">
              {t.label}
            </option>
          ))}
        </select>
      </Field>

      <fieldset aria-describedby={errors.expertiseAreas ? "expertise-error" : undefined}>
        <legend className="form-label mb-2">
          Expertise Areas
          <span className="text-cy-orange ml-1" aria-label="required">*</span>
        </legend>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {EXPERTISE_AREAS.map((area) => {
            const checked = data.expertiseAreas.includes(area.value);
            return (
              <label
                key={area.value}
                className={clsx(
                  "flex items-center gap-3 px-4 py-3 rounded-xl border cursor-pointer transition-all duration-150 min-h-[44px]",
                  checked
                    ? "border-cy-orange/50 bg-cy-orange/10 text-white"
                    : "border-cy-glass-border bg-cy-glass-bg text-cy-gray-400 hover:border-white/15 hover:text-white"
                )}
              >
                <input
                  type="checkbox"
                  value={area.value}
                  checked={checked}
                  onChange={() => onToggleExpertise(area.value)}
                  className="sr-only"
                  aria-checked={checked}
                />
                <span
                  className={clsx(
                    "flex-shrink-0 w-4 h-4 rounded border-2 flex items-center justify-center transition-colors",
                    checked
                      ? "border-cy-orange bg-cy-orange"
                      : "border-cy-gray-600"
                  )}
                  aria-hidden="true"
                >
                  {checked && (
                    <svg
                      className="w-2.5 h-2.5 text-white"
                      viewBox="0 0 12 12"
                      fill="none"
                    >
                      <path
                        d="M2 6l3 3 5-5"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  )}
                </span>
                <span className="text-sm">{area.label}</span>
              </label>
            );
          })}
        </div>
        {errors.expertiseAreas && (
          <p
            className="form-error mt-2"
            role="alert"
            id="expertise-error"
          >
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" aria-hidden="true" />
            {errors.expertiseAreas}
          </p>
        )}
      </fieldset>

      <Field
        label="Years in Business"
        required
        error={errors.yearsInBusiness}
        htmlFor={`${id}-yearsInBusiness`}
      >
        <select
          id={`${id}-yearsInBusiness`}
          value={data.yearsInBusiness}
          onChange={(e) => onChange("yearsInBusiness", e.target.value)}
          className={clsx(
            "form-select",
            errors.yearsInBusiness && "border-red-500/50 focus:border-red-500/70"
          )}
          aria-describedby={errors.yearsInBusiness ? `${id}-yearsInBusiness-error` : undefined}
          aria-invalid={!!errors.yearsInBusiness}
        >
          <option value="" disabled className="bg-cy-dark">
            Select years in business
          </option>
          {YEARS_OPTIONS.map((y) => (
            <option key={y.value} value={y.value} className="bg-cy-dark">
              {y.label}
            </option>
          ))}
        </select>
      </Field>
    </div>
  );
}

// ─── Step 3: Contact & Agreement ─────────────────────────────────────────────

function Step3({
  data,
  errors,
  onChange,
  onToggleConsent,
}: {
  data: FormData;
  errors: FieldErrors;
  onChange: (field: keyof FormData, value: string) => void;
  onToggleConsent: () => void;
}) {
  const id = useId();
  return (
    <div className="space-y-5">
      <Field
        label="Full Name"
        required
        error={errors.contactName}
        htmlFor={`${id}-contactName`}
      >
        <input
          id={`${id}-contactName`}
          type="text"
          value={data.contactName}
          onChange={(e) => onChange("contactName", e.target.value)}
          className={clsx(
            "form-input",
            errors.contactName && "border-red-500/50"
          )}
          placeholder="Jane Doe"
          autoComplete="name"
          aria-describedby={errors.contactName ? `${id}-contactName-error` : undefined}
          aria-invalid={!!errors.contactName}
        />
      </Field>

      <Field
        label="Work Email"
        required
        error={errors.email}
        htmlFor={`${id}-email`}
      >
        <input
          id={`${id}-email`}
          type="email"
          value={data.email}
          onChange={(e) => onChange("email", e.target.value)}
          className={clsx(
            "form-input",
            errors.email && "border-red-500/50"
          )}
          placeholder="jane@company.com"
          autoComplete="email"
          aria-describedby={errors.email ? `${id}-email-error` : undefined}
          aria-invalid={!!errors.email}
        />
      </Field>

      <Field
        label="Phone Number"
        error={errors.phone}
        htmlFor={`${id}-phone`}
        hint="Optional — include country code for faster response."
      >
        <input
          id={`${id}-phone`}
          type="tel"
          value={data.phone}
          onChange={(e) => onChange("phone", e.target.value)}
          className={clsx(
            "form-input",
            errors.phone && "border-red-500/50"
          )}
          placeholder="+1 234 567 8900"
          autoComplete="tel"
          aria-describedby={errors.phone ? `${id}-phone-error` : undefined}
          aria-invalid={!!errors.phone}
        />
      </Field>

      <Field
        label="Message"
        error={errors.message}
        htmlFor={`${id}-message`}
        hint="Tell us about your business and why you want to partner with CyberCom."
      >
        <textarea
          id={`${id}-message`}
          value={data.message}
          onChange={(e) => onChange("message", e.target.value)}
          className="form-textarea"
          placeholder="We specialize in healthcare IT and serve 50+ hospitals across the region…"
          rows={4}
        />
      </Field>

      {/* GDPR Consent */}
      <div className="space-y-2">
        <label
          className={clsx(
            "flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all duration-150",
            data.gdprConsent
              ? "border-cy-orange/40 bg-cy-orange/8"
              : errors.gdprConsent
              ? "border-red-500/40 bg-red-500/5"
              : "border-cy-glass-border bg-cy-glass-bg hover:border-white/15"
          )}
        >
          <input
            type="checkbox"
            checked={data.gdprConsent}
            onChange={onToggleConsent}
            className="sr-only"
            aria-describedby={errors.gdprConsent ? "gdpr-error" : undefined}
            aria-invalid={!!errors.gdprConsent}
            aria-required="true"
          />
          <span
            className={clsx(
              "flex-shrink-0 mt-0.5 w-4 h-4 rounded border-2 flex items-center justify-center transition-colors",
              data.gdprConsent
                ? "border-cy-orange bg-cy-orange"
                : errors.gdprConsent
                ? "border-red-500"
                : "border-cy-gray-600"
            )}
            aria-hidden="true"
          >
            {data.gdprConsent && (
              <svg className="w-2.5 h-2.5 text-white" viewBox="0 0 12 12" fill="none">
                <path
                  d="M2 6l3 3 5-5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </span>
          <span className="text-sm text-cy-gray-400 leading-relaxed">
            I consent to CyberCom Revolution processing my personal data to
            evaluate my partner application and contact me about the partner
            program. I have read and agree to the{" "}
            <a
              href="https://cy-com.com/privacy"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cy-orange hover:text-cy-orange-light underline underline-offset-2 transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              Privacy Policy
            </a>
            .{" "}
            <span className="text-cy-orange">*</span>
          </span>
        </label>
        {errors.gdprConsent && (
          <p className="form-error" role="alert" id="gdpr-error">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" aria-hidden="true" />
            {errors.gdprConsent}
          </p>
        )}
      </div>
    </div>
  );
}

// ─── Success State ────────────────────────────────────────────────────────────

function SuccessScreen({ referenceNumber }: { referenceNumber: string }) {
  return (
    <motion.div
      className="text-center py-8"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div
        className="w-20 h-20 rounded-full bg-cy-orange/15 border border-cy-orange/30 flex items-center justify-center mx-auto mb-6"
        aria-hidden="true"
      >
        <PartyPopper className="w-9 h-9 text-cy-orange" />
      </div>
      <h2 className="text-3xl font-heading font-bold text-white mb-3">
        Application Submitted!
      </h2>
      <p className="text-cy-gray-400 text-lg mb-8 max-w-md mx-auto leading-relaxed">
        Your partner application is under review. Our team will contact you
        within 5 business days.
      </p>
      <div className="inline-flex flex-col items-center gap-1 glass-card px-8 py-5 mb-8">
        <span className="text-xs text-cy-gray-400 uppercase tracking-widest">
          Reference Number
        </span>
        <span className="text-2xl font-heading font-bold text-gradient-orange">
          {referenceNumber}
        </span>
        <span className="text-xs text-cy-gray-400">
          Save this for your records
        </span>
      </div>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Link href="/" className="btn-primary">
          Back to Partner Portal
        </Link>
        <a href="mailto:partners@cy-com.com" className="btn-secondary">
          Contact the Team
        </a>
      </div>
    </motion.div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ApplyPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<FormData>(INITIAL_FORM);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [referenceNumber, setReferenceNumber] = useState<string | null>(null);

  function handleChange(field: keyof FormData, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  }

  function handleToggleExpertise(value: string) {
    setFormData((prev) => ({
      ...prev,
      expertiseAreas: prev.expertiseAreas.includes(value)
        ? prev.expertiseAreas.filter((v) => v !== value)
        : [...prev.expertiseAreas, value],
    }));
    if (errors.expertiseAreas) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next.expertiseAreas;
        return next;
      });
    }
  }

  function handleToggleConsent() {
    setFormData((prev) => ({ ...prev, gdprConsent: !prev.gdprConsent }));
    if (errors.gdprConsent) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next.gdprConsent;
        return next;
      });
    }
  }

  function handleNext() {
    const stepErrors = validateStep(step, formData);
    if (Object.keys(stepErrors).length > 0) {
      setErrors(stepErrors);
      // Focus first error field
      const firstKey = Object.keys(stepErrors)[0];
      const el = document.querySelector<HTMLElement>(
        `[aria-invalid="true"], [id$="${firstKey}"]`
      );
      el?.focus();
      return;
    }
    setErrors({});
    setStep((s) => s + 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleBack() {
    setErrors({});
    setStep((s) => s - 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const stepErrors = validateStep(3, formData);
    if (Object.keys(stepErrors).length > 0) {
      setErrors(stepErrors);
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const response = await fetch(
        "https://api.cy-com.com/api/v1/public/partners/apply/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            company_name: formData.companyName,
            website: formData.website || undefined,
            country: formData.country,
            company_size: formData.companySize,
            partner_type: formData.partnerType,
            expertise_areas: formData.expertiseAreas,
            years_in_business: formData.yearsInBusiness,
            contact_name: formData.contactName,
            email: formData.email,
            phone: formData.phone || undefined,
            message: formData.message || undefined,
            gdpr_consent: formData.gdprConsent,
          }),
        }
      );

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(
          body?.detail ?? `Server error (${response.status}). Please try again.`
        );
      }

      const data = await response.json();
      const ref =
        data?.reference_number ??
        `PAR-${Math.floor(100000 + Math.random() * 900000)}`;
      setReferenceNumber(ref);
    } catch (err) {
      setSubmitError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again or email partners@cy-com.com."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const progress = ((step - 1) / (STEPS.length - 1)) * 100;

  return (
    <div className="min-h-dvh bg-cy-black flex flex-col">
      {/* Top bar */}
      <header className="border-b border-cy-glass-border bg-cy-black/80 backdrop-blur-md px-4 py-4">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-cy-gray-400 hover:text-white transition-colors text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cy-orange rounded"
            aria-label="Back to partner portal"
          >
            <ArrowLeft className="w-4 h-4" aria-hidden="true" />
            Partner Portal
          </Link>
          <span className="text-cy-glass-border">/</span>
          <span className="text-sm text-cy-gray-400">Partner Application</span>
        </div>
      </header>

      <main id="main-content" className="flex-1 flex flex-col py-10 px-4">
        <div className="max-w-2xl mx-auto w-full flex-1 flex flex-col">
          {referenceNumber ? (
            <SuccessScreen referenceNumber={referenceNumber} />
          ) : (
            <>
              {/* Page title */}
              <div className="mb-8 text-center">
                <h1 className="text-3xl font-heading font-bold text-white mb-2">
                  Partner Application
                </h1>
                <p className="text-cy-gray-400">
                  Complete all 3 steps to submit your application.
                </p>
              </div>

              {/* Step indicator */}
              <nav
                aria-label="Application progress"
                className="mb-10"
              >
                {/* Progress bar */}
                <div
                  className="h-1 bg-cy-glass-border rounded-full mb-6 overflow-hidden"
                  role="progressbar"
                  aria-valuenow={step}
                  aria-valuemin={1}
                  aria-valuemax={STEPS.length}
                  aria-label={`Step ${step} of ${STEPS.length}`}
                >
                  <motion.div
                    className="h-full bg-gradient-to-r from-cy-orange to-cy-orange-light rounded-full"
                    initial={false}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.35, ease: "easeOut" }}
                  />
                </div>

                {/* Step list */}
                <ol className="flex items-center justify-between">
                  {STEPS.map((s) => {
                    const Icon = s.icon;
                    const isCompleted = step > s.id;
                    const isCurrent = step === s.id;
                    return (
                      <li
                        key={s.id}
                        className="flex flex-col items-center gap-1.5"
                        aria-current={isCurrent ? "step" : undefined}
                      >
                        <div
                          className={clsx(
                            "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                            isCompleted
                              ? "bg-cy-orange border-cy-orange text-white"
                              : isCurrent
                              ? "border-cy-orange text-cy-orange bg-cy-orange/10"
                              : "border-cy-glass-border text-cy-gray-600 bg-cy-glass-bg"
                          )}
                          aria-hidden="true"
                        >
                          {isCompleted ? (
                            <CheckCircle2 className="w-5 h-5" />
                          ) : (
                            <Icon className="w-4.5 h-4.5" />
                          )}
                        </div>
                        <span
                          className={clsx(
                            "text-xs font-medium hidden sm:block",
                            isCurrent ? "text-white" : "text-cy-gray-400"
                          )}
                        >
                          {s.label}
                        </span>
                      </li>
                    );
                  })}
                </ol>
              </nav>

              {/* Form card */}
              <div className="glass-card p-6 md:p-8 flex-1">
                <form
                  onSubmit={step === 3 ? handleSubmit : (e) => { e.preventDefault(); handleNext(); }}
                  noValidate
                >
                  {/* Step heading */}
                  <h2 className="text-xl font-heading font-semibold text-white mb-6">
                    {step === 1 && "Company Information"}
                    {step === 2 && "Your Expertise"}
                    {step === 3 && "Contact & Agreement"}
                  </h2>

                  {/* Animated step content */}
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={step}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.25 }}
                    >
                      {step === 1 && (
                        <Step1
                          data={formData}
                          errors={errors}
                          onChange={handleChange}
                        />
                      )}
                      {step === 2 && (
                        <Step2
                          data={formData}
                          errors={errors}
                          onChange={handleChange}
                          onToggleExpertise={handleToggleExpertise}
                        />
                      )}
                      {step === 3 && (
                        <Step3
                          data={formData}
                          errors={errors}
                          onChange={handleChange}
                          onToggleConsent={handleToggleConsent}
                        />
                      )}
                    </motion.div>
                  </AnimatePresence>

                  {/* Submit error */}
                  {submitError && (
                    <div
                      className="mt-6 p-4 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-sm flex items-start gap-2"
                      role="alert"
                      aria-live="assertive"
                    >
                      <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
                      {submitError}
                    </div>
                  )}

                  {/* Navigation */}
                  <div className="flex items-center justify-between mt-8 pt-6 border-t border-cy-glass-border">
                    {step > 1 ? (
                      <button
                        type="button"
                        onClick={handleBack}
                        className="btn-ghost"
                        disabled={isSubmitting}
                      >
                        <ChevronLeft className="w-4 h-4" aria-hidden="true" />
                        Back
                      </button>
                    ) : (
                      <div />
                    )}

                    {step < 3 ? (
                      <button
                        type="submit"
                        className="btn-primary"
                      >
                        Continue
                        <ChevronRight className="w-4 h-4" aria-hidden="true" />
                      </button>
                    ) : (
                      <button
                        type="submit"
                        className="btn-primary"
                        disabled={isSubmitting}
                        aria-busy={isSubmitting}
                      >
                        {isSubmitting ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                            Submitting…
                          </>
                        ) : (
                          <>
                            Submit Application
                            <ChevronRight className="w-4 h-4" aria-hidden="true" />
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </form>
              </div>

              {/* Step counter */}
              <p className="text-center text-xs text-cy-gray-400 mt-4">
                Step {step} of {STEPS.length}
              </p>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
