"use client";

import { useEffect, useState } from "react";
import { Search, CheckCircle2, Clock, XCircle, Loader2, CalendarClock } from "lucide-react";
import { adminApi, type TenantSubscriptionInvoice } from "@/lib/adminApi";

const STATUS_CONFIG: Record<string, { label: string; icon: React.ElementType; className: string }> = {
  pending: { label: "Pending", icon: Clock, className: "text-cy-orange bg-cy-orange/10 border-cy-orange/20" },
  paid: { label: "Paid", icon: CheckCircle2, className: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  void: { label: "Void", icon: XCircle, className: "text-cy-gray-400 bg-cy-gray-500/10 border-cy-gray-500/20" },
};

export default function AdminInvoicesPage() {
  const [invoices, setInvoices] = useState<TenantSubscriptionInvoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("pending");
  const [actingId, setActingId] = useState<string | null>(null);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    return adminApi
      .listInvoices()
      .then(setInvoices)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load invoices"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function markPaid(inv: TenantSubscriptionInvoice) {
    setConfirmingId(null);
    setActingId(inv.id);
    try {
      await adminApi.markInvoicePaid(inv.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to mark invoice paid");
    } finally {
      setActingId(null);
    }
  }

  const filtered = invoices.filter((inv) => {
    const matchesSearch =
      inv.tenant_name.toLowerCase().includes(search.toLowerCase()) ||
      inv.invoice_number.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || inv.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const pendingCount = invoices.filter((i) => i.status === "pending").length;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-semibold text-white mb-1">Invoices</h1>
        <p className="text-sm text-cy-gray-400">
          {invoices.length} total · {pendingCount} awaiting approval
        </p>
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
            placeholder="Search by customer or invoice number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1 p-1 rounded-lg bg-cy-dark/60 border border-cy-glass-border">
          {["pending", "paid", "void", "all"].map((s) => (
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

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-5 h-5 text-cy-orange animate-spin" />
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((inv) => {
            const status = STATUS_CONFIG[inv.status] ?? STATUS_CONFIG.pending!;
            const StatusIcon = status.icon;
            return (
              <div key={inv.id} className="glass-card rounded-xl p-4 flex items-center gap-4 flex-wrap">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">{inv.tenant_name}</div>
                  <div className="text-xs text-cy-gray-400 font-mono">{inv.invoice_number}</div>
                </div>
                <div className="hidden sm:flex items-center gap-1.5 text-xs text-cy-gray-400">
                  <CalendarClock className="w-3.5 h-3.5" />
                  Due {new Date(inv.due_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                </div>
                <div className="text-xs text-cy-gray-400 capitalize">{inv.payment_method.replace("_", " ")}</div>
                <span className={`inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full border shrink-0 ${status.className}`}>
                  <StatusIcon className="w-3 h-3" />
                  {status.label}
                </span>
                <div className="text-right w-24 shrink-0">
                  <div className="text-sm font-semibold text-white">{inv.amount} {inv.currency}</div>
                </div>
                {inv.status === "pending" && confirmingId === inv.id ? (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-cy-gray-400">Confirm paid?</span>
                    <button
                      onClick={() => markPaid(inv)}
                      disabled={actingId === inv.id}
                      className="btn-primary text-xs py-2 px-3 disabled:opacity-50 inline-flex items-center gap-1.5"
                    >
                      {actingId === inv.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                      Yes
                    </button>
                    <button
                      onClick={() => setConfirmingId(null)}
                      disabled={actingId === inv.id}
                      className="text-xs py-2 px-3 rounded-lg border border-cy-glass-border text-cy-gray-300 hover:bg-cy-glass-border/50 disabled:opacity-50"
                    >
                      Cancel
                    </button>
                  </div>
                ) : inv.status === "pending" ? (
                  <button
                    onClick={() => setConfirmingId(inv.id)}
                    className="btn-primary text-xs py-2 px-3 inline-flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Mark Paid
                  </button>
                ) : (
                  <div className="text-xs text-cy-gray-500 w-24 text-right">{inv.approved_by || "—"}</div>
                )}
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="text-center py-12 text-cy-gray-400 text-sm">No invoices match your filter.</div>
          )}
        </div>
      )}
    </div>
  );
}
