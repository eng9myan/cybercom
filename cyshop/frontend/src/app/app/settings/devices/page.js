"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Plus, RefreshCw, X, Trash2, Monitor, ExternalLink,
  CheckCircle2, AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";

const DEVICE_TYPES = [
  { value: "POS", label: "POS Terminal", route: "/pos-terminal" },
  { value: "KDS", label: "Kitchen Display", route: "/kds" },
  { value: "WAITER", label: "Waiter Handheld", route: "/waiter" },
  { value: "CUSTOMER_DISPLAY", label: "Customer-Facing Display", route: "/customer-display" },
  { value: "WAREHOUSE_SCANNER", label: "Warehouse Scanner", route: "/warehouse-scanner" },
  { value: "SELF_ORDER", label: "Self-Order Kiosk", route: "/self-order" },
];

const EMPTY_FORM = { name: "", code: "", branch: "", company: "", device_type: "POS" };

function Toast({ msg, ok, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3500); return () => clearTimeout(t); }, [onDone]);
  return (
    <div className={`fixed bottom-6 right-6 z-[200] flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl text-white text-sm font-medium ${ok ? "bg-[#16A34A]" : "bg-[#DC2626]"}`}>
      {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
      {msg}
    </div>
  );
}

function DeviceModal({ companies, branches, onSave, onClose }) {
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/api/v1/pos/devices/", form);
      onSave("Device registered.");
    } catch (err) {
      onSave(null, err.message);
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg flex items-center gap-2">
            <Monitor className="w-5 h-5 text-[#0E7C9B]" /> Register Device
          </h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          <div>
            <label className="cy-label">Device Name *</label>
            <input required className="cy-input" value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="Kitchen Display 1" />
          </div>
          <div>
            <label className="cy-label">Device Code *</label>
            <input required className="cy-input" value={form.code} onChange={(e) => set("code", e.target.value)} placeholder="KDS-01" />
          </div>
          <div>
            <label className="cy-label">Device Type *</label>
            <select required className="cy-input" value={form.device_type} onChange={(e) => set("device_type", e.target.value)}>
              {DEVICE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div>
            <label className="cy-label">Company *</label>
            <select required className="cy-input" value={form.company} onChange={(e) => set("company", e.target.value)}>
              <option value="">— select —</option>
              {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="cy-label">Branch *</label>
            <select required className="cy-input" value={form.branch} onChange={(e) => set("branch", e.target.value)}>
              <option value="">— select —</option>
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="cy-btn cy-btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="cy-btn cy-btn-primary">
              {saving ? "Registering…" : "Register Device"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function typeInfo(type) {
  return DEVICE_TYPES.find((t) => t.value === type) || { label: type, route: "/" };
}

export default function DevicesPage() {
  const [devices, setDevices] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [devs, comps, brs] = await Promise.all([
        api.get("/api/v1/pos/devices/"),
        api.get("/api/v1/tenants/companies/"),
        api.get("/api/v1/tenants/branches/"),
      ]);
      setDevices(Array.isArray(devs) ? devs : devs.results || []);
      setCompanies(Array.isArray(comps) ? comps : comps.results || []);
      setBranches(Array.isArray(brs) ? brs : brs.results || []);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = (ok, err) => {
    if (ok) { setModal(false); setToast({ msg: ok, ok: true }); load(); }
    else setToast({ msg: err, ok: false });
  };

  const handleDelete = async (id) => {
    if (!confirm("Deregister this device?")) return;
    try {
      await api.del(`/api/v1/pos/devices/${id}/`);
      setToast({ msg: "Device deregistered.", ok: true });
      load();
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading font-bold text-2xl">Device Registry</h2>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">
            {devices.length} device{devices.length !== 1 ? "s" : ""} · POS terminals, kitchen displays, waiter handhelds, and more
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setModal(true)} className="cy-btn cy-btn-primary">
            <Plus className="w-4 h-4" /> Register Device
          </button>
        </div>
      </div>

      <div className="cy-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-surface)]">
                {["Name", "Code", "Type", "Branch", "Route", "Last Seen", "Actions"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-line)]">
              {loading ? (
                <tr><td colSpan={7} className="text-center py-16 text-[var(--color-ink-muted)]">Loading…</td></tr>
              ) : devices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-16">
                    <Monitor className="w-10 h-10 mx-auto mb-3 text-[var(--color-ink-muted)] opacity-40" />
                    <p className="text-[var(--color-ink-muted)]">No devices registered yet.</p>
                    <button onClick={() => setModal(true)} className="mt-3 cy-btn cy-btn-primary !py-2 !text-xs">
                      <Plus className="w-3.5 h-3.5" /> Register first device
                    </button>
                  </td>
                </tr>
              ) : devices.map((d) => {
                const info = typeInfo(d.device_type);
                return (
                  <tr key={d.id} className="hover:bg-[var(--color-surface)] transition-colors">
                    <td className="px-4 py-3 font-semibold">{d.name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-[var(--color-ink-muted)]">{d.code}</td>
                    <td className="px-4 py-3">{d.device_type_display || info.label}</td>
                    <td className="px-4 py-3 text-[var(--color-ink-muted)]">{d.branch_name || "—"}</td>
                    <td className="px-4 py-3">
                      <a href={d.route || info.route} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-[#0E7C9B] hover:underline">
                        {d.route || info.route} <ExternalLink className="w-3 h-3" />
                      </a>
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--color-ink-muted)]">
                      {d.last_seen_at ? new Date(d.last_seen_at).toLocaleString() : "Never"}
                    </td>
                    <td className="px-4 py-3">
                      <button onClick={() => handleDelete(d.id)} className="w-7 h-7 rounded-md hover:bg-red-50 hover:text-[#DC2626] flex items-center justify-center text-[var(--color-ink-muted)]">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {modal && (
        <DeviceModal companies={companies} branches={branches} onSave={handleSave} onClose={() => setModal(false)} />
      )}
      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
