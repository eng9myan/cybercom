"use client";

import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { BookOpen, Plus, Check, X, RefreshCw } from "lucide-react";

const TABS = ["Chart of Accounts", "Journal Entries", "Trial Balance", "Income Statement"];
const ACCOUNT_TYPES = ["asset", "liability", "equity", "revenue", "expense"];
const money = (v) => Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function Panel({ children }) {
  return <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] overflow-hidden">{children}</div>;
}

export default function AccountingPage() {
  const [tab, setTab] = useState(TABS[0]);
  const [accounts, setAccounts] = useState([]);
  const [journals, setJournals] = useState([]);
  const [entries, setEntries] = useState([]);
  const [tb, setTb] = useState(null);
  const [pnl, setPnl] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

  const load = useCallback(async () => {
    setErr("");
    try {
      const [a, j, e, t, p] = await Promise.all([
        apiFetch("/api/v1/accounting/accounts/"),
        apiFetch("/api/v1/accounting/journals/"),
        apiFetch("/api/v1/accounting/entries/"),
        apiFetch("/api/v1/accounting/reports/trial-balance/"),
        apiFetch("/api/v1/accounting/reports/income-statement/"),
      ]);
      setAccounts(asList(a)); setJournals(asList(j)); setEntries(asList(e));
      setTb(t); setPnl(p);
    } catch (e) { setErr(e.message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  // ---- new account
  const [na, setNa] = useState({ code: "", name: "", name_ar: "", account_type: "asset" });
  const addAccount = async (ev) => {
    ev.preventDefault(); setBusy(true); setErr("");
    try {
      await apiFetch("/api/v1/accounting/accounts/", { method: "POST", body: JSON.stringify(na) });
      setNa({ code: "", name: "", name_ar: "", account_type: "asset" });
      load();
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  // ---- new journal entry (2 lines minimum)
  const [ne, setNe] = useState({ journal: "", reference: "", entry_date: "", description: "" });
  const [lines, setLines] = useState([{ account: "", debit: "", credit: "" }, { account: "", debit: "", credit: "" }]);
  const setLine = (i, k, v) => setLines((L) => L.map((l, j) => (j === i ? { ...l, [k]: v } : l)));
  const totD = lines.reduce((s, l) => s + Number(l.debit || 0), 0);
  const totC = lines.reduce((s, l) => s + Number(l.credit || 0), 0);
  const addEntry = async (ev) => {
    ev.preventDefault(); setBusy(true); setErr("");
    try {
      const body = {
        ...ne,
        lines_input: lines
          .filter((l) => l.account && (l.debit || l.credit))
          .map((l) => ({ account: l.account, debit: Number(l.debit || 0), credit: Number(l.credit || 0) })),
      };
      const created = await apiFetch("/api/v1/accounting/entries/", { method: "POST", body: JSON.stringify(body) });
      await apiFetch(`/api/v1/accounting/entries/${created.id}/post_entry/`, { method: "POST" });
      setNe({ journal: ne.journal, reference: "", entry_date: "", description: "" });
      setLines([{ account: "", debit: "", credit: "" }, { account: "", debit: "", credit: "" }]);
      load();
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  const inp = "cy-input h-9 text-sm";
  const th = "text-start px-3 py-2 text-[11px] uppercase tracking-wide text-[var(--color-ink-muted)] font-semibold";
  const td = "px-3 py-2 text-sm border-t border-[var(--color-line)]";

  return (
    <div className="p-4 md:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BookOpen className="w-6 h-6 text-brand-orange" />
          <h1 className="text-xl font-heading font-bold">Accounting &amp; Finance</h1>
        </div>
        <button onClick={load} className="cy-btn cy-btn-ghost !py-1.5 !px-3 text-sm"><RefreshCw className="w-3.5 h-3.5" /> Refresh</button>
      </div>

      {err && <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300">{err}</div>}

      <div className="flex gap-1 border-b border-[var(--color-line)]">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px transition ${tab === t ? "border-brand-orange text-[var(--color-ink)]" : "border-transparent text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === "Chart of Accounts" && (
        <div className="space-y-4">
          <form onSubmit={addAccount} className="flex flex-wrap items-end gap-2">
            <input className={inp} placeholder="Code" value={na.code} onChange={(e) => setNa({ ...na, code: e.target.value })} required />
            <input className={inp} placeholder="Name" value={na.name} onChange={(e) => setNa({ ...na, name: e.target.value })} required />
            <input className={inp} placeholder="الاسم (Arabic)" value={na.name_ar} onChange={(e) => setNa({ ...na, name_ar: e.target.value })} />
            <select className={inp} value={na.account_type} onChange={(e) => setNa({ ...na, account_type: e.target.value })}>
              {ACCOUNT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <button disabled={busy} className="cy-btn cy-btn-primary !py-2 !px-3 text-sm"><Plus className="w-4 h-4" /> Add account</button>
          </form>
          <Panel>
            <table className="w-full">
              <thead><tr><th className={th}>Code</th><th className={th}>Name</th><th className={th}>Type</th><th className={th}>Active</th></tr></thead>
              <tbody>
                {accounts.map((a) => (
                  <tr key={a.id}><td className={td}>{a.code}</td><td className={td}>{a.name}{a.name_ar ? ` · ${a.name_ar}` : ""}</td>
                    <td className={td}><span className="cy-pill text-xs">{a.account_type}</span></td>
                    <td className={td}>{a.is_active ? <Check className="w-4 h-4 text-green-400" /> : <X className="w-4 h-4 text-[var(--color-ink-muted)]" />}</td></tr>
                ))}
                {!accounts.length && <tr><td className={td} colSpan={4}>No accounts yet. Add your first above.</td></tr>}
              </tbody>
            </table>
          </Panel>
        </div>
      )}

      {tab === "Journal Entries" && (
        <div className="space-y-4">
          <Panel>
            <form onSubmit={addEntry} className="p-4 space-y-3">
              <div className="flex flex-wrap gap-2">
                <select className={inp} value={ne.journal} onChange={(e) => setNe({ ...ne, journal: e.target.value })} required>
                  <option value="">— journal —</option>
                  {journals.map((j) => <option key={j.id} value={j.id}>{j.name}</option>)}
                </select>
                <input className={inp} type="date" value={ne.entry_date} onChange={(e) => setNe({ ...ne, entry_date: e.target.value })} required />
                <input className={inp} placeholder="Reference" value={ne.reference} onChange={(e) => setNe({ ...ne, reference: e.target.value })} required />
                <input className={`${inp} flex-1`} placeholder="Description" value={ne.description} onChange={(e) => setNe({ ...ne, description: e.target.value })} required />
              </div>
              {lines.map((l, i) => (
                <div key={i} className="flex flex-wrap gap-2">
                  <select className={`${inp} flex-1`} value={l.account} onChange={(e) => setLine(i, "account", e.target.value)}>
                    <option value="">— account —</option>
                    {accounts.map((a) => <option key={a.id} value={a.id}>{a.code} · {a.name}</option>)}
                  </select>
                  <input className={`${inp} w-32`} type="number" step="0.01" min="0" placeholder="Debit" value={l.debit} onChange={(e) => setLine(i, "debit", e.target.value)} />
                  <input className={`${inp} w-32`} type="number" step="0.01" min="0" placeholder="Credit" value={l.credit} onChange={(e) => setLine(i, "credit", e.target.value)} />
                </div>
              ))}
              <div className="flex items-center gap-4 text-sm">
                <button type="button" onClick={() => setLines([...lines, { account: "", debit: "", credit: "" }])} className="text-brand-blue">+ line</button>
                <span className="text-[var(--color-ink-muted)]">Debits {money(totD)} · Credits {money(totC)}</span>
                <span className={totD === totC && totD > 0 ? "text-green-400" : "text-amber-400"}>{totD === totC && totD > 0 ? "balanced" : "not balanced"}</span>
                <button disabled={busy || totD !== totC || !totD} className="cy-btn cy-btn-primary !py-2 !px-3 text-sm ms-auto">Post entry</button>
              </div>
            </form>
          </Panel>
          <Panel>
            <table className="w-full">
              <thead><tr><th className={th}>Date</th><th className={th}>Ref</th><th className={th}>Description</th><th className={th}>Journal</th><th className={th}>Status</th><th className={th}>Balanced</th></tr></thead>
              <tbody>
                {entries.map((e) => (
                  <tr key={e.id}><td className={td}>{e.entry_date}</td><td className={td}>{e.reference}</td><td className={td}>{e.description}</td>
                    <td className={td}>{e.journal_name}</td>
                    <td className={td}><span className={`cy-pill text-xs ${e.status === "posted" ? "cy-pill-orange" : ""}`}>{e.status}</span></td>
                    <td className={td}>{e.is_balanced ? <Check className="w-4 h-4 text-green-400" /> : <X className="w-4 h-4 text-amber-400" />}</td></tr>
                ))}
                {!entries.length && <tr><td className={td} colSpan={6}>No journal entries yet.</td></tr>}
              </tbody>
            </table>
          </Panel>
        </div>
      )}

      {tab === "Trial Balance" && tb && (
        <Panel>
          <table className="w-full">
            <thead><tr><th className={th}>Code</th><th className={th}>Account</th><th className={`${th} text-end`}>Debit</th><th className={`${th} text-end`}>Credit</th></tr></thead>
            <tbody>
              {tb.rows.map((r) => (
                <tr key={r.account_id}><td className={td}>{r.code}</td><td className={td}>{r.name}</td>
                  <td className={`${td} text-end tabular-nums`}>{money(r.debit)}</td><td className={`${td} text-end tabular-nums`}>{money(r.credit)}</td></tr>
              ))}
              <tr className="font-bold"><td className={td} colSpan={2}>Total</td>
                <td className={`${td} text-end tabular-nums`}>{money(tb.total_debit)}</td><td className={`${td} text-end tabular-nums`}>{money(tb.total_credit)}</td></tr>
              {!tb.rows.length && <tr><td className={td} colSpan={4}>No posted entries yet.</td></tr>}
            </tbody>
          </table>
          <div className={`px-3 py-2 text-sm ${tb.balanced ? "text-green-400" : "text-red-400"}`}>{tb.balanced ? "In balance" : "OUT OF BALANCE"}</div>
        </Panel>
      )}

      {tab === "Income Statement" && pnl && (
        <Panel>
          <div className="p-4 space-y-4 text-sm">
            <div>
              <div className={th}>Revenue</div>
              {pnl.revenue.map((r) => <div key={r.account_id} className="flex justify-between py-1"><span>{r.code} {r.name}</span><span className="tabular-nums">{money(r.balance)}</span></div>)}
              <div className="flex justify-between py-1 font-bold border-t border-[var(--color-line)]"><span>Total revenue</span><span className="tabular-nums">{money(pnl.total_revenue)}</span></div>
            </div>
            <div>
              <div className={th}>Expenses</div>
              {pnl.expenses.map((r) => <div key={r.account_id} className="flex justify-between py-1"><span>{r.code} {r.name}</span><span className="tabular-nums">{money(r.balance)}</span></div>)}
              <div className="flex justify-between py-1 font-bold border-t border-[var(--color-line)]"><span>Total expenses</span><span className="tabular-nums">{money(pnl.total_expenses)}</span></div>
            </div>
            <div className="flex justify-between py-2 text-base font-bold border-t-2 border-[var(--color-line)]">
              <span>Net income</span><span className={`tabular-nums ${pnl.net_income >= 0 ? "text-green-400" : "text-red-400"}`}>{money(pnl.net_income)}</span>
            </div>
          </div>
        </Panel>
      )}
    </div>
  );
}
