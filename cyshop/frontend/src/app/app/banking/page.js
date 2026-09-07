"use client";

import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { Landmark, RefreshCw, Upload, Wand2, CheckCircle2, Link2, Link2Off } from "lucide-react";

const money = (v) => Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 });
const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

export default function BankingPage() {
  const { t } = useT();
  const [accounts, setAccounts] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [glAccounts, setGl] = useState([]);
  const [sel, setSel] = useState(null);
  const [lines, setLines] = useState([]);
  const [session, setSession] = useState(null);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try {
      const [a, c, g] = await Promise.all([
        apiFetch("/api/v1/banking/accounts/"),
        apiFetch("/api/v1/tenants/companies/"),
        apiFetch("/api/v1/accounting/accounts/?account_type=asset").catch(() => []),
      ]);
      setAccounts(asList(a)); setCompanies(asList(c)); setGl(asList(g));
    } catch (e) { setErr(e.message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const loadLines = useCallback(async (baId) => {
    setSel(baId);
    try { setLines(asList(await apiFetch(`/api/v1/banking/statement-lines/?bank_account=${baId}`))); }
    catch (e) { setErr(e.message); }
  }, []);

  const [na, setNa] = useState({ company: "", name: "", bank_name: "", currency: "SAR", gl_account_id: "", opening_balance: 0 });
  const addAccount = async (e) => {
    e.preventDefault(); setErr("");
    try { await apiFetch("/api/v1/banking/accounts/", { method: "POST", body: JSON.stringify(na) }); setNa({ ...na, name: "" }); load(); }
    catch (e) { setErr(e.message); }
  };

  const [csv, setCsv] = useState("");
  const importCsv = async () => {
    if (!sel || !csv) return;
    setErr("");
    try { await apiFetch(`/api/v1/banking/accounts/${sel}/import-statement/`, { method: "POST", body: JSON.stringify({ csv }) }); setCsv(""); loadLines(sel); }
    catch (e) { setErr(e.message); }
  };

  const [rp, setRp] = useState({ period_start: "", period_end: "", statement_closing_balance: "" });
  const startRecon = async () => {
    if (!sel) return; setErr("");
    try {
      const s = await apiFetch("/api/v1/banking/reconciliations/", { method: "POST", body: JSON.stringify({ bank_account: sel, ...rp }) });
      setSession(s);
    } catch (e) { setErr(e.message); }
  };
  const autoMatch = async () => { if (!session) return; try { const r = await apiFetch(`/api/v1/banking/reconciliations/${session.id}/auto-match/`, { method: "POST", body: "{}" }); setSession(r.session); loadLines(sel); } catch (e) { setErr(e.message); } };
  const completeRecon = async () => { if (!session) return; try { setSession(await apiFetch(`/api/v1/banking/reconciliations/${session.id}/complete/`, { method: "POST", body: "{}" })); } catch (e) { setErr(e.message); } };
  const toggleMatch = async (ln) => {
    try {
      await apiFetch(`/api/v1/banking/statement-lines/${ln.id}/${ln.matched ? "unmatch" : "match"}/`, { method: "POST", body: JSON.stringify({ match_type: "manual" }) });
      loadLines(sel);
    } catch (e) { setErr(e.message); }
  };

  const inp = "cy-input h-9 text-sm";
  const th = "text-start px-3 py-2 text-[11px] uppercase tracking-wide text-[var(--color-ink-muted)] font-semibold";
  const td = "px-3 py-2 text-sm border-t border-[var(--color-line)]";

  return (
    <div className="p-4 md:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3"><Landmark className="w-6 h-6 text-brand-blue" /><h1 className="text-xl font-heading font-bold">{t("bank.title")}</h1></div>
        <button onClick={load} className="cy-btn cy-btn-ghost !py-1.5 !px-3 text-sm"><RefreshCw className="w-3.5 h-3.5" /> {t("common.refresh")}</button>
      </div>
      {err && <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300">{err}</div>}

      <form onSubmit={addAccount} className="flex flex-wrap items-end gap-2">
        <select className={inp} value={na.company} onChange={(e) => setNa({ ...na, company: e.target.value })} required>
          <option value="">— company —</option>{companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <input className={inp} placeholder={t("accounting.name")} value={na.name} onChange={(e) => setNa({ ...na, name: e.target.value })} required />
        <input className={inp} placeholder="Bank" value={na.bank_name} onChange={(e) => setNa({ ...na, bank_name: e.target.value })} />
        <input className={`${inp} w-20`} value={na.currency} onChange={(e) => setNa({ ...na, currency: e.target.value })} />
        <select className={inp} value={na.gl_account_id} onChange={(e) => setNa({ ...na, gl_account_id: e.target.value })}>
          <option value="">— GL account —</option>{glAccounts.map((g) => <option key={g.id} value={g.id}>{g.code} {g.name}</option>)}
        </select>
        <button className="cy-btn cy-btn-primary !py-2 !px-3 text-sm">{t("bank.newAccount")}</button>
      </form>

      <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] overflow-x-auto">
        <table className="w-full">
          <thead><tr><th className={th}>{t("accounting.name")}</th><th className={th}>Bank</th><th className={th}>{t("bank.amount")}</th><th className={`${th} text-end`}>{t("bank.bookBalance")}</th><th className={th}></th></tr></thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={a.id} className={sel === a.id ? "bg-white/5" : ""}>
                <td className={td}>{a.name}</td><td className={td}>{a.bank_name}</td><td className={td}>{a.currency}</td>
                <td className={`${td} text-end tabular-nums`}>{money(a.book_balance)}</td>
                <td className={td}><button onClick={() => loadLines(a.id)} className="text-brand-blue text-xs font-semibold">{t("bank.reconcile")}</button></td>
              </tr>
            ))}
            {!accounts.length && <tr><td className={td} colSpan={5}>{t("bank.noAccounts")}</td></tr>}
          </tbody>
        </table>
      </div>

      {sel && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-4 space-y-3">
            <div className="text-sm font-semibold flex items-center gap-2"><Upload className="w-4 h-4" /> {t("bank.importStatement")}</div>
            <textarea className="cy-input text-xs font-mono w-full" rows={4} placeholder={"date,description,reference,amount\n2026-09-01,Card settlement,POS,1240.50"} value={csv} onChange={(e) => setCsv(e.target.value)} />
            <button onClick={importCsv} className="cy-btn cy-btn-ghost !py-1.5 !px-3 text-sm">{t("common.add")}</button>
          </div>

          <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-4 flex flex-wrap items-end gap-2">
            <input className={inp} type="date" value={rp.period_start} onChange={(e) => setRp({ ...rp, period_start: e.target.value })} />
            <input className={inp} type="date" value={rp.period_end} onChange={(e) => setRp({ ...rp, period_end: e.target.value })} />
            <input className={inp} type="number" step="0.01" placeholder={t("bank.statementBalance")} value={rp.statement_closing_balance} onChange={(e) => setRp({ ...rp, statement_closing_balance: e.target.value })} />
            <button onClick={startRecon} className="cy-btn cy-btn-ghost !py-2 !px-3 text-sm">{t("bank.period")}</button>
            {session && <>
              <button onClick={autoMatch} className="cy-btn cy-btn-ghost !py-2 !px-3 text-sm"><Wand2 className="w-4 h-4" /> {t("bank.autoMatch")}</button>
              <button onClick={completeRecon} className="cy-btn cy-btn-primary !py-2 !px-3 text-sm"><CheckCircle2 className="w-4 h-4" /> {t("bank.complete")}</button>
              <span className="text-sm ms-auto">
                {t("bank.bookBalance")} {money(session.book_balance)} · {t("bank.statementBalance")} {money(session.statement_closing_balance)} ·
                <span className={Number(session.difference) === 0 ? " text-green-400" : " text-amber-400"}> {t("bank.difference")} {money(session.difference)}</span>
              </span>
            </>}
          </div>

          <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] overflow-x-auto">
            <table className="w-full">
              <thead><tr><th className={th}>{t("common.date")}</th><th className={th}>{t("accounting.description")}</th><th className={`${th} text-end`}>{t("bank.amount")}</th><th className={th}>{t("bank.matched")}</th><th className={th}></th></tr></thead>
              <tbody>
                {lines.map((l) => (
                  <tr key={l.id}>
                    <td className={td}>{l.txn_date}</td><td className={td}>{l.description}{l.match_note ? ` · ${l.match_note}` : ""}</td>
                    <td className={`${td} text-end tabular-nums ${Number(l.amount) < 0 ? "text-red-300" : "text-green-300"}`}>{money(l.amount)}</td>
                    <td className={td}>{l.reconciled ? <span className="text-green-400 text-xs">{t("bank.matched")}</span> : <span className="text-[var(--color-ink-muted)] text-xs">{t("bank.unmatched")}</span>}</td>
                    <td className={td}><button onClick={() => toggleMatch(l)} className="text-brand-blue text-xs">{l.matched ? <><Link2Off className="w-3 h-3 inline" /> {t("bank.unmatched")}</> : <><Link2 className="w-3 h-3 inline" /> {t("bank.matched")}</>}</button></td>
                  </tr>
                ))}
                {!lines.length && <tr><td className={td} colSpan={5}>{t("bank.noLines")}</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
