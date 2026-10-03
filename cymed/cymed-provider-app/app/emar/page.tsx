'use client';

import React, { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Pill, ScanLine, X, Check, Ban, Clock } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type MarRow = {
  id: string;
  medication_order: string;
  patient_id: string;
  admission_id: string;
  status: 'scheduled' | 'given' | 'held' | 'refused' | 'missed';
  scheduled_at: string | null;
  administered_at: string | null;
  administered_by: string;
  witnessed_by: string;
  dose_given: string;
  dose_unit: string;
  route: string;
  site: string;
  reason: string;
  notes: string;
  drug_name: string;
  ordered_dose: string;
  frequency: string;
  is_controlled: boolean;
};

type MedOrder = {
  id: string;
  admission_id: string;
  order_type: string;
  status: string;
  drug_name: string;
  dose: string;
  dose_unit: string;
  route: string;
  frequency: string;
  is_controlled: boolean;
};

type Page<T> = { results: T[]; next: string | null };

async function fetchAll<T>(url: string): Promise<T[]> {
  const all: T[] = [];
  let next: string | null = url;
  while (next) {
    const res = await fetch(next, { credentials: 'include' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const json = (await res.json()) as Page<T>;
    all.push(...json.results);
    next = json.next;
  }
  return all;
}

function formatDateTime(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

const STATUS_BADGE: Record<MarRow['status'], string> = {
  scheduled: 'badge-yellow',
  given: 'badge-green',
  held: 'badge-blue',
  refused: 'badge-red',
  missed: 'badge-red',
};

const GIVABLE_ORDER_STATUSES = new Set(['verified', 'active']);

export default function EmarPage() {
  return (
    <Suspense fallback={null}>
      <EmarPageInner />
    </Suspense>
  );
}

function EmarPageInner() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const admissionId = searchParams.get('admission') || '';

  const [rows, setRows] = useState<MarRow[] | null>(null);
  const [orders, setOrders] = useState<MedOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [adminTarget, setAdminTarget] = useState<MarRow | null>(null);
  const [patientBarcode, setPatientBarcode] = useState('');
  const [medBarcode, setMedBarcode] = useState('');
  const [doseGiven, setDoseGiven] = useState('');
  const [routeGiven, setRouteGiven] = useState('');
  const [siteGiven, setSiteGiven] = useState('');
  const [adminReason, setAdminReason] = useState('');
  const [witness, setWitness] = useState('');
  const [notes, setNotes] = useState('');
  const [adminSaving, setAdminSaving] = useState(false);
  const [adminError, setAdminError] = useState<string | null>(null);

  const [notGivenTarget, setNotGivenTarget] = useState<MarRow | null>(null);
  const [notGivenStatus, setNotGivenStatus] = useState<'held' | 'refused' | 'missed'>('held');
  const [notGivenReason, setNotGivenReason] = useState('');
  const [notGivenError, setNotGivenError] = useState<string | null>(null);
  const [notGivenSaving, setNotGivenSaving] = useState(false);

  const [generating, setGenerating] = useState(false);
  const [genOrderId, setGenOrderId] = useState('');
  const [genHours, setGenHours] = useState(24);
  const [genError, setGenError] = useState<string | null>(null);
  const [genSaving, setGenSaving] = useState(false);

  const load = useCallback(() => {
    if (!admissionId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    fetchAll<MarRow>(`/api/cymed/rest/hospital/nursing/mar/?admission_id=${admissionId}`)
      .then((mar) => setRows(mar))
      .catch((e) => setError(e instanceof Error ? e.message : t('emar.loadFailed')))
      .finally(() => setLoading(false));
    // Best-effort: the order catalog needs the pharmacy.hospital feature tier,
    // which isn't licensed for every tenant — a worklist with no "generate
    // schedule" picker is still useful, so this never blocks the page.
    fetchAll<MedOrder>('/api/cymed/rest/pharmacy/prescriptions/orders/')
      .then((allOrders) => setOrders(allOrders.filter((o) => o.admission_id === admissionId)))
      .catch(() => setOrders([]));
  }, [admissionId, t]);

  useEffect(() => {
    if (!authLoading && user) load();
  }, [authLoading, user, load]);

  const givableOrders = useMemo(() => orders.filter((o) => GIVABLE_ORDER_STATUSES.has(o.status)), [orders]);

  const openAdminister = (row: MarRow) => {
    setAdminTarget(row);
    setPatientBarcode('');
    setMedBarcode('');
    setDoseGiven('');
    setRouteGiven('');
    setSiteGiven('');
    setAdminReason('');
    setWitness('');
    setNotes('');
    setAdminError(null);
  };

  const submitAdminister = async () => {
    if (!adminTarget || !patientBarcode.trim() || !medBarcode.trim()) {
      setAdminError(t('emar.scanValidation'));
      return;
    }
    setAdminSaving(true);
    try {
      const res = await fetch(`/api/cymed/rest/hospital/nursing/mar/${adminTarget.id}/administer/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          patient_barcode: patientBarcode.trim(),
          medication_barcode: medBarcode.trim(),
          dose: doseGiven.trim(),
          route: routeGiven.trim(),
          site: siteGiven.trim(),
          reason: adminReason.trim(),
          witness: witness.trim(),
          notes: notes.trim(),
        }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      setAdminTarget(null);
      load();
    } catch (e) {
      setAdminError(e instanceof Error ? e.message : t('emar.administerFailed'));
    } finally {
      setAdminSaving(false);
    }
  };

  const openNotGiven = (row: MarRow) => {
    setNotGivenTarget(row);
    setNotGivenStatus('held');
    setNotGivenReason('');
    setNotGivenError(null);
  };

  const submitNotGiven = async () => {
    if (!notGivenTarget || !notGivenReason.trim()) {
      setNotGivenError(t('emar.reasonRequired'));
      return;
    }
    setNotGivenSaving(true);
    try {
      const res = await fetch(`/api/cymed/rest/hospital/nursing/mar/${notGivenTarget.id}/not-given/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ status: notGivenStatus, reason: notGivenReason.trim() }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      setNotGivenTarget(null);
      load();
    } catch (e) {
      setNotGivenError(e instanceof Error ? e.message : t('emar.notGivenFailed'));
    } finally {
      setNotGivenSaving(false);
    }
  };

  const submitGenerate = async () => {
    if (!genOrderId) {
      setGenError(t('emar.orderRequired'));
      return;
    }
    setGenSaving(true);
    setGenError(null);
    try {
      const res = await fetch('/api/cymed/rest/hospital/nursing/mar/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ medication_order: genOrderId, hours: genHours }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      setGenerating(false);
      load();
    } catch (e) {
      setGenError(e instanceof Error ? e.message : t('emar.generateFailed'));
    } finally {
      setGenSaving(false);
    }
  };

  if (authLoading) {
    return <LoadingCard label={t('common.loading')} />;
  }

  if (!user) {
    return (
      <div className="glass-card p-10 text-center max-w-md mx-auto mt-16">
        <h2 className="text-lg font-bold mb-2">{t('auth.signInTitle')}</h2>
        <p className="text-sm text-slate-400 mb-5">{t('auth.signInDetail')}</p>
        <a href="/login" className="btn-primary inline-block">{t('auth.signIn')}</a>
      </div>
    );
  }

  if (!admissionId) {
    return <EmptyCard label={t('emar.noAdmission')} />;
  }

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('emar.title')}</h1>
          <p className="page-subtitle">{t('emar.subtitle')}</p>
        </div>
        <button onClick={() => { setGenerating(true); setGenError(null); setGenOrderId(givableOrders[0]?.id || ''); }} className="btn-primary text-xs px-3 py-1.5">
          {t('emar.generateSchedule')}
        </button>
      </div>

      {loading ? (
        <LoadingCard label={t('common.loading')} />
      ) : error ? (
        <ErrorCard error={error} />
      ) : !rows || rows.length === 0 ? (
        <EmptyCard label={t('emar.empty')} />
      ) : (
        <div className="glass-card p-2">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('emar.drug')}</th>
                <th>{t('emar.dose')}</th>
                <th>{t('emar.due')}</th>
                <th>{t('emar.status')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td className="font-semibold text-white">
                    {row.drug_name}
                    {row.is_controlled && <span className="badge badge-red ms-1.5 text-[9px]">{t('emar.controlled')}</span>}
                  </td>
                  <td className="text-xs text-slate-400">{row.ordered_dose} {row.frequency && `· ${row.frequency}`}</td>
                  <td className="text-xs text-slate-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDateTime(row.scheduled_at || row.administered_at)}
                  </td>
                  <td>
                    <span className={`badge ${STATUS_BADGE[row.status]}`}>{row.status}</span>
                  </td>
                  <td>
                    {row.status === 'scheduled' && (
                      <div className="flex items-center gap-1.5">
                        <button onClick={() => openAdminister(row)} className="btn-primary text-xs px-2 py-1 flex items-center gap-1">
                          <ScanLine className="w-3 h-3" />
                          {t('emar.administer')}
                        </button>
                        <button onClick={() => openNotGiven(row)} className="btn-secondary text-xs px-2 py-1 flex items-center gap-1">
                          <Ban className="w-3 h-3" />
                          {t('emar.notGiven')}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {adminTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-md space-y-3 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white flex items-center gap-2">
                <Pill className="w-4 h-4 text-[var(--cy-teal)]" />
                {adminTarget.drug_name}
              </h3>
              <button onClick={() => setAdminTarget(null)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-slate-500">{t('emar.fiveRightsNote')}</p>
            <input type="text" value={patientBarcode} onChange={(e) => setPatientBarcode(e.target.value)} placeholder={t('emar.patientBarcodePlaceholder')} className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500" />
            <input type="text" value={medBarcode} onChange={(e) => setMedBarcode(e.target.value)} placeholder={t('emar.medBarcodePlaceholder')} className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500" />
            <div className="grid grid-cols-3 gap-2">
              <input type="text" value={doseGiven} onChange={(e) => setDoseGiven(e.target.value)} placeholder={t('emar.dosePlaceholder')} className="bg-transparent border border-white/8 rounded-lg px-2 py-2 text-xs text-white placeholder-slate-500" />
              <input type="text" value={routeGiven} onChange={(e) => setRouteGiven(e.target.value)} placeholder={t('emar.routePlaceholder')} className="bg-transparent border border-white/8 rounded-lg px-2 py-2 text-xs text-white placeholder-slate-500" />
              <input type="text" value={siteGiven} onChange={(e) => setSiteGiven(e.target.value)} placeholder={t('emar.sitePlaceholder')} className="bg-transparent border border-white/8 rounded-lg px-2 py-2 text-xs text-white placeholder-slate-500" />
            </div>
            {adminTarget.is_controlled && (
              <input type="text" value={witness} onChange={(e) => setWitness(e.target.value)} placeholder={t('emar.witnessPlaceholder')} className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500" />
            )}
            <input type="text" value={adminReason} onChange={(e) => setAdminReason(e.target.value)} placeholder={t('emar.reasonPlaceholder')} className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500" />
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={t('emar.notesPlaceholder')} rows={2} className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 resize-none" />
            {adminError && <p className="text-xs text-rose-400">{adminError}</p>}
            <div className="flex justify-end gap-2">
              <button onClick={() => setAdminTarget(null)} className="btn-secondary text-xs px-3 py-1.5">{t('common.cancel')}</button>
              <button onClick={submitAdminister} disabled={adminSaving} className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1">
                <Check className="w-3.5 h-3.5" />
                {t('emar.confirmAdminister')}
              </button>
            </div>
          </div>
        </div>
      )}

      {notGivenTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white">{notGivenTarget.drug_name}</h3>
              <button onClick={() => setNotGivenTarget(null)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <select value={notGivenStatus} onChange={(e) => setNotGivenStatus(e.target.value as typeof notGivenStatus)} className="w-full bg-[#0a0f1e] border border-white/8 rounded-lg px-3 py-2 text-xs text-white">
              <option value="held">{t('emar.held')}</option>
              <option value="refused">{t('emar.refused')}</option>
              <option value="missed">{t('emar.missed')}</option>
            </select>
            <textarea value={notGivenReason} onChange={(e) => setNotGivenReason(e.target.value)} placeholder={t('emar.reasonPlaceholder')} rows={3} className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 resize-none" />
            {notGivenError && <p className="text-xs text-rose-400">{notGivenError}</p>}
            <div className="flex justify-end gap-2">
              <button onClick={() => setNotGivenTarget(null)} className="btn-secondary text-xs px-3 py-1.5">{t('common.cancel')}</button>
              <button onClick={submitNotGiven} disabled={notGivenSaving} className="btn-primary text-xs px-3 py-1.5">{t('emar.confirmNotGiven')}</button>
            </div>
          </div>
        </div>
      )}

      {generating && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white">{t('emar.generateSchedule')}</h3>
              <button onClick={() => setGenerating(false)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            {givableOrders.length === 0 ? (
              <p className="text-xs text-slate-500">{t('emar.noGivableOrders')}</p>
            ) : (
              <>
                <select value={genOrderId} onChange={(e) => setGenOrderId(e.target.value)} className="w-full bg-[#0a0f1e] border border-white/8 rounded-lg px-3 py-2 text-xs text-white">
                  {givableOrders.map((o) => (
                    <option key={o.id} value={o.id}>{o.drug_name} — {o.dose}{o.dose_unit} {o.frequency}</option>
                  ))}
                </select>
                <input type="number" min={1} max={72} value={genHours} onChange={(e) => setGenHours(Number(e.target.value))} className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white" />
              </>
            )}
            {genError && <p className="text-xs text-rose-400">{genError}</p>}
            <div className="flex justify-end gap-2">
              <button onClick={() => setGenerating(false)} className="btn-secondary text-xs px-3 py-1.5">{t('common.cancel')}</button>
              <button onClick={submitGenerate} disabled={genSaving || givableOrders.length === 0} className="btn-primary text-xs px-3 py-1.5">{t('emar.confirmGenerate')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
