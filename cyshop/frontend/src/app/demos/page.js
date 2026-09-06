"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft, ArrowRight, ShoppingBag, Store, HeartPulse, Truck,
  Loader2, ExternalLink, Sparkles,
} from "lucide-react";

// Each demo is a pre-seeded environment (see the seed_*_sim management
// commands). "instant" demos log straight into a cyshop workspace; the
// others open their own product surface.
const DEMOS = [
  {
    key: "qsr",
    kind: "instant",
    title: "Quick-Service Restaurant Chain",
    industry: "Food & Beverage",
    icon: ShoppingBag,
    accent: "text-brand-blue",
    blurb:
      "A McDonald's-style operator — 4 countries, 16 branches, a full week of trading: counter / kiosk / drive-thru / online orders, kitchen timing, BOM-driven inventory, supplier deliveries and store crew.",
    stats: ["16 branches", "~4,500 orders/week", "156 products", "324 staff"],
    cred: { subdomain: "qsr-demo", username: "qsr-demo-ops", password: "demo1234" },
  },
  {
    key: "retail",
    kind: "instant",
    title: "Independent Retail Shop",
    industry: "Retail",
    icon: Store,
    accent: "text-purple-600",
    blurb:
      "A single-owner workspace: company, two branches, warehouses, a product catalogue, opening stock and a POS device — the smallest end-to-end setup.",
    stats: ["2 branches", "POS + KDS", "Inter-branch transfers"],
    cred: { subdomain: "demo", username: "demo", password: "Demo@cyshop1" },
  },
  {
    key: "hospital",
    kind: "external",
    title: "Specialty Hospital & Clinic Network",
    industry: "Healthcare",
    icon: HeartPulse,
    accent: "text-rose-600",
    blurb:
      "A US-style specialty hospital in Amman plus a 5-clinic network — a week of emergency arrivals, admissions, ICU, lab / imaging / pharmacy orders and outpatient clinics across six service lines.",
    stats: ["218 beds", "~200 ED visits/wk", "75 admissions", "2,500 orders"],
    href: process.env.NEXT_PUBLIC_CYMED_URL || "http://localhost:8095/",
  },
  {
    key: "logistics",
    kind: "external",
    title: "Logistics & Export Distribution",
    industry: "Logistics",
    icon: Truck,
    accent: "text-amber-600",
    blurb:
      "Two scenarios: a two-person last-mile courier (routes, proof of delivery, exceptions) and the Anabtawi sweets group — plant batches, 4-branch retail and consolidated international shipments to SA / AE / US / DE.",
    stats: ["Consolidated shipments", "Carton net/gross weights", "Incoterms + customs"],
    href: process.env.NEXT_PUBLIC_CYCOM_URL || "http://localhost:8090/admin/cycom_logistics/shipment/",
  },
];

export default function DemosPage() {
  const router = useRouter();
  const [launching, setLaunching] = useState("");
  const [error, setError] = useState("");

  const launch = async (demo) => {
    setError("");
    setLaunching(demo.key);
    try {
      const base = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${base}/api/v1/identity/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(demo.cred.subdomain ? { "X-Tenant-Subdomain": demo.cred.subdomain } : {}),
        },
        body: JSON.stringify({
          username: demo.cred.username,
          password: demo.cred.password,
          workspace: demo.cred.subdomain,
        }),
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.detail || e.non_field_errors?.[0] || "Could not start the demo.");
      }
      const data = await res.json();
      localStorage.setItem("access_token", data.access_token);
      if (data.refresh_token) localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("tenant_id", data.tenant_id);
      localStorage.setItem("tenant_name", data.tenant_name);
      localStorage.setItem("username", data.username);
      localStorage.setItem("email", data.email || "");
      localStorage.setItem("scopes", JSON.stringify(data.scopes || []));
      router.push("/app");
    } catch (e) {
      setError(e.message);
      setLaunching("");
    }
  };

  return (
    <main className="min-h-screen bg-[var(--color-bg,#fafafa)]">
      <div className="mx-auto max-w-6xl px-6 py-14">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-neutral-500 hover:text-neutral-800"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </Link>

        <div className="mt-8 mb-2 inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1 text-xs font-semibold text-brand-blue">
          <Sparkles className="w-3.5 h-3.5" /> Live sandboxes
        </div>
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-neutral-900">
          Choose a demo and walk the platform
        </h1>
        <p className="mt-3 max-w-2xl text-neutral-600">
          Every demo is a real, seeded environment — a full week of operations you can
          click through: orders, inventory, scheduling, deliveries, reports. Nothing is
          mocked. Pick the one closest to your business.
        </p>

        {error && (
          <div className="mt-6 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <div className="mt-10 grid gap-6 md:grid-cols-2">
          {DEMOS.map((d) => {
            const Icon = d.icon;
            const busy = launching === d.key;
            return (
              <div
                key={d.key}
                className="flex flex-col rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm transition hover:shadow-md"
              >
                <div className="flex items-start gap-4">
                  <div className="rounded-xl bg-neutral-50 p-3">
                    <Icon className={`w-7 h-7 ${d.accent}`} />
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
                      {d.industry}
                    </div>
                    <h2 className="text-lg font-bold text-neutral-900">{d.title}</h2>
                  </div>
                </div>

                <p className="mt-4 text-sm leading-relaxed text-neutral-600">{d.blurb}</p>

                <div className="mt-4 flex flex-wrap gap-2">
                  {d.stats.map((s) => (
                    <span
                      key={s}
                      className="rounded-full bg-neutral-100 px-2.5 py-1 text-xs font-medium text-neutral-600"
                    >
                      {s}
                    </span>
                  ))}
                </div>

                <div className="mt-6 pt-4 border-t border-neutral-100">
                  {d.kind === "instant" ? (
                    <button
                      onClick={() => launch(d)}
                      disabled={busy || !!launching}
                      className="inline-flex items-center gap-2 rounded-lg bg-neutral-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-neutral-700 disabled:opacity-60"
                    >
                      {busy ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" /> Starting the demo…
                        </>
                      ) : (
                        <>
                          Launch demo <ArrowRight className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  ) : (
                    <a
                      href={d.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 px-4 py-2.5 text-sm font-semibold text-neutral-800 transition hover:bg-neutral-50"
                    >
                      Open demo <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-14 rounded-2xl border border-neutral-200 bg-white p-6">
          <h3 className="font-bold text-neutral-900">Ready to run your own?</h3>
          <p className="mt-1 text-sm text-neutral-600">
            Start a free workspace, pick your plan, and import your own catalogue.
          </p>
          <div className="mt-4 flex gap-3">
            <Link
              href="/wizard"
              className="inline-flex items-center gap-2 rounded-lg bg-brand-blue px-4 py-2.5 text-sm font-semibold text-white hover:opacity-90"
            >
              Create a workspace <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/pricing"
              className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 px-4 py-2.5 text-sm font-semibold text-neutral-800 hover:bg-neutral-50"
            >
              See pricing
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
