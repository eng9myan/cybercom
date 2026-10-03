'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { FlaskConical, Radiation, Pill, ListOrdered, Eye, X } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type LabResultValue = {
  id: string;
  analyte_name: string;
  value_numeric: string | null;
  value_text: string;
  unit: string;
  interpretation: string;
  is_critical: boolean;
  is_abnormal: boolean;
};

type LabResultRow = {
  id: string;
  order_item: string;
  status: string;
  comments: string;
  values: LabResultValue[];
};

type RadiologyReportRow = {
  id: string;
  order_item: string;
  status: string;
  clinical_indication: string;
  findings: string;
  impression: string;
  recommendations: string;
};

const RESULT_VIEWABLE_KINDS = new Set(['lab', 'imaging']);
const RESULT_VIEWABLE_STATUSES = new Set(['completed', 'verified', 'resulted', 'approved']);

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

  const [resultTarget, setResultTarget] = useState<OrderRow | null>(null);
  const [resultLoading, setResultLoading] = useState(false);
  const [resultError, setResultError] = useState<string | null>(null);
  const [labResults, setLabResults] = useState<LabResultRow[]>([]);
  const [imagingReport, setImagingReport] = useState<RadiologyReportRow | null>(null);

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

  const openResult = useCallback(async (row: OrderRow) => {
    setResultTarget(row);
    setResultLoading(true);
    setResultError(null);
    setLabResults([]);
    setImagingReport(null);
    // Both the order detail and the result list sit behind a licensable
    // feature tier (same as eMAR's medication-order picker) — a tenant
    // without it sees "not available" here, not a scary error banner,
    // since there's nothing actionable to do from this read-only preview.
    try {
      const basePath = row.kind === 'lab' ? 'lab/orders/orders' : 'imaging/orders/orders';
      const orderRes = await fetch(`/api/cymed/rest/${basePath}/${row.id}/`, { credentials: 'include' });
      if (!orderRes.ok) {
        setResultLoading(false);
        return;
      }
      const orderDetail = (await orderRes.json()) as { items?: { id: string }[] };
      const itemIds = new Set((orderDetail.items || []).map((i) => i.id));

      if (row.kind === 'lab') {
        const all = await fetchAll<LabResultRow>('/api/cymed/rest/lab/results/results/').catch(() => []);
        setLabResults(all.filter((r) => itemIds.has(r.order_item)));
      } else {
        const all = await fetchAll<RadiologyReportRow>('/api/cymed/rest/imaging/reporting/reports/').catch(() => []);
        setImagingReport(all.find((r) => itemIds.has(r.order_item)) || null);
      }
    } catch (e) {
      setResultError(e instanceof Error ? e.message : t('orders.resultLoadFailed'));
    } finally {
      setResultLoading(false);
    }
  }, [t]);

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
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((o) => {
                const Icon = KIND_ICON[o.kind];
                const canViewResult = RESULT_VIEWABLE_KINDS.has(o.kind) && RESULT_VIEWABLE_STATUSES.has(o.status);
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
                    <td>
                      {canViewResult && (
                        <button onClick={() => openResult(o)} className="btn-secondary text-xs px-2 py-1 flex items-center gap-1">
                          <Eye className="w-3 h-3" />
                          {t('orders.viewResult')}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {resultTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-lg space-y-3 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white">{resultTarget.order_number}</h3>
                <p className="text-xs text-slate-500">{resultTarget.patient_name}{resultTarget.label && ` — ${resultTarget.label}`}</p>
              </div>
              <button onClick={() => setResultTarget(null)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            {resultLoading ? (
              <LoadingCard label={t('common.loading')} />
            ) : resultError ? (
              <ErrorCard error={resultError} />
            ) : resultTarget.kind === 'lab' ? (
              labResults.length === 0 ? (
                <EmptyCard label={t('orders.resultNotAvailable')} />
              ) : (
                <div className="space-y-3">
                  {labResults.map((r) => (
                    <div key={r.id} className="space-y-1.5">
                      {r.comments && <p className="text-xs text-slate-400">{r.comments}</p>}
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>{t('orders.analyte')}</th>
                            <th>{t('orders.value')}</th>
                            <th>{t('orders.flag')}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {r.values.map((v) => (
                            <tr key={v.id}>
                              <td className="text-xs text-slate-300">{v.analyte_name}</td>
                              <td className="text-xs font-mono text-white">
                                {v.value_numeric ?? v.value_text} {v.unit}
                              </td>
                              <td>
                                {v.is_critical ? (
                                  <span className="badge badge-red">{t('orders.critical')}</span>
                                ) : v.is_abnormal ? (
                                  <span className="badge badge-yellow">{v.interpretation || t('orders.abnormal')}</span>
                                ) : (
                                  <span className="badge badge-green">{t('orders.normal')}</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>
              )
            ) : !imagingReport ? (
              <EmptyCard label={t('orders.resultNotAvailable')} />
            ) : (
              <div className="space-y-3 text-xs">
                {imagingReport.clinical_indication && (
                  <div>
                    <p className="text-slate-500 font-semibold mb-0.5">{t('orders.clinicalIndication')}</p>
                    <p className="text-slate-300 whitespace-pre-wrap">{imagingReport.clinical_indication}</p>
                  </div>
                )}
                <div>
                  <p className="text-slate-500 font-semibold mb-0.5">{t('orders.findings')}</p>
                  <p className="text-slate-300 whitespace-pre-wrap">{imagingReport.findings || '—'}</p>
                </div>
                <div>
                  <p className="text-slate-500 font-semibold mb-0.5">{t('orders.impression')}</p>
                  <p className="text-slate-300 whitespace-pre-wrap">{imagingReport.impression || '—'}</p>
                </div>
                {imagingReport.recommendations && (
                  <div>
                    <p className="text-slate-500 font-semibold mb-0.5">{t('orders.recommendations')}</p>
                    <p className="text-slate-300 whitespace-pre-wrap">{imagingReport.recommendations}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
