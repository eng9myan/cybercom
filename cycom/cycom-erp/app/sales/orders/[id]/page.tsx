'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, FileText, Package } from 'lucide-react';
import { useT } from '@/lib/i18n';
import CustomFieldsPanel from '@/components/CustomFieldsPanel';
import { LoadingCard } from '@/components/CycomEmptyStates';
import { statusTone, REAL_SALES_ORDER_STATE } from '@/lib/status';

interface SOLine {
  id: string;
  description: string;
  quantity: string;
  unit_price: string;
  subtotal: string;
}

interface SODetail {
  id: string;
  number: string;
  customer_name: string;
  order_date: string;
  currency: string;
  amount_total: number;
  status: string;
  lines: SOLine[];
}

export default function SalesOrderDetailPage() {
  const t = useT();
  const router = useRouter();
  const params = useParams();
  const orderId = params?.id as string;

  const [order, setOrder] = useState<SODetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!orderId) return;
    fetch(`/api/cycom/rest/sales/orders/${orderId}/`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then(setOrder)
      .finally(() => setLoading(false));
  }, [orderId]);

  if (loading) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8"><LoadingCard label={t('soDetail.loading')} /></div>;
  if (!order) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-center text-slate-400">{t('soDetail.notFound')}</div>;

  const statusKey = REAL_SALES_ORDER_STATE[order.status] || 'unknown';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push('/sales/orders')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
            <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
              <FileText className="w-6 h-6 text-purple-400" /> {order.customer_name}
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-mono">{order.number} · {order.order_date}</p>
          </div>
        </div>
        <span className={`badge ${statusTone(statusKey)}`}>{t(`status.${statusKey}`)}</span>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
              <Package className="w-4 h-4 text-purple-400" /> {t('soDetail.linesHeading')}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[480px] text-xs">
                <thead>
                  <tr className="bg-slate-950 text-slate-500 uppercase border-b border-slate-850">
                    <th className="p-2 text-start font-bold">{t('soDetail.colDescription')}</th>
                    <th className="p-2 text-end font-bold">{t('poDetail.colQty')}</th>
                    <th className="p-2 text-end font-bold">{t('soDetail.colUnitPrice')}</th>
                    <th className="p-2 text-end font-bold">{t('common.subtotal')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {order.lines.map((line) => (
                    <tr key={line.id}>
                      <td className="p-2 text-slate-200">{line.description || '—'}</td>
                      <td className="p-2 text-end font-mono text-slate-300">{Number(line.quantity).toFixed(2)}</td>
                      <td className="p-2 text-end font-mono text-slate-300">{Number(line.unit_price).toFixed(2)}</td>
                      <td className="p-2 text-end font-mono text-slate-400">{Number(line.subtotal).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex justify-between text-sm font-black text-white border-t border-white/10 pt-3">
              <span>{t('common.total')}</span>
              <span className="text-purple-400">{order.currency} {Number(order.amount_total).toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <CustomFieldsPanel modelKey="sales_order" recordId={orderId} />
        </div>
      </div>
    </div>
  );
}
