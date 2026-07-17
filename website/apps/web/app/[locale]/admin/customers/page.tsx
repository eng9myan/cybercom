"use client";

import { useEffect, useState } from "react";
import {
  Search, Filter, CheckCircle2, Clock, AlertCircle, Loader2,
} from "lucide-react";
import { adminApi, type Tenant, type TenantSubscription } from "@/lib/adminApi";

const STATUS_CONFIG: Record<string, { label: string; icon: React.ElementType; className: string }> = {
  active: { label: "Active", icon: CheckCircle2, className: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  trial: { label: "Trial", icon: Clock, className: "text-cy-orange bg-cy-orange/10 border-cy-orange/20" },
  suspended: { label: "Suspended", icon: AlertCircle, className: "text-red-400 bg-red-500/10 border-red-500/20" },
  provisioning: { label: "Provisioning", icon: Clock, className: "text-cy-gray-400 bg-cy-gray-500/10 border-cy-gray-500/20" },
  archived: { label: "Archived", icon: AlertCircle, className: "text-cy-gray-400 bg-cy-gray-500/10 border-cy-gray-500/20" },
};

export default function AdminCustomersPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [subsByTenant, setSubsByTenant] = useState<Record<string, TenantSubscription>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    Promise.all([adminApi.listTenants(), adminApi.listSubscriptions()])
      .then(([tenantRows, subRows]) => {
        setTenants(tenantRows);
        const map: Record<string, TenantSubscription> = {};
        for (const sub of subRows) {
          // most recent subscription per tenant wins (results are newest-first)
          if (!map[sub.tenant]) map[sub.tenant] = sub;
        }
        setSubsByTenant(map);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load customers"))
      .finally(() => setLoading(false));
  }, []);

  function displayStatus(t: Tenant): string {
    const sub = subsByTenant[t.id];
    if (sub?.is_trial && !sub.is_expired) return "trial";
    return t.status;
  }

  const filtered = tenants.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      (t.country_code || "").toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || displayStatus(t) === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalMRR = tenants
    .filter((t) => displayStatus(t) === "active")
    .reduce((sum, t) => sum + Number(subsByTenant[t.id]?.monthly_price_usd || 0), 0);

  return (
    <div>
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-heading font-semibold text-white mb-1">Customers</h1>
          <p className="text-sm text-cy-gray-400">
            {tenants.length} total · ${totalMRR.toLocaleString()}/mo active MRR
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-4 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      <div className="flex gap-3 mb-6 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cy-gray-500" />
          <input
            className="w-full glass-card rounded-lg pl-9 pr-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
            placeholder="Search customers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1 p-1 rounded-lg bg-cy-dark/60 border border-cy-glass-border">
          <Filter className="w-4 h-4 text-cy-gray-500 ml-2" />
          {["all", "active", "trial", "suspended"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all capitalize ${statusFilter === s ? "bg-cy-glass-border text-white" : "text-cy-gray-400 hover:text-white"}`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-5 h-5 text-cy-orange animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-cy-glass-border">
                  {["Customer", "Country", "Tier", "MRR", "Status", "Since"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium text-cy-gray-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => {
                  const status = STATUS_CONFIG[displayStatus(t)] ?? STATUS_CONFIG.provisioning!;
                  const StatusIcon = status.icon;
                  const sub = subsByTenant[t.id];
                  const mrr = Number(sub?.monthly_price_usd || 0);
                  return (
                    <tr key={t.id} className="border-b border-cy-glass-border/50 hover:bg-cy-glass-border/20 transition-colors">
                      <td className="px-4 py-4">
                        <div className="font-medium text-white">{t.display_name || t.name}</div>
                        <div className="text-xs text-cy-gray-400">{t.slug}</div>
                      </td>
                      <td className="px-4 py-4 text-cy-gray-300">{t.country_code || "—"}</td>
                      <td className="px-4 py-4 text-cy-gray-300 capitalize">{t.tier}</td>
                      <td className="px-4 py-4">
                        {mrr > 0
                          ? <span className="font-semibold text-white">${mrr.toLocaleString()}</span>
                          : <span className="text-cy-gray-400 text-xs">{displayStatus(t) === "trial" ? "Trial" : "—"}</span>}
                      </td>
                      <td className="px-4 py-4">
                        <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${status.className}`}>
                          <StatusIcon className="w-3 h-3" />
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-xs text-cy-gray-400">
                        {new Date(t.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {!loading && filtered.length === 0 && (
          <div className="text-center py-12 text-cy-gray-400 text-sm">No customers match your filter.</div>
        )}
      </div>
    </div>
  );
}
