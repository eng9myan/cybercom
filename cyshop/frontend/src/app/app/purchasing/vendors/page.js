"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Plus, Search, RefreshCw, X, Pencil, Building2,
  CheckCircle2, AlertTriangle, Trash2,
} from "lucide-react";
import { api } from "@/lib/api";

const EMPTY_FORM = {
  name: "", code: "", email: "", phone: "", address: "",
  contact_name: "", tax_id: "", currency: "USD", payment_terms_days: "30",
  notes: "", company: "",
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

function VendorModal({ vendor, companies, onSave, onClose }) {
  const [form, setForm] = useState(vendor ? { ...vendor, company: vendor.company || "" } : { ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const isEdit = Boolean(vendor);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (isEdit) await api.patch(`/api/v1/purchasing/vendors/${vendor.id}/`, form);
      else await api.post("/api/v1/purchasing/vendors/", form);
      onSave(isEdit ? "Vendor updated." : "Vendor created.");
    } catch (err) {
      onSave(null, err.message);
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg">{isEdit ? "Edit Vendor" : "New Vendor"}</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="cy-label">Vendor Name *</label>
              <input required className="cy-input" value={form.name} onChange={e => set("name", e.target.value)} placeholder="Supplier Co." />
            </div>
            <div>
              <label className="cy-label">Code</label>
              <input className="cy-input" value={form.code} onChange={e => set("code", e.target.value)} placeholder="SUP-001" />
            </div>
            <div>
              <label className="cy-label">Company *</label>
              <select required className="cy-input" value={form.company} onChange={e => set("company", e.target.value)}>
                <option value="">— select —</option>
                {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">Contact Name</label>
              <input className="cy-input" value={form.contact_name} onChange={e => set("contact_name", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Email</label>
              <input type="email" className="cy-input" value={form.email} onChange={e => set("email", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Phone</label>
              <input className="cy-input" value={form.phone} onChange={e => set("phone", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Tax ID</label>
              <input className="cy-input" value={form.tax_id} onChange={e => set("tax_id", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Currency</label>
              <select className="cy-input" value={form.currency} onChange={e => set("currency", e.target.value)}>
                {["USD", "JOD", "SAR", "AED", "EUR", "GBP"].map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">Payment Terms (days)</label>
              <input type="number" min="0" className="cy-input" value={form.payment_terms_days} onChange={e => set("payment_terms_days", e.target.value)} />
            </div>
            <div className="col-span-2">
              <label className="cy-label">Address</label>
              <textarea rows={2} className="cy-input" value={form.address} onChange={e => set("address", e.target.value)} />
            </div>
            <div className="col-span-2">
              <label className="cy-label">Notes</label>
              <textarea rows={2} className="cy-input" value={form.notes} onChange={e => set("notes", e.target.value)} />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="cy-btn cy-btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="cy-btn cy-btn-primary">
              {saving ? "Saving…" : isEdit ? "Update" : "Create Vendor"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function VendorsPage() {
  const [vendors, setVendors] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState(null); // null | "create" | vendor object
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [v, c] = await Promise.all([
        api.get("/api/v1/purchasing/vendors/"),
        api.get("/api/v1/tenants/companies/"),
      ]);
      setVendors(Array.isArray(v) ? v : v.results || []);
      setCompanies(Array.isArray(c) ? c : c.results || []);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = (ok, err) => {
    setModal(null);
    if (ok) { setToast({ msg: ok, ok: true }); load(); }
    else setToast({ msg: err, ok: false });
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this vendor?")) return;
    try {
      await api.del(`/api/v1/purchasing/vendors/${id}/`);
      setToast({ msg: "Vendor deleted.", ok: true });
      load();
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    }
  };

  const filtered = vendors.filter(v =>
    !search || v.name.toLowerCase().includes(search.toLowerCase()) ||
    (v.code || "").toLowerCase().includes(search.toLowerCase()) ||
    (v.email || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading font-bold text-2xl">Vendors</h2>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">{vendors.length} vendor{vendors.length !== 1 ? "s" : ""}</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setModal("create")} className="cy-btn cy-btn-primary">
            <Plus className="w-4 h-4" /> New Vendor
          </button>
        </div>
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-ink-muted)]" />
        <input
          placeholder="Search vendors…"
          className="cy-input pl-9"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="cy-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-surface)]">
                {["Vendor", "Code", "Contact", "Email", "Phone", "Terms", "Currency", "Actions"].map(h => (
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
                    <Building2 className="w-10 h-10 mx-auto mb-3 opacity-30" />
                    <p className="text-[var(--color-ink-muted)]">No vendors yet.</p>
                    <button onClick={() => setModal("create")} className="mt-3 cy-btn cy-btn-primary !py-2 !text-xs">
                      <Plus className="w-3.5 h-3.5" /> Add first vendor
                    </button>
                  </td>
                </tr>
              ) : filtered.map(v => (
                <tr key={v.id} className="hover:bg-[var(--color-surface)] transition-colors">
                  <td className="px-4 py-3 font-semibold">{v.name}</td>
                  <td className="px-4 py-3 font-mono text-xs text-[var(--color-ink-muted)]">{v.code || "—"}</td>
                  <td className="px-4 py-3 text-[var(--color-ink-muted)]">{v.contact_name || "—"}</td>
                  <td className="px-4 py-3 text-[var(--color-ink-muted)]">{v.email || "—"}</td>
                  <td className="px-4 py-3 text-[var(--color-ink-muted)]">{v.phone || "—"}</td>
                  <td className="px-4 py-3">{v.payment_terms_days}d</td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs px-2 py-0.5 rounded-full bg-[var(--color-surface-2)] border border-[var(--color-line)]">
                      {v.currency}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button onClick={() => setModal(v)} className="w-7 h-7 rounded-md hover:bg-[var(--color-surface-2)] flex items-center justify-center text-[var(--color-ink-muted)]">
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => handleDelete(v.id)} className="w-7 h-7 rounded-md hover:bg-red-50 hover:text-[#DC2626] flex items-center justify-center text-[var(--color-ink-muted)]">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modal && (
        <VendorModal
          vendor={modal === "create" ? null : modal}
          companies={companies}
          onSave={handleSave}
          onClose={() => setModal(null)}
        />
      )}
      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
