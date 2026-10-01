'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, FileCheck2, Loader2, CheckCircle2, AlertTriangle, Send, KeyRound, Globe2 } from 'lucide-react';
import { useT } from '@/lib/i18n';
import { LoadingCard } from '@/components/CycomEmptyStates';
import { EInvoiceFieldInput, EInvoiceFieldSpec, useModeLabel } from '@/components/EInvoiceFields';
import { formatApiErrors } from '@/lib/apiErrors';

interface ProfilePayload {
  country_code: string;
  mode: string | null;
  mode_label: string | null;
  is_national: boolean;
  fields: EInvoiceFieldSpec[];
  values: Record<string, string>;
  fallbacks: Record<string, string>;
  transport_configured: boolean;
  signing_supported: boolean;
  signing_configured: boolean;
}

function StatusPill({ ok, okLabel, offLabel }: { ok: boolean; okLabel: string; offLabel: string }) {
  return (
    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
      ok ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
    }`}>
      {ok ? okLabel : offLabel}
    </span>
  );
}

export default function EInvoicingSettingsPage() {
  const t = useT();
  const modeLabel = useModeLabel();
  const router = useRouter();
  const [data, setData] = useState<ProfilePayload | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [errors, setErrors] = useState<{ key?: string; message: string }[] | null>(null);

  useEffect(() => {
    fetch('/api/cycom/rest/ar-ap/einvoice-profile/', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((d: ProfilePayload | null) => {
        setData(d);
        if (d) setValues(Object.fromEntries(Object.entries(d.values).map(([k, v]) => [k, v ?? ''])));
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setErrors(null);
    try {
      const resp = await fetch('/api/cycom/rest/ar-ap/einvoice-profile/', {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ values }),
      });
      const body = await resp.json().catch(() => null);
      if (resp.ok && body) {
        setData(body);
        setSaved(true);
      } else if (body?.errors) {
        setErrors(body.errors);
      } else {
        setErrors(formatApiErrors(body).map((m) => ({ message: m })));
      }
    } finally {
      setSaving(false);
    }
  };

  const errorKeys = new Set((errors || []).map((e) => e.key).filter(Boolean));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex items-center gap-4 mb-8">
        <button onClick={() => router.push('/settings')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <FileCheck2 className="w-6 h-6 text-cyan-400" /> {t('einvoicing.title')}
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('einvoicing.subtitle')}</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto space-y-6">
        {loading ? (
          <LoadingCard label={t('einvoicing.loading')} />
        ) : !data ? (
          <div className="glass-card p-8 text-center text-slate-400">{t('einvoicing.loadFailed')}</div>
        ) : (
          <>
            <div className="glass-card p-5 grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1"><Globe2 className="w-3 h-3" /> {t('einvoicing.format')}</p>
                <p className="text-slate-200 font-semibold mt-1">{data.mode ? modeLabel(data.mode, data.mode_label) : t('einvoicing.noMandate')}</p>
                <p className="text-[10px] text-slate-500">{t('einvoicing.countryLine', { country: data.country_code || '—' })}</p>
              </div>
              {data.is_national && (
                <>
                  <div>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1"><Send className="w-3 h-3" /> {t('einvoicing.transmission')}</p>
                    <div className="mt-1.5"><StatusPill ok={data.transport_configured} okLabel={t('einvoicing.connected')} offLabel={t('einvoicing.manualFiling')} /></div>
                  </div>
                  {data.signing_supported && (
                    <div>
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1"><KeyRound className="w-3 h-3" /> {t('einvoicing.signing')}</p>
                      <div className="mt-1.5"><StatusPill ok={data.signing_configured} okLabel={t('einvoicing.certInstalled')} offLabel={t('einvoicing.noCert')} /></div>
                    </div>
                  )}
                </>
              )}
            </div>

            {data.is_national && !data.transport_configured && (
              <div className="flex items-start gap-2 p-3 rounded-lg border bg-amber-950/30 border-amber-500/20 text-amber-300 text-[11px]">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" /> {t('einvoicing.manualFilingNote')}
              </div>
            )}

            {!data.is_national ? (
              <div className="glass-card p-6 text-slate-400">{t('einvoicing.notNational')}</div>
            ) : (
              <div className="glass-card p-6 space-y-5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 pb-3">{t('einvoicing.sellerHeading')}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {data.fields.map((spec) => (
                    <div key={spec.key}>
                      <EInvoiceFieldInput
                        spec={spec}
                        mode={data.mode}
                        value={values[spec.key] || ''}
                        onChange={(v) => setValues((prev) => ({ ...prev, [spec.key]: v }))}
                        invalid={errorKeys.has(spec.key)}
                      />
                      {!values[spec.key] && data.fallbacks[spec.key] && (
                        <p className="text-[10px] text-slate-500 mt-0.5">{t('einvoicing.fallback', { value: data.fallbacks[spec.key] })}</p>
                      )}
                    </div>
                  ))}
                </div>

                {errors && (
                  <div className="flex items-start gap-2 p-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400 text-[11px]">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <div>{errors.map((e, i) => <p key={i}>{e.key ? `${e.key}: ` : ''}{e.message}</p>)}</div>
                  </div>
                )}

                <div className="flex items-center justify-end gap-3">
                  {saved && <span className="flex items-center gap-1 text-emerald-400 text-[11px]"><CheckCircle2 className="w-3.5 h-3.5" /> {t('einvoicing.saved')}</span>}
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-white font-semibold transition text-xs"
                  >
                    {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                    {t('einvoicing.save')}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
