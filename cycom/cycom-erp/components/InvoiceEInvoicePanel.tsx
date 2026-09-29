'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { FileCheck2, Loader2, AlertTriangle, CheckCircle2, Download, RefreshCw, Save, Send } from 'lucide-react';
import { useT } from '@/lib/i18n';
import { EInvoiceFieldInput, EInvoiceFieldSpec } from '@/components/EInvoiceFields';
import { formatApiErrors } from '@/lib/apiErrors';

interface Problem { scope: string; key: string; label: string; message: string }
interface EInvoiceState {
  mode: string | null;
  mode_label: string | null;
  is_national: boolean;
  status: string;
  reference: string;
  response: { problems?: Problem[]; error?: string; note?: string };
  has_document: boolean;
  document_filename: string;
  buyer_fields: EInvoiceFieldSpec[];
  line_fields: EInvoiceFieldSpec[];
  document_fields: EInvoiceFieldSpec[];
  buyer_values: Record<string, string>;
  document_values: Record<string, string>;
  lines: { id: string; description: string; tax_percent: string; values: Record<string, string> }[];
}

const TONE: Record<string, string> = {
  cleared: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
  reported: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
  generated: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400',
  incomplete: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
  rejected: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
};

/** Per-invoice national e-invoicing: status, exactly what's missing, the
 * buyer/line fields to fix it, retry, and download of the legal document. */
