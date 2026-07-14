"use client";

import { useState } from "react";
import {
  Search, CheckCircle2, Clock, AlertCircle, Pause,
  Play, X, ChevronDown, ChevronUp, Calendar,
  Building2, Stethoscope, ShoppingCart, BarChart3, Pill, FlaskConical, Scan,
} from "lucide-react";

const PRODUCT_ICONS: Record<string, React.ElementType> = {
  "CyMed Hospital": Building2,
  "CyMed Clinic": Stethoscope,
  "CyMed Pharmacy": Pill,
  "CyMed Laboratory": FlaskConical,
  "CyMed Imaging": Scan,
  CyShop: ShoppingCart,
  "CyCom ERP": BarChart3,
};
const PRODUCT_COLORS: Record<string, { color: string; bg: string; border: string }> = {
  "CyMed Hospital": { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  "CyMed Clinic": { color: "text-teal-400", bg: "bg-teal-500/10", border: "border-teal-500/20" },
  "CyMed Pharmacy": { color: "text-violet-400", bg: "bg-violet-500/10", border: "border-violet-500/20" },
  "CyMed Laboratory": { color: "text-cyan-400", bg: "bg-cyan-500/10", border: "border-cyan-500/20" },
  "CyMed Imaging": { color: "text-sky-400", bg: "bg-sky-500/10", border: "border-sky-500/20" },
  CyShop: { color: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/20" },
  "CyCom ERP": { color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
};

const SUBSCRIPTIONS = [
  {
    id: "SUB-2025-001", customer: "King Abdullah University Hospital", product: "CyMed Hospital",
    edition: "Hospital Advanced", billing: "annual", status: "active",
    mrr: 4500, seats: 120, usedSeats: 87, start: "2025-01-15", renewal: "2026-01-15",
  },
  {
    id: "SUB-2025-002", customer: "King Abdullah University Hospital", product: "CyCom ERP",
    edition: "Enterprise", billing: "annual", status: "active",
    mrr: 2499, seats: 50, usedSeats: 32, start: "2025-01-15", renewal: "2026-01-15",
  },
  {
    id: "SUB-2025-003", customer: "King Abdullah University Hospital", product: "CyMed Pharmacy",
    edition: "Pharmacy Clinical", billing: "annual", status: "active",
    mrr: 399, seats: 20, usedSeats: 14, start: "2025-01-15", renewal: "2026-01-15",
  },
  {
    id: "SUB-2026-001", customer: "Al Noor Specialist Clinics", product: "CyMed Clinic",
    edition: "Clinic Professional", billing: "annual", status: "active",
    mrr: 599, seats: 15, usedSeats: 9, start: "2026-03-20", renewal: "2027-03-20",
  },
  {
    id: "SUB-2026-002", customer: "Al Noor Specialist Clinics", product: "CyCom ERP",
    edition: "Business", billing: "annual", status: "active",
    mrr: 999, seats: 30, usedSeats: 18, start: "2026-03-20", renewal: "2027-03-20",
  },
  {
    id: "SUB-2026-003", customer: "Riyadh Digital Health Initiative", product: "CyMed Hospital",
    edition: "Hospital Enterprise", billing: "trial", status: "trial",
    mrr: 0, seats: 50, usedSeats: 3, start: "2026-07-01", renewal: "2026-07-15",
  },
  {
    id: "SUB-2025-004", customer: "Jordan Medical Laboratory", product: "CyMed Laboratory",
    edition: "Lab Full", billing: "annual", status: "active",
    mrr: 549, seats: 10, usedSeats: 8, start: "2025-09-22", renewal: "2026-09-22",
  },
];

const STATUS_CONFIG: Record<string, { label: string; icon: React.ElementType; className: string }> = {
  active: { label: "Active", icon: CheckCircle2, className: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  trial: { label: "Trial", icon: Clock, className: "text-cy-orange bg-cy-orange/10 border-cy-orange/20" },
  suspended: { label: "Suspended", icon: Pause, className: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
  cancelled: { label: "Cancelled", icon: X, className: "text-red-400 bg-red-500/10 border-red-500/20" },
};

export default function AdminSubscriptionsPage() {
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = SUBSCRIPTIONS.filter((s) =>
    s.customer.toLowerCase().includes(search.toLowerCase()) ||
    s.product.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-semibold text-white mb-1">Subscriptions</h1>
        <p className="text-sm text-cy-gray-400">{SUBSCRIPTIONS.length} subscriptions · {SUBSCRIPTIONS.filter((s) => s.status === "active").length} active</p>
      </div>

      {/* Search */}
      <div className="relative mb-6 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cy-gray-500" />
        <input
          className="w-full glass-card rounded-lg pl-9 pr-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
          placeholder="Search by customer or product..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Table */}
      <div className="space-y-2">
        {filtered.map((sub) => {
          const Icon = PRODUCT_ICONS[sub.product] ?? Building2;
          const pColors = PRODUCT_COLORS[sub.product] ?? { color: "text-white", bg: "bg-cy-glass-border", border: "border-cy-glass-border" };
          const status = STATUS_CONFIG[sub.status] ?? STATUS_CONFIG.active!;
          const StatusIcon = status.icon;
          const expanded = expandedId === sub.id;
          const usagePct = sub.seats > 0 ? Math.round((sub.usedSeats / sub.seats) * 100) : 0;

          return (
            <div key={sub.id} className="glass-card rounded-xl overflow-hidden">
              <button
                onClick={() => setExpandedId(expanded ? null : sub.id)}
                className="w-full text-left p-4 flex items-center gap-4"
              >
                <div className={`w-9 h-9 rounded-lg ${pColors.bg} border ${pColors.border} flex items-center justify-center flex-shrink-0`}>
                  <Icon className={`w-4 h-4 ${pColors.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">{sub.customer}</div>
                  <div className="text-xs text-cy-gray-400">{sub.product} — {sub.edition}</div>
                </div>
                <div className="hidden sm:flex items-center gap-4 flex-shrink-0">
                  <span className={`inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full border ${status.className}`}>
                    <StatusIcon className="w-3 h-3" />
                    {status.label}
                  </span>
                  <div className="text-right">
                    {sub.mrr > 0
                      ? <div className="text-sm font-semibold text-white">${sub.mrr.toLocaleString()}/mo</div>
                      : <div className="text-xs text-cy-orange">Trial</div>}
                  </div>
                </div>
                {expanded ? <ChevronUp className="w-4 h-4 text-cy-gray-400 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-cy-gray-400 flex-shrink-0" />}
              </button>

              {expanded && (
                <div className="border-t border-cy-glass-border p-4 space-y-4">
                  <div className="grid sm:grid-cols-3 gap-4">
                    <div>
                      <div className="text-xs text-cy-gray-400 mb-1">Subscription ID</div>
                      <div className="text-sm font-mono text-white">{sub.id}</div>
                    </div>
                    <div>
                      <div className="text-xs text-cy-gray-400 mb-1">Billing</div>
                      <div className="text-sm text-white capitalize">{sub.billing}</div>
                    </div>
                    <div>
                      <div className="text-xs text-cy-gray-400 mb-1">Renewal</div>
                      <div className="flex items-center gap-1.5 text-sm text-white">
                        <Calendar className="w-3.5 h-3.5 text-cy-gray-400" />
                        {new Date(sub.renewal).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5 text-xs text-cy-gray-400">
                      <span>Seat Usage</span>
                      <span>{sub.usedSeats}/{sub.seats}</span>
                    </div>
                    <div className="h-2 bg-cy-glass-border rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${usagePct > 85 ? "bg-amber-400" : "bg-emerald-500"}`}
                        style={{ width: `${usagePct}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 pt-1">
                    {sub.status === "active" && (
                      <>
                        <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-white bg-blue-500/20 border border-blue-500/20 hover:bg-blue-500/30 transition-colors">
                          Change Edition
                        </button>
                        <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-cy-gray-300 border border-cy-glass-border hover:border-cy-glass-bg-hover transition-colors">
                          <Pause className="w-3 h-3" /> Suspend
                        </button>
                        <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-red-400 border border-red-500/20 hover:bg-red-500/10 transition-colors ml-auto">
                          <X className="w-3 h-3" /> Cancel
                        </button>
                      </>
                    )}
                    {sub.status === "trial" && (
                      <>
                        <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-white bg-emerald-500/20 border border-emerald-500/20 hover:bg-emerald-500/30 transition-colors">
                          <Play className="w-3 h-3" /> Convert to Paid
                        </button>
                        <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-cy-gray-300 border border-cy-glass-border hover:border-cy-glass-bg-hover transition-colors">
                          Extend Trial
                        </button>
                      </>
                    )}
                    {sub.status === "suspended" && (
                      <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/10 transition-colors">
                        <Play className="w-3 h-3" /> Reactivate
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {filtered.length === 0 && (
          <div className="text-center py-12 text-cy-gray-400 text-sm">No subscriptions match your search.</div>
        )}
      </div>
    </div>
  );
}
