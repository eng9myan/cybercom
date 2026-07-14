"use client";

import {
  TrendingUp, Users, DollarSign, ArrowUpRight, ArrowDownRight,
  Building2, ShoppingCart, BarChart3, Stethoscope, Pill,
  FlaskConical, Scan, Activity, Calendar, UserCheck,
} from "lucide-react";
import Link from "next/link";

/* ── revenue snapshot ── */
const METRICS = [
  { label: "MRR", value: "$147,230", change: "+12.4%", up: true, icon: DollarSign, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  { label: "ARR", value: "$1.77M", change: "+14.1%", up: true, icon: TrendingUp, color: "text-blue-400", bg: "bg-blue-500/10" },
  { label: "Active Customers", value: "38", change: "+3 this month", up: true, icon: Users, color: "text-cy-orange", bg: "bg-cy-orange/10" },
  { label: "Churn Rate", value: "1.8%", change: "-0.4%", up: false, icon: Activity, color: "text-violet-400", bg: "bg-violet-500/10" },
];

const PRODUCT_MIX = [
  { name: "CyMed Hospital", icon: Building2, color: "text-emerald-400", bg: "bg-emerald-500/10", customers: 12, mrr: 52400, pct: 35.6 },
  { name: "CyCom ERP", icon: BarChart3, color: "text-blue-400", bg: "bg-blue-500/10", customers: 22, mrr: 43900, pct: 29.8 },
  { name: "CyMed Clinic", icon: Stethoscope, color: "text-teal-400", bg: "bg-teal-500/10", customers: 15, mrr: 21300, pct: 14.5 },
  { name: "CyShop", icon: ShoppingCart, color: "text-orange-400", bg: "bg-orange-500/10", customers: 8, mrr: 14800, pct: 10.1 },
  { name: "CyMed Pharmacy", icon: Pill, color: "text-violet-400", bg: "bg-violet-500/10", customers: 11, mrr: 8930, pct: 6.1 },
  { name: "CyMed Lab", icon: FlaskConical, color: "text-cyan-400", bg: "bg-cyan-500/10", customers: 5, mrr: 3950, pct: 2.7 },
  { name: "CyMed Imaging", icon: Scan, color: "text-sky-400", bg: "bg-sky-500/10", customers: 3, mrr: 1950, pct: 1.3 },
];

const RECENT_SIGNUPS = [
  { customer: "King Fahad Medical City", product: "CyMed Hospital Advanced", date: "2026-07-03", value: 4500, country: "SA" },
  { customer: "Al Jazeera Pharmacy Chain", product: "CyMed Pharmacy Clinical", date: "2026-07-02", value: 399, country: "JO" },
  { customer: "Gulf Retail Group", product: "CyShop Enterprise", date: "2026-07-01", value: null, country: "AE" },
  { customer: "Amman Specialized Clinics", product: "CyMed Clinic Pro", date: "2026-06-30", value: 599, country: "JO" },
  { customer: "National Lab Services", product: "CyMed Lab Full", date: "2026-06-28", value: 549, country: "KW" },
];

const MONTHLY_DATA = [
  { month: "Jan", mrr: 98000 },
  { month: "Feb", mrr: 104000 },
  { month: "Mar", mrr: 109000 },
  { month: "Apr", mrr: 115000 },
  { month: "May", mrr: 124000 },
  { month: "Jun", mrr: 134000 },
  { month: "Jul", mrr: 147230 },
];
const maxMRR = Math.max(...MONTHLY_DATA.map((d) => d.mrr));

export default function AdminRevenuePage() {
  return (
    <div>
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-heading font-semibold text-white mb-1">Revenue Dashboard</h1>
          <p className="text-sm text-cy-gray-400">CyberCom SaaS business overview — July 2026</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-cy-gray-400">
          <Calendar className="w-3.5 h-3.5" />
          Last updated: just now
        </div>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {METRICS.map(({ label, value, change, up, icon: Icon, color, bg }) => (
          <div key={label} className="glass-card p-5 rounded-xl">
            <div className={`w-8 h-8 ${bg} rounded-lg flex items-center justify-center mb-3`}>
              <Icon className={`w-4 h-4 ${color}`} />
            </div>
            <div className="text-xl font-heading font-bold text-white">{value}</div>
            <div className="text-xs text-cy-gray-400 mt-0.5 mb-2">{label}</div>
            <div className={`flex items-center gap-1 text-xs font-medium ${up ? "text-emerald-400" : "text-red-400"}`}>
              {up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
              {change}
            </div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        {/* MRR chart */}
        <div className="lg:col-span-2 glass-card p-5 rounded-xl">
          <h2 className="font-heading font-semibold text-white mb-6">MRR Growth</h2>
          <div className="flex items-end gap-3 h-32">
            {MONTHLY_DATA.map((d) => (
              <div key={d.month} className="flex-1 flex flex-col items-center gap-1">
                <div className="text-xs text-cy-gray-400 font-medium">${Math.round(d.mrr / 1000)}k</div>
                <div
                  className="w-full rounded-t-md bg-gradient-to-t from-cy-orange/70 to-cy-orange transition-all"
                  style={{ height: `${(d.mrr / maxMRR) * 80}px` }}
                />
                <div className="text-xs text-cy-gray-500">{d.month}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Product mix */}
        <div className="glass-card p-5 rounded-xl">
          <h2 className="font-heading font-semibold text-white mb-4">Revenue by Product</h2>
          <div className="space-y-3">
            {PRODUCT_MIX.map((p) => {
              const Icon = p.icon;
              return (
                <div key={p.name}>
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className={`w-3.5 h-3.5 ${p.color} flex-shrink-0`} />
                    <span className="text-xs text-cy-gray-300 flex-1 min-w-0 truncate">{p.name}</span>
                    <span className="text-xs font-medium text-white">{p.pct}%</span>
                  </div>
                  <div className="h-1.5 bg-cy-glass-border rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${p.bg.replace("bg-", "bg-").replace("/10", "/80")}`} style={{ width: `${p.pct}%`, background: "currentColor" }}>
                      <div className={`h-full rounded-full ${p.color.replace("text-", "bg-")}`} style={{ width: "100%", opacity: 0.7 }} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Product table */}
        <div className="lg:col-span-2 glass-card rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-cy-glass-border">
            <h2 className="font-heading font-semibold text-white">Product Breakdown</h2>
            <Link href="/en/admin/products" className="text-xs text-cy-orange hover:text-cy-orange-light">Manage →</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-cy-glass-border">
                  {["Product", "Customers", "MRR", "% of Total"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium text-cy-gray-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {PRODUCT_MIX.map((p) => {
                  const Icon = p.icon;
                  return (
                    <tr key={p.name} className="border-b border-cy-glass-border/50 hover:bg-cy-glass-border/20 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className={`w-6 h-6 rounded ${p.bg} flex items-center justify-center`}>
                            <Icon className={`w-3.5 h-3.5 ${p.color}`} />
                          </div>
                          <span className="text-white font-medium">{p.name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-cy-gray-300">{p.customers}</td>
                      <td className="px-4 py-3 text-white font-semibold">${p.mrr.toLocaleString()}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-cy-glass-border rounded-full max-w-16 overflow-hidden">
                            <div className="h-full bg-cy-orange rounded-full" style={{ width: `${p.pct}%` }} />
                          </div>
                          <span className="text-cy-gray-300">{p.pct}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent signups */}
        <div className="glass-card rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-cy-glass-border">
            <h2 className="font-heading font-semibold text-white">Recent Signups</h2>
            <Link href="/en/admin/customers" className="text-xs text-cy-orange hover:text-cy-orange-light">All →</Link>
          </div>
          <div className="divide-y divide-cy-glass-border/50">
            {RECENT_SIGNUPS.map((s) => (
              <div key={s.customer} className="px-4 py-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-xs font-medium text-white truncate">{s.customer}</div>
                    <div className="text-xs text-cy-gray-400 mt-0.5 truncate">{s.product}</div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    {s.value !== null
                      ? <div className="text-xs font-semibold text-emerald-400">${s.value}/mo</div>
                      : <div className="text-xs text-cy-orange">Custom</div>}
                    <div className="text-xs text-cy-gray-500 mt-0.5">{s.country}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid sm:grid-cols-3 gap-4 mt-6">
        {[
          { label: "View all customers", href: "/en/admin/customers", icon: UserCheck },
          { label: "Manage subscriptions", href: "/en/admin/subscriptions", icon: ShoppingCart },
          { label: "Product catalog", href: "/en/admin/products", icon: BarChart3 },
        ].map(({ label, href, icon: Icon }) => (
          <Link key={href} href={href} className="glass-card p-4 rounded-xl flex items-center gap-3 hover:border-cy-orange/30 border border-cy-glass-border transition-colors">
            <Icon className="w-5 h-5 text-cy-orange" />
            <span className="text-sm font-medium text-white">{label}</span>
            <ArrowUpRight className="w-4 h-4 text-cy-gray-400 ml-auto" />
          </Link>
        ))}
      </div>
    </div>
  );
}
