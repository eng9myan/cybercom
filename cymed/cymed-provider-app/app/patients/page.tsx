'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Search, Users } from 'lucide-react';
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

type Page = {
  results: Patient[];
  next: string | null;
};

export default function PatientsPage() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [query, setQuery] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    try {
      // The roster is one provider's own patient panel — small enough to
      // page through fully client-side rather than build server-side text
      // search. (Patient.first_name/last_name are blind-indexed for exact-
      // match DB lookups only; substring search only works once the plain
      // decrypted values are already in hand, i.e. after they're fetched.)
      let url: string | null = '/api/cymed/rest/providers/me/patients/';
      const all: Patient[] = [];
      while (url) {
        const res = await fetch(url, { credentials: 'include' });
        if (res.status === 404) {
          setNotFound(true);
          setPatients(null);
          return;
        }
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const json = (await res.json()) as Page;
        all.push(...json.results);
        url = json.next;
      }
      setPatients(all);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('patients.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    if (!authLoading && user) load();
  }, [authLoading, user, load]);

  const filtered = useMemo(() => {
    if (!patients) return [];
    const q = query.trim().toLowerCase();
    if (!q) return patients;
    return patients.filter(
      (p) =>
        `${p.first_name} ${p.last_name}`.toLowerCase().includes(q) ||
        p.mrn.toLowerCase().includes(q),
    );
  }, [patients, query]);

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

  if (notFound) {
    return <EmptyCard label={`${t('overview.noProviderLinkedTitle')} — ${t('overview.noProviderLinkedDetail')}`} />;
  }

  if (error || !patients) {
    return <ErrorCard error={error || t('patients.loadFailed')} />;
  }

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('patients.title')}</h1>
          <p className="page-subtitle">{t('patients.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2 bg-white/3 border border-white/8 rounded-xl px-3 py-1.5 w-[280px]">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('patients.searchPlaceholder')}
            className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full"
          />
        </div>
      </div>

      {patients.length === 0 ? (
        <EmptyCard label={t('patients.empty')} />
      ) : filtered.length === 0 ? (
        <EmptyCard label={t('patients.noResults')} />
      ) : (
        <div className="glass-card p-2">
          <div className="flex items-center gap-2 px-3 py-2 text-xs text-slate-500">
            <Users className="w-3.5 h-3.5" />
            {t('patients.count', { n: filtered.length })}
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('patients.name')}</th>
                <th>{t('patients.mrn')}</th>
                <th>{t('patients.dob')}</th>
                <th>{t('patients.gender')}</th>
                <th>{t('patients.status')}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id}>
                  <td className="font-semibold text-white">
                    {p.first_name} {p.last_name}
                  </td>
                  <td className="font-mono">{p.mrn}</td>
                  <td>{p.dob}</td>
                  <td className="capitalize">{p.gender}</td>
                  <td>
                    <span className={`badge ${p.is_active ? 'badge-green' : 'badge-red'}`}>
                      {p.is_active ? t('patients.active') : t('patients.inactive')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
