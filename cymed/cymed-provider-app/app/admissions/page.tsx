'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { BedDouble, ArrowRightLeft, LogOut as DischargeIcon, X, Check, Pill } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type Admission = {
  id: string;
  encounter: string;
  patient_id: string;
  patient_name: string;
  admission_type: string;
  admission_type_name: string;
  admission_reason: string;
  admission_reason_name: string;
  admitting_physician_id: string;
  admitted_at: string;
  status: 'admitted' | 'discharged';
};

type TransferRequestRow = {
  id: string;
  patient: string;
  encounter: string;
  source_bed_id: string | null;
  target_bed_id: string;
  requested_by: string;
  requested_at: string;
  status: 'pending' | 'approved' | 'rejected';
  reason: string;
};

type Lookup = { id: string; name: string; code: string };

type Page<T> = { results: T[]; next: string | null } | T[];

async function fetchAll<T>(url: string): Promise<T[]> {
  const all: T[] = [];
  let next: string | null = url;
  while (next) {
    const res = await fetch(next, { credentials: 'include' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const json = (await res.json()) as Page<T>;
    if (Array.isArray(json)) {
      all.push(...json);
      next = null;
    } else {
      all.push(...json.results);
      next = json.next;
    }
  }
  return all;
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export default function AdmissionsPage() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();

  const [admissions, setAdmissions] = useState<Admission[] | null>(null);
  const [transfers, setTransfers] = useState<TransferRequestRow[] | null>(null);
  const [dispositions, setDispositions] = useState<Lookup[]>([]);
  const [dischargeReasons, setDischargeReasons] = useState<Lookup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'admitted' | 'discharged' | 'all'>('admitted');

  const [transferTarget, setTransferTarget] = useState<Admission | null>(null);
  const [targetBed, setTargetBed] = useState('');
  const [sourceBed, setSourceBed] = useState('');
  const [transferReason, setTransferReason] = useState('');
  const [transferSaving, setTransferSaving] = useState(false);
  const [transferError, setTransferError] = useState<string | null>(null);

  const [dischargeTarget, setDischargeTarget] = useState<Admission | null>(null);
  const [dispositionId, setDispositionId] = useState('');
  const [reasonId, setReasonId] = useState('');
  const [summaryText, setSummaryText] = useState('');
  const [instructions, setInstructions] = useState('');
  const [dischargeSaving, setDischargeSaving] = useState(false);
  const [dischargeError, setDischargeError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetchAll<Admission>('/api/cymed/rest/hospital/adt/admissions/'),
      fetchAll<TransferRequestRow>('/api/cymed/rest/hospital/adt/transfer-requests/'),
      fetchAll<Lookup>('/api/cymed/rest/hospital/adt/dispositions/'),
      fetchAll<Lookup>('/api/cymed/rest/hospital/adt/discharge-reasons/'),
    ])
      .then(([adm, tx, disp, reasons]) => {
        setAdmissions(adm);
        setTransfers(tx);
        setDispositions(disp);
        setDischargeReasons(reasons);
      })
      .catch((e) => setError(e instanceof Error ? e.message : t('admissions.loadFailed')))
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => {
    if (!authLoading && user) load();
  }, [authLoading, user, load]);

  const filtered = useMemo(() => {
    if (!admissions) return [];
    if (statusFilter === 'all') return admissions;
    return admissions.filter((a) => a.status === statusFilter);
  }, [admissions, statusFilter]);

  const pendingTransfers = useMemo(
    () => (transfers || []).filter((tx) => tx.status === 'pending'),
    [transfers],
  );

  const openTransfer = (a: Admission) => {
    setTransferTarget(a);
    setTargetBed('');
    setSourceBed('');
    setTransferReason('');
    setTransferError(null);
  };

  const submitTransfer = async () => {
    if (!transferTarget || !targetBed.trim() || !transferReason.trim()) {
      setTransferError(t('admissions.transferValidation'));
      return;
    }
    setTransferSaving(true);
    try {
      const res = await fetch('/api/cymed/rest/hospital/adt/transfer-requests/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          patient: transferTarget.patient_id,
          encounter: transferTarget.encounter,
          source_bed_id: sourceBed.trim() || null,
          target_bed_id: targetBed.trim(),
          requested_by: user?.uid,
          reason: transferReason.trim(),
        }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      setTransferTarget(null);
      load();
    } catch (e) {
      setTransferError(e instanceof Error ? e.message : t('admissions.transferFailed'));
    } finally {
      setTransferSaving(false);
    }
  };

  const approveTransfer = async (tx: TransferRequestRow) => {
    try {
      const res = await fetch('/api/cymed/rest/hospital/adt/transfer-approvals/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ transfer_request: tx.id, approved_by: user?.uid, notes: '' }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : t('admissions.approveFailed'));
    }
  };

  const openDischarge = (a: Admission) => {
    setDischargeTarget(a);
    setDispositionId(dispositions[0]?.id || '');
    setReasonId(dischargeReasons[0]?.id || '');
    setSummaryText('');
    setInstructions('');
    setDischargeError(null);
  };

  const submitDischarge = async () => {
    if (!dischargeTarget || !dispositionId || !reasonId || !summaryText.trim()) {
      setDischargeError(t('admissions.dischargeValidation'));
      return;
    }
    setDischargeSaving(true);
    try {
      const res = await fetch('/api/cymed/rest/hospital/adt/discharge-summaries/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          admission: dischargeTarget.id,
          discharged_by: user?.uid,
          disposition: dispositionId,
          reason: reasonId,
          summary_text: summaryText.trim(),
          instructions: instructions.trim(),
        }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      setDischargeTarget(null);
      load();
    } catch (e) {
      setDischargeError(e instanceof Error ? e.message : t('admissions.dischargeFailed'));
    } finally {
      setDischargeSaving(false);
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

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('admissions.title')}</h1>
          <p className="page-subtitle">{t('admissions.subtitle')}</p>
        </div>
        <div className="flex items-center gap-1.5">
          {(['admitted', 'discharged', 'all'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={statusFilter === s ? 'btn-primary text-xs px-3 py-1.5' : 'btn-secondary text-xs px-3 py-1.5'}
            >
              {s === 'admitted' ? t('admissions.filterAdmitted') : s === 'discharged' ? t('admissions.filterDischarged') : t('admissions.filterAll')}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingCard label={t('common.loading')} />
      ) : error ? (
        <ErrorCard error={error} />
      ) : (
        <>
          <div className="glass-card p-2">
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-slate-500">
              <BedDouble className="w-3.5 h-3.5" />
              {t('admissions.count', { n: filtered.length })}
            </div>
            {filtered.length === 0 ? (
              <EmptyCard label={t('admissions.empty')} />
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('admissions.patient')}</th>
                    <th>{t('admissions.type')}</th>
                    <th>{t('admissions.reason')}</th>
                    <th>{t('admissions.admitted')}</th>
                    <th>{t('admissions.status')}</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((a) => (
                    <tr key={a.id}>
                      <td className="font-semibold text-white">{a.patient_name}</td>
                      <td className="text-xs text-slate-400">{a.admission_type_name}</td>
                      <td className="text-xs text-slate-400">{a.admission_reason_name}</td>
                      <td className="text-xs text-slate-500">{formatDateTime(a.admitted_at)}</td>
                      <td>
                        <span className={`badge ${a.status === 'admitted' ? 'badge-green' : 'badge-blue'}`}>
                          {a.status === 'admitted' ? t('admissions.filterAdmitted') : t('admissions.filterDischarged')}
                        </span>
                      </td>
                      <td>
                        {a.status === 'admitted' && (
                          <div className="flex items-center gap-1.5">
                            <Link href={`/emar?admission=${a.id}`} className="btn-secondary text-xs px-2 py-1 flex items-center gap-1">
                              <Pill className="w-3 h-3" />
                              {t('admissions.emar')}
                            </Link>
                            <button onClick={() => openTransfer(a)} className="btn-secondary text-xs px-2 py-1 flex items-center gap-1">
                              <ArrowRightLeft className="w-3 h-3" />
                              {t('admissions.transfer')}
                            </button>
                            <button onClick={() => openDischarge(a)} className="btn-secondary text-xs px-2 py-1 flex items-center gap-1">
                              <DischargeIcon className="w-3 h-3" />
                              {t('admissions.discharge')}
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="glass-card p-4">
            <h2 className="font-bold text-white flex items-center gap-2 mb-3">
              <ArrowRightLeft className="w-4 h-4 text-[var(--cy-teal)]" />
              {t('admissions.pendingTransfers')}
            </h2>
            {pendingTransfers.length === 0 ? (
              <EmptyCard label={t('admissions.noPendingTransfers')} />
            ) : (
              <div className="space-y-2">
                {pendingTransfers.map((tx) => (
                  <div key={tx.id} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-white/3 border border-white/8">
                    <div className="text-xs text-slate-300">
                      <span className="font-mono text-slate-500">{tx.source_bed_id || '—'}</span>
                      {' → '}
                      <span className="font-mono">{tx.target_bed_id}</span>
                      <span className="block text-slate-500 mt-0.5">{tx.reason}</span>
                    </div>
                    <button onClick={() => approveTransfer(tx)} className="btn-primary text-xs px-2 py-1 flex items-center gap-1 shrink-0">
                      <Check className="w-3 h-3" />
                      {t('admissions.approve')}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {transferTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-md space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white">{t('admissions.transferTitle', { name: transferTarget.patient_name })}</h3>
              <button onClick={() => setTransferTarget(null)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <input
              type="text"
              value={sourceBed}
              onChange={(e) => setSourceBed(e.target.value)}
              placeholder={t('admissions.sourceBedPlaceholder')}
              className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500"
            />
            <input
              type="text"
              value={targetBed}
              onChange={(e) => setTargetBed(e.target.value)}
              placeholder={t('admissions.targetBedPlaceholder')}
              className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500"
            />
            <textarea
              value={transferReason}
              onChange={(e) => setTransferReason(e.target.value)}
              placeholder={t('admissions.transferReasonPlaceholder')}
              rows={3}
              className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 resize-none"
            />
            {transferError && <p className="text-xs text-rose-400">{transferError}</p>}
            <div className="flex justify-end gap-2">
              <button onClick={() => setTransferTarget(null)} className="btn-secondary text-xs px-3 py-1.5">{t('common.cancel')}</button>
              <button onClick={submitTransfer} disabled={transferSaving} className="btn-primary text-xs px-3 py-1.5">{t('admissions.submitTransfer')}</button>
            </div>
          </div>
        </div>
      )}

      {dischargeTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-md space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white">{t('admissions.dischargeTitle', { name: dischargeTarget.patient_name })}</h3>
              <button onClick={() => setDischargeTarget(null)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <select
              value={dispositionId}
              onChange={(e) => setDispositionId(e.target.value)}
              className="w-full bg-[#0a0f1e] border border-white/8 rounded-lg px-3 py-2 text-xs text-white"
            >
              {dispositions.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
            <select
              value={reasonId}
              onChange={(e) => setReasonId(e.target.value)}
              className="w-full bg-[#0a0f1e] border border-white/8 rounded-lg px-3 py-2 text-xs text-white"
            >
              {dischargeReasons.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
            <textarea
              value={summaryText}
              onChange={(e) => setSummaryText(e.target.value)}
              placeholder={t('admissions.summaryPlaceholder')}
              rows={3}
              className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 resize-none"
            />
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder={t('admissions.instructionsPlaceholder')}
              rows={2}
              className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 resize-none"
            />
            {dischargeError && <p className="text-xs text-rose-400">{dischargeError}</p>}
            <div className="flex justify-end gap-2">
              <button onClick={() => setDischargeTarget(null)} className="btn-secondary text-xs px-3 py-1.5">{t('common.cancel')}</button>
              <button onClick={submitDischarge} disabled={dischargeSaving} className="btn-primary text-xs px-3 py-1.5">{t('admissions.submitDischarge')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
