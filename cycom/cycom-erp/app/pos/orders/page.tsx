'use client';

import React, { useState } from 'react';
import { ShoppingBag, Lock } from 'lucide-react';
import { useCycomList, m2oName, type Many2One } from '@/lib/cycomModels';
import { useT } from '@/lib/i18n';

type CyPosOrder = {
  id: number;
  name?: string;
  session_id?: Many2One;
  date_order?: string;
  partner_id?: Many2One;
  amount_total?: number;
  state?: string;
};

const mapPosOrder = (r: CyPosOrder) => ({
  id: r.name || `ORD-${r.id}`,
  name: m2oName(r.partner_id, 'Walk-in'),
  price: r.amount_total ?? 0,
  qty: 1,
  total: r.amount_total ?? 0,
});

export default function POSOrderCheckout() {
  const t = useT();
  const { rows: items, loading } = useCycomList<CyPosOrder, ReturnType<typeof mapPosOrder>>(
    'pos.order',
    [],
    ['name', 'session_id', 'date_order', 'partner_id', 'amount_total', 'state'],
    mapPosOrder,
    { order: 'date_order desc', limit: 200 },
  );

  const [pledgeMode, setPledgeMode] = useState(false);
  const [discountPercent, setDiscountPercent] = useState(0);

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>{t('common.loading')}</div>;

  const subTotal = items.reduce((acc, curr) => acc + curr.total, 0);
  const discountAmount = subTotal * (discountPercent / 100);
  const finalTotal = subTotal - discountAmount;
  const roundedTotal = Math.round(finalTotal * 20) / 20;
  const roundingDifference = roundedTotal - finalTotal;

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('posOrders.title')}</h1>
          <p className="page-subtitle">{t('posOrders.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('posOrders.activeCart')}</h2>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('posOrders.product')}</th>
                    <th>{t('common.price')}</th>
                    <th>{t('common.quantity')}</th>
                    <th>{t('common.total')}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <div className="font-semibold text-slate-100">{item.name}</div>
                        <div className="text-[10px] text-slate-500">{item.id}</div>
                      </td>
                      <td>JOD {item.price.toFixed(2)}</td>
                      <td>{t('posOrders.unitsN', { n: item.qty })}</td>
                      <td className="font-bold text-slate-300">JOD {item.total.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="glass-card p-6 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('posOrders.predefinedDiscounts')}</h3>
            <div className="flex gap-3">
              {[0, 5, 10, 15, 20].map((d) => (
                <button
                  key={d}
                  onClick={() => setDiscountPercent(d)}
                  className={`flex-1 py-2 rounded-lg text-xs font-bold border transition-colors ${
                    discountPercent === d
                      ? 'bg-cyan-500/10 border-cyan-500 text-cyan-400 font-bold'
                      : 'border-white/5 bg-white/5 text-slate-300 hover:bg-white/10'
                  }`}
                >
                  {d === 0 ? t('posOrders.noDiscount') : t('posOrders.percentOff', { n: d })}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('posOrders.checkoutBill')}</h3>

            <div className="space-y-2 text-sm border-b border-white/5 pb-4">
              <div className="flex justify-between text-slate-400">
                <span>{t('common.subtotal')}</span>
                <span>JOD {subTotal.toFixed(2)}</span>
              </div>
              {discountPercent > 0 && (
                <div className="flex justify-between text-emerald-400">
                  <span>{t('common.discount')} ({discountPercent}%)</span>
                  <span>-JOD {discountAmount.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between text-slate-400">
                <span>{t('posOrders.rounding')}</span>
                <span className="font-mono text-xs">{roundingDifference >= 0 ? '+' : ''}JOD {roundingDifference.toFixed(3)}</span>
              </div>
            </div>

            <div className="flex justify-between items-baseline py-2">
              <span className="text-sm font-bold text-white">{t('posOrders.totalPayable')}</span>
              <span className="text-3xl font-black text-cyan-400">JOD {roundedTotal.toFixed(2)}</span>
            </div>

            <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-rose-400" />
                  <span className="text-xs font-bold text-slate-200">{t('posOrders.enforcePledge')}</span>
                </div>
                <input
                  type="checkbox"
                  checked={pledgeMode}
                  onChange={(e) => setPledgeMode(e.target.checked)}
                  className="w-4 h-4 cursor-pointer"
                />
              </div>
              <p className="text-[10px] text-slate-500">{t('posOrders.pledgeNote')}</p>
            </div>

            <button className="btn-primary w-full py-3 flex items-center justify-center gap-2 text-sm">
              <ShoppingBag className="w-5 h-5" />
              {pledgeMode ? t('posOrders.registerPledge') : t('posOrders.disburseReceipt')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
