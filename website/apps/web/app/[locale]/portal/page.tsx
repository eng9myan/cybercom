"use client";

import Link from "next/link";
import {
  Building2, BarChart3, Pill,
  ArrowRight, TrendingUp,
  AlertCircle, Download, CheckCircle2, Users, CreditCard,
  Activity,
} from "lucide-react";

/* ── demo data (replace with real API in production) ── */
const SUBSCRIBED_PRODUCTS = [
  {
    id: "cymed-hospital",
    name: "CyMed Hospital",
    edition: "Hospital Advanced",
    icon: Building2,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    status: "active",
    renewalDate: "2027-07-01",
    seats: 120,
    usedSeats: 87,
    demoUrl: "https://cymed.cy-com.com/hospital",
  },
  {
    id: "cymed-pharmacy",
    name: "CyMed Pharmacy",
    edition: "Pharmacy Clinical",
    icon: Pill,
    color: "text-violet-400",
    bg: "bg-violet-500/10",
    border: "border-violet-500/20",
    status: "active",
    renewalDate: "2027-07-01",
    seats: 20,
    usedSeats: 14,
    demoUrl: "https://cymed.cy-com.com/pharmacy",
  },
  {
    id: "cycom-erp",
    name: "CyCom ERP",
    edition: "Enterprise",
    icon: BarChart3,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    status: "active",
    renewalDate: "2027-07-01",
    seats: 50,
    usedSeats: 32,
    demoUrl: "https://health.cy-com.com",
  },
];

const INVOICES = [
  { id: "INV-2026-006", date: "2026-07-01", amount: 7898, status: "paid" },
  { id: "INV-2026-005", date: "2026-06-01", amount: 7898, status: "paid" },
  { id: "INV-2026-004", date: "2026-05-01", amount: 7898, status: "paid" },
];

const TICKETS = [
  { id: "TKT-1042", title: "Lab integration HL7 mapping question", status: "open", updated: "2h ago" },
  { id: "TKT-1038", title: "Pharmacy auto-verification threshold", status: "resolved", updated: "3d ago" },
];

