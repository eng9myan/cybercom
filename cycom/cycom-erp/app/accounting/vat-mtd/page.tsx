'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Landmark, Loader2, Link2, Unlink, RefreshCw, Send, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useT } from '@/lib/i18n';
import { LoadingCard } from '@/components/CycomEmptyStates';
import { formatApiErrors } from '@/lib/apiErrors';

interface Status { configured: boolean; sandbox: boolean; connected: boolean; vrn: string; connected_at: string | null }
interface Obligation { periodKey: string; start: string; end: string; due: string; status: 'O' | 'F'; received?: string; filed_here: boolean }
interface Preview { boxes: Record<string, string | number | boolean>; notes: string[]; invoice_counts: { sales: number; purchases: number } }
interface Submission { id: string; period_key: string; date_from: string; date_to: string; receipt: Record<string, string>; submitted_by: string; submitted_at: string }

const BOXES = ['box1', 'box2', 'box3', 'box4', 'box5', 'box6', 'box7', 'box8', 'box9'];
const inputCls = 'bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none text-xs';

/** Fraud-prevention data HMRC requires for WEB_APP_VIA_SERVER, read from
 * this browser. The device id is a random id persisted per browser. */
function browserFraudData() {
  let deviceId = '';
  try {
    deviceId = localStorage.getItem('cycom.hmrc.device_id') || '';
    if (!deviceId) {
      deviceId = crypto.randomUUID();
      localStorage.setItem('cycom.hmrc.device_id', deviceId);
    }
  } catch {
    deviceId = crypto.randomUUID();
  }
  const off = -new Date().getTimezoneOffset();
  const pad = (n: number) => String(Math.floor(Math.abs(n))).padStart(2, '0');
  return {
    device_id: deviceId,
    user_agent: navigator.userAgent,
    screens: { width: window.screen.width, height: window.screen.height, scaling_factor: window.devicePixelRatio || 1, colour_depth: window.screen.colorDepth },
    window_size: { width: window.innerWidth, height: window.innerHeight },
    timezone: `UTC${off >= 0 ? '+' : '-'}${pad(off / 60)}:${pad(off % 60)}`,
  };
}

async function api(path: string, init?: RequestInit) {
  const resp = await fetch(`/api/cycom/rest/accounting/mtd/${path}`, {
    credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...init,
  });
  const body = await resp.json().catch(() => null);
  return { ok: resp.ok, status: resp.status, body };
}

