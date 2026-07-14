"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Building2, User, Mail, Lock, ArrowRight, ChevronLeft,
  Play, Sparkles, Check, AlertCircle,
} from "lucide-react";
import Logo from "@/components/brand/Logo";

const STEPS = [
  { id: 1, label: "Organization" },
  { id: 2, label: "Admin Account" },
  { id: 3, label: "Ready" },
];

export default function WizardPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [tenantName, setTenantName] = useState("");
  const [subdomain, setSubdomain] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [error, setError] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setStatusMsg("Connecting to cloud gateway…");

    const messages = [
      "Creating isolated tenant schema…",
      "Provisioning core organization…",
      "Initializing admin credentials & RBAC…",
    ];
    messages.forEach((msg, i) => setTimeout(() => setStatusMsg(msg), (i + 1) * 1000));

    try {
      const base = process.env.NEXT_PUBLIC_API_URL || "";
      const response = await fetch(`${base}/api/v1/tenants/register/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: tenantName, subdomain, email, username, password }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || errData.detail || "Failed to provision workspace");
      }

      setStatusMsg("Workspace ready! Redirecting…");
      setTimeout(() => router.push("/login"), 1500);
    } catch (err) {
      setError(err.message || "Provisioning error. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-dvh bg-[var(--color-bg)] text-[var(--color-ink)] flex flex-col">
      {/* Top bar */}
      <header className="h-16 px-6 flex items-center justify-between border-b border-[var(--color-line)]">
        <Logo />
        <Link href="/login" className="text-sm font-semibold text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] transition flex items-center gap-1.5">
          <ChevronLeft className="w-4 h-4" /> Back to login
        </Link>
      </header>

      {/* Demo shortcut banner */}
      <div className="bg-[rgba(89,195,225,0.07)] border-b border-[rgba(89,195,225,0.15)] px-6 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 text-sm">
          <span className="cy-blink" />
          <span className="text-[var(--color-ink-soft)]">Want to explore without registering?</span>
        </div>
        <button
          onClick={() => router.push("/login?demo=1")}
          className="cy-btn cy-btn-ghost !py-1.5 !px-4 text-sm"
        >
          <Play className="w-3.5 h-3.5 text-[var(--color-brand-blue)]" />
          Try Demo Instead
        </button>
      </div>

      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-lg">
          {/* Step indicator */}
          <div className="flex items-center gap-2 mb-8">
            {STEPS.map((s, i) => (
              <div key={s.id} className="flex items-center gap-2 flex-1">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border transition ${
                  step > s.id
                    ? "bg-[#ED6C00] border-[#ED6C00] text-white"
                    : step === s.id
                    ? "border-[#ED6C00] text-[#ED6C00]"
                    : "border-[var(--color-line)] text-[var(--color-ink-muted)]"
                }`}>
                  {step > s.id ? <Check className="w-3.5 h-3.5" /> : s.id}
                </div>
                <span className={`text-xs font-medium hidden sm:inline ${step === s.id ? "text-[var(--color-ink)]" : "text-[var(--color-ink-muted)]"}`}>
                  {s.label}
                </span>
                {i < STEPS.length - 1 && <div className="flex-1 h-px bg-[var(--color-line)] ml-2" />}
              </div>
            ))}
          </div>

          <div className="cy-glass p-8">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-4 h-4 text-[#ED6C00]" />
              <span className="text-xs font-bold uppercase tracking-[0.18em] text-[#ED6C00]">New Workspace</span>
            </div>
            <h1 className="text-2xl font-heading font-black mb-1">
              {step === 1 && "Your Organization"}
              {step === 2 && "Admin Account"}
              {step === 3 && "Workspace Ready"}
            </h1>
            <p className="text-sm text-[var(--color-ink-soft)] mb-7">
              {step === 1 && "Set up your isolated tenant space in seconds."}
              {step === 2 && "Create the administrator account for this workspace."}
            </p>

            {error && (
              <div role="alert" className="mb-6 flex items-start gap-3 p-3 rounded-xl border border-[rgba(220,38,38,0.3)] bg-[rgba(220,38,38,0.06)] text-[#DC2626] text-sm">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {loading ? (
              <div className="text-center py-10 space-y-6">
                <div className="w-14 h-14 mx-auto rounded-full border-4 border-[var(--color-line)] border-t-[#ED6C00] animate-spin" />
                <p className="text-[var(--color-ink-soft)] text-sm font-mono tracking-wide animate-pulse">{statusMsg}</p>
              </div>
            ) : step === 1 ? (
              <div className="space-y-5">
                <WizField
                  id="tenantName" label="Organization Name" icon={Building2}
                  placeholder="Acme Retail Ltd"
                  value={tenantName}
                  onChange={(v) => {
                    setTenantName(v);
                    setSubdomain(v.toLowerCase().replace(/[^a-z0-9]/g, ""));
                  }}
                  required
                />
                <div>
                  <label htmlFor="subdomain" className="cy-label">Workspace URL</label>
                  <div className="flex">
                    <input
                      id="subdomain"
                      type="text"
                      required
                      placeholder="acmeretail"
                      value={subdomain}
                      onChange={(e) => setSubdomain(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, ""))}
                      className="cy-input rounded-r-none border-r-0 flex-1"
                    />
                    <span className="h-11 flex items-center px-4 bg-[var(--color-surface-2)] border border-[var(--color-line)] rounded-r-xl text-sm text-[var(--color-ink-muted)] font-mono whitespace-nowrap">
                      .cyshop.cy-com.com
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={!tenantName || !subdomain}
                  className="cy-btn cy-btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                >
                  Continue <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            ) : step === 2 ? (
              <form onSubmit={handleRegister} className="space-y-5">
                <WizField id="username" label="Admin Username" icon={User} placeholder="acmeadmin" value={username} onChange={setUsername} required />
                <WizField id="email" label="Admin Email" icon={Mail} type="email" placeholder="admin@company.com" value={email} onChange={setEmail} required autoComplete="email" />
                <WizField id="password" label="Password" icon={Lock} type="password" placeholder="Min 8 characters" value={password} onChange={setPassword} required autoComplete="new-password" />
                <div className="flex gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="cy-btn cy-btn-ghost flex-1"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={!username || !email || !password}
                    className="cy-btn cy-btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Deploy Workspace
                  </button>
                </div>
              </form>
            ) : null}
          </div>

          <p className="text-center text-xs text-[var(--color-ink-muted)] mt-6">
            Already have a workspace?{" "}
            <Link href="/login" className="text-[#ED6C00] font-semibold hover:underline">
              Sign in →
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}

function WizField({ id, label, icon: Icon, value, onChange, placeholder, type = "text", required, autoComplete }) {
  return (
    <div>
      <label htmlFor={id} className="cy-label">{label}</label>
      <div className="relative">
        <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-ink-muted)]" />
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          autoComplete={autoComplete}
          className="cy-input !pl-10 h-11"
        />
      </div>
    </div>
  );
}