export default function PortalDashboardPage() {
  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-heading font-semibold text-white mb-1">Welcome back</h1>
          <p className="text-sm text-cy-gray-400">Your CyberCom subscription overview</p>
        </div>
        <Link
          href="/en/subscribe"
          className="hidden sm:inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-colors"
        >
          Add Product <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Active Products", value: "3", icon: Activity, color: "text-emerald-400", bg: "bg-emerald-500/10" },
          { label: "Total Users", value: "133", icon: Users, color: "text-blue-400", bg: "bg-blue-500/10" },
          { label: "Monthly Spend", value: "$6,398", icon: CreditCard, color: "text-cy-orange", bg: "bg-cy-orange/10" },
          { label: "Uptime (30d)", value: "99.97%", icon: TrendingUp, color: "text-violet-400", bg: "bg-violet-500/10" },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="glass-card p-5 rounded-xl">
            <div className={`w-8 h-8 ${bg} rounded-lg flex items-center justify-center mb-3`}>
              <Icon className={`w-4 h-4 ${color}`} />
            </div>
            <div className="text-xl font-heading font-bold text-white">{value}</div>
            <div className="text-xs text-cy-gray-400 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Active products */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-heading font-semibold text-white">Active Subscriptions</h2>
            <Link href="/en/portal/subscriptions" className="text-xs text-cy-orange hover:text-cy-orange-light">Manage all →</Link>
          </div>
          <div className="space-y-3">
            {SUBSCRIBED_PRODUCTS.map((p) => {
              const Icon = p.icon;
              const usagePct = Math.round((p.usedSeats / p.seats) * 100);
              return (
                <div key={p.id} className="glass-card p-5 rounded-xl">
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded-lg ${p.bg} border ${p.border} flex items-center justify-center flex-shrink-0`}>
                      <Icon className={`w-5 h-5 ${p.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="font-heading font-semibold text-sm text-white">{p.name}</span>
                        <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                          Active
                        </span>
                      </div>
                      <div className="text-xs text-cy-gray-400 mb-3">
                        {p.edition} · Renews{" "}
                        {new Date(p.renewalDate).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 h-1.5 bg-cy-glass-border rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${usagePct > 85 ? "bg-amber-400" : "bg-emerald-500"}`}
                            style={{ width: `${usagePct}%` }}
                          />
                        </div>
                        <span className="text-xs text-cy-gray-400 flex-shrink-0">{p.usedSeats}/{p.seats} seats</span>
                      </div>
                    </div>
                    <a
                      href={p.demoUrl}
                      target="_blank"
                      rel="noreferrer"
                      className={`flex-shrink-0 text-xs ${p.color} hover:opacity-80 transition-opacity`}
                    >
                      Open →
                    </a>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Add product prompt */}
          <div className="mt-3 p-4 rounded-xl border border-dashed border-cy-glass-border flex items-center justify-between">
            <span className="text-sm text-cy-gray-400">Need another product?</span>
            <Link href="/en/subscribe" className="text-sm text-cy-orange hover:text-cy-orange-light flex items-center gap-1.5">
              Add product <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Recent invoices */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading font-semibold text-white">Recent Invoices</h2>
              <Link href="/en/portal/billing" className="text-xs text-cy-orange hover:text-cy-orange-light">View all →</Link>
            </div>
            <div className="space-y-2">
              {INVOICES.map((inv) => (
                <div key={inv.id} className="glass-card px-4 py-3 rounded-xl flex items-center justify-between">
                  <div>
                    <div className="text-xs font-medium text-white">{inv.id}</div>
                    <div className="text-xs text-cy-gray-400">
                      {new Date(inv.date).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-white">${inv.amount.toLocaleString()}</span>
                    <button className="p-1.5 rounded-lg hover:bg-cy-glass-border/50 text-cy-gray-400 hover:text-white transition-colors">
                      <Download className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Support tickets */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading font-semibold text-white">Support</h2>
              <Link href="/en/portal/support" className="text-xs text-cy-orange hover:text-cy-orange-light">All tickets →</Link>
            </div>
            <div className="space-y-2">
              {TICKETS.map((t) => (
                <div key={t.id} className="glass-card px-4 py-3 rounded-xl">
                  <div className="flex items-start gap-2">
                    {t.status === "open"
                      ? <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                      : <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />}
                    <div>
                      <div className="text-xs font-medium text-white mb-0.5">{t.title}</div>
                      <div className="text-xs text-cy-gray-500">{t.id} · {t.updated}</div>
                    </div>
                  </div>
                </div>
              ))}
              <Link
                href="/en/portal/support"
                className="block text-center text-xs text-cy-orange hover:text-cy-orange-light py-2 border border-dashed border-cy-glass-border rounded-xl transition-colors"
              >
                + New support ticket
              </Link>
            </div>
          </div>

          {/* Quick links */}
          <div className="glass-card p-4 rounded-xl space-y-2">
            <div className="text-xs font-medium text-cy-gray-400 mb-3">Quick links</div>
            {[
              { label: "CyCom ERP", href: "https://health.cy-com.com", ext: true },
              { label: "CyMed Hospital", href: "https://cymed.cy-com.com/hospital", ext: true },
              { label: "Upgrade plan", href: "/en/portal/subscriptions" },
              { label: "Download invoices", href: "/en/portal/billing" },
            ].map(({ label, href, ext }) => (
              <a
                key={label}
                href={href}
                target={ext ? "_blank" : undefined}
                rel={ext ? "noreferrer" : undefined}
                className="flex items-center justify-between text-sm text-cy-gray-300 hover:text-white transition-colors py-1.5"
              >
                {label}
                <ArrowRight className="w-3.5 h-3.5 text-cy-gray-500" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
