'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { Calendar, Users, FlaskConical, Video, ShieldAlert, RefreshCw } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type CDSAlert = {
  id: string;
  title: string;
  detail: string;
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
  kind: string;
  acknowledged_at: string | null;
};

type PortalProfile = {
  id: string;
  provider_name: string;
  npi: string;
  is_on_call: boolean;
};

type Credentialing = {
  status: string;
};

type Provider = {
  id: string;
  first_name: string;
  last_name: string;
  provider_type: string;
};

type DashboardData = {
  provider: Provider;
  todays_appointments: number;
  active_patients: number;
  pending_results: number;
  telemedicine_queue: number;
  recent_alerts: CDSAlert[];
  profile: PortalProfile | null;
  credentialing: Credentialing | null;
};

function StatCard({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: number }) {
  return (
    <div className="stat-card flex items-center justify-between">
      <div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{label}</span>
        <p className="text-2xl font-black text-white">{value}</p>
      </div>
      <div className="p-3 rounded-xl bg-[var(--cy-teal)]/10 text-[var(--cy-teal)]">
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [ackingId, setAckingId] = useState<string | null>(null);
  const [togglingOnCall, setTogglingOnCall] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    fetch('/api/cymed/rest/providers/me/dashboard/', { credentials: 'include' })
      .then(async (res) => {
        if (res.status === 404) {
          setNotFound(true);
          return null;
        }
        if (!res.ok) {
          throw new Error(`${res.status} ${res.statusText}`);
        }
        return res.json();
      })
      .then((json) => {
        if (json) setData(json as DashboardData);
      })
      .catch((e) => setError(e instanceof Error ? e.message : t('overview.loadFailed')))
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => {
    if (!authLoading && user) load();
  }, [authLoading, user, load]);

  const acknowledge = async (alertId: string) => {
    setAckingId(alertId);
    try {
      const res = await fetch(`/api/cymed/rest/ai-cds/alerts/${alertId}/acknowledge/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      setData((prev) =>
        prev
          ? { ...prev, recent_alerts: prev.recent_alerts.filter((a) => a.id !== alertId) }
          : prev,
      );
    } catch {
      // leave the alert in place — the ack didn't actually happen, don't pretend it did
    } finally {
      setAckingId(null);
    }
  };

  const toggleOnCall = async () => {
    if (!data?.profile) return;
    setTogglingOnCall(true);
    try {
      const res = await fetch(
        `/api/cymed/rest/provider-portal/profiles/${data.profile.id}/toggle-on-call/`,
        { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: '{}' },
      );
      if (!res.ok) throw new Error(`${res.status}`);
      const json = await res.json();
      setData((prev) =>
        prev && prev.profile ? { ...prev, profile: { ...prev.profile, is_on_call: json.is_on_call } } : prev,
      );
    } catch {
      // state unchanged — real toggle failed, UI must not claim it flipped
    } finally {
      setTogglingOnCall(false);
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

  if (error || !data) {
    return <ErrorCard error={error || t('overview.loadFailed')} />;
  }

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('overview.title')}</h1>
          <p className="page-subtitle">
            {data.provider.first_name} {data.provider.last_name} — {t('overview.subtitle')}
          </p>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2 text-xs">
          <RefreshCw className="w-3.5 h-3.5" />
          {t('common.refresh')}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Calendar} label={t('overview.todaysAppointments')} value={data.todays_appointments} />
        <StatCard icon={Users} label={t('overview.activePatients')} value={data.active_patients} />
        <StatCard icon={FlaskConical} label={t('overview.pendingResults')} value={data.pending_results} />
        <StatCard icon={Video} label={t('overview.telemedicineQueue')} value={data.telemedicine_queue} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-5 space-y-3">
          <div className="flex items-center gap-2 border-b border-white/5 pb-3">
            <ShieldAlert className="w-4 h-4 text-[#EF4444]" />
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">
              {t('overview.criticalAlerts')}
            </h2>
          </div>
          {data.recent_alerts.length === 0 ? (
            <p className="text-sm text-slate-500 py-4">{t('overview.noAlerts')}</p>
          ) : (
            <div className="space-y-2">
              {data.recent_alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center gap-4 p-3 rounded-xl bg-white/[0.02] border border-white/5"
                >
                  <div className="flex-1">
                    <div className="font-bold text-sm">{alert.title}</div>
                    {alert.detail && <div className="text-xs text-slate-400">{alert.detail}</div>}
                  </div>
                  <span className={`badge badge-${alert.severity}`}>{alert.severity}</span>
                  <button
                    onClick={() => acknowledge(alert.id)}
                    disabled={ackingId === alert.id}
                    className="btn-secondary text-xs py-1.5 px-3"
                  >
                    {t('overview.acknowledge')}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-card p-5 space-y-3 h-fit">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">
            {t('nav.overview')}
          </h2>
          {data.profile ? (
            <>
              <div className="text-sm">
                <div className="font-bold">{data.profile.provider_name}</div>
                <div className="text-xs text-slate-500">
                  {t('overview.npi')}: {data.profile.npi}
                </div>
              </div>
              <button
                onClick={toggleOnCall}
                disabled={togglingOnCall}
                className={`badge ${data.profile.is_on_call ? 'badge-green' : 'badge-blue'} cursor-pointer`}
              >
                {data.profile.is_on_call ? t('overview.onCall') : t('overview.offCall')}
              </button>
            </>
          ) : (
            <p className="text-sm text-slate-500">
              {data.provider.first_name} {data.provider.last_name}
            </p>
          )}
          {data.credentialing && (
            <div className="text-xs text-slate-500 pt-2 border-t border-white/5">
              {data.credentialing.status}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
