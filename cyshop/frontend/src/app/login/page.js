"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff, Sparkles, AlertCircle, ArrowRight, Play, Zap } from "lucide-react";
import Logo from "@/components/brand/Logo";
import { Suspense } from "react";

const DEMO = { subdomain: "", username: "m.alnsour@outlook.com", password: "12345678" };

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [subdomain, setSubdomain] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (searchParams.get("demo") === "1") {
      fillAndSubmitDemo();
    }
  }, []);

  const fillAndSubmitDemo = async () => {
    setError("");
    setLoading(true);
    try {
      const base = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${base}/api/v1/identity/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(DEMO.subdomain ? { "X-Tenant-Subdomain": DEMO.subdomain } : {}),
        },
        body: JSON.stringify({ username: DEMO.username, password: DEMO.password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.non_field_errors?.[0] || err.detail || "Invalid credentials");
      }
      const data = await res.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("tenant_id", data.tenant_id);
      localStorage.setItem("tenant_name", data.tenant_name);
      localStorage.setItem("username", data.username);
      localStorage.setItem("email", data.email);
      localStorage.setItem("scopes", JSON.stringify(data.scopes || []));
      router.push("/app");
    } catch (err) {
      setError(err.message || "Demo login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const base = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${base}/api/v1/identity/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(subdomain ? { "X-Tenant-Subdomain": subdomain } : {}),
        },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.non_field_errors?.[0] || err.detail || "Invalid credentials");
      }
      const data = await res.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("tenant_id", data.tenant_id);
      localStorage.setItem("tenant_name", data.tenant_name);
      localStorage.setItem("username", data.username);
      localStorage.setItem("email", data.email);
      localStorage.setItem("scopes", JSON.stringify(data.scopes || []));
      router.push("/app");
    } catch (err) {
      setError(err.message || "Sign-in failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-dvh grid lg:grid-cols-2 bg-[var(--color-bg)] text-[var(--color-ink)]">
      {/* Form column */}
      <div className="relative flex flex-col justify-between p-6 md:p-10">
        <div className="flex items-center justify-between">
          <Logo />
          <Link href="/" className="text-sm font-semibold text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] transition">
            ← Back home
          </Link>
        </div>

        <div className="mx-auto w-full max-w-md py-12">
          <span className="cy-pill cy-pill-orange">
            <Sparkles className="w-3.5 h-3.5" /> Sign in to CyShop
          </span>
          <h1 className="mt-5 text-3xl md:text-4xl font-heading font-black leading-tight">
            Welcome back.
          </h1>
          <p className="mt-2 text-[var(--color-ink-soft)]">Pick up where the AI left off.</p>

          {/* Demo Credentials Banner */}
          <div className="mt-6 rounded-2xl border border-[rgba(89,195,225,0.25)] bg-[rgba(89,195,225,0.06)] p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <Zap className="w-4 h-4 text-[var(--color-brand-blue)]" />
                  <span className="text-sm font-bold text-[var(--color-brand-blue)]">Try the live demo instantly</span>
                </div>
                <div className="text-xs text-[var(--color-ink-muted)] space-y-0.5">
                  <div>Username: <code className="font-mono text-[var(--color-ink-soft)]">m.alnsour@outlook.com</code></div>
                  <div>Password: <code className="font-mono text-[var(--color-ink-soft)]">12345678</code></div>
                </div>
              </div>
              <button
                type="button"
                onClick={fillAndSubmitDemo}
                className="cy-btn cy-btn-ghost !py-2 !px-4 text-sm shrink-0"
              >
                <Play className="w-3.5 h-3.5 text-[var(--color-brand-blue)]" />
                Launch Demo
              </button>
            </div>
          </div>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[var(--color-line)]" />
            </div>
            <div className="relative flex justify-center text-xs text-[var(--color-ink-muted)]">
              <span className="bg-[var(--color-bg)] px-3">or sign in with your account</span>
            </div>
          </div>

          {error && (
            <div role="alert" className="mb-5 flex items-start gap-3 p-3 rounded-xl border border-[rgba(220,38,38,0.3)] bg-[rgba(220,38,38,0.06)] text-[#DC2626] text-sm">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <Field
              id="subdomain"
              label="Workspace"
              hint="Leave blank to use your default tenant."
              value={subdomain}
              onChange={setSubdomain}
              placeholder="acme"
              autoComplete="organization"
              suffix=".cyshop.cy-com.com"
            />
            <Field
              id="username"
              label="Email or username"
              type="text"
              required
              value={username}
              onChange={setUsername}
              placeholder="you@company.com"
              autoComplete="username"
            />
            <div>
              <label htmlFor="password" className="block text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-ink-soft)] mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className="w-full h-11 rounded-xl bg-[var(--color-surface)] border border-[var(--color-line)] px-4 pr-11 text-sm focus:outline-none focus:border-[#ED6C00] focus:ring-2 focus:ring-[rgba(237,108,0,0.18)] transition text-[var(--color-ink)] placeholder:text-[var(--color-ink-muted)]"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  aria-label={showPw ? "Hide password" : "Show password"}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] flex items-center justify-center transition"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex justify-between items-center text-sm">
              <label className="flex items-center gap-2 cursor-pointer text-[var(--color-ink-soft)]">
                <input type="checkbox" className="w-4 h-4 rounded border-[var(--color-line)] accent-[#ED6C00]" />
                Remember me
              </label>
              <a href="#" className="font-semibold text-[#ED6C00] hover:underline">Forgot password?</a>
            </div>

            <button
              type="submit"
              id="login-submit-btn"
              disabled={loading}
              className="cy-btn cy-btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              ) : (
                <>Sign in <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          <div className="mt-8 text-center text-sm text-[var(--color-ink-muted)]">
            New to CyShop?{" "}
            <Link href="/wizard" className="font-semibold text-[var(--color-ink)] hover:text-[#ED6C00]">
              Create your workspace →
            </Link>
          </div>
        </div>

        <p className="text-xs text-[var(--color-ink-muted)]">
          © {new Date().getFullYear()} CyShop · A CyberCom company
        </p>
      </div>

      {/* Visual column */}
      <div className="relative hidden lg:block overflow-hidden bg-[var(--color-brand-ink)] text-white">
        <div
          className="absolute inset-0 opacity-80"
          style={{
            background:
              "radial-gradient(40rem 30rem at 80% 10%, rgba(237,108,0,.45), transparent 60%), radial-gradient(40rem 30rem at 10% 100%, rgba(89,195,225,.4), transparent 60%)",
          }}
        />
        <div className="cy-grid absolute inset-0" aria-hidden />
        <div className="relative h-full flex flex-col justify-between p-12">
          <div />
          <div className="max-w-md">
            <span className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-white/60">
              <span className="cy-blink" /> Live AI workspace
            </span>
            <h2 className="mt-4 text-3xl xl:text-4xl font-heading font-black leading-tight">
              Your retail stack,<br />
              <span className="cy-text-gradient">already thinking ahead.</span>
            </h2>
            <p className="mt-4 text-white/70 leading-relaxed">
              POS, inventory, CRM, AI forecasting and loyalty — all in one platform.
              Tenant-isolated. Production-grade.
            </p>
            <ul className="mt-6 space-y-2 text-sm">
              {["Multi-tenant by design", "Works offline (POS)", "AI-powered demand forecasting"].map((t) => (
                <li key={t} className="flex items-center gap-2 text-white/80">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#59C3E1]" aria-hidden /> {t}
                </li>
              ))}
            </ul>
          </div>
          <div className="text-xs text-white/40">SOC2 controls · GDPR ready · Built for global commerce</div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-dvh bg-[#0a0a0f]" />}>
      <LoginForm />
    </Suspense>
  );
}

function Field({ id, label, hint, value, onChange, placeholder, autoComplete, type = "text", required, suffix }) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-ink-soft)] mb-1.5">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          required={required}
          className={`w-full h-11 rounded-xl bg-[var(--color-surface)] border border-[var(--color-line)] px-4 ${suffix ? "pr-40" : ""} text-sm focus:outline-none focus:border-[#ED6C00] focus:ring-2 focus:ring-[rgba(237,108,0,0.18)] transition text-[var(--color-ink)] placeholder:text-[var(--color-ink-muted)]`}
        />
        {suffix && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[var(--color-ink-muted)] font-mono">
            {suffix}
          </span>
        )}
      </div>
      {hint && <p className="mt-1 text-xs text-[var(--color-ink-muted)]">{hint}</p>}
    </div>
  );
}
