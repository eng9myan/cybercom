"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Plus, RefreshCw, Truck, X, CheckCircle2, AlertTriangle,
  PackageCheck, PackageX, Send, Inbox,
} from "lucide-react";
import { api } from "@/lib/api";

const STATUS_INFO = {
  DRAFT: { label: "Draft", color: "#8A8A8A" },
  IN_TRANSIT: { label: "In Transit", color: "#ED6C00" },
  COMPLETED: { label: "Completed", color: "#16A34A" },
  CANCELLED: { label: "Cancelled", color: "#DC2626" },
};

const EMPTY_FORM = {
  from_branch: "", to_branch: "", from_location: "", to_location: "",
  product: "", variant: "", quantity: "1", notes: "",
};

function Toast({ msg, ok, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3500); return () => clearTimeout(t); }, [onDone]);
  return (
    <div className={`fixed bottom-6 right-6 z-[200] flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl text-white text-sm font-medium ${ok ? "bg-[#16A34A]" : "bg-[#DC2626]"}`}>
      {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
      {msg}
    </div>
  );
}

function TransferModal({ products, branches, locations, onSave, onClose }) {
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (form.from_location === form.to_location) {
      onSave(null, "Source and destination locations must differ.");
      return;
    }
    setSaving(true);
    const payload = {
      ...form,
      variant: form.variant || null,
    };
    try {
      await api.post("/api/v1/inventory/transfers/", payload);
      onSave("Transfer created as draft. Dispatch it when goods leave the source branch.");
    } catch (err) {
      onSave(null, err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg flex items-center gap-2">
            <Truck className="w-5 h-5 text-[#0E7C9B]" /> New Inter-Branch Transfer
          </h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          <div>
            <label className="cy-label">Product *</label>
            <select required className="cy-input" value={form.product} onChange={(e) => set("product", e.target.value)}>
              <option value="">— select product —</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.name} {p.internal_ref ? `(${p.internal_ref})` : ""}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="cy-label">From Branch *</label>
              <select required className="cy-input" value={form.from_branch} onChange={(e) => set("from_branch", e.target.value)}>
                <option value="">— select branch —</option>
                {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">To Branch *</label>
              <select required className="cy-input" value={form.to_branch} onChange={(e) => set("to_branch", e.target.value)}>
                <option value="">— select branch —</option>
                {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">From Location *</label>
              <select required className="cy-input" value={form.from_location} onChange={(e) => set("from_location", e.target.value)}>
                <option value="">— select location —</option>
                {locations.map((l) => <option key={l.id} value={l.id}>{l.warehouse_name} / {l.code}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">To Location *</label>
              <select required className="cy-input" value={form.to_location} onChange={(e) => set("to_location", e.target.value)}>
                <option value="">— select location —</option>
                {locations.map((l) => <option key={l.id} value={l.id}>{l.warehouse_name} / {l.code}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">Quantity *</label>
              <input required type="number" step="0.0001" min="0.0001" className="cy-input" value={form.quantity} onChange={(e) => set("quantity", e.target.value)} />
            </div>
            <div className="col-span-2">
              <label className="cy-label">Notes</label>
              <textarea rows={2} className="cy-input" value={form.notes} onChange={(e) => set("notes", e.target.value)} />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="cy-btn cy-btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="cy-btn cy-btn-primary">
              {saving ? "Creating…" : "Create Transfer"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function StockTransfersPage() {
  const [transfers, setTransfers] = useState([]);
  const [products, setProducts] = useState([]);
  const [branches, setBranches] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [modal, setModal] = useState(false);
  const [toast, setToast] = useState(null);
  const [statusFilter, setStatusFilter] = useState("ALL");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [trs, prods, brs, locs] = await Promise.all([
        api.get("/api/v1/inventory/transfers/"),
        api.get("/api/v1/catalog/products/"),
        api.get("/api/v1/tenants/branches/"),
        api.get("/api/v1/inventory/locations/"),
      ]);
      setTransfers(Array.isArray(trs) ? trs : trs.results || []);
      setProducts(Array.isArray(prods) ? prods : prods.results || []);
      setBranches(Array.isArray(brs) ? brs : brs.results || []);
      setLocations(Array.isArray(locs) ? locs : locs.results || []);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = (ok, err) => {
    if (ok) { setModal(false); setToast({ msg: ok, ok: true }); load(); }
    else setToast({ msg: err, ok: false });
  };

  const runAction = async (id, action, successMsg) => {
    setBusyId(id);
    try {
      await api.post(`/api/v1/inventory/transfers/${id}/${action}/`, {});
      setToast({ msg: successMsg, ok: true });
      load();
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally {
      setBusyId(null);
    }
  };

  const filtered = statusFilter === "ALL" ? transfers : transfers.filter((t) => t.status === statusFilter);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading font-bold text-2xl">Inter-Branch Transfers</h2>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">
            {transfers.length} transfers · dispatch debits the source, receive credits the destination
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setModal(true)} className="cy-btn cy-btn-primary">
            <Plus className="w-4 h-4" /> New Transfer
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {["ALL", ...Object.keys(STATUS_INFO)].map((v) => {
          const info = v === "ALL" ? { label: "All", color: "#8A8A8A" } : STATUS_INFO[v];
          return (
            <button
              key={v}
              onClick={() => setStatusFilter(v)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors border ${
                statusFilter === v
                  ? "bg-[var(--color-brand-ink)] text-white border-transparent"
                  : "bg-white border-[var(--color-line)] text-[var(--color-ink-soft)] hover:border-[var(--color-ink)]"
              }`}
            >
              {info.label}
            </button>
          );
        })}
      </div>

      <div className="cy-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-surface)]">
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Transfer #</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Product</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden md:table-cell">Branch → Branch</th>
                <th className="text-right px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Qty</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Status</th>
                <th className="text-right px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-line)]">
              {loading ? (
                <tr><td colSpan={6} className="text-center py-16 text-[var(--color-ink-muted)]">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-16">
                    <Truck className="w-10 h-10 mx-auto mb-3 text-[var(--color-ink-muted)] opacity-40" />
                    <p className="text-[var(--color-ink-muted)]">No transfers yet.</p>
                    <button onClick={() => setModal(true)} className="mt-3 cy-btn cy-btn-primary !py-2 !text-xs">
                      <Plus className="w-3.5 h-3.5" /> Create first transfer
                    </button>
                  </td>
                </tr>
              ) : filtered.map((t) => {
                const info = STATUS_INFO[t.status] || { label: t.status, color: "#8A8A8A" };
                return (
                  <tr key={t.id} className="hover:bg-[var(--color-surface)] transition-colors">
                    <td className="px-4 py-3 font-mono text-xs font-semibold">{t.transfer_number}</td>
                    <td className="px-4 py-3 font-semibold">{t.product_name}</td>
                    <td className="px-4 py-3 text-xs text-[var(--color-ink-muted)] hidden md:table-cell">
                      {t.from_branch_name} → {t.to_branch_name}
                    </td>
                    <td className="px-4 py-3 text-right font-bold tabular-nums">{parseFloat(t.quantity).toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: `${info.color}18`, color: info.color }}>
                        {info.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {t.status === "DRAFT" && (
                        <button
                          disabled={busyId === t.id}
                          onClick={() => runAction(t.id, "dispatch", `Transfer ${t.transfer_number} dispatched.`)}
                          className="cy-btn cy-btn-ghost !py-1.5 !text-xs"
                        >
                          <Send className="w-3.5 h-3.5" /> Dispatch
                        </button>
                      )}
                      {t.status === "IN_TRANSIT" && (
                        <button
                          disabled={busyId === t.id}
                          onClick={() => runAction(t.id, "receive", `Transfer ${t.transfer_number} received.`)}
                          className="cy-btn cy-btn-primary !py-1.5 !text-xs"
                        >
                          <Inbox className="w-3.5 h-3.5" /> Receive
                        </button>
                      )}
                      {t.status === "COMPLETED" && (
                        <span className="inline-flex items-center gap-1 text-xs text-[#16A34A]"><PackageCheck className="w-3.5 h-3.5" /> Done</span>
                      )}
                      {t.status === "CANCELLED" && (
                        <span className="inline-flex items-center gap-1 text-xs text-[#DC2626]"><PackageX className="w-3.5 h-3.5" /> Cancelled</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {modal && (
        <TransferModal
          products={products}
          branches={branches}
          locations={locations}
          onSave={handleSave}
          onClose={() => setModal(false)}
        />
      )}
      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
