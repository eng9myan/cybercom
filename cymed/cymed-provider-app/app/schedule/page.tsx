'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, CalendarDays } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type Appointment = {
  id: string;
  patient_name: string;
  patient_mrn: string;
  appointment_type: string;
  status: string;
  start_time: string;
  end_time: string;
};

type ScheduleResponse = {
  date: string;
  appointments: Appointment[];
};

const STATUS_BADGE: Record<string, string> = {
  proposed: 'badge-blue',
  pending: 'badge-yellow',
  booked: 'badge-teal',
  arrived: 'badge-green',
  fulfilled: 'badge-green',
  cancelled: 'badge-red',
};

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function addDays(iso: string, days: number): string {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

export default function SchedulePage() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();
  const [dateStr, setDateStr] = useState(todayISO());
  const [data, setData] = useState<ScheduleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const load = useCallback(
    (date: string) => {
      setLoading(true);
      setError(null);
      setNotFound(false);
      fetch(`/api/cymed/rest/providers/me/schedule/?date=${date}`, { credentials: 'include' })
        .then(async (res) => {
          if (res.status === 404) {
            setNotFound(true);
            return null;
          }
          if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
          return res.json();
        })
        .then((json) => {
          if (json) setData(json as ScheduleResponse);
        })
        .catch((e) => setError(e instanceof Error ? e.message : t('schedule.loadFailed')))
        .finally(() => setLoading(false));
    },
    [t],
  );

  useEffect(() => {
    if (!authLoading && user) load(dateStr);
  }, [authLoading, user, dateStr, load]);

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
          <h1 className="page-title text-white">{t('schedule.title')}</h1>
          <p className="page-subtitle">{t('schedule.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setDateStr((d) => addDays(d, -1))}
            className="btn-secondary p-2"
            title={t('schedule.previousDay')}
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button onClick={() => setDateStr(todayISO())} className="btn-secondary text-xs px-3">
            {t('schedule.today')}
          </button>
          <input
            type="date"
            value={dateStr}
            onChange={(e) => setDateStr(e.target.value)}
            className="input-field !w-auto"
          />
          <button
            onClick={() => setDateStr((d) => addDays(d, 1))}
            className="btn-secondary p-2"
            title={t('schedule.nextDay')}
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingCard label={t('common.loading')} />
      ) : notFound ? (
        <EmptyCard label={`${t('overview.noProviderLinkedTitle')} — ${t('overview.noProviderLinkedDetail')}`} />
      ) : error || !data ? (
        <ErrorCard error={error || t('schedule.loadFailed')} />
      ) : data.appointments.length === 0 ? (
        <EmptyCard label={t('schedule.empty')} />
      ) : (
        <div className="glass-card p-2">
          <div className="flex items-center gap-2 px-3 py-2 text-xs text-slate-500">
            <CalendarDays className="w-3.5 h-3.5" />
            {t('schedule.count', { n: data.appointments.length })}
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('schedule.time')}</th>
                <th>{t('schedule.patient')}</th>
                <th>{t('schedule.type')}</th>
                <th>{t('schedule.status')}</th>
              </tr>
            </thead>
            <tbody>
              {data.appointments.map((a) => (
                <tr key={a.id}>
                  <td className="font-mono">{formatTime(a.start_time)}</td>
                  <td className="font-semibold text-white">
                    {a.patient_name}
                    <span className="text-slate-500 font-normal ms-2 font-mono text-xs">{a.patient_mrn}</span>
                  </td>
                  <td className="capitalize">{a.appointment_type}</td>
                  <td>
                    <span className={`badge ${STATUS_BADGE[a.status] || 'badge-blue'}`}>{a.status}</span>
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
