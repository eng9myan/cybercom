"use client";

import { useEffect, useState } from "react";
import { Search, CheckCircle2, Clock, AlertCircle, Loader2, Calendar } from "lucide-react";
import { adminApi, type Tenant, type TenantSubscription } from "@/lib/adminApi";

const STATUS_CONFIG: Record<string, { label: string; icon: React.ElementType; className: string }> = {
  active: { label: "Active", icon: CheckCircle2, className: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  trial: { label: "Trial", icon: Clock, className: "text-cy-orange bg-cy-orange/10 border-cy-orange/20" },
  expired: { label: "Expired", icon: AlertCircle, className: "text-red-400 bg-red-500/10 border-red-500/20" },
  inactive: { label: "Inactive", icon: AlertCircle, className: "text-cy-gray-400 bg-cy-gray-500/10 border-cy-gray-500/20" },
};

function subStatus(s: TenantSubscription): string {
  if (s.is_expired) return "expired";
  if (s.is_trial) return "trial";
  if (s.is_active) return "active";
  return "inactive";
}

export default function AdminSubscriptionsPage() {
  const [subs, setSubs] = useState<TenantSubscription[]>([]);
  const [tenantsById, setTenantsById] = useState<Record<string, Tenant>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    Promise.all([adminApi.listSubscriptions(), adminApi.listTenants()])
      .then(([subRows, tenantRows]) => {
        setSubs(subRows);
        setTenantsById(Object.fromEntries(tenantRows.map((t) => [t.id, t])));
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load subscriptions"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = subs.filter((s) => {
    const tenantName = tenantsById[s.tenant]?.display_name || tenantsById[s.tenant]?.name || "";
    return (
      tenantName.toLowerCase().includes(search.toLowerCase()) ||
      s.plan.toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-semibold text-white mb-1">Subscriptions</h1>
        <p className="text-sm text-cy-gray-400">
          {subs.length} subscriptions · {subs.filter((s) => subStatus(s) === "active").length} active
        </p>
      </div>

      {error && (
        <div className="mb-4 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      <div className="relative mb-6 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cy-gray-500" />
        <input
          className="w-full glass-card rounded-lg pl-9 pr-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
          placeholder="Search by customer or plan..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-5 h-5 text-cy-orange animate-spin" />
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((sub) => {
            const status = STATUS_CONFIG[subStatus(sub)] ?? STATUS_CONFIG.inactive!;
            const StatusIcon = status.icon;
            const tenant = tenantsById[sub.tenant];
            const mrr = Number(sub.monthly_price_usd || 0);
            return (
              <div key={sub.id} className="glass-card rounded-xl p-4 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">
                    {tenant?.display_name || tenant?.name || sub.tenant}
                  </div>
                  <div className="text-xs text-cy-gray-400 capitalize">{sub.plan} plan</div>
                </div>
                <div className="hidden sm:flex items-center gap-1.5 text-xs text-cy-gray-400">
                  <Calendar className="w-3.5 h-3.5" />
                  {sub.ends_at
                    ? new Date(sub.ends_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })
                    : "—"}
                </div>
                <span className={`inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full border shrink-0 ${status.className}`}>
                  <StatusIcon className="w-3 h-3" />
                  {status.label}
                </span>
                <div className="text-right w-20 shrink-0">
                  {mrr > 0
                    ? <div className="text-sm font-semibold text-white">${mrr.toLocaleString()}/mo</div>
                    : <div className="text-xs text-cy-orange">Trial</div>}
                </div>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="text-center py-12 text-cy-gray-400 text-sm">No subscriptions match your search.</div>
          )}
        </div>
      )}
    </div>
  );
}