export default function InvoiceEInvoicePanel({ invoiceId, invoiceStatus }: { invoiceId: string; invoiceStatus: string }) {
  const t = useT();
  const [state, setState] = useState<EInvoiceState | null>(null);
  const [buyer, setBuyer] = useState<Record<string, string>>({});
  const [lineValues, setLineValues] = useState<Record<string, Record<string, string>>>({});
  const [busy, setBusy] = useState<'save' | 'retry' | null>(null);
  const [errors, setErrors] = useState<string[] | null>(null);

  const adopt = (s: EInvoiceState) => {
    setState(s);
    setBuyer(Object.fromEntries(Object.entries(s.buyer_values || {}).map(([k, v]) => [k, v ?? ''])));
    setLineValues(Object.fromEntries(s.lines.map((l) => [l.id, { ...l.values }])));
  };

  const load = useCallback(() => {
    fetch(`/api/cycom/rest/ar-ap/invoices/${invoiceId}/einvoice/`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((s) => s && adopt(s));
  }, [invoiceId]);

  useEffect(load, [load, invoiceStatus]);

  if (!state || (!state.is_national && state.status === 'none')) return null;

  const problems = state.response?.problems || [];
  const problemKeys = new Set(problems.map((p) => `${p.scope.startsWith('line') ? 'line' : p.scope}:${p.key}`));
  const editable = state.is_national && ['none', 'incomplete', 'rejected'].includes(state.status);
  const posted = ['posted', 'partial', 'paid'].includes(invoiceStatus);

  const call = async (kind: 'save' | 'retry'): Promise<boolean> => {
    setBusy(kind);
    setErrors(null);
    try {
      const resp = await fetch(
        `/api/cycom/rest/ar-ap/invoices/${invoiceId}/einvoice/${kind === 'retry' ? 'retry/' : ''}`,
        {
          method: kind === 'retry' ? 'POST' : 'PATCH', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          // Only changed buyer keys: unchanged ones are read live from the
          // partner record and shouldn't be frozen into e-invoice overrides.
          body: kind === 'retry' ? '{}' : JSON.stringify({
            buyer: Object.fromEntries(Object.entries(buyer).filter(([k, v]) => (state?.buyer_values[k] ?? '') !== v)),
            lines: lineValues,
          }),
        },
      );
      const body = await resp.json().catch(() => null);
      if (resp.ok && body) {
        adopt(body);
        return true;
      }
      if (body?.errors) setErrors(body.errors.map((e: { scope: string; key: string; message: string }) => `${e.scope}.${e.key}: ${e.message}`));
      else setErrors(formatApiErrors(body).length ? formatApiErrors(body) : [String(resp.status)]);
      return false;
    } finally {
      setBusy(null);
    }
  };

  const saveThenRetry = async () => {
    if (await call('save')) await call('retry');
  };

  return (
    <div className="glass-card p-6 space-y-4">
      <div className="flex items-center justify-between gap-2 border-b border-white/5 pb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <FileCheck2 className="w-4 h-4 text-cyan-400" /> {t('einvoicing.panelTitle')}
        </h3>
        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${TONE[state.status] || 'bg-slate-800 border-slate-700 text-slate-400'}`}>
          {t(`einvoicing.status.${state.status}`)}
        </span>
      </div>
      <p className="text-[11px] text-slate-400">{state.mode_label || state.mode}</p>
      {state.reference && <p className="text-[11px] text-slate-400">{t('einvoicing.reference')}: <span className="font-mono text-slate-200">{state.reference}</span></p>}

      {state.status === 'incomplete' && (
        <div className="p-3 rounded-lg border bg-amber-950/30 border-amber-500/20 text-amber-300 text-[11px] space-y-1">
          <p className="font-semibold flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> {t('einvoicing.incompleteNote')}</p>
          <ul className="list-disc ps-5">
            {problems.map((p, i) => <li key={i}><span className="text-amber-200">{p.scope} · {p.label}</span> — {p.message}</li>)}
          </ul>
          {problems.some((p) => p.scope === 'seller') && (
            <Link href="/settings/einvoicing" className="inline-block text-cyan-300 hover:text-cyan-200 font-semibold">{t('einvoicing.fixSeller')}</Link>
          )}
        </div>
      )}
      {state.status === 'not_applicable' && state.response?.note && (
        <div className="p-3 rounded-lg border bg-slate-900 border-slate-800 text-slate-400 text-[11px]">{state.response.note}</div>
      )}
      {state.status === 'generated' && (
        <div className="p-3 rounded-lg border bg-cyan-950/30 border-cyan-500/20 text-cyan-300 text-[11px]">{t('einvoicing.generatedNote')}</div>
      )}
      {state.status === 'rejected' && state.response?.error && (
        <div className="p-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400 text-[11px] break-words">{state.response.error}</div>
      )}

      {editable && (state.buyer_fields.length > 0 || state.line_fields.length > 0) && (
        <div className="space-y-4">
          {state.buyer_fields.length > 0 && (
            <div className="space-y-2">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('einvoicing.buyerHeading')}</p>
              <div className="grid grid-cols-1 gap-3">
                {state.buyer_fields.map((spec) => (
                  <EInvoiceFieldInput
                    key={spec.key} spec={spec} value={buyer[spec.key] || ''}
                    invalid={problemKeys.has(`buyer:${spec.key}`)}
                    onChange={(v) => setBuyer((b) => ({ ...b, [spec.key]: v }))}
                  />
                ))}
              </div>
            </div>
          )}
          {state.line_fields.length > 0 && (
            <div className="space-y-2">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('einvoicing.linesHeading')}</p>
              {state.lines.map((line) => (
                <div key={line.id} className="p-2 rounded-lg border border-slate-850 space-y-2">
                  <p className="text-[11px] text-slate-300">{line.description || '—'} <span className="text-slate-500 font-mono">· {Number(line.tax_percent).toFixed(2)}%</span></p>
                  {state.line_fields.map((spec) => (
                    <EInvoiceFieldInput
                      key={spec.key} spec={spec}
                      value={(lineValues[line.id] || {})[spec.key] || ''}
                      invalid={problemKeys.has(`line:${spec.key}`) && !(lineValues[line.id] || {})[spec.key]}
                      onChange={(v) => setLineValues((lv) => ({ ...lv, [line.id]: { ...(lv[line.id] || {}), [spec.key]: v } }))}
                    />
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {errors && (
        <div className="p-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400 text-[11px]">
          {errors.map((e, i) => <p key={i}>{e}</p>)}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {editable && (
          <button onClick={() => call('save')} disabled={busy !== null}
            className="flex items-center gap-1.5 px-3 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition text-xs font-semibold disabled:opacity-50">
            {busy === 'save' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />} {t('einvoicing.saveFields')}
          </button>
        )}
        {editable && posted && (
          <button onClick={saveThenRetry} disabled={busy !== null}
            className="flex items-center gap-1.5 px-3 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white transition text-xs font-semibold disabled:opacity-50">
            {busy === 'retry' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />} {t('einvoicing.saveAndIssue')}
          </button>
        )}
        {state.status === 'generated' && (
          <button onClick={() => call('retry')} disabled={busy !== null}
            className="flex items-center gap-1.5 px-3 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white transition text-xs font-semibold disabled:opacity-50">
            {busy === 'retry' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />} {t('einvoicing.transmit')}
          </button>
        )}
        {state.has_document && (
          <a href={`/api/cycom/rest/ar-ap/invoices/${invoiceId}/einvoice/document/`} download={state.document_filename}
            className="flex items-center gap-1.5 px-3 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition text-xs font-semibold">
            <Download className="w-3.5 h-3.5" /> {t('einvoicing.download')}
          </a>
        )}
        {(state.status === 'cleared' || state.status === 'reported') && (
          <span className="flex items-center gap-1 text-emerald-400 text-[11px]"><CheckCircle2 className="w-3.5 h-3.5" /> {t('einvoicing.accepted')}</span>
        )}
      </div>
    </div>
  );
}
