'use client';

import React, { useState } from 'react';
import { ShoppingBag, AlertTriangle, ShieldCheck } from 'lucide-react';
import { useCycomList, m2oName, type Many2One } from '@/lib/cycomModels';
import { useT } from '@/lib/i18n';

type CySaleOrderItem = {
  id: number;
  name?: string;
  partner_id?: Many2One;
  date_order?: string;
  amount_total?: number;
  state?: string;
  user_id?: Many2One;
};

const mapSaleOrderItem = (r: CySaleOrderItem) => ({
  id: r.name || `SO-${r.id}`,
  name: m2oName(r.partner_id, '—'),
  listPrice: r.amount_total ?? 0,
  minPrice: 0,
  customPrice: r.amount_total ?? 0,
  qty: 1,
  error: false,
});

export default function SalesOrderCreation() {
  const t = useT();
  const { rows: baseItems, loading } = useCycomList<CySaleOrderItem, ReturnType<typeof mapSaleOrderItem>>(
    'sale.order',
    [],
    ['name', 'partner_id', 'date_order', 'amount_total', 'state', 'user_id'],
    mapSaleOrderItem,
    { order: 'date_order desc' },
  );
  const [priceOverrides, setPriceOverrides] = useState<Record<string, { customPrice: number; error: boolean }>>({});
  const items = baseItems.map((item) => ({ ...item, ...(priceOverrides[item.id] || {}) }));
  const [customer] = useState('Cycom Trading Est');

  const updatePrice = (id: string, priceVal: number) => {
    const baseItem = baseItems.find((i) => i.id === id);
    const hasError = baseItem ? priceVal < baseItem.minPrice : false;
    setPriceOverrides((prev) => ({ ...prev, [id]: { customPrice: priceVal, error: hasError } }));
  };

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>{t('common.loading')}</div>;

  const total = items.reduce((acc, curr) => acc + curr.customPrice * curr.qty, 0);
  const hasValidationExceptions = items.some((item) => item.error);

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('salesOrders.title')}</h1>
          <p className="page-subtitle">{t('salesOrders.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-white/5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('salesOrders.orderLines')}</h2>
              <span className="badge badge-purple">{customer}</span>
            </div>

            <div className="space-y-4">
              {items.map((item) => (
                <div key={item.id} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-3">
                  <div className="flex justify-between">
                    <div>
                      <h4 className="font-bold text-slate-200">{item.name}</h4>
                      <span className="text-[10px] font-mono text-slate-500">SKU: {item.id} • {t('salesOrders.listPrice')}: JOD {item.listPrice.toFixed(2)}</span>
                    </div>
                    <span className="badge badge-cyan">{t('salesOrders.qtyUnits', { n: item.qty })}</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <div>
                      <label className="text-xs text-slate-400 block mb-1">{t('salesOrders.overrideUnitPrice')}</label>
                      <input
                        type="number"
                        step="0.05"
                        className="input-field font-mono"
                        value={item.customPrice}
                        onChange={(e) => updatePrice(item.id, parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div className="flex items-center text-xs">
                      {item.error ? (
                        <div className="text-rose-400 flex items-center gap-1.5 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20">
                          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                          <span>{t('salesOrders.belowFloor', { min: item.minPrice.toFixed(2) })}</span>
                        </div>
                      ) : (
                        <div className="text-emerald-400 flex items-center gap-1.5 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                          <ShieldCheck className="w-4 h-4 flex-shrink-0" />
                          <span>{t('salesOrders.withinBounds')}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('salesOrders.checkout')}</h3>

            <div className="space-y-2 text-sm border-b border-white/5 pb-4 text-slate-400">
              <div className="flex justify-between">
                <span>{t('salesOrders.totalLines')}</span>
                <span className="text-white font-bold">{t('salesOrders.itemsN', { n: items.length })}</span>
              </div>
              <div className="flex justify-between">
                <span>{t('salesOrders.calculatedTotal')}</span>
                <span className="text-white font-bold">JOD {total.toFixed(2)}</span>
              </div>
            </div>

            {hasValidationExceptions && (
              <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 space-y-2">
                <div className="flex items-center gap-1.5 font-bold">
                  <AlertTriangle className="w-4 h-4" />
                  <span>{t('salesOrders.validationExceptions')}</span>
                </div>
                <p className="leading-relaxed">{t('salesOrders.validationBody')}</p>
              </div>
            )}

            <button className="btn-primary w-full py-3 flex items-center justify-center gap-2 text-sm">
              <ShoppingBag className="w-5 h-5" />
              {hasValidationExceptions ? t('salesOrders.submitForApproval') : t('salesOrders.confirmDisburse')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
