'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { Video, ExternalLink, PlayCircle } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type Visit = {
  id: string;
  patient_name: string;
  patient_mrn: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  scheduled_start: string;
  connection_url: string | null;
};

const STATUS_BADGE: Record<Visit['status'], string> = {
  scheduled: 'badge-blue',
  in_progress: 'badge-green',
  completed: 'badge-teal',
  cancelled: 'badge-red',
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export default function TelemedicinePage() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();
  const [visits, setVisits] = useState<Visit[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [filter, setFilter] = useState<'all' | Visit['status']>('all');
  const [startingId, setStartingId] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    fetch('/api/cymed/rest/providers/me/telemedicine/', { credentials: 'include' })
      .then(async (res) => {
        if (res.status === 404) {
          setNotFound(true);
          return null;
        }
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then((json) => {
        if (json) setVisits(json.visits as Visit[]);
      })
      .catch((e) => setError(e instanceof Error ? e.message : t('telemedicine.loadFailed')))
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => {
    if (!authLoading && user) load();
  }, [authLoading, user, load]);

  const startSession = async (visitId: string) => {
    setStartingId(visitId);
    try {
      const res = await fetch(`/api/cymed/rest/clinic/telemedicine/visits/${visitId}/start_session/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      });
      if (!res.ok) throw new Error(`${res.status}`);
      load();
    } catch {
      // leave state as-is — the session didn't actually start
    } finally {
      setStartingId(null);
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

  if (notFound) {
    return <EmptyCard label={`${t('overview.noProviderLinkedTitle')} — ${t('overview.noProviderLinkedDetail')}`} />;
  }

  if (error || !visits) {
    return <ErrorCard error={error || t('telemedicine.loadFailed')} />;
  }

  const filtered = filter === 'all' ? visits : visits.filter((v) => v.status === filter);

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('telemedicine.title')}</h1>
          <p className="page-subtitle">{t('telemedicine.subtitle')}</p>
        </div>
        <div className="flex items-center gap-1.5">
          {(['all', 'scheduled', 'in_progress', 'completed'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={filter === s ? 'btn-primary text-xs px-3 py-1.5' : 'btn-secondary text-xs px-3 py-1.5'}
            >
              {s === 'all' && t('telemedicine.filterAll')}
              {s === 'scheduled' && t('telemedicine.filterScheduled')}
              {s === 'in_progress' && t('telemedicine.filterInProgress')}
              {s === 'completed' && t('telemedicine.filterCompleted')}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyCard label={t('telemedicine.empty')} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((v) => (
            <div key={v.id} className="glass-card p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-bold text-white">{v.patient_name}</div>
                  <div className="text-xs text-slate-500 font-mono">{v.patient_mrn}</div>
                </div>
                <span className={`badge ${STATUS_BADGE[v.status]}`}>{v.status}</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Video className="w-3.5 h-3.5" />
                {t('telemedicine.scheduledFor')}: {formatDateTime(v.scheduled_start)}
              </div>
              {v.connection_url ? (
                <a
                  href={v.connection_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-primary w-full py-2 flex items-center justify-center gap-2 text-xs"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  {t('telemedicine.join')}
                </a>
              ) : v.status === 'scheduled' ? (
                <button
                  onClick={() => startSession(v.id)}
                  disabled={startingId === v.id}
                  className="btn-secondary w-full py-2 flex items-center justify-center gap-2 text-xs"
                >
                  <PlayCircle className="w-3.5 h-3.5" />
                  {t('telemedicine.startSession')}
                </button>
              ) : (
                <p className="text-xs text-slate-600 text-center py-1">{t('telemedicine.notStarted')}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
