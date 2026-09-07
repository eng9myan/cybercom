"use client";

import { useState, useEffect, useCallback } from "react";
import { apiFetch, openAuthed } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { FileText, Plus, RefreshCw, Send, FileCode, QrCode } from "lucide-react";

const money = (v) => Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 });
const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

export default function EInvoicingPage() {
  const { t } = useT();
  const [tab, setTab] = useState("invoices");
  const [invoices, setInvoices] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [profile, setProfile] = useState(null);
  const [detail, setDetail] = useState(null);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try {
      const [inv, co, pr] = await Promise.all([
        apiFetch("/api/v1/einvoicing/invoices/"),
        apiFetch("/api/v1/tenants/companies/"),
        apiFetch("/api/v1/einvoicing/tax-profiles/").catch(() => []),
      ]);
      setInvoices(asList(inv)); setCompanies(asList(co));
      setProfile(asList(pr)[0] || null);
    } catch (e) { setErr(e.message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const [nv, setNv] = useState({ number: "", company: "", invoice_type: "simplified", customer_name: "", customer_tax_number: "", issue_date: "", currency: "SAR" });
  const [lines, setLines] = useState([{ description: "", quantity: 1, unit_price: "", tax_rate: 0.15 }]);
  const setLn = (i, k, v) => setLines((L) => L.map((l, j) => (j === i ? { ...l, [k]: v } : l)));

  const create = async (e) => {
    e.preventDefault(); setErr("");
    try {
      const body = { ...nv, number: nv.number || `INV-${Date.now()}`, lines: lines.filter((l) => l.description && l.unit_price) };
      const inv = await apiFetch("/api/v1/einvoicing/invoices/", { method: "POST", body: JSON.stringify(body) });
      const r = await apiFetch(`/api/v1/einvoicing/invoices/${inv.id}/issue/`, { method: "POST" });
      setDetail(r.einvoice);
      setNv({ ...nv, number: "", customer_name: "" });
      setLines([{ description: "", quantity: 1, unit_price: "", tax_rate: 0.15 }]);
      load();
    } catch (e) { setErr(e.message); }
  };
  const issue = async (id) => { try { const r = await apiFetch(`/api/v1/einvoicing/invoices/${id}/issue/`, { method: "POST" }); setDetail(r.einvoice); load(); } catch (e) { setErr(e.message); } };
  const sign = async (id) => { try { setDetail(await apiFetch(`/api/v1/einvoicing/invoices/${id}/sign/`, { method: "POST" })); load(); } catch (e) { setErr(e.message); } };
  const submit = async (id) => { try { setDetail(await apiFetch(`/api/v1/einvoicing/invoices/${id}/submit/`, { method: "POST" })); load(); } catch (e) { setErr(e.message); } };

  const [pf, setPf] = useState({ company: "", scheme: "none", legal_name: "", legal_name_ar: "", vat_number: "", country_code: "SA" });
  useEffect(() => { if (profile) setPf({ ...pf, ...profile }); /* eslint-disable-next-line */ }, [profile]);
  const saveProfile = async (e) => {
    e.preventDefault(); setErr("");
    try {
      if (profile?.id) await apiFetch(`/api/v1/einvoicing/tax-profiles/${profile.id}/`, { method: "PATCH", body: JSON.stringify(pf) });
      else await apiFetch("/api/v1/einvoicing/tax-profiles/", { method: "POST", body: JSON.stringify(pf) });
      load();
    } catch (e) { setErr(e.message); }
  };

  const inp = "cy-input h-9 text-sm";
  const th = "text-start px-3 py-2 text-[11px] uppercase tracking-wide text-[var(--color-ink-muted)] font-semibold";
  const td = "px-3 py-2 text-sm border-t border-[var(--color-line)]";

  return (
    <div className="p-4 md:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3"><FileText className="w-6 h-6 text-brand-orange" /><h1 className="text-xl font-heading font-bold">{t("einv.title")}</h1></div>
        <button onClick={load} className="cy-btn cy-btn-ghost !py-1.5 !px-3 text-sm"><RefreshCw className="w-3.5 h-3.5" /> {t("common.refresh")}</button>
      </div>
      {err && <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300">{err}</div>}

      <div className="flex gap-1 border-b border-[var(--color-line)]">
        {[["invoices", t("einv.tabs.invoices")], ["profile", t("einv.tabs.profile")]].map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)} className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px ${tab === k ? "border-brand-orange text-[var(--color-ink)]" : "border-transparent text-[var(--color-ink-muted)]"}`}>{l}</button>
        ))}
      </div>

      {tab === "invoices" && (
        <div className="space-y-4">
          <form onSubmit={create} className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-4 space-y-3">
            <div className="flex flex-wrap gap-2">
              <select className={inp} value={nv.company} onChange={(e) => setNv({ ...nv, company: e.target.value })} required>
                <option value="">— company —</option>{companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <select className={inp} value={nv.invoice_type} onChange={(e) => setNv({ ...nv, invoice_type: e.target.value })}>
                <option value="simplified">Simplified (B2C)</option><option value="standard">Standard (B2B)</option>
              </select>
              <input className={inp} type="date" value={nv.issue_date} onChange={(e) => setNv({ ...nv, issue_date: e.target.value })} required />
              <input className={inp} placeholder={t("einv.customer")} value={nv.customer_name} onChange={(e) => setNv({ ...nv, customer_name: e.target.value })} required />
              <input className={inp} placeholder="Customer VAT #" value={nv.customer_tax_number} onChange={(e) => setNv({ ...nv, customer_tax_number: e.target.value })} />
              <input className={`${inp} w-24`} value={nv.currency} onChange={(e) => setNv({ ...nv, currency: e.target.value })} />
            </div>
            {lines.map((l, i) => (
              <div key={i} className="flex flex-wrap gap-2">
                <input className={`${inp} flex-1`} placeholder={t("accounting.description")} value={l.description} onChange={(e) => setLn(i, "description", e.target.value)} />
                <input className={`${inp} w-24`} type="number" step="0.01" min="0" placeholder="Qty" value={l.quantity} onChange={(e) => setLn(i, "quantity", e.target.value)} />
                <input className={`${inp} w-28`} type="number" step="0.01" min="0" placeholder="Unit price" value={l.unit_price} onChange={(e) => setLn(i, "unit_price", e.target.value)} />
                <input className={`${inp} w-24`} type="number" step="0.01" min="0" max="1" placeholder="VAT" value={l.tax_rate} onChange={(e) => setLn(i, "tax_rate", e.target.value)} />
              </div>
            ))}
            <div className="flex gap-3 items-center">
              <button type="button" className="text-brand-blue text-sm" onClick={() => setLines([...lines, { description: "", quantity: 1, unit_price: "", tax_rate: 0.15 }])}>+ {t("accounting.line")}</button>
              <button className="cy-btn cy-btn-primary !py-2 !px-3 text-sm ms-auto"><Plus className="w-4 h-4" /> {t("einv.issue")}</button>
            </div>
          </form>

          {detail && (
            <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-4 text-sm space-y-2">
              <div className="flex gap-6 flex-wrap">
                <span><span className="text-[var(--color-ink-muted)]">{t("einv.scheme")}:</span> {detail.scheme}</span>
                <span><span className="text-[var(--color-ink-muted)]">{t("common.status")}:</span> <span className="cy-pill cy-pill-orange text-xs">{detail.status}</span></span>
                <span className="font-mono text-xs"><span className="text-[var(--color-ink-muted)]">{t("einv.hash")}:</span> {(detail.invoice_hash || "").slice(0, 24)}…</span>
              </div>
              <div className="flex items-start gap-2"><QrCode className="w-4 h-4 mt-0.5 text-[var(--color-ink-muted)]" /><span className="font-mono text-[11px] break-all">{detail.qr_code}</span></div>
              {detail.warnings?.length > 0 && <ul className="text-amber-400 text-xs list-disc ps-5">{detail.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>}
            </div>
          )}

          <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] overflow-x-auto">
            <table className="w-full">
              <thead><tr><th className={th}>{t("einv.number")}</th><th className={th}>{t("einv.customer")}</th><th className={th}>{t("einv.type")}</th><th className={th}>{t("einv.issueDate")}</th><th className={`${th} text-end`}>{t("einv.subtotal")}</th><th className={`${th} text-end`}>{t("einv.vat")}</th><th className={`${th} text-end`}>{t("common.total")}</th><th className={th}>{t("einv.scheme")}</th><th className={th}></th></tr></thead>
              <tbody>
                {invoices.map((iv) => (
                  <tr key={iv.id}>
                    <td className={td}>{iv.number}</td><td className={td}>{iv.customer_name}</td><td className={td}>{iv.invoice_type}</td><td className={td}>{iv.issue_date}</td>
                    <td className={`${td} text-end tabular-nums`}>{money(iv.subtotal)}</td><td className={`${td} text-end tabular-nums`}>{money(iv.tax_total)}</td>
                    <td className={`${td} text-end tabular-nums font-semibold`}>{money(iv.total)} {iv.currency}</td>
                    <td className={td}>{iv.einvoice ? <span className="cy-pill text-xs">{iv.einvoice.scheme}/{iv.einvoice.status}</span> : "—"}</td>
                    <td className={`${td} whitespace-nowrap`}>
                      <button onClick={() => issue(iv.id)} className="text-brand-blue text-xs font-semibold">{t("einv.issue")}</button>{" · "}
                      <button onClick={() => sign(iv.id)} className="text-brand-blue text-xs font-semibold">{t("einv.sign")}</button>{" · "}
                      <button onClick={() => submit(iv.id)} className="text-green-400 text-xs font-semibold"><Send className="w-3 h-3 inline" /> {t("einv.submit")}</button>{" · "}
                      <a href={`${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/einvoicing/invoices/${iv.id}/xml/`} target="_blank" rel="noreferrer" className="text-[var(--color-ink-muted)] text-xs"><FileCode className="w-3 h-3 inline" /> XML</a>{" · "}
                      <button type="button" onClick={() => openAuthed(`/api/v1/einvoicing/invoices/${iv.id}/print/`)} className="text-[var(--color-ink-muted)] text-xs">Print / PDF</button>
                    </td>
                  </tr>
                ))}
                {!invoices.length && <tr><td className={td} colSpan={9}>{t("einv.noInvoices")}</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "profile" && (
        <form onSubmit={saveProfile} className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-5 space-y-3 max-w-xl">
          <select className={inp} value={pf.company} onChange={(e) => setPf({ ...pf, company: e.target.value })} required>
            <option value="">— company —</option>{companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select className={inp} value={pf.scheme} onChange={(e) => setPf({ ...pf, scheme: e.target.value })}>
            <option value="none">None</option><option value="zatca">ZATCA (Saudi Arabia)</option><option value="jofotara">JoFotara (Jordan)</option>
          </select>
          <input className={inp} placeholder={t("einv.legalName")} value={pf.legal_name} onChange={(e) => setPf({ ...pf, legal_name: e.target.value })} required />
          <input className={inp} placeholder={t("einv.legalNameAr")} value={pf.legal_name_ar} onChange={(e) => setPf({ ...pf, legal_name_ar: e.target.value })} />
          <input className={inp} placeholder={t("einv.sellerVat")} value={pf.vat_number} onChange={(e) => setPf({ ...pf, vat_number: e.target.value })} />
          <input className={`${inp} w-24`} placeholder="Country" value={pf.country_code} onChange={(e) => setPf({ ...pf, country_code: e.target.value })} />
          {pf.scheme !== "none" && (
            <div className="space-y-2 border-t border-[var(--color-line)] pt-3">
              <p className="text-xs text-[var(--color-ink-muted)]">{t("einv.csidHint")}</p>
              <textarea className={`${inp} h-24 font-mono text-xs`} placeholder="-----BEGIN CERTIFICATE----- (CSID)" value={pf.certificate_pem || ""} onChange={(e) => setPf({ ...pf, certificate_pem: e.target.value })} />
              <textarea className={`${inp} h-24 font-mono text-xs`} placeholder="-----BEGIN PRIVATE KEY-----" value={pf.private_key_pem || ""} onChange={(e) => setPf({ ...pf, private_key_pem: e.target.value })} />
            </div>
          )}
          <button className="cy-btn cy-btn-primary !py-2 !px-3 text-sm">{t("einv.saveProfile")}</button>
        </form>
      )}
    </div>
  );
}
