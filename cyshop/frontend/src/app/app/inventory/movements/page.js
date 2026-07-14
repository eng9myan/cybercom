"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Plus, RefreshCw, ArrowDown, ArrowUp, ArrowLeftRight, Sliders,
  X, CheckCircle2, AlertTriangle, ClipboardList,
} from "lucide-react";
import { api } from "@/lib/api";

const MOVEMENT_TYPES = [
  { value: "RECEIPT", label: "Vendor Receipt", icon: ArrowDown, color: "#16A34A" },
  { value: "ISSUE", label: "Issue / Sale", icon: ArrowUp, color: "#ED6C00" },
  { value: "TRANSFER", label: "Internal Transfer", icon: ArrowLeftRight, color: "#0E7C9B" },
  { value: "ADJUSTMENT", label: "Manual Adjustment", icon: Sliders, color: "#9333EA" },
  { value: "OPENING", label: "Opening Balance", icon: ArrowDown, color: "#16A34A" },
  { value: "RETURN_IN", label: "Customer Return", icon: ArrowDown, color: "#16A34A" },
];

const EMPTY_FORM = {
  product: "", variant: "", from_location: "", to_location: "",
  quantity: "1", unit_cost: "0.0000", movement_type: "RECEIPT",
  reference: "", notes: "", warehouse: "",
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

function MovementModal({ products, locations, warehouses, onSave, onClose }) {
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const selectedType = MOVEMENT_TYPES.find((t) => t.value === form.movement_type) || MOVEMENT_TYPES[0];
  const needsFrom = ["ISSUE", "TRANSFER", "RETURN_OUT", "PRODUCTION_OUT"].includes(form.movement_type);
  const needsTo = ["RECEIPT", "TRANSFER", "RETURN_IN", "PRODUCTION_IN", "OPENING", "ADJUSTMENT"].includes(form.movement_type);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = {
      ...form,
      from_location: form.from_location || null,
      to_location: form.to_location || null,
      variant: form.variant || null,
      warehouse: form.warehouse || null,
    };
    try {
      await api.post("/api/v1/inventory/movements/", payload);
      onSave("Stock movement posted successfully.");
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
            <selectedType.icon className="w-5 h-5" style={{ color: selectedType.color }} />
            Post Stock Movement
          </h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          <div>
            <label className="cy-label">Movement Type *</label>
            <select required className="cy-input" value={form.movement_type} onChange={(e) => set("movement_type", e.target.value)}>
              {MOVEMENT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="cy-label">Product *</label>
              <select required className="cy-input" value={form.product} onChange={(e) => set("product", e.target.value)}>
                <option value="">— select product —</option>
                {products.map((p) => <option key={p.id} value={p.id}>{p.name} {p.internal_ref ? `(${p.internal_ref})` : ""}</option>)}
              </select>
            </div>

            {needsFrom && (
              <div>
                <label className="cy-label">From Location *</label>
                <select required={needsFrom && !needsTo} className="cy-input" value={form.from_location} onChange={(e) => set("from_location", e.target.value)}>
                  <option value="">— select location —</option>
                  {locations.map((l) => <option key={l.id} value={l.id}>{l.warehouse_name} / {l.code}</option>)}
                </select>
              </div>
            )}

            {needsTo && (
              <div>
                <label className="cy-label">To Location *</label>
                <select required={needsTo && !needsFrom} className="cy-input" value={form.to_location} onChange={(e) => set("to_location", e.target.value)}>
                  <option value="">— select location —</option>
                  {locations.map((l) => <option key={l.id} value={l.id}>{l.warehouse_name} / {l.code}</option>)}
                </select>
              </div>
            )}

            {!needsFrom && !needsTo && (
              <div className="col-span-2 text-sm text-[var(--color-ink-muted)] rounded-lg bg-[var(--color-surface-2)] p-3">
                Select at least one of From / To Location based on movement type.
              </div>
            )}

            <div>
              <label className="cy-label">Quantity *</label>
              <input required type="number" step="0.0001" min="0.0001" className="cy-input" value={form.quantity} onChange={(e) => set("quantity", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Unit Cost</label>
              <input type="number" step="0.0001" min="0" className="cy-input" value={form.unit_cost} onChange={(e) => set("unit_cost", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Reference (PO/SO/INV)</label>
              <input className="cy-input" value={form.reference} onChange={(e) => set("reference", e.target.value)} placeholder="PO-2026-001" />
            </div>
            <div>
              <label className="cy-label">Warehouse</label>
              <select className="cy-input" value={form.warehouse} onChange={(e) => set("warehouse", e.target.value)}>
                <option value="">— optional —</option>
                {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
              </select>
            </div>
            <div className="col-span-2">
              <label className="cy-label">Notes</label>
              <textarea rows={2} className="cy-input" value={form.notes} onChange={(e) => set("notes", e.target.value)} />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="cy-btn cy-btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="cy-btn cy-btn-primary">
              {saving ? "Posting…" : "Post Movement"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function typeInfo(type) {
  return MOVEMENT_TYPES.find((t) => t.value === type) || { label: type, icon: Sliders, color: "#8A8A8A" };
}

export default function StockMovementsPage() {
  const [movements, setMovements] = useState([]);
  const [products, setProducts] = useState([]);
  const [locations, setLocations] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [toast, setToast] = useState(null);
  const [typeFilter, setTypeFilter] = useState("ALL");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [mvs, prods, locs, whs] = await Promise.all([
        api.get("/api/v1/inventory/movements/"),
        api.get("/api/v1/catalog/products/"),
        api.get("/api/v1/inventory/locations/"),
        api.get("/api/v1/inventory/warehouses/"),
      ]);
      setMovements(Array.isArray(mvs) ? mvs : mvs.results || []);
      setProducts(Array.isArray(prods) ? prods : prods.results || []);
      setLocations(Array.isArray(locs) ? locs : locs.results || []);
      setWarehouses(Array.isArray(whs) ? whs : whs.results || []);
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

  const filtered = typeFilter === "ALL" ? movements : movements.filter((m) => m.movement_type === typeFilter);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading font-bold text-2xl">Stock Movements</h2>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">
            {movements.length} movements · immutable ledger
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setModal(true)} className="cy-btn cy-btn-primary">
            <Plus className="w-4 h-4" /> Post Movement
          </button>
        </div>
      </div>

      {/* Type filter pills */}
      <div className="flex flex-wrap gap-2">
        {["ALL", ...MOVEMENT_TYPES.map((t) => t.value)].map((v) => {
          const info = v === "ALL" ? { label: "All", color: "#8A8A8A" } : typeInfo(v);
          return (
            <button
              key={v}
              onClick={() => setTypeFilter(v)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors border ${
                typeFilter === v
                  ? "bg-[var(--color-brand-ink)] text-white border-transparent"
                  : "bg-white border-[var(--color-line)] text-[var(--color-ink-soft)] hover:border-[var(--color-ink)]"
              }`}
            >
              {info.label}
            </button>
          );
        })}
      </div>

      {/* Movements table */}
      <div className="cy-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-surface)]">
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Type</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Product</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden md:table-cell">From → To</th>
                <th className="text-right px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Qty</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden lg:table-cell">Reference</th>
                <th className="text-right px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden sm:table-cell">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-line)]">
              {loading ? (
                <tr><td colSpan={6} className="text-center py-16 text-[var(--color-ink-muted)]">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-16">
                    <ClipboardList className="w-10 h-10 mx-auto mb-3 text-[var(--color-ink-muted)] opacity-40" />
                    <p className="text-[var(--color-ink-muted)]">No movements yet.</p>
                    <button onClick={() => setModal(true)} className="mt-3 cy-btn cy-btn-primary !py-2 !text-xs">
                      <Plus className="w-3.5 h-3.5" /> Post first movement
                    </button>
                  </td>
                </tr>
              ) : filtered.map((mv) => {
                const info = typeInfo(mv.movement_type);
                const Icon = info.icon;
                return (
                  <tr key={mv.id} className="hover:bg-[var(--color-surface)] transition-colors">
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: `${info.color}18`, color: info.color }}>
                        <Icon className="w-3 h-3" /> {info.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-semibold">{mv.product_name}</td>
                    <td className="px-4 py-3 text-xs text-[var(--color-ink-muted)] font-mono hidden md:table-cell">
                      {mv.from_location_code || "—"} → {mv.to_location_code || "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-bold tabular-nums">{parseFloat(mv.quantity).toFixed(2)}</td>
                    <td className="px-4 py-3 text-[var(--color-ink-muted)] hidden lg:table-cell">{mv.reference || "—"}</td>
                    <td className="px-4 py-3 text-right text-xs text-[var(--color-ink-muted)] hidden sm:table-cell">
                      {mv.created_at ? new Date(mv.created_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {modal && (
        <MovementModal
          products={products}
          locations={locations}
          warehouses={warehouses}
          onSave={handleSave}
          onClose={() => setModal(false)}
        />
      )}
      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
