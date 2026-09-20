'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { FlaskConical, Radiation, Pill, ListOrdered } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type OrderKind = 'lab' | 'imaging' | 'medication';

type OrderRow = {
  id: string;
  kind: OrderKind;
  order_number: string;
  patient_name: string;
  label: string | null;
  status: string;
  priority: string;
  created_at: string;
};

const KIND_ICON: Record<OrderKind, React.ElementType> = {
  lab: FlaskConical,
  imaging: Radiation,
  medication: Pill,
};

const GREEN_STATUSES = new Set(['completed', 'verified', 'active', 'approved', 'resulted']);
const RED_STATUSES = new Set(['cancelled', 'discontinued', 'on_hold']);
const YELLOW_STATUSES = new Set(['pending', 'draft', 'pending_verification', 'partial']);

function statusBadge(status: string): string {
  if (GREEN_STATUSES.has(status)) return 'badge-green';
  if (RED_STATUSES.has(status)) return 'badge-red';
  if (YELLOW_STATUSES.has(status)) return 'badge-yellow';
  return 'badge-blue';
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export default function OrdersPage() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();
  const [orders, setOrders] = useState<OrderRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [kindFilter, setKindFilter] = useState<OrderKind | 'all'>('all');

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    fetch('/api/cymed/rest/providers/me/orders/', { credentials: 'include' })
      .then(async (res) => {
        if (res.status === 404) {
          setNotFound(true);
          return null;
        }
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then((json) => {
        if (json) setOrders(json.orders as OrderRow[]);
      })
      .catch((e) => setError(e instanceof Error ? e.message : t('orders.loadFailed')))
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => {
    if (!authLoading && user) load();
  }, [authLoading, user, load]);

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

  if (error || !orders) {
    return <ErrorCard error={error || t('orders.loadFailed')} />;
  }

  const filtered = kindFilter === 'all' ? orders : orders.filter((o) => o.kind === kindFilter);
  const kindLabel: Record<OrderKind, string> = {
    lab: t('orders.lab'),
    imaging: t('orders.imaging'),
    medication: t('orders.medication'),
  };

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('orders.title')}</h1>
          <p className="page-subtitle">{t('orders.subtitle')}</p>
        </div>
        <div className="flex items-center gap-1.5">
          {(['all', 'lab', 'imaging', 'medication'] as const).map((k) => (
            <button
              key={k}
              onClick={() => setKindFilter(k)}
              className={kindFilter === k ? 'btn-primary text-xs px-3 py-1.5' : 'btn-secondary text-xs px-3 py-1.5'}
            >
              {k === 'all' ? t('orders.all') : kindLabel[k]}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyCard label={t('orders.empty')} />
      ) : (
        <div className="glass-card p-2">
          <div className="flex items-center gap-2 px-3 py-2 text-xs text-slate-500">
            <ListOrdered className="w-3.5 h-3.5" />
            {t('orders.count', { n: filtered.length })}
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('orders.kind')}</th>
                <th>{t('orders.order')}</th>
                <th>{t('orders.patient')}</th>
                <th>{t('orders.status')}</th>
                <th>{t('orders.priority')}</th>
                <th>{t('orders.placed')}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((o) => {
                const Icon = KIND_ICON[o.kind];
                return (
                  <tr key={`${o.kind}-${o.id}`}>
                    <td>
                      <span className="flex items-center gap-1.5 text-xs text-slate-400">
                        <Icon className="w-3.5 h-3.5" />
                        {kindLabel[o.kind]}
                      </span>
                    </td>
                    <td className="font-mono text-xs">
                      {o.order_number}
                      {o.label && <span className="text-slate-500"> — {o.label}</span>}
                    </td>
                    <td className="font-semibold text-white">{o.patient_name}</td>
                    <td>
                      <span className={`badge ${statusBadge(o.status)}`}>{o.status}</span>
                    </td>
                    <td className="capitalize text-xs">{o.priority}</td>
                    <td className="text-xs text-slate-500">{formatDateTime(o.created_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
