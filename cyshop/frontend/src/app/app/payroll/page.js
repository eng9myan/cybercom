"use client";

import { useState, useEffect, useCallback } from "react";
import { apiFetch, openAuthed } from "@/lib/api";
import { Wallet, RefreshCw } from "lucide-react";

const money = (v) => Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function PayrollPage() {
  const [batches, setBatches] = useState([]);
  const [payslips, setPayslips] = useState([]);
  const [sel, setSel] = useState(null);
  const [err, setErr] = useState("");
  const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

  const load = useCallback(async () => {
    setErr("");
    try {
      const [b, p] = await Promise.all([
        apiFetch("/api/v1/payroll/batches/"),
        apiFetch("/api/v1/payroll/payslips/"),
      ]);
      setBatches(asList(b)); setPayslips(asList(p));
    } catch (e) { setErr(e.message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const th = "text-start px-3 py-2 text-[11px] uppercase tracking-wide text-[var(--color-ink-muted)] font-semibold";
  const td = "px-3 py-2 text-sm border-t border-[var(--color-line)]";
  const Panel = ({ children }) => <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] overflow-x-auto">{children}</div>;
  const slipsFor = (bid) => payslips.filter((s) => s.batch === bid || s.batch_id === bid);

  return (
    <div className="p-4 md:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3"><Wallet className="w-6 h-6 text-brand-orange" /><h1 className="text-xl font-heading font-bold">Payroll</h1></div>
        <button onClick={load} className="cy-btn cy-btn-ghost !py-1.5 !px-3 text-sm"><RefreshCw className="w-3.5 h-3.5" /> Refresh</button>
      </div>
      {err && <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300">{err}</div>}

      <div>
        <h2 className={th}>Payroll runs</h2>
        <Panel>
          <table className="w-full">
            <thead><tr><th className={th}>Period</th><th className={th}>Status</th><th className={th}>Payslips</th><th className={`${th} text-end`}>Gross</th><th className={`${th} text-end`}>Net</th><th className={th}></th></tr></thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id}>
                  <td className={td}>{b.period || b.pay_period || `${b.period_start || ""}–${b.period_end || ""}`}</td>
                  <td className={td}><span className="cy-pill text-xs">{b.status}</span></td>
                  <td className={td}>{slipsFor(b.id).length}</td>
                  <td className={`${td} text-end tabular-nums`}>{money(b.total_gross)}</td>
                  <td className={`${td} text-end tabular-nums`}>{money(b.total_net)}</td>
                  <td className={td}><button className="text-brand-blue text-xs font-semibold" onClick={() => setSel(sel === b.id ? null : b.id)}>{sel === b.id ? "Hide" : "View slips"}</button></td>
                </tr>
              ))}
              {!batches.length && <tr><td className={td} colSpan={6}>No payroll runs yet. Create one from the API or a future "Run payroll" action.</td></tr>}
            </tbody>
          </table>
        </Panel>
      </div>

      {sel && (
        <div>
          <h2 className={th}>Payslips — run {sel.slice(0, 8)}</h2>
          <Panel>
            <table className="w-full">
              <thead><tr><th className={th}>Employee</th><th className={`${th} text-end`}>Gross</th><th className={`${th} text-end`}>Deductions</th><th className={`${th} text-end`}>Net</th><th className={th}></th></tr></thead>
              <tbody>
                {slipsFor(sel).map((s) => (
                  <tr key={s.id}><td className={td}>{s.employee_name || s.employee}</td>
                    <td className={`${td} text-end tabular-nums`}>{money(s.gross_pay || s.gross)}</td>
                    <td className={`${td} text-end tabular-nums`}>{money(s.total_deductions || s.deductions)}</td>
                    <td className={`${td} text-end tabular-nums font-semibold`}>{money(s.net_pay || s.net)}</td>
                    <td className={td}><button type="button" onClick={() => openAuthed(`/api/v1/payroll/payslips/${s.id}/print/`)} className="text-brand-blue text-xs">Print</button></td></tr>
                ))}
                {!slipsFor(sel).length && <tr><td className={td} colSpan={4}>No payslips in this run.</td></tr>}
              </tbody>
            </table>
          </Panel>
        </div>
      )}
    </div>
  );
}
