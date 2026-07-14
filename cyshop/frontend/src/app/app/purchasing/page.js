"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Plus, Search, RefreshCw, X, Eye, ChevronRight,
  CheckCircle2, AlertTriangle, Package, Trash2, ShoppingCart,
} from "lucide-react";
import { api } from "@/lib/api";

const STATUS_COLORS = {
  DRAFT: "bg-gray-100 text-gray-700 border-gray-200",
  CONFIRMED: "bg-blue-50 text-blue-700 border-blue-200",
  PARTIAL: "bg-amber-50 text-amber-700 border-amber-200",
  RECEIVED: "bg-green-50 text-green-700 border-green-200",
  CANCELLED: "bg-red-50 text-red-700 border-red-200",
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

function CreatePoModal({ vendors, companies, products, onSave, onClose }) {
  const [form, setForm] = useState({
    vendor: "", company: "", currency: "USD",
    order_date: new Date().toISOString().slice(0, 10),
    expected_date: "", notes: "",
  });
  const [lines, setLines] = useState([{ product: "", quantity: "1", unit_cost: "" }]);
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const setLine = (i, k, v) => setLines(prev => prev.map((l, idx) => idx === i ? { ...l, [k]: v } : l));
  const addLine = () => setLines(prev => [...prev, { product: "", quantity: "1", unit_cost: "" }]);
  const removeLine = (i) => setLines(prev => prev.filter((_, idx) => idx !== i));

  const handleProductChange = (i, pid) => {
    const p = products.find(x => String(x.id) === pid);
    setLines(prev => prev.map((l, idx) =>
      idx === i ? { ...l, product: pid, unit_cost: p ? String(parseFloat(p.cost_price).toFixed(4)) : "" } : l
    ));
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!form.vendor || !form.company) return;
    const validLines = lines.filter(l => l.product && parseFloat(l.quantity) > 0);
    if (validLines.length === 0) { alert("Add at least one product line."); return; }
    setSaving(true);
    try {
      await api.post("/api/v1/purchasing/orders/", {
        ...form,
        lines_input: validLines.map(l => ({
          product: l.product,
          quantity: l.quantity,
          unit_cost: l.unit_cost || undefined,
        })),
      });
      onSave("Purchase order created.");
    } catch (err) {
      onSave(null, err.message);
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg">New Purchase Order</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-5 max-h-[85vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="cy-label">Vendor *</label>
              <select required className="cy-input" value={form.vendor} onChange={e => set("vendor", e.target.value)}>
                <option value="">— select —</option>
                {vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">Company *</label>
              <select required className="cy-input" value={form.company} onChange={e => set("company", e.target.value)}>
                <option value="">— select —</option>
                {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">Order Date</label>
              <input type="date" className="cy-input" value={form.order_date} onChange={e => set("order_date", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Expected Delivery</label>
              <input type="date" className="cy-input" value={form.expected_date} onChange={e => set("expected_date", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Currency</label>
              <select className="cy-input" value={form.currency} onChange={e => set("currency", e.target.value)}>
                {["USD", "JOD", "SAR", "AED", "EUR", "GBP"].map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="col-span-2">
              <label className="cy-label">Notes</label>
              <textarea rows={2} className="cy-input" value={form.notes} onChange={e => set("notes", e.target.value)} />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold">Order Lines</span>
              <button type="button" onClick={addLine} className="cy-btn cy-btn-ghost !py-1 !text-xs">
                <Plus className="w-3.5 h-3.5" /> Add line
              </button>
            </div>
            <div className="space-y-2">
              {lines.map((line, i) => (
                <div key={i} className="grid grid-cols-[1fr_80px_120px_32px] gap-2 items-center">
                  <select
                    className="cy-input !text-sm"
                    value={line.product}
                    onChange={e => handleProductChange(i, e.target.value)}
                  >
                    <option value="">— product —</option>
                    {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                  <input
                    type="number" step="0.001" min="0.001"
                    placeholder="Qty"
                    className="cy-input !text-sm"
                    value={line.quantity}
                    onChange={e => setLine(i, "quantity", e.target.value)}
                  />
                  <input
                    type="number" step="0.0001" min="0"
                    placeholder="Unit cost"
                    className="cy-input !text-sm"
                    value={line.unit_cost}
                    onChange={e => setLine(i, "unit_cost", e.target.value)}
                  />
                  {lines.length > 1 && (
                    <button type="button" onClick={() => removeLine(i)} className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-red-50 hover:text-[#DC2626] text-[var(--color-ink-muted)]">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="cy-btn cy-btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="cy-btn cy-btn-primary">
              {saving ? "Creating…" : "Create PO"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function PoDetailDrawer({ po, onClose, onConfirm, onCancel }) {
  const [confirming, setConfirming] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const confirm = async () => {
    setConfirming(true);
    try { await onConfirm(po.id); } finally { setConfirming(false); }
  };

  const cancel = async () => {
    if (!window.confirm("Cancel this purchase order?")) return;
    setCancelling(true);
    try { await onCancel(po.id); } finally { setCancelling(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-end bg-black/30 backdrop-blur-sm">
      <div className="h-full w-full max-w-lg bg-white shadow-2xl border-l border-[var(--color-line)] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)] sticky top-0 bg-white z-10">
          <div>
            <div className="font-heading font-bold text-lg">{po.po_number}</div>
            <span className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full border ${STATUS_COLORS[po.status] || ""}`}>
              {po.status}
            </span>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4 text-sm">
            {[
              ["Vendor", po.vendor_name],
              ["Currency", po.currency],
              ["Order Date", po.order_date],
              ["Expected", po.expected_date || "—"],
            ].map(([k, v]) => (
              <div key={k}>
                <div className="text-xs text-[var(--color-ink-muted)] mb-0.5">{k}</div>
                <div className="font-semibold">{v}</div>
              </div>
            ))}
          </div>

          {po.lines && po.lines.length > 0 && (
            <div>
              <div className="text-sm font-semibold mb-3">Order Lines</div>
              <div className="space-y-2">
                {po.lines.map(l => (
                  <div key={l.id} className="flex items-center justify-between p-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-line)] text-sm">
                    <div>
                      <div className="font-semibold">{l.product_name}</div>
                      <div className="text-xs text-[var(--color-ink-muted)] mt-0.5">
                        Ordered: {l.quantity} · Received: {l.received_qty} · Outstanding: {l.outstanding_qty}
                      </div>
                    </div>
                    <div className="text-right shrink-0 ml-4">
                      <div className="font-bold">{parseFloat(l.line_subtotal || 0).toFixed(2)}</div>
                      <div className="text-xs text-[var(--color-ink-muted)]">{l.unit_cost} ea</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-line)] text-sm space-y-1">
            <div className="flex justify-between text-[var(--color-ink-muted)]"><span>Subtotal</span><span>{parseFloat(po.subtotal || 0).toFixed(2)}</span></div>
            <div className="flex justify-between text-[var(--color-ink-muted)]"><span>Tax</span><span>{parseFloat(po.tax_amount || 0).toFixed(2)}</span></div>
            <div className="flex justify-between font-bold text-base border-t border-[var(--color-line)] pt-2 mt-1">
              <span>Total ({po.currency})</span><span className="text-[#ED6C00]">{parseFloat(po.total || 0).toFixed(2)}</span>
            </div>
          </div>

          {po.notes && (
            <div className="text-sm text-[var(--color-ink-muted)]">{po.notes}</div>
          )}

          <div className="flex gap-3">
            {po.status === "DRAFT" && (
              <button onClick={confirm} disabled={confirming} className="cy-btn cy-btn-primary flex-1 justify-center">
                {confirming ? "Confirming…" : "Confirm PO"}
              </button>
            )}
            {["DRAFT", "CONFIRMED"].includes(po.status) && (
              <button onClick={cancel} disabled={cancelling} className="cy-btn cy-btn-ghost flex-1 justify-center !text-[#DC2626] hover:!bg-red-50">
                {cancelling ? "Cancelling…" : "Cancel PO"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PurchasingPage() {
  const [orders, setOrders] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [createOpen, setCreateOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [o, v, c, p] = await Promise.all([
        api.get("/api/v1/purchasing/orders/"),
        api.get("/api/v1/purchasing/vendors/"),
        api.get("/api/v1/tenants/companies/"),
        api.get("/api/v1/catalog/products/"),
      ]);
      setOrders(Array.isArray(o) ? o : o.results || []);
      setVendors(Array.isArray(v) ? v : v.results || []);
      setCompanies(Array.isArray(c) ? c : c.results || []);
      setProducts(Array.isArray(p) ? p : p.results || []);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const loadDetail = async (id) => {
    try {
      const po = await api.get(`/api/v1/purchasing/orders/${id}/`);
      setDetail(po);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    }
  };

  const handleConfirm = async (id) => {
    try {
      await api.post(`/api/v1/purchasing/orders/${id}/confirm/`, {});
      setToast({ msg: "PO confirmed.", ok: true });
      load();
      loadDetail(id);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    }
  };

  const handleCancel = async (id) => {
    try {
      await api.post(`/api/v1/purchasing/orders/${id}/cancel/`, {});
      setToast({ msg: "PO cancelled.", ok: true });
      setDetail(null);
      load();
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    }
  };

  const handleSave = (ok, err) => {
    setCreateOpen(false);
    if (ok) { setToast({ msg: ok, ok: true }); load(); }
    else setToast({ msg: err, ok: false });
  };

  const filtered = useMemo(() => orders.filter(o => {
    const matchStatus = statusFilter === "ALL" || o.status === statusFilter;
    const matchSearch = !search ||
      (o.po_number || "").toLowerCase().includes(search.toLowerCase()) ||
      (o.vendor_name || "").toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  }), [orders, statusFilter, search]);

  const statuses = ["ALL", "DRAFT", "CONFIRMED", "PARTIAL", "RECEIVED", "CANCELLED"];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading font-bold text-2xl">Purchase Orders</h2>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">{orders.length} order{orders.length !== 1 ? "s" : ""}</p>
        </div>
        <div className="flex items-center gap-3">
          <a href="/app/purchasing/vendors" className="cy-btn cy-btn-ghost !py-2 text-sm">
            Vendors
          </a>
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setCreateOpen(true)} className="cy-btn cy-btn-primary">
            <Plus className="w-4 h-4" /> New PO
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-ink-muted)]" />
          <input
            placeholder="Search POs…"
            className="cy-input pl-9 w-56"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        {statuses.map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
              statusFilter === s
                ? "bg-[#333] text-white border-transparent"
                : "bg-white border-[var(--color-line)] text-[var(--color-ink-soft)] hover:border-[var(--color-ink)]"
            }`}
          >
            {s === "ALL" ? "All" : s.charAt(0) + s.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      <div className="cy-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-surface)]">
                {["PO Number", "Vendor", "Status", "Date", "Expected", "Lines", "Total", ""].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-line)]">
              {loading ? (
                <tr><td colSpan={8} className="text-center py-16 text-[var(--color-ink-muted)]">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-16">
                    <ShoppingCart className="w-10 h-10 mx-auto mb-3 opacity-30" />
                    <p className="text-[var(--color-ink-muted)]">No purchase orders yet.</p>
                    <button onClick={() => setCreateOpen(true)} className="mt-3 cy-btn cy-btn-primary !py-2 !text-xs">
                      <Plus className="w-3.5 h-3.5" /> Create first PO
                    </button>
                  </td>
                </tr>
              ) : filtered.map(o => (
                <tr
                  key={o.id}
                  className="hover:bg-[var(--color-surface)] transition-colors cursor-pointer"
                  onClick={() => loadDetail(o.id)}
                >
                  <td className="px-4 py-3 font-mono font-semibold text-xs">{o.po_number}</td>
                  <td className="px-4 py-3 font-semibold">{o.vendor_name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex text-xs font-semibold px-2 py-0.5 rounded-full border ${STATUS_COLORS[o.status] || ""}`}>
                      {o.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[var(--color-ink-muted)]">{o.order_date}</td>
                  <td className="px-4 py-3 text-[var(--color-ink-muted)]">{o.expected_date || "—"}</td>
                  <td className="px-4 py-3 tabular-nums">{o.line_count ?? "—"}</td>
                  <td className="px-4 py-3 font-bold tabular-nums">{parseFloat(o.total || 0).toFixed(2)}</td>
                  <td className="px-4 py-3">
                    <ChevronRight className="w-4 h-4 text-[var(--color-ink-muted)]" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {createOpen && (
        <CreatePoModal
          vendors={vendors}
          companies={companies}
          products={products}
          onSave={handleSave}
          onClose={() => setCreateOpen(false)}
        />
      )}
      {detail && (
        <PoDetailDrawer
          po={detail}
          onClose={() => setDetail(null)}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}
      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
