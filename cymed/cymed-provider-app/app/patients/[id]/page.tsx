'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, ClipboardList, Plus, Check } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type Patient = {
  id: string;
  first_name: string;
  last_name: string;
  mrn: string;
  dob: string;
  gender: string;
  is_active: boolean;
};

type ConditionSystem = 'icd11' | 'snomed';

type Condition = {
  id: string;
  patient: string;
  code: string;
  display: string;
  system: ConditionSystem;
  category: string;
  clinical_status: 'active' | 'inactive' | 'remission' | 'resolved';
  verification_status: string;
  onset_date: string | null;
  abatement_date: string | null;
  recorded_at: string;
  recorded_by: string;
};

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export default function PatientDetailPage() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();
  const params = useParams();
  const patientId = params.id as string;

  const [patient, setPatient] = useState<Patient | null>(null);
  const [problems, setProblems] = useState<Condition[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [includeResolved, setIncludeResolved] = useState(false);

  const [adding, setAdding] = useState(false);
  const [newSystem, setNewSystem] = useState<ConditionSystem>('snomed');
  const [newCode, setNewCode] = useState('');
  const [newDisplay, setNewDisplay] = useState('');
  const [newOnset, setNewOnset] = useState('');
  const [addError, setAddError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetch(`/api/cymed/rest/patients/${patientId}/`, { credentials: 'include' }).then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      }),
      fetch(
        `/api/cymed/rest/clinical/conditions/problem-list/?patient=${patientId}${includeResolved ? '&include_resolved=1' : ''}`,
        { credentials: 'include' },
      ).then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      }),
    ])
      .then(([p, probs]) => {
        setPatient(p);
        setProblems(probs);
      })
      .catch((e) => setError(e instanceof Error ? e.message : t('patientDetail.loadFailed')))
      .finally(() => setLoading(false));
  }, [patientId, includeResolved, t]);

  useEffect(() => {
    if (!authLoading && user && patientId) load();
  }, [authLoading, user, patientId, load]);

  const resolveProblem = async (id: string) => {
    try {
      const res = await fetch(`/api/cymed/rest/clinical/conditions/${id}/resolve/`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : t('patientDetail.resolveFailed'));
    }
  };

  const submitNewProblem = async () => {
    setAddError(null);
    if (!newCode.trim() || !newDisplay.trim()) {
      setAddError(t('patientDetail.addValidation'));
      return;
    }
    setSaving(true);
    try {
      const res = await fetch('/api/cymed/rest/clinical/conditions/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          patient: patientId,
          category: 'problem_list_item',
          system: newSystem,
          code: newCode.trim(),
          display: newDisplay.trim(),
          onset_date: newOnset || null,
          recorded_by: user?.username || user?.name || '',
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      }
      setAdding(false);
      setNewCode('');
      setNewDisplay('');
      setNewOnset('');
      load();
    } catch (e) {
      setAddError(e instanceof Error ? e.message : t('patientDetail.addFailed'));
    } finally {
      setSaving(false);
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

  if (loading) {
    return <LoadingCard label={t('common.loading')} />;
  }

  if (error || !patient) {
    return <ErrorCard error={error || t('patientDetail.loadFailed')} />;
  }

  return (
    <div className="space-y-6">
      <Link href="/patients" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white">
        <ArrowLeft className="w-3.5 h-3.5 rtl:-scale-x-100" />
        {t('patientDetail.backToPatients')}
      </Link>

      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{patient.first_name} {patient.last_name}</h1>
          <p className="page-subtitle">
            {t('patients.mrn')}: {patient.mrn} · {t('patients.dob')}: {patient.dob} ·{' '}
            <span className="capitalize">{patient.gender}</span>
          </p>
        </div>
        <span className={`badge ${patient.is_active ? 'badge-green' : 'badge-red'}`}>
          {patient.is_active ? t('patients.active') : t('patients.inactive')}
        </span>
      </div>

      <div className="glass-card p-4 space-y-4">
        <div className="flex items-center justify-between gap-2">
          <h2 className="font-bold text-white flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-[var(--cy-teal)]" />
            {t('patientDetail.problemList')}
          </h2>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5 text-xs text-slate-400">
              <input
                type="checkbox"
                checked={includeResolved}
                onChange={(e) => setIncludeResolved(e.target.checked)}
              />
              {t('patientDetail.includeResolved')}
            </label>
            <button
              onClick={() => { setAdding(true); setAddError(null); }}
              className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" />
              {t('patientDetail.addProblem')}
            </button>
          </div>
        </div>

        {adding && (
          <div className="border border-white/8 rounded-xl p-3 space-y-2 bg-white/3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <select
                value={newSystem}
                onChange={(e) => setNewSystem(e.target.value as ConditionSystem)}
                className="bg-[#0a0f1e] border border-white/8 rounded-lg px-3 py-2 text-xs text-white"
              >
                <option value="snomed">SNOMED-CT</option>
                <option value="icd11">ICD-11</option>
              </select>
              <input
                type="text"
                value={newCode}
                onChange={(e) => setNewCode(e.target.value)}
                placeholder={t('patientDetail.codePlaceholder')}
                className="bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500"
              />
              <input
                type="text"
                value={newDisplay}
                onChange={(e) => setNewDisplay(e.target.value)}
                placeholder={t('patientDetail.displayPlaceholder')}
                className="bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 sm:col-span-2"
              />
              <input
                type="date"
                value={newOnset}
                onChange={(e) => setNewOnset(e.target.value)}
                className="bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white"
              />
            </div>
            {addError && <p className="text-xs text-rose-400">{addError}</p>}
            <div className="flex justify-end gap-2">
              <button onClick={() => setAdding(false)} className="btn-secondary text-xs px-3 py-1.5">
                {t('common.cancel')}
              </button>
              <button onClick={submitNewProblem} disabled={saving} className="btn-primary text-xs px-3 py-1.5">
                {t('patientDetail.save')}
              </button>
            </div>
          </div>
        )}

        {!problems || problems.length === 0 ? (
          <EmptyCard label={t('patientDetail.noProblems')} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('patientDetail.problem')}</th>
                <th>{t('patientDetail.code')}</th>
                <th>{t('patientDetail.status')}</th>
                <th>{t('patientDetail.onset')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {problems.map((c) => (
                <tr key={c.id}>
                  <td className="font-semibold text-white">{c.display}</td>
                  <td className="font-mono text-xs text-slate-400">
                    {c.system.toUpperCase()} {c.code}
                  </td>
                  <td>
                    <span className={`badge ${c.clinical_status === 'active' ? 'badge-green' : c.clinical_status === 'remission' ? 'badge-yellow' : 'badge-blue'}`}>
                      {c.clinical_status}
                    </span>
                  </td>
                  <td className="text-xs text-slate-500">{formatDate(c.onset_date)}</td>
                  <td>
                    {(c.clinical_status === 'active' || c.clinical_status === 'remission') && (
                      <button
                        onClick={() => resolveProblem(c.id)}
                        className="btn-secondary text-xs px-2 py-1 flex items-center gap-1"
                      >
                        <Check className="w-3 h-3" />
                        {t('patientDetail.resolve')}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
