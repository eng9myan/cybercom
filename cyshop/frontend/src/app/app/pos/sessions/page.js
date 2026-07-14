"use client";

import { useState, useEffect, useCallback } from "react";
import { Plus, RefreshCw, X, CheckCircle2, AlertTriangle, DollarSign, ShoppingBag, Clock, Lock } from "lucide-react";
import { api } from "@/lib/api";

function Toast({ msg, ok, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3500); return () => clearTimeout(t); }, [onDone]);
  return (
    <div className={`fixed bottom-6 right-6 z-[200] flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl text-white text-sm font-medium ${ok ? "bg-[#16A34A]" : "bg-[#DC2626]"}`}>
      {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
      {msg}
    </div>
  );
}

function OpenSessionModal({ companies, onSave, onClose }) {
  const [form, setForm] = useState({ company: companies[0]?.id || "", opening_float: "0", notes: "" });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.company) return;
    setSaving(true);
    try {
      await api.post("/api/v1/pos/sessions/", {
        ...form,
        cashier: localStorage.getItem("user_id"),
      });
      onSave("Session opened.");
    } catch (err) {
      onSave(null, err.message);
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg">Open POS Session</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          <div>
            <label className="cy-label">Company *</label>
            <select required className="cy-input" value={form.company} onChange={e => set("company", e.target.value)}>
              <option value="">— select —</option>
              {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="cy-label">Opening Float (cash in drawer)</label>
            <input type="number" step="0.01" min="0" className="cy-input" value={form.opening_float} onChange={e => set("opening_float", e.target.value)} />
          </div>
          <div>
            <label className="cy-label">Notes</label>
            <textarea rows={2} className="cy-input" value={form.notes} onChange={e => set("notes", e.target.value)} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="cy-btn cy-btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="cy-btn cy-btn-primary">
              {saving ? "Opening…" : "Open Session"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CloseSessionModal({ session, onSave, onClose }) {
  const [closingFloat, setClosingFloat] = useState("0");
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/api/v1/pos/sessions/${session.id}/close/`, { closing_float: closingFloat });
      onSave("Session closed.");
    } catch (err) {
      onSave(null, err.message);
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg flex items-center gap-2">
            <Lock className="w-4 h-4 text-[#DC2626]" /> Close Session
          </h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-line)]">
            <div className="text-sm text-[var(--color-ink-muted)]">Session</div>
            <div className="font-semibold">{session.name}</div>
            <div className="text-sm text-[var(--color-ink-muted)] mt-1">
              Sales: {session.order_count} orders · Total: {parseFloat(session.total_sales || 0).toFixed(2)}
            </div>
          </div>
          <div>
            <label className="cy-label">Closing Float (cash counted in drawer)</label>
            <input type="number" step="0.01" min="0" className="cy-input" value={closingFloat} onChange={e => setClosingFloat(e.target.value)} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="cy-btn cy-btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="cy-btn !bg-[#DC2626] !text-white cy-btn-primary">
              {saving ? "Closing…" : "Close Session"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function PosSessionsPage() {
  const [sessions, setSessions] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openModal, setOpenModal] = useState(false);
  const [closeTarget, setCloseTarget] = useState(null);
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sess, comps] = await Promise.all([
        api.get("/api/v1/pos/sessions/"),
        api.get("/api/v1/tenants/companies/"),
      ]);
      setSessions(Array.isArray(sess) ? sess : sess.results || []);
      setCompanies(Array.isArray(comps) ? comps : comps.results || []);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = (ok, err) => {
    setOpenModal(false);
    setCloseTarget(null);
    if (ok) { setToast({ msg: ok, ok: true }); load(); }
    else setToast({ msg: err, ok: false });
  };

  const openSessions = sessions.filter(s => s.status === "OPEN");
  const closedSessions = sessions.filter(s => s.status === "CLOSED");

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading font-bold text-2xl">POS Sessions</h2>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">
            {openSessions.length} open · {closedSessions.length} closed
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setOpenModal(true)} className="cy-btn cy-btn-primary">
            <Plus className="w-4 h-4" /> Open Session
          </button>
        </div>
      </div>

      {/* KPI strip */}
      {openSessions.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Open Sessions", value: openSessions.length, icon: Clock, color: "#16A34A" },
            { label: "Today's Sales", value: openSessions.reduce((s, x) => s + parseFloat(x.total_sales || 0), 0).toFixed(2), icon: DollarSign, color: "#ED6C00" },
            { label: "Today's Orders", value: openSessions.reduce((s, x) => s + (x.order_count || 0), 0), icon: ShoppingBag, color: "#0E7C9B" },
            { label: "Total Sessions", value: sessions.length, icon: Clock, color: "#9333EA" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="cy-card p-4">
              <div className="flex items-center gap-2 mb-1">
                <Icon className="w-4 h-4" style={{ color }} />
                <span className="text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-muted)]">{label}</span>
              </div>
              <div className="font-heading font-bold text-2xl">{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Sessions table */}
      <div className="cy-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-surface)]">
                {["Session", "Status", "Cashier", "Opened", "Orders", "Sales", "Actions"].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-line)]">
              {loading ? (
                <tr><td colSpan={7} className="text-center py-16 text-[var(--color-ink-muted)]">Loading…</td></tr>
              ) : sessions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-16">
                    <Clock className="w-10 h-10 mx-auto mb-3 text-[var(--color-ink-muted)] opacity-40" />
                    <p className="text-[var(--color-ink-muted)]">No sessions yet.</p>
                    <button onClick={() => setOpenModal(true)} className="mt-3 cy-btn cy-btn-primary !py-2 !text-xs">
                      <Plus className="w-3.5 h-3.5" /> Open first session
                    </button>
                  </td>
                </tr>
              ) : sessions.map(s => (
                <tr key={s.id} className="hover:bg-[var(--color-surface)] transition-colors">
                  <td className="px-4 py-3 font-semibold">{s.name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded-full ${
                      s.status === "OPEN"
                        ? "bg-green-50 text-green-700 border border-green-200"
                        : "bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] border border-[var(--color-line)]"
                    }`}>
                      {s.status === "OPEN" && <span className="w-1.5 h-1.5 rounded-full bg-green-500" />}
                      {s.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[var(--color-ink-muted)]">{s.cashier_username || "—"}</td>
                  <td className="px-4 py-3 text-xs text-[var(--color-ink-muted)]">
                    {s.opening_at ? new Date(s.opening_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3 tabular-nums">{s.order_count ?? "—"}</td>
                  <td className="px-4 py-3 font-semibold tabular-nums">
                    {parseFloat(s.total_sales || 0).toFixed(2)}
                  </td>
                  <td className="px-4 py-3">
                    {s.status === "OPEN" && (
                      <button
                        onClick={() => setCloseTarget(s)}
                        className="text-xs font-semibold text-[#DC2626] hover:underline"
                      >
                        Close
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {openModal && (
        <OpenSessionModal companies={companies} onSave={handleSave} onClose={() => setOpenModal(false)} />
      )}
      {closeTarget && (
        <CloseSessionModal session={closeTarget} onSave={handleSave} onClose={() => setCloseTarget(null)} />
      )}
      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
