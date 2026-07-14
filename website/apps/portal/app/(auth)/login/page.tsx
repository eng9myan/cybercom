"use client";

import { useEffect, useState, useCallback } from "react";
import {
  ShieldCheck,
  Download,
  LifeBuoy,
  Server,
  BookOpen,
  ArrowRight,
  Lock,
  Zap,
} from "lucide-react";

// ── PKCE helpers ─────────────────────────────────────────────────────────────

function generateCodeVerifier(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

function generateState(): string {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return Array.from(array, (b) => b.toString(16).padStart(2, "0")).join("");
}

// ── Constants ─────────────────────────────────────────────────────────────────

const AUTH_URL = "https://id.cy-com.com/oauth/authorize";
const REDIRECT_URI = "https://portal.cy-com.com/auth/callback";
const SCOPES = [
  "openid",
  "profile",
  "email",
  "customer.licenses",
  "customer.downloads",
  "support.tickets",
].join(" ");

// ── Feature list ─────────────────────────────────────────────────────────────

const PORTAL_FEATURES = [
  {
    icon: ShieldCheck,
    label: "License Management",
    description: "View active licenses, seats, and expiry dates",
    color: "#ed6c00",
  },
  {
    icon: Download,
    label: "Software Downloads",
    description: "Access installers, updates, and documentation",
    color: "#59c3e1",
  },
  {
    icon: LifeBuoy,
    label: "Support Tickets",
    description: "Create and track support requests",
    color: "#a78bfa",
  },
  {
    icon: Server,
    label: "Deployments",
    description: "Monitor your active deployments and health",
    color: "#34d399",
  },
  {
    icon: BookOpen,
    label: "Training Resources",
    description: "Access courses, certifications, and guides",
    color: "#fb923c",
  },
  {
    icon: Zap,
    label: "Quick Actions",
    description: "Renew licenses, open tickets, download latest",
    color: "#f472b6",
  },
] as const;

// ── Component ─────────────────────────────────────────────────────────────────

export default function LoginPage() {
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Clear any stale auth state on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const errorParam = params.get("error");
    if (errorParam === "session_expired") {
      setError("Your session has expired. Please sign in again.");
    } else if (errorParam === "access_denied") {
      setError("Access was denied. Please try again or contact support.");
    }
  }, []);

  const handleSignIn = useCallback(async () => {
    if (isRedirecting) return;
    setIsRedirecting(true);
    setError(null);

    try {
      const verifier = generateCodeVerifier();
      const challenge = await generateCodeChallenge(verifier);
      const state = generateState();

      // Store for callback verification
      sessionStorage.setItem("pkce_verifier", verifier);
      sessionStorage.setItem("oauth_state", state);
      sessionStorage.setItem("oauth_return_to", window.location.href);

      const clientId = process.env.NEXT_PUBLIC_PORTAL_CLIENT_ID ?? "portal-client";

      const url = new URL(AUTH_URL);
      url.searchParams.set("response_type", "code");
      url.searchParams.set("client_id", clientId);
      url.searchParams.set("redirect_uri", REDIRECT_URI);
      url.searchParams.set("scope", SCOPES);
      url.searchParams.set("state", state);
      url.searchParams.set("code_challenge", challenge);
      url.searchParams.set("code_challenge_method", "S256");
      url.searchParams.set("acr_values", "portal:customer");
      url.searchParams.set("prompt", "login");

      window.location.href = url.toString();
    } catch (err) {
      console.error("Failed to initiate OAuth flow:", err);
      setError("Failed to start sign-in. Please try again.");
      setIsRedirecting(false);
    }
  }, [isRedirecting]);

  return (
    <div
      className="min-h-dvh flex flex-col lg:flex-row"
      style={{ background: "#0a0a0f" }}
    >
      {/* ── Decorative background ── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div
          className="glow-orb w-[600px] h-[600px] -top-48 -left-48 opacity-20"
          style={{ background: "radial-gradient(circle, #ed6c00, transparent 70%)" }}
        />
        <div
          className="glow-orb w-[500px] h-[500px] bottom-0 right-0 opacity-10"
          style={{ background: "radial-gradient(circle, #59c3e1, transparent 70%)" }}
        />
        <div
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
      </div>

      {/* ── Left panel – branding & features ── */}
      <div className="hidden lg:flex lg:w-[45%] xl:w-[42%] flex-col justify-between p-12 relative z-10">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: "rgba(237,108,0,0.15)", border: "1px solid rgba(237,108,0,0.3)" }}
          >
            <Lock className="w-5 h-5" style={{ color: "#ed6c00" }} aria-hidden="true" />
          </div>
          <div>
            <div className="font-heading font-semibold text-white text-base leading-none">
              CyberCom
            </div>
            <div className="text-xs mt-0.5" style={{ color: "#94a3b8" }}>
              Customer Portal
            </div>
          </div>
        </div>

        {/* Headline */}
        <div className="space-y-6">
          <div>
            <h1 className="font-heading text-4xl xl:text-5xl font-semibold text-white leading-tight">
              Your enterprise
              <br />
              <span className="text-gradient">command center.</span>
            </h1>
            <p className="mt-4 text-base leading-relaxed" style={{ color: "#94a3b8", maxWidth: "36ch" }}>
              Everything you need to manage your CyberCom products, licenses,
              support, and deployments — in one secure portal.
            </p>
          </div>

          {/* Feature grid */}
          <ul className="grid grid-cols-2 gap-3" role="list" aria-label="Portal features">
            {PORTAL_FEATURES.map(({ icon: Icon, label, description, color }) => (
              <li
                key={label}
                className="glass-card p-4 space-y-2"
                style={{ borderRadius: "0.875rem" }}
              >
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: `${color}18`, border: `1px solid ${color}30` }}
                  aria-hidden="true"
                >
                  <Icon className="w-4 h-4" style={{ color }} />
                </div>
                <div>
                  <p className="font-heading text-sm font-medium text-white">{label}</p>
                  <p className="text-xs mt-0.5 leading-relaxed" style={{ color: "#64748b" }}>
                    {description}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Footer note */}
        <p className="text-xs" style={{ color: "#475569" }}>
          Secured by CyIdentity — OAuth 2.1 with PKCE
        </p>
      </div>

      {/* ── Right panel – login card ── */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-10 relative z-10">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(237,108,0,0.15)", border: "1px solid rgba(237,108,0,0.3)" }}
            >
              <Lock className="w-4 h-4" style={{ color: "#ed6c00" }} aria-hidden="true" />
            </div>
            <span className="font-heading font-semibold text-white">CyberCom Portal</span>
          </div>

          {/* Card */}
          <div
            className="glass-card p-8 sm:p-10"
            role="main"
            id="main-content"
          >
            {/* Header */}
            <div className="mb-8">
              <h2 className="font-heading text-2xl font-semibold text-white">
                Welcome back
              </h2>
              <p className="mt-2 text-sm" style={{ color: "#94a3b8" }}>
                Sign in with your CyberCom Identity credentials to access your
                portal.
              </p>
            </div>

            {/* Error message */}
            {error && (
              <div
                role="alert"
                aria-live="assertive"
                className="mb-6 px-4 py-3 rounded-xl text-sm flex items-start gap-3"
                style={{
                  background: "rgba(239,68,68,0.1)",
                  border: "1px solid rgba(239,68,68,0.2)",
                  color: "#fca5a5",
                }}
              >
                <span className="mt-0.5 shrink-0" aria-hidden="true">⚠</span>
                <span>{error}</span>
              </div>
            )}

            {/* SSO Button */}
            <button
              onClick={handleSignIn}
              disabled={isRedirecting}
              aria-busy={isRedirecting}
              className="btn-primary w-full"
              style={{ minHeight: "52px", fontSize: "1rem" }}
            >
              {isRedirecting ? (
                <>
                  <span
                    className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
                    aria-hidden="true"
                  />
                  <span>Redirecting to CyIdentity…</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-5 h-5" aria-hidden="true" />
                  <span>Sign in with CyberCom Identity</span>
                  <ArrowRight className="w-4 h-4 ml-auto" aria-hidden="true" />
                </>
              )}
            </button>

            {/* Divider */}
            <div className="my-6 flex items-center gap-3" aria-hidden="true">
              <div className="flex-1 h-px" style={{ background: "rgba(255,255,255,0.06)" }} />
              <span className="text-xs" style={{ color: "#475569" }}>
                Secured by CyIdentity
              </span>
              <div className="flex-1 h-px" style={{ background: "rgba(255,255,255,0.06)" }} />
            </div>

            {/* Trust indicators */}
            <div className="grid grid-cols-3 gap-3 text-center">
              {[
                { label: "OAuth 2.1", sub: "PKCE Flow" },
                { label: "TLS 1.3", sub: "Encrypted" },
                { label: "SOC 2", sub: "Certified" },
              ].map(({ label, sub }) => (
                <div
                  key={label}
                  className="py-3 px-2 rounded-xl"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}
                >
                  <p className="font-heading text-xs font-semibold text-white">{label}</p>
                  <p className="text-2xs mt-0.5" style={{ color: "#64748b", fontSize: "0.625rem" }}>
                    {sub}
                  </p>
                </div>
              ))}
            </div>

            {/* Help */}
            <p className="mt-6 text-center text-xs" style={{ color: "#475569" }}>
              Need access?{" "}
              <a
                href="https://cy-com.com/contact"
                className="underline underline-offset-2 transition-colors hover:text-white"
                style={{ color: "#94a3b8" }}
              >
                Contact sales
              </a>{" "}
              or{" "}
              <a
                href="mailto:support@cy-com.com"
                className="underline underline-offset-2 transition-colors hover:text-white"
                style={{ color: "#94a3b8" }}
              >
                support@cy-com.com
              </a>
            </p>
          </div>

          {/* Bottom note */}
          <p className="mt-6 text-center text-xs" style={{ color: "#334155" }}>
            By signing in, you agree to CyberCom&apos;s{" "}
            <a
              href="https://cy-com.com/legal/terms"
              className="underline underline-offset-2 hover:text-white transition-colors"
              style={{ color: "#475569" }}
            >
              Terms of Service
            </a>{" "}
            and{" "}
            <a
              href="https://cy-com.com/legal/privacy"
              className="underline underline-offset-2 hover:text-white transition-colors"
              style={{ color: "#475569" }}
            >
              Privacy Policy
            </a>
            .
          </p>
        </div>
      </div>
    </div>
  );
}
