'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, ShoppingBag, Package } from 'lucide-react';
import { useT } from '@/lib/i18n';
import CustomFieldsPanel from '@/components/CustomFieldsPanel';
import { LoadingCard } from '@/components/CycomEmptyStates';
import { statusTone, REAL_PURCHASE_ORDER_STATE } from '@/lib/status';

interface POLine {
  id: string;
  product: string;
  product_name: string;
  quantity: string;
  unit_cost: string;
  quantity_received: string;
  quantity_remaining: string;
}

interface PODetail {
  id: string;
  vendor: string;
  vendor_name: string;
  warehouse: string;
  currency: string;
  status: string;
  amount_total: number;
  lines: POLine[];
  created_at: string;
}

export default function PurchaseOrderDetailPage() {
  const t = useT();
  const router = useRouter();
  const params = useParams();
  const orderId = params?.id as string;

  const [order, setOrder] = useState<PODetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!orderId) return;
    fetch(`/api/cycom/rest/procurement/orders/${orderId}/`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then(setOrder)
      .finally(() => setLoading(false));
  }, [orderId]);

  if (loading) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8"><LoadingCard label={t('poDetail.loading')} /></div>;
  if (!order) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-center text-slate-400">{t('poDetail.notFound')}</div>;

  const statusKey = REAL_PURCHASE_ORDER_STATE[order.status] || 'unknown';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push('/purchase')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
            <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
              <ShoppingBag className="w-6 h-6 text-amber-400" /> {order.vendor_name}
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-mono">{t('poDetail.poCode', { id: order.id.slice(0, 8) })}</p>
          </div>
        </div>
        <span className={`badge ${statusTone(statusKey)}`}>{t(`status.${statusKey}`)}</span>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
              <Package className="w-4 h-4 text-amber-400" /> {t('poDetail.linesHeading')}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[480px] text-xs">
                <thead>
                  <tr className="bg-slate-950 text-slate-500 uppercase border-b border-slate-850">
                    <th className="p-2 text-start font-bold">{t('poDetail.colProduct')}</th>
                    <th className="p-2 text-end font-bold">{t('poDetail.colQty')}</th>
                    <th className="p-2 text-end font-bold">{t('poDetail.colUnitCost')}</th>
                    <th className="p-2 text-end font-bold">{t('poDetail.colReceived')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {order.lines.map((line) => (
                    <tr key={line.id}>
                      <td className="p-2 text-slate-200">{line.product_name || '—'}</td>
                      <td className="p-2 text-end font-mono text-slate-300">{Number(line.quantity).toFixed(2)}</td>
                      <td className="p-2 text-end font-mono text-slate-300">{Number(line.unit_cost).toFixed(4)}</td>
                      <td className="p-2 text-end font-mono text-slate-400">{Number(line.quantity_received).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex justify-between text-sm font-black text-white border-t border-white/10 pt-3">
              <span>{t('common.total')}</span>
              <span className="text-amber-400">{order.currency} {Number(order.amount_total).toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <CustomFieldsPanel modelKey="purchase_order" recordId={orderId} />
        </div>
      </div>
    </div>
  );
}
