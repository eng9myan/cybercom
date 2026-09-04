'use client';

import React from 'react';
import Link from 'next/link';
import { Briefcase, AlertCircle, ShoppingBag, Users } from 'lucide-react';
import { useCycomList, fmtDate, fmtMoney, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';
import { useT } from '@/lib/i18n';
import { PURCHASE_STATE, statusTone, type StatusKey } from '@/lib/status';

type CycomPO = {
  id: number;
  name?: string;
  partner_id?: Many2One;
  date_order?: string;
  amount_total?: number;
  state?: string;
  currency_id?: Many2One;
};

interface PurchaseOrderRow {
  rawId: number;
  id: string;
  vendorName: string;
  date: string;
  total: string;
  statusKey: StatusKey;
}

const mapPO = (r: CycomPO): PurchaseOrderRow => ({
  rawId: r.id,
  id: r.name || `PO/${r.id}`,
  vendorName: m2oName(r.partner_id, '—'),
  date: fmtDate(r.date_order),
  total: fmtMoney(r.amount_total ?? 0, m2oName(r.currency_id, '')),
  statusKey: PURCHASE_STATE[r.state ?? ''] || 'unknown',
});

export default function PurchasePage() {
  const t = useT();
  const { rows: orders, loading, error } = useCycomList<CycomPO, PurchaseOrderRow>(
    'purchase.order',
    [],
    ['name', 'partner_id', 'date_order', 'amount_total', 'state', 'currency_id'],
    mapPO,
    { limit: 200, order: 'date_order desc' },
  );

  const counts = orders.reduce<Record<string, number>>((acc, o) => {
    acc[o.statusKey] = (acc[o.statusKey] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('purchase.title')}</h1>
          <p className="page-subtitle">{t('purchase.subtitle')}</p>
        </div>
        <div className="flex gap-3">
          <Link href="/purchase/vendors" className="btn-primary flex items-center gap-2">
            <Users className="w-4 h-4" /> {t('purchase.vendorDirectory')}
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label={t('purchase.totalPOs')} value={orders.length} icon={<Briefcase className="w-5 h-5" />} tone="cyan" />
        <KpiCard label={t('purchase.awaitingApproval')} value={counts['waitingApproval'] || 0} icon={<AlertCircle className="w-5 h-5" />} tone="amber" />
        <KpiCard label={t('purchase.confirmed')} value={counts['confirmed'] || 0} icon={<ShoppingBag className="w-5 h-5" />} tone="emerald" />
        <KpiCard label={t('purchase.cancelled')} value={counts['cancelled'] || 0} icon={<AlertCircle className="w-5 h-5" />} tone="red" />
      </div>

      {loading && <LoadingCard label={t('purchase.loading')} />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && orders.length === 0 && <EmptyCard label={t('purchase.empty')} />}

      {!loading && !error && orders.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('purchase.register')}</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('purchase.po')}</th>
                  <th>{t('purchase.vendor')}</th>
                  <th>{t('common.date')}</th>
                  <th>{t('common.total')}</th>
                  <th>{t('common.status')}</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.rawId}>
                    <td className="font-mono text-xs font-bold text-slate-400">{o.id}</td>
                    <td className="font-semibold text-slate-200">{o.vendorName}</td>
                    <td className="text-slate-400">{o.date}</td>
                    <td className="font-bold text-white">{o.total}</td>
                    <td><span className={`badge ${statusTone(o.statusKey)}`}>{t(`status.${o.statusKey}`)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function KpiCard({ label, value, icon, tone }: { label: string; value: number; icon: React.ReactNode; tone: 'cyan' | 'amber' | 'emerald' | 'red' }) {
  const colors = {
    cyan: 'bg-cyan-500/10 text-cyan-400',
    amber: 'bg-amber-500/10 text-amber-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    red: 'bg-red-500/10 text-red-400',
  }[tone];
  return (
    <div className="stat-card flex items-center justify-between">
      <div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{label}</span>
        <p className="text-2xl font-black text-white">{value}</p>
      </div>
      <div className={`p-3 rounded-xl ${colors}`}>{icon}</div>
    </div>
  );
}
