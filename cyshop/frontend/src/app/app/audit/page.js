"use client";

import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { ScrollText, RefreshCw } from "lucide-react";

const METHOD_COLOR = {
  GET: "text-[var(--color-ink-muted)]", POST: "text-green-400",
  PUT: "text-amber-400", PATCH: "text-amber-400", DELETE: "text-red-400",
};

export default function AuditPage() {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [method, setMethod] = useState("");
  const [err, setErr] = useState("");
  const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

  const load = useCallback(async () => {
    setErr("");
    try {
      const params = new URLSearchParams();
      if (method) params.set("method", method);
      if (q) params.set("search", q);
      setRows(asList(await apiFetch(`/api/v1/audit/?${params.toString()}`)));
    } catch (e) { setErr(e.message); }
  }, [method, q]);
  useEffect(() => { load(); }, [load]);

  const th = "text-start px-3 py-2 text-[11px] uppercase tracking-wide text-[var(--color-ink-muted)] font-semibold";
  const td = "px-3 py-2 text-sm border-t border-[var(--color-line)]";

  return (
    <div className="p-4 md:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3"><ScrollText className="w-6 h-6 text-brand-blue" /><h1 className="text-xl font-heading font-bold">Audit Log</h1></div>
        <button onClick={load} className="cy-btn cy-btn-ghost !py-1.5 !px-3 text-sm"><RefreshCw className="w-3.5 h-3.5" /> Refresh</button>
      </div>
      {err && <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300">{err}</div>}

      <div className="flex flex-wrap gap-2">
        <input className="cy-input h-9 text-sm" placeholder="Search user / path…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="cy-input h-9 text-sm" value={method} onChange={(e) => setMethod(e.target.value)}>
          <option value="">All methods</option>
          {["GET", "POST", "PUT", "PATCH", "DELETE"].map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] overflow-x-auto">
        <table className="w-full">
          <thead><tr><th className={th}>Time</th><th className={th}>User</th><th className={th}>Method</th><th className={th}>Path</th><th className={th}>Action</th><th className={th}>IP</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td className={`${td} whitespace-nowrap`}>{new Date(r.timestamp).toLocaleString()}</td>
                <td className={td}>{r.username || r.user_id || "—"}</td>
                <td className={`${td} font-mono text-xs ${METHOD_COLOR[r.method] || ""}`}>{r.method}</td>
                <td className={`${td} font-mono text-xs`}>{r.path}</td>
                <td className={td}>{r.action || "—"}</td>
                <td className={`${td} font-mono text-xs text-[var(--color-ink-muted)]`}>{r.ip_address || "—"}</td>
              </tr>
            ))}
            {!rows.length && <tr><td className={td} colSpan={6}>No audit entries match.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
