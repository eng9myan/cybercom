'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, FileArchive, Loader2, Download, AlertTriangle, CheckCircle2, Save, Search } from 'lucide-react';
import { useT } from '@/lib/i18n';
import { LoadingCard } from '@/components/CycomEmptyStates';
import { formatApiErrors } from '@/lib/apiErrors';

interface AccountRow { id: string; code: string; name: string; account_type: string; grouping_category: string; grouping_code: string }
interface Grouping { category: string; codes: { code: string; description: string }[] }
interface CodeOpt { code: string; description: string }
interface SettingsPayload {
  accounts: AccountRow[];
  grouping: Grouping[];
  settings: Record<string, string>;
  sales_zero_codes: CodeOpt[];
  purchase_zero_codes: CodeOpt[];
}
interface Problem { scope: string; key: string; label: string; message: string }

const inputCls = 'w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none text-xs';

export default function SaftPage() {
  const t = useT();
  const router = useRouter();
  const year = new Date().getFullYear();
  const [data, setData] = useState<SettingsPayload | null>(null);
  const [mapping, setMapping] = useState<Record<string, { grouping_category: string; grouping_code: string }>>({});
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [dateFrom, setDateFrom] = useState(`${year}-01-01`);
  const [dateTo, setDateTo] = useState(`${year}-12-31`);
  const [search, setSearch] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{ ok: boolean; lines: string[] } | null>(null);
  const [exporting, setExporting] = useState(false);
  const [problems, setProblems] = useState<Problem[] | null>(null);
  const [exportError, setExportError] = useState<string[] | null>(null);
  const [exported, setExported] = useState(false);

  const adopt = (d: SettingsPayload) => {
    setData(d);
    setMapping(Object.fromEntries(d.accounts.map((a) => [a.id, { grouping_category: a.grouping_category, grouping_code: a.grouping_code }])));
    setSettings({ ...d.settings });
  };

  useEffect(() => {
    fetch('/api/cycom/rest/accounting/saft/settings/', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && adopt(d));
  }, []);

  const codesByCategory = useMemo(
    () => Object.fromEntries((data?.grouping || []).map((g) => [g.category, g.codes])),
    [data],
  );

  const handleSave = async () => {
    if (!data) return;
    setSaving(true);
    setSaveMsg(null);
    const changed = Object.fromEntries(
      data.accounts
        .filter((a) => mapping[a.id].grouping_category !== a.grouping_category || mapping[a.id].grouping_code !== a.grouping_code)
        .map((a) => [a.id, mapping[a.id]]),
    );
    try {
      const resp = await fetch('/api/cycom/rest/accounting/saft/settings/', {
        method: 'PATCH', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accounts: changed, settings }),
      });
      const body = await resp.json().catch(() => null);
      if (resp.ok && body) {
        adopt(body);
        setSaveMsg({ ok: true, lines: [t('saft.saved')] });
      } else {
        setSaveMsg({ ok: false, lines: body?.errors ? body.errors.map((e: { key: string; message: string }) => `${e.key}: ${e.message}`) : formatApiErrors(body) });
      }
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    setProblems(null);
    setExportError(null);
    setExported(false);
    try {
      const resp = await fetch(`/api/cycom/rest/accounting/saft/export/?date_from=${dateFrom}&date_to=${dateTo}`, { credentials: 'include' });
      const type = resp.headers.get('content-type') || '';
      if (resp.ok && type.includes('xml')) {
        const blob = await resp.blob();
        const disposition = resp.headers.get('content-disposition') || '';
        const name = /filename="([^"]+)"/.exec(disposition)?.[1] || `SAF-T_${dateFrom}_${dateTo}.xml`;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = name;
        a.click();
        URL.revokeObjectURL(url);
        setExported(true);
      } else {
        const body = await resp.json().catch(() => null);
        if (body?.problems) setProblems(body.problems);
        else setExportError(formatApiErrors(body).length ? formatApiErrors(body) : [String(resp.status)]);
      }
    } finally {
      setExporting(false);
    }
  };

  const q = search.trim().toLowerCase();
  const accounts = (data?.accounts || []).filter((a) => !q || a.code.toLowerCase().includes(q) || a.name.toLowerCase().includes(q));
  const unmapped = (data?.accounts || []).filter((a) => !mapping[a.id]?.grouping_code).length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8 text-xs md:text-sm">
      <div className="max-w-5xl mx-auto flex items-center gap-4 mb-8">
        <button onClick={() => router.push('/accounting')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <FileArchive className="w-6 h-6 text-cyan-400" /> {t('saft.title')}
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('saft.subtitle')}</p>
        </div>
      </div>

      {!data ? (
        <div className="max-w-5xl mx-auto"><LoadingCard label={t('saft.loading')} /></div>
      ) : (
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="glass-card p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">{t('saft.exportHeading')}</h3>
            <div className="flex flex-wrap items-end gap-3">
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('saft.from')}</label>
                <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className={`${inputCls} mt-0.5`} />
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('saft.to')}</label>
                <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className={`${inputCls} mt-0.5`} />
              </div>
              <button onClick={handleExport} disabled={exporting}
                className="flex items-center gap-2 px-5 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded-lg text-white font-semibold transition text-xs">
                {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} {t('saft.generate')}
              </button>
            </div>
            {exported && <p className="flex items-center gap-1.5 text-emerald-400 text-[11px]"><CheckCircle2 className="w-3.5 h-3.5" /> {t('saft.exported')}</p>}
            {problems && (
              <div className="p-3 rounded-lg border bg-amber-950/30 border-amber-500/20 text-amber-300 text-[11px] space-y-1">
                <p className="font-semibold flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> {t('saft.problemsHeading')}</p>
                <ul className="list-disc ps-5">{problems.map((p, i) => <li key={i}><span className="text-amber-200">{p.label}</span> — {p.message}</li>)}</ul>
              </div>
            )}
            {exportError && (
              <div className="p-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400 text-[11px]">{exportError.map((e, i) => <p key={i}>{e}</p>)}</div>
            )}
          </div>

          <div className="glass-card p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">{t('saft.settingsHeading')}</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {(['saft_contact_first_name', 'saft_contact_last_name', 'saft_contact_phone'] as const).map((k) => (
                <div key={k}>
                  <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t(`saft.${k}`)}</label>
                  <input value={settings[k] || ''} onChange={(e) => setSettings((s) => ({ ...s, [k]: e.target.value }))} className={`${inputCls} mt-0.5`} />
                </div>
              ))}
              {([['saft_sales_zero_code', data.sales_zero_codes], ['saft_purchase_zero_code', data.purchase_zero_codes]] as const).map(([k, opts]) => (
                <div key={k} className="sm:col-span-3 md:col-span-1">
                  <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t(`saft.${k}`)}</label>
                  <select value={settings[k] || ''} onChange={(e) => setSettings((s) => ({ ...s, [k]: e.target.value }))} className={`${inputCls} mt-0.5`}>
                    <option value="">{t('saft.none')}</option>
                    {opts.map((o) => <option key={o.code} value={o.code}>{o.code} — {o.description}</option>)}
                  </select>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-slate-500">{t('saft.companyNote')}</p>
          </div>

          <div className="glass-card p-5 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                {t('saft.mappingHeading')} <span className="normal-case font-normal text-slate-500">· {t('saft.unmapped', { n: unmapped })}</span>
              </h3>
              <div className="relative w-full sm:w-64">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute start-3 top-1/2 -translate-y-1/2" />
                <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t('saft.search')} className={`${inputCls} ps-8`} />
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-xs">
                <thead>
                  <tr className="bg-slate-950 text-slate-500 uppercase border-b border-slate-850">
                    <th className="p-2 text-start font-bold">{t('saft.colAccount')}</th>
                    <th className="p-2 text-start font-bold">{t('saft.colCategory')}</th>
                    <th className="p-2 text-start font-bold">{t('saft.colCode')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {accounts.map((a) => {
                    const m = mapping[a.id];
                    return (
                      <tr key={a.id}>
                        <td className="p-2 text-slate-200"><span className="font-mono text-slate-400">{a.code}</span> {a.name}</td>
                        <td className="p-2">
                          <select value={m.grouping_category} className={inputCls}
                            onChange={(e) => setMapping((mp) => ({ ...mp, [a.id]: { grouping_category: e.target.value, grouping_code: '' } }))}>
                            <option value="">{t('saft.none')}</option>
                            {data.grouping.map((g) => <option key={g.category} value={g.category}>{g.category}</option>)}
                          </select>
                        </td>
                        <td className="p-2">
                          <select value={m.grouping_code} disabled={!m.grouping_category} className={`${inputCls} disabled:opacity-40`}
                            onChange={(e) => setMapping((mp) => ({ ...mp, [a.id]: { ...mp[a.id], grouping_code: e.target.value } }))}>
                            <option value="">{t('saft.none')}</option>
                            {(codesByCategory[m.grouping_category] || []).map((c) => <option key={c.code} value={c.code}>{c.code} — {c.description}</option>)}
                          </select>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {saveMsg && (
              <div className={`p-3 rounded-lg border text-[11px] ${saveMsg.ok ? 'bg-emerald-950/30 border-emerald-500/20 text-emerald-400' : 'bg-rose-950/40 border-rose-500/20 text-rose-400'}`}>
                {saveMsg.lines.map((l, i) => <p key={i}>{l}</p>)}
              </div>
            )}
            <div className="flex justify-end">
              <button onClick={handleSave} disabled={saving}
                className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-white font-semibold transition text-xs">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} {t('saft.save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
