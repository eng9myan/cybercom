"use client";

import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { UserRound, RefreshCw } from "lucide-react";

const TABS = ["Employees", "Contracts", "Leave Requests"];
const money = (v, c) => `${Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })} ${c || ""}`.trim();

export default function HrPage() {
  const [tab, setTab] = useState(TABS[0]);
  const [emps, setEmps] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [leave, setLeave] = useState([]);
  const [err, setErr] = useState("");
  const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

  const load = useCallback(async () => {
    setErr("");
    try {
      const [e, c, l] = await Promise.all([
        apiFetch("/api/v1/hr/employees/"),
        apiFetch("/api/v1/hr/contracts/").catch(() => []),
        apiFetch("/api/v1/hr/leave-requests/").catch(() => []),
      ]);
      setEmps(asList(e)); setContracts(asList(c)); setLeave(asList(l));
    } catch (e) { setErr(e.message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const act = async (id, action) => {
    try { await apiFetch(`/api/v1/hr/leave-requests/${id}/${action}/`, { method: "POST" }); load(); }
    catch (e) { setErr(e.message); }
  };

  const th = "text-left px-3 py-2 text-[11px] uppercase tracking-wide text-[var(--color-ink-muted)] font-semibold";
  const td = "px-3 py-2 text-sm border-t border-[var(--color-line)]";
  const Panel = ({ children }) => <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] overflow-x-auto">{children}</div>;

  return (
    <div className="p-4 md:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3"><UserRound className="w-6 h-6 text-brand-blue" /><h1 className="text-xl font-heading font-bold">Human Resources</h1></div>
        <button onClick={load} className="cy-btn cy-btn-ghost !py-1.5 !px-3 text-sm"><RefreshCw className="w-3.5 h-3.5" /> Refresh</button>
      </div>
      {err && <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300">{err}</div>}

      <div className="flex gap-1 border-b border-[var(--color-line)]">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px transition ${tab === t ? "border-brand-blue text-[var(--color-ink)]" : "border-transparent text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"}`}>
            {t} {t === "Employees" ? `(${emps.length})` : ""}
          </button>
        ))}
      </div>

      {tab === "Employees" && (
        <Panel>
          <table className="w-full">
            <thead><tr><th className={th}>ID</th><th className={th}>Name</th><th className={th}>Job title</th><th className={th}>Type</th><th className={th}>Hired</th><th className={`${th} text-right`}>Base salary</th><th className={th}>Status</th></tr></thead>
            <tbody>
              {emps.slice(0, 300).map((e) => (
                <tr key={e.id}><td className={td}>{e.employee_id}</td><td className={td}>{e.full_name}</td><td className={td}>{e.job_title}</td>
                  <td className={td}>{e.employment_type}</td><td className={td}>{e.hire_date}</td>
                  <td className={`${td} text-right tabular-nums`}>{money(e.base_salary, e.currency)}</td>
                  <td className={td}><span className="cy-pill text-xs">{e.status}</span></td></tr>
              ))}
              {!emps.length && <tr><td className={td} colSpan={7}>No employees.</td></tr>}
            </tbody>
          </table>
        </Panel>
      )}

      {tab === "Contracts" && (
        <Panel>
          <table className="w-full">
            <thead><tr><th className={th}>Employee</th><th className={th}>Type</th><th className={th}>Start</th><th className={th}>End</th><th className={`${th} text-right`}>Gross</th><th className={th}>Active</th></tr></thead>
            <tbody>
              {contracts.map((c) => (
                <tr key={c.id}><td className={td}>{c.employee_name || c.employee}</td><td className={td}>{c.contract_type}</td><td className={td}>{c.start_date}</td>
                  <td className={td}>{c.end_date || "—"}</td><td className={`${td} text-right tabular-nums`}>{money(c.gross_salary)}</td><td className={td}>{c.is_active ? "yes" : "no"}</td></tr>
              ))}
              {!contracts.length && <tr><td className={td} colSpan={6}>No contracts recorded.</td></tr>}
            </tbody>
          </table>
        </Panel>
      )}

      {tab === "Leave Requests" && (
        <Panel>
          <table className="w-full">
            <thead><tr><th className={th}>Employee</th><th className={th}>Type</th><th className={th}>From</th><th className={th}>To</th><th className={th}>Days</th><th className={th}>Status</th><th className={th}></th></tr></thead>
            <tbody>
              {leave.map((l) => (
                <tr key={l.id}><td className={td}>{l.employee_name || l.employee}</td><td className={td}>{l.leave_type_name || l.leave_type}</td>
                  <td className={td}>{l.start_date}</td><td className={td}>{l.end_date}</td><td className={td}>{l.days_requested}</td>
                  <td className={td}><span className="cy-pill text-xs">{l.status}</span></td>
                  <td className={td}>{l.status === "pending" && (
                    <span className="flex gap-2">
                      <button onClick={() => act(l.id, "approve")} className="text-green-400 text-xs font-semibold">Approve</button>
                      <button onClick={() => act(l.id, "reject")} className="text-red-400 text-xs font-semibold">Reject</button>
                    </span>)}</td></tr>
              ))}
              {!leave.length && <tr><td className={td} colSpan={7}>No leave requests.</td></tr>}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}