export default function VatMtdPage() {
  const t = useT();
  const router = useRouter();
  const [status, setStatus] = useState<Status | null>(null);
  const [vrn, setVrn] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string[] | null>(null);
  const [obligations, setObligations] = useState<Obligation[] | null>(null);
  const [selected, setSelected] = useState<Obligation | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [declared, setDeclared] = useState(false);
  const [receipt, setReceipt] = useState<Submission | null>(null);
  const [history, setHistory] = useState<Submission[]>([]);

  const fail = (body: unknown, fallback: number) => {
    const b = body as { problems?: { label: string; message: string }[] } | null;
    setError(b?.problems ? b.problems.map((p) => `${p.label}: ${p.message}`) : (formatApiErrors(body).length ? formatApiErrors(body) : [String(fallback)]));
  };

  const loadStatus = useCallback(async () => {
    const r = await api('status/');
    if (r.ok) setStatus(r.body);
    const h = await api('submissions/');
    if (h.ok) setHistory(h.body);
  }, []);

  // HMRC redirects back here with ?code&state after the user grants access.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    (async () => {
      if (code && state) {
        setBusy('connect');
        const r = await api('callback/', { method: 'POST', body: JSON.stringify({ code, state }) });
        if (!r.ok) fail(r.body, r.status);
        window.history.replaceState(null, '', window.location.pathname);
        setBusy(null);
      } else if (params.get('error')) {
        setError([params.get('error_description') || params.get('error') || 'HMRC authorisation was not granted.']);
      }
      await loadStatus();
    })();
  }, [loadStatus]);

  const connect = async () => {
    setBusy('connect');
    setError(null);
    const r = await api('connect/', { method: 'POST', body: JSON.stringify({ vrn }) });
    if (r.ok && r.body?.authorize_url) window.location.href = r.body.authorize_url;
    else { fail(r.body, r.status); setBusy(null); }
  };

  const disconnect = async () => {
    setBusy('disconnect');
    await api('disconnect/', { method: 'POST', body: '{}' });
    setObligations(null); setSelected(null); setPreview(null);
    await loadStatus();
    setBusy(null);
  };

  const loadObligations = async () => {
    setBusy('obligations');
    setError(null);
    const r = await api('obligations/', { method: 'POST', body: JSON.stringify({ browser: browserFraudData() }) });
    if (r.ok) setObligations(r.body); else fail(r.body, r.status);
    setBusy(null);
  };

  const choose = async (o: Obligation) => {
    setSelected(o); setPreview(null); setDeclared(false); setReceipt(null); setError(null);
    setBusy('preview');
    const r = await api(`preview/?date_from=${o.start}&date_to=${o.end}`);
    if (r.ok) setPreview(r.body); else fail(r.body, r.status);
    setBusy(null);
  };

  const submit = async () => {
    if (!selected) return;
    setBusy('submit');
    setError(null);
    const r = await api('submit/', {
      method: 'POST',
      body: JSON.stringify({ period_key: selected.periodKey, date_from: selected.start, date_to: selected.end, declaration: declared, browser: browserFraudData() }),
    });
    if (r.ok) { setReceipt(r.body); await loadStatus(); await loadObligations(); } else fail(r.body, r.status);
    setBusy(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex items-center gap-4 mb-8">
        <button onClick={() => router.push('/accounting')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Landmark className="w-6 h-6 text-cyan-400" /> {t('vatMtd.title')}
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('vatMtd.subtitle')}</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto space-y-6">
        {error && (
          <div className="flex items-start gap-2 p-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400 text-[11px]">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" /><div>{error.map((e, i) => <p key={i}>{e}</p>)}</div>
          </div>
        )}

        {!status ? <LoadingCard label={t('vatMtd.loading')} /> : !status.configured ? (
          <div className="glass-card p-6 text-slate-400">{t('vatMtd.notConfigured')}</div>
        ) : (
          <div className="glass-card p-5 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">{t('vatMtd.connection')}</h3>
              {status.sandbox && <span className="px-2.5 py-1 rounded-full text-[10px] font-bold border bg-amber-500/10 border-amber-500/30 text-amber-400">{t('vatMtd.sandbox')}</span>}
            </div>
            {status.connected ? (
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-slate-300">{t('vatMtd.connectedAs', { vrn: status.vrn })}</p>
                <div className="flex gap-2">
                  <button onClick={loadObligations} disabled={busy !== null} className="flex items-center gap-1.5 px-3 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white text-xs font-semibold disabled:opacity-50">
                    {busy === 'obligations' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />} {t('vatMtd.loadObligations')}
                  </button>
                  <button onClick={disconnect} disabled={busy !== null} className="flex items-center gap-1.5 px-3 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg text-xs font-semibold disabled:opacity-50">
                    <Unlink className="w-3.5 h-3.5" /> {t('vatMtd.disconnect')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">{t('vatMtd.vrn')}</label>
                  <input value={vrn} onChange={(e) => setVrn(e.target.value)} dir="ltr" placeholder="123456789" className={`${inputCls} mt-0.5`} />
                </div>
                <button onClick={connect} disabled={busy !== null || !vrn.trim()} className="flex items-center gap-1.5 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white text-xs font-semibold disabled:opacity-50">
                  {busy === 'connect' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Link2 className="w-3.5 h-3.5" />} {t('vatMtd.connect')}
                </button>
              </div>
            )}
          </div>
        )}

        {obligations && (
          <div className="glass-card p-5 space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">{t('vatMtd.obligations')}</h3>
            {obligations.length === 0 ? <p className="text-slate-500">{t('vatMtd.noObligations')}</p> : obligations.map((o) => (
              <button key={o.periodKey} onClick={() => o.status === 'O' && !o.filed_here && choose(o)}
                className={`w-full flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl border text-start transition ${selected?.periodKey === o.periodKey ? 'border-cyan-500/40 bg-cyan-500/5' : 'border-slate-850 hover:bg-white/5'}`}>
                <span className="text-slate-200">{o.start} → {o.end}</span>
                <span className="text-[11px] text-slate-400">{t('vatMtd.due', { date: o.due })}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${o.status === 'F' || o.filed_here ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-amber-500/10 border-amber-500/30 text-amber-400'}`}>
                  {o.status === 'F' || o.filed_here ? t('vatMtd.fulfilled') : t('vatMtd.open')}
                </span>
              </button>
            ))}
          </div>
        )}

        {selected && (busy === 'preview' ? <LoadingCard label={t('vatMtd.computing')} /> : preview && (
          <div className="glass-card p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">{t('vatMtd.returnFor', { from: selected.start, to: selected.end })}</h3>
            <div className="divide-y divide-white/5">
              {BOXES.map((b) => (
                <div key={b} className="flex justify-between gap-4 py-2">
                  <span className="text-slate-400"><span className="font-mono text-slate-500">{b.replace('box', '')}</span> · {t(`vatMtd.${b}`)}</span>
                  <span className="font-mono text-slate-100">£{String(preview.boxes[b])}</span>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-slate-500">{t('vatMtd.sourceNote', { sales: preview.invoice_counts.sales, purchases: preview.invoice_counts.purchases })}</p>
            {preview.notes.length > 0 && <p className="text-[11px] text-amber-300">{t('vatMtd.niNote')}</p>}
            <label className="flex items-start gap-2 p-3 rounded-lg border border-slate-800 text-[11px] text-slate-300 cursor-pointer">
              <input type="checkbox" checked={declared} onChange={(e) => setDeclared(e.target.checked)} className="mt-0.5" />
              <span>{t('vatMtd.declaration')}</span>
            </label>
            <div className="flex justify-end">
              <button onClick={submit} disabled={!declared || busy !== null} className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 rounded-lg text-white font-semibold text-xs">
                {busy === 'submit' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} {t('vatMtd.submit')}
              </button>
            </div>
          </div>
        ))}

        {receipt && (
          <div className="glass-card p-5 space-y-1 border border-emerald-500/20">
            <p className="flex items-center gap-2 text-emerald-400 font-semibold"><CheckCircle2 className="w-4 h-4" /> {t('vatMtd.filed')}</p>
            <p className="text-[11px] text-slate-400">{t('vatMtd.formBundle')}: <span className="font-mono text-slate-200">{receipt.receipt.formBundleNumber}</span></p>
            <p className="text-[11px] text-slate-400">{t('vatMtd.processingDate')}: <span className="font-mono text-slate-200">{receipt.receipt.processingDate}</span></p>
          </div>
        )}

        {history.length > 0 && (
          <div className="glass-card p-5 space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">{t('vatMtd.history')}</h3>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[520px] text-xs">
                <thead><tr className="text-slate-500 uppercase border-b border-slate-850">
                  <th className="p-2 text-start">{t('vatMtd.colPeriod')}</th><th className="p-2 text-start">{t('vatMtd.formBundle')}</th>
                  <th className="p-2 text-start">{t('vatMtd.colBy')}</th><th className="p-2 text-start">{t('vatMtd.colWhen')}</th>
                </tr></thead>
                <tbody className="divide-y divide-white/5">
                  {history.map((s) => (
                    <tr key={s.id}>
                      <td className="p-2 text-slate-200">{s.date_from} → {s.date_to}</td>
                      <td className="p-2 font-mono text-slate-300">{s.receipt.formBundleNumber}</td>
                      <td className="p-2 text-slate-400">{s.submitted_by}</td>
                      <td className="p-2 text-slate-400">{new Date(s.submitted_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
