'use client';

import React from 'react';
import { TrendingUp, DollarSign, AlertTriangle, ShieldAlert } from 'lucide-react';
import { useCycomList, fmtDate, fmtMoney, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';
import { useT } from '@/lib/i18n';
import { SALES_STATE, statusTone, type StatusKey } from '@/lib/status';

type CycomSaleOrder = {
  id: number;
  name?: string;
  partner_id?: Many2One;
  date_order?: string;
  amount_total?: number;
  state?: string;
  currency_id?: Many2One;
};

interface SalesOrderRow {
  rawId: number;
  id: string;
  clientName: string;
  date: string;
  total: number;
  totalFmt: string;
  statusKey: StatusKey;
}

const mapOrder = (o: CycomSaleOrder): SalesOrderRow => ({
  rawId: o.id,
  id: o.name || `SO/${o.id}`,
  clientName: m2oName(o.partner_id, '—'),
  date: fmtDate(o.date_order),
  total: Number(o.amount_total ?? 0),
  totalFmt: fmtMoney(o.amount_total ?? 0, m2oName(o.currency_id, '')),
  statusKey: SALES_STATE[o.state ?? ''] || 'draft',
});

export default function SalesDashboard() {
  const t = useT();
  const { rows: salesOrders, loading, error } = useCycomList<CycomSaleOrder, SalesOrderRow>(
    'sale.order',
    [],
    ['name', 'partner_id', 'date_order', 'amount_total', 'state', 'currency_id'],
    mapOrder,
    { limit: 200, order: 'date_order desc' },
  );

  const totalPipeline = salesOrders.reduce((acc, o) => acc + o.total, 0);
  const pending = salesOrders.filter((o) => o.statusKey === 'pendingApproval').length;
  const confirmed = salesOrders.filter((o) => o.statusKey === 'confirmed').length;

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('sales.title')}</h1>
          <p className="page-subtitle">{t('sales.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Kpi label={t('sales.totalPipeline')} value={fmtMoney(totalPipeline, '')} tone="cyan" icon={<TrendingUp className="w-5 h-5" />} />
        <Kpi label={t('sales.pendingApproval')} value={pending} tone="amber" icon={<AlertTriangle className="w-5 h-5" />} />
        <Kpi label={t('sales.confirmedOrders')} value={confirmed} tone="emerald" icon={<DollarSign className="w-5 h-5" />} />
        <Kpi label={t('sales.totalOrders')} value={salesOrders.length} tone="purple" icon={<ShieldAlert className="w-5 h-5" />} />
      </div>

      {loading && <LoadingCard label={t('sales.loading')} />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && salesOrders.length === 0 && <EmptyCard label={t('sales.empty')} />}

      {!loading && !error && salesOrders.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('sales.register')}</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('sales.order')}</th>
                  <th>{t('common.customer')}</th>
                  <th>{t('common.date')}</th>
                  <th>{t('common.total')}</th>
                  <th>{t('common.status')}</th>
                </tr>
              </thead>
              <tbody>
                {salesOrders.map((o) => (
                  <tr key={o.rawId}>
                    <td className="font-mono text-xs font-bold text-slate-400">{o.id}</td>
                    <td className="font-semibold text-slate-200">{o.clientName}</td>
                    <td className="text-slate-400">{o.date}</td>
                    <td className="font-bold text-white">{o.totalFmt}</td>
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

function Kpi({ label, value, tone, icon }: { label: string; value: number | string; tone: 'cyan' | 'amber' | 'emerald' | 'purple'; icon: React.ReactNode }) {
  const colors = {
    cyan: 'bg-cyan-500/10 text-cyan-400',
    amber: 'bg-amber-500/10 text-amber-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    purple: 'bg-purple-500/10 text-purple-400',
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
