'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Pill, ScanLine, Check, X, PackageCheck } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type DispenseStatus =
  | 'queued' | 'in_progress' | 'verification_pending' | 'verified'
  | 'ready' | 'dispensed' | 'partial' | 'returned' | 'cancelled';

type DispenseItem = {
  id: string;
  drug_name: string;
  ndc_code: string;
  quantity_prescribed: string;
  quantity_dispensed: string;
  quantity_unit: string;
  barcode_verified: boolean;
  status: string;
};

type DispenseOrder = {
  id: string;
  dispense_number: string;
  patient_id: string;
  patient_name: string;
  dispense_type: string;
  status: DispenseStatus;
  pickup_method: string;
  created_at: string;
  items: DispenseItem[];
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

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

const STATUS_BADGE: Record<DispenseStatus, string> = {
  queued: 'badge-yellow',
  in_progress: 'badge-blue',
  verification_pending: 'badge-yellow',
  verified: 'badge-blue',
  ready: 'badge-blue',
  dispensed: 'badge-green',
  partial: 'badge-yellow',
  returned: 'badge-red',
  cancelled: 'badge-red',
};

const OPEN_STATUSES = new Set<DispenseStatus>(['queued', 'in_progress', 'verification_pending', 'verified', 'ready']);

export default function DispensingPage() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();

  const [orders, setOrders] = useState<DispenseOrder[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'open' | 'dispensed' | 'all'>('open');

  const [selected, setSelected] = useState<DispenseOrder | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const [barcodeItem, setBarcodeItem] = useState<DispenseItem | null>(null);
  const [ndcInput, setNdcInput] = useState('');
  const [barcodeSaving, setBarcodeSaving] = useState(false);
  const [barcodeError, setBarcodeError] = useState<string | null>(null);

  const [dispensing, setDispensing] = useState(false);
  const [pickedUpBy, setPickedUpBy] = useState('');
  const [pickupIdVerified, setPickupIdVerified] = useState(false);
  const [counselingProvided, setCounselingProvided] = useState(false);
  const [dispenseSaving, setDispenseSaving] = useState(false);
  const [dispenseError, setDispenseError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchAll<DispenseOrder>('/api/cymed/rest/pharmacy/dispensing/orders/')
      .then((rows) => setOrders(rows))
      .catch((e) => setError(e instanceof Error ? e.message : t('dispensing.loadFailed')))
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => {
    if (!authLoading && user) load();
  }, [authLoading, user, load]);

  const filtered = useMemo(() => {
    if (!orders) return [];
    if (statusFilter === 'open') return orders.filter((o) => OPEN_STATUSES.has(o.status));
    if (statusFilter === 'dispensed') return orders.filter((o) => o.status === 'dispensed');
    return orders;
  }, [orders, statusFilter]);

  const openOrder = (o: DispenseOrder) => {
    setSelected(o);
    setActionError(null);
    setPickedUpBy('');
    setPickupIdVerified(false);
    setCounselingProvided(false);
  };

  const refreshSelected = async (id: string) => {
    const rows = await fetchAll<DispenseOrder>('/api/cymed/rest/pharmacy/dispensing/orders/');
    setOrders(rows);
    setSelected(rows.find((r) => r.id === id) || null);
  };

  const verifyOrder = async () => {
    if (!selected) return;
    setActionError(null);
    try {
      const res = await fetch(`/api/cymed/rest/pharmacy/dispensing/orders/${selected.id}/verify/`, {
        method: 'POST', credentials: 'include',
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      await refreshSelected(selected.id);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : t('dispensing.verifyFailed'));
    }
  };

  const openBarcode = (item: DispenseItem) => {
    setBarcodeItem(item);
    setNdcInput('');
    setBarcodeError(null);
  };

  const submitBarcode = async () => {
    if (!selected || !barcodeItem || !ndcInput.trim()) {
      setBarcodeError(t('dispensing.ndcRequired'));
      return;
    }
    setBarcodeSaving(true);
    try {
      const res = await fetch(`/api/cymed/rest/pharmacy/dispensing/orders/${selected.id}/barcode-verify/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ item_id: barcodeItem.id, ndc_code: ndcInput.trim() }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      setBarcodeItem(null);
      await refreshSelected(selected.id);
    } catch (e) {
      setBarcodeError(e instanceof Error ? e.message : t('dispensing.barcodeFailed'));
    } finally {
      setBarcodeSaving(false);
    }
  };

  const submitDispense = async () => {
    if (!selected) return;
    setDispenseSaving(true);
    setDispenseError(null);
    try {
      const res = await fetch(`/api/cymed/rest/pharmacy/dispensing/orders/${selected.id}/dispense/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          picked_up_by: pickedUpBy.trim(),
          pickup_id_verified: pickupIdVerified,
          counseling_provided: counselingProvided,
        }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      setDispensing(false);
      await refreshSelected(selected.id);
    } catch (e) {
      setDispenseError(e instanceof Error ? e.message : t('dispensing.dispenseFailed'));
    } finally {
      setDispenseSaving(false);
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
          <h1 className="page-title text-white">{t('dispensing.title')}</h1>
          <p className="page-subtitle">{t('dispensing.subtitle')}</p>
        </div>
        <div className="flex items-center gap-1.5">
          {(['open', 'dispensed', 'all'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={statusFilter === s ? 'btn-primary text-xs px-3 py-1.5' : 'btn-secondary text-xs px-3 py-1.5'}
            >
              {s === 'open' ? t('dispensing.filterOpen') : s === 'dispensed' ? t('dispensing.filterDispensed') : t('dispensing.filterAll')}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingCard label={t('common.loading')} />
      ) : error ? (
        <ErrorCard error={error} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-4">
          <div className="glass-card p-2">
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-slate-500">
              <Pill className="w-3.5 h-3.5" />
              {t('dispensing.count', { n: filtered.length })}
            </div>
            {filtered.length === 0 ? (
              <EmptyCard label={t('dispensing.empty')} />
            ) : (
              <div className="divide-y divide-white/5">
                {filtered.map((o) => (
                  <button
                    key={o.id}
                    onClick={() => openOrder(o)}
                    className={`w-full text-start px-3 py-3 hover:bg-white/5 transition-colors ${selected?.id === o.id ? 'bg-white/5' : ''}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-sm text-white">{o.patient_name}</span>
                      <span className={`badge ${STATUS_BADGE[o.status]}`}>{o.status.replace('_', ' ')}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                      <span className="font-mono">{o.dispense_number}</span>
                      <span>{formatDateTime(o.created_at)}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="glass-card p-4 min-h-[300px]">
            {!selected ? (
              <EmptyCard label={t('dispensing.selectOrder')} />
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-white">{selected.patient_name}</h3>
                    <p className="text-xs text-slate-500 font-mono">{selected.dispense_number}</p>
                  </div>
                  <span className={`badge ${STATUS_BADGE[selected.status]}`}>{selected.status.replace('_', ' ')}</span>
                </div>

                <div className="space-y-1.5">
                  {selected.items.map((item) => (
                    <div key={item.id} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-white/3 border border-white/8">
                      <div className="text-xs">
                        <span className="text-white font-semibold">{item.drug_name}</span>
                        <span className="block text-slate-500">{item.quantity_prescribed} {item.quantity_unit}</span>
                      </div>
                      {item.barcode_verified ? (
                        <span className="badge badge-green text-[9px]">{t('dispensing.scanned')}</span>
                      ) : (
                        <button onClick={() => openBarcode(item)} className="btn-secondary text-xs px-2 py-1 flex items-center gap-1">
                          <ScanLine className="w-3 h-3" />
                          {t('dispensing.scan')}
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {actionError && <p className="text-xs text-rose-400">{actionError}</p>}

                <div className="flex items-center gap-2 pt-2 border-t border-white/5">
                  {(selected.status === 'queued' || selected.status === 'verification_pending') && (
                    <button onClick={verifyOrder} className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1">
                      <Check className="w-3.5 h-3.5" />
                      {t('dispensing.verify')}
                    </button>
                  )}
                  {selected.status === 'verified' && (
                    <button onClick={() => { setDispensing(true); setDispenseError(null); }} className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1">
                      <PackageCheck className="w-3.5 h-3.5" />
                      {t('dispensing.dispense')}
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {barcodeItem && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white">{barcodeItem.drug_name}</h3>
              <button onClick={() => setBarcodeItem(null)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <input
              type="text"
              value={ndcInput}
              onChange={(e) => setNdcInput(e.target.value)}
              placeholder={t('dispensing.ndcPlaceholder')}
              className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500"
            />
            {barcodeError && <p className="text-xs text-rose-400">{barcodeError}</p>}
            <div className="flex justify-end gap-2">
              <button onClick={() => setBarcodeItem(null)} className="btn-secondary text-xs px-3 py-1.5">{t('common.cancel')}</button>
              <button onClick={submitBarcode} disabled={barcodeSaving} className="btn-primary text-xs px-3 py-1.5">{t('dispensing.confirmScan')}</button>
            </div>
          </div>
        </div>
      )}

      {dispensing && selected && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white">{t('dispensing.dispense')}</h3>
              <button onClick={() => setDispensing(false)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <input
              type="text"
              value={pickedUpBy}
              onChange={(e) => setPickedUpBy(e.target.value)}
              placeholder={t('dispensing.pickedUpByPlaceholder')}
              className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500"
            />
            <label className="flex items-center gap-1.5 text-xs text-slate-400">
              <input type="checkbox" checked={pickupIdVerified} onChange={(e) => setPickupIdVerified(e.target.checked)} />
              {t('dispensing.idVerified')}
            </label>
            <label className="flex items-center gap-1.5 text-xs text-slate-400">
              <input type="checkbox" checked={counselingProvided} onChange={(e) => setCounselingProvided(e.target.checked)} />
              {t('dispensing.counselingProvided')}
            </label>
            {dispenseError && <p className="text-xs text-rose-400">{dispenseError}</p>}
            <div className="flex justify-end gap-2">
              <button onClick={() => setDispensing(false)} className="btn-secondary text-xs px-3 py-1.5">{t('common.cancel')}</button>
              <button onClick={submitDispense} disabled={dispenseSaving} className="btn-primary text-xs px-3 py-1.5">{t('dispensing.confirmDispense')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
