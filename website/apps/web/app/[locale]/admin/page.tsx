"use client";

import { useEffect, useMemo, useState } from "react";
import {
  TrendingUp, Users, DollarSign, ArrowUpRight,
  BarChart3, Calendar, UserCheck, Receipt, Loader2, ShoppingBag,
} from "lucide-react";
import Link from "next/link";
import {
  adminApi, type Tenant, type TenantSubscription, type TenantSubscriptionInvoice,
} from "@/lib/adminApi";

const PRODUCT_LABEL: Record<string, string> = {
  cycom: "CyCom ERP",
  cyshop: "CyShop",
  cymed_hospital: "CyMed Hospital",
  cymed_clinic: "CyMed Clinic",
  cymed_pharmacy: "CyMed Pharmacy",
  cymed_laboratory: "CyMed Laboratory",
  cymed_imaging: "CyMed Imaging",
};

function productCodeOf(t: Tenant): string {
  return (t.metadata?.product_code as string) || "unknown";
}

export default function AdminRevenuePage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [subs, setSubs] = useState<TenantSubscription[]>([]);
  const [invoices, setInvoices] = useState<TenantSubscriptionInvoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([adminApi.listTenants(), adminApi.listSubscriptions(), adminApi.listInvoices()])
      .then(([t, s, i]) => {
        setTenants(t);
        setSubs(s);
        setInvoices(i);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load revenue data"))
      .finally(() => setLoading(false));
  }, []);

  const subByTenant = useMemo(() => {
    const map: Record<string, TenantSubscription> = {};
    for (const sub of subs) if (!map[sub.tenant]) map[sub.tenant] = sub; // newest-first
    return map;
  }, [subs]);

  const activeTenants = tenants.filter((t) => t.status === "active");
  const mrr = activeTenants.reduce((sum, t) => sum + Number(subByTenant[t.id]?.monthly_price_usd || 0), 0);
  const pendingInvoices = invoices.filter((i) => i.status === "pending");
  const pendingAmount = pendingInvoices.reduce((sum, i) => sum + Number(i.amount || 0), 0);

  const productMix = useMemo(() => {
    const byProduct: Record<string, { customers: number; mrr: number }> = {};
    for (const t of activeTenants) {
      const code = productCodeOf(t);
      const entry = (byProduct[code] ??= { customers: 0, mrr: 0 });
      entry.customers += 1;
      entry.mrr += Number(subByTenant[t.id]?.monthly_price_usd || 0);
    }
    const rows = Object.entries(byProduct).map(([code, v]) => ({
      code, name: PRODUCT_LABEL[code] || code, ...v,
    }));
    const total = rows.reduce((s, r) => s + r.mrr, 0) || 1;
    return rows
      .map((r) => ({ ...r, pct: Math.round((r.mrr / total) * 1000) / 10 }))
      .sort((a, b) => b.mrr - a.mrr);
  }, [activeTenants, subByTenant]);

  const recentSignups = useMemo(
    () =>
      [...tenants]
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 6),
    [tenants],
  );

  const METRICS = [
    { label: "MRR", value: `$${mrr.toLocaleString()}`, icon: DollarSign, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    { label: "ARR", value: `$${(mrr * 12).toLocaleString()}`, icon: TrendingUp, color: "text-blue-400", bg: "bg-blue-500/10" },
    { label: "Active Customers", value: String(activeTenants.length), icon: Users, color: "text-cy-orange", bg: "bg-cy-orange/10" },
    { label: "Pending Invoices", value: `$${pendingAmount.toLocaleString()}`, icon: Receipt, color: "text-violet-400", bg: "bg-violet-500/10" },
  ];

  return (
    <div>
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-heading font-semibold text-white mb-1">Revenue Dashboard</h1>
          <p className="text-sm text-cy-gray-400">CyberCom SaaS business overview</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-cy-gray-400">
          <Calendar className="w-3.5 h-3.5" />
          {tenants.length} total tenants
        </div>
      </div>

      {error && (
        <div className="mb-4 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-5 h-5 text-cy-orange animate-spin" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {METRICS.map(({ label, value, icon: Icon, color, bg }) => (
              <div key={label} className="glass-card p-5 rounded-xl">
                <div className={`w-8 h-8 ${bg} rounded-lg flex items-center justify-center mb-3`}>
                  <Icon className={`w-4 h-4 ${color}`} />
                </div>
                <div className="text-xl font-heading font-bold text-white">{value}</div>
                <div className="text-xs text-cy-gray-400 mt-0.5">{label}</div>
              </div>
            ))}
          </div>

          <div className="grid lg:grid-cols-3 gap-6 mb-6">
            {/* Product mix */}
            <div className="lg:col-span-2 glass-card rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-cy-glass-border">
                <h2 className="font-heading font-semibold text-white">Revenue by Product</h2>
                <Link href="/en/admin/subscriptions" className="text-xs text-cy-orange hover:text-cy-orange-light">All subscriptions →</Link>
              </div>
              {productMix.length === 0 ? (
                <div className="px-5 py-8 text-center text-sm text-cy-gray-400">No active revenue yet.</div>
              ) : (
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
                      {productMix.map((p) => (
                        <tr key={p.code} className="border-b border-cy-glass-border/50 hover:bg-cy-glass-border/20 transition-colors">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded bg-cy-orange/10 flex items-center justify-center">
                                <BarChart3 className="w-3.5 h-3.5 text-cy-orange" />
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
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Recent signups */}
            <div className="glass-card rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-cy-glass-border">
                <h2 className="font-heading font-semibold text-white">Recent Signups</h2>
                <Link href="/en/admin/customers" className="text-xs text-cy-orange hover:text-cy-orange-light">All →</Link>
              </div>
              <div className="divide-y divide-cy-glass-border/50">
                {recentSignups.length === 0 && (
                  <div className="px-4 py-8 text-center text-sm text-cy-gray-400">No signups yet.</div>
                )}
                {recentSignups.map((t) => {
                  const sub = subByTenant[t.id];
                  const mrrVal = Number(sub?.monthly_price_usd || 0);
                  return (
                    <div key={t.id} className="px-4 py-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="text-xs font-medium text-white truncate">{t.display_name || t.name}</div>
                          <div className="text-xs text-cy-gray-400 mt-0.5 truncate">
                            {PRODUCT_LABEL[productCodeOf(t)] || productCodeOf(t)} · {sub?.plan || t.tier}
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0">
                          {mrrVal > 0
                            ? <div className="text-xs font-semibold text-emerald-400">${mrrVal}/mo</div>
                            : <div className="text-xs text-cy-orange">Trial</div>}
                          <div className="text-xs text-cy-gray-500 mt-0.5">{t.country_code || "—"}</div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Quick actions */}
          <div className="grid sm:grid-cols-3 gap-4 mt-6">
            {[
              { label: "View all customers", href: "/en/admin/customers", icon: UserCheck },
              { label: `Approve invoices (${pendingInvoices.length} pending)`, href: "/en/admin/invoices", icon: Receipt },
              { label: "Manage subscriptions", href: "/en/admin/subscriptions", icon: ShoppingBag },
            ].map(({ label, href, icon: Icon }) => (
              <Link key={href} href={href} className="glass-card p-4 rounded-xl flex items-center gap-3 hover:border-cy-orange/30 border border-cy-glass-border transition-colors">
                <Icon className="w-5 h-5 text-cy-orange" />
                <span className="text-sm font-medium text-white">{label}</span>
                <ArrowUpRight className="w-4 h-4 text-cy-gray-400 ml-auto" />
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
