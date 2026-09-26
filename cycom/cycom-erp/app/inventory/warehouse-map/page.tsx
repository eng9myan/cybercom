'use client';

// Warehouse map: zone > aisle > rack > shelf > bin, with stock rolled up
// from bins to their parents server-side (inventory.layout.build_layout).
//
// Deliberately a clear 2D map rather than a 3D render: an operator is
// looking for "which bin is full / where is this stock", and a flat map
// answers that faster than a rotatable warehouse model.

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft, Warehouse as WarehouseIcon, Boxes, PackageOpen, ChevronRight, AlertTriangle,
} from 'lucide-react';
import { useT } from '@/lib/i18n';

interface LocationNode {
  id: string;
  code: string;
  name: string;
  location_type: string;
  capacity: number | null;
  occupancy_percent: number | null;
  direct_quantity: number;
  total_quantity: number;
  total_value: number;
  total_product_count: number;
  children: LocationNode[];
}

interface Layout {
  warehouse: { id: string; code: string; name: string };
  tree: LocationNode[];
  unassigned: { quantity: number; value: number; product_count: number };
  totals: { locations: number; bins: number; quantity: number; value: number };
}

interface WarehouseRow { id: string; code: string; name: string }

function occupancyTone(pct: number | null) {
  if (pct === null) return 'bg-slate-800 border-slate-700 text-slate-400';
  if (pct >= 100) return 'bg-rose-950/60 border-rose-500/40 text-rose-300';
  if (pct >= 75) return 'bg-amber-950/60 border-amber-500/40 text-amber-300';
  if (pct >= 40) return 'bg-cyan-950/60 border-cyan-500/40 text-cyan-300';
  if (pct > 0) return 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300';
  return 'bg-slate-900/60 border-slate-800 text-slate-500';
}

function LocationCard({ node, depth }: { node: LocationNode; depth: number }) {
  const t = useT();
  const isLeaf = node.children.length === 0;
  return (
    <div className={depth === 0 ? 'glass-card p-4' : ''}>
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          {depth > 0 && <ChevronRight className="w-3 h-3 text-slate-600 flex-shrink-0 rtl:-scale-x-100" />}
          <span className="font-semibold text-slate-200 truncate">{node.code}</span>
          {node.name && <span className="text-[10px] text-slate-500 truncate">{node.name}</span>}
          <span className="text-[9px] uppercase tracking-wider text-slate-600 border border-slate-800 rounded px-1.5 py-0.5 flex-shrink-0">
            {node.location_type}
          </span>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 text-[10px]">
          <span className="text-slate-400 font-mono">{node.total_quantity.toLocaleString()}</span>
          {node.occupancy_percent !== null ? (
            <span className={`font-mono font-bold ${
              node.occupancy_percent >= 100 ? 'text-rose-400'
                : node.occupancy_percent >= 75 ? 'text-amber-400' : 'text-slate-400'
            }`}>
              {node.occupancy_percent}%
            </span>
          ) : (
            <span className="text-slate-600" title={t('warehouseMap.noCapacity')}>—</span>
          )}
        </div>
      </div>

      {isLeaf ? (
        <div
          className={`rounded-lg border px-3 py-2 text-[10px] ${occupancyTone(node.occupancy_percent)}`}
          title={node.capacity ? `${node.total_quantity} / ${node.capacity}` : t('warehouseMap.noCapacity')}
        >
          {node.total_product_count > 0
            ? t('warehouseMap.binSummary', {
                products: String(node.total_product_count),
                qty: node.total_quantity.toLocaleString(),
              })
            : t('warehouseMap.binEmpty')}
        </div>
      ) : (
        <div className={`grid gap-2 ${depth === 0 ? 'md:grid-cols-2 xl:grid-cols-3' : 'grid-cols-1'} ${depth > 0 ? 'ps-3 border-s border-white/5' : ''}`}>
          {node.children.map((child) => (
            <div key={child.id} className={depth === 0 ? 'bg-slate-950/40 border border-slate-850 rounded-xl p-3' : ''}>
              <LocationCard node={child} depth={depth + 1} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function WarehouseMapPage() {
  const t = useT();
  const router = useRouter();

  const [warehouses, setWarehouses] = useState<WarehouseRow[]>([]);
  const [warehouseId, setWarehouseId] = useState('');
  const [layout, setLayout] = useState<Layout | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/cycom/rest/inventory/warehouses/', { credentials: 'include' })
      .then((r) => r.json())
      .then((d) => {
        const rows = (d.results || d) as WarehouseRow[];
        setWarehouses(rows);
        if (rows.length) setWarehouseId(rows[0].id);
      })
      .catch((err) => setError(t('warehouseMap.loadFailed', { msg: err.message })));
  }, [t]);

  const load = useCallback(async () => {
    if (!warehouseId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/cycom/rest/inventory/warehouses/${warehouseId}/layout/`, {
        credentials: 'include',
      });
      const data = await res.json();
      if (res.ok) setLayout(data);
      else setError(t('warehouseMap.loadFailed', { msg: data.detail || res.statusText }));
    } catch (err: any) {
      setError(t('warehouseMap.loadFailed', { msg: err.message }));
    } finally {
      setLoading(false);
    }
  }, [warehouseId, t]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-6xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/inventory')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent flex items-center gap-2">
              <WarehouseIcon className="w-6 h-6 text-amber-400" /> {t('warehouseMap.title')}
            </h1>
            <p className="text-xs text-slate-400 mt-1">{t('warehouseMap.subtitle')}</p>
          </div>
        </div>
        <select
          value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)}
          className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none min-w-[220px]"
        >
          {warehouses.length === 0 && <option value="">{t('warehouseMap.noWarehouses')}</option>}
          {warehouses.map((w) => <option key={w.id} value={w.id}>{w.code} — {w.name}</option>)}
        </select>
      </div>

      <div className="max-w-6xl mx-auto space-y-6">
        {error && (
          <div className="flex items-start gap-3 px-4 py-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {layout && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { icon: Boxes, label: t('warehouseMap.locations'), value: String(layout.totals.locations) },
                { icon: PackageOpen, label: t('warehouseMap.bins'), value: String(layout.totals.bins) },
                { icon: Boxes, label: t('warehouseMap.totalQty'), value: layout.totals.quantity.toLocaleString() },
                { icon: Boxes, label: t('warehouseMap.totalValue'), value: layout.totals.value.toLocaleString() },
              ].map((c, i) => (
                <div key={i} className="glass-card p-4">
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                    <c.icon className="w-3.5 h-3.5" /> {c.label}
                  </div>
                  <div className="mt-1 text-lg font-bold font-mono text-slate-200">{c.value}</div>
                </div>
              ))}
            </div>

            {layout.unassigned.quantity > 0 && (
              <div className="flex items-center justify-between gap-4 px-4 py-3 rounded-lg border bg-amber-950/30 border-amber-500/20 text-amber-300">
                <span className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  {t('warehouseMap.unassignedNote', {
                    qty: layout.unassigned.quantity.toLocaleString(),
                    products: String(layout.unassigned.product_count),
                  })}
                </span>
              </div>
            )}

            {layout.tree.length === 0 ? (
              <div className="glass-card p-12 text-center text-slate-500">{t('warehouseMap.noLayout')}</div>
            ) : (
              <div className="space-y-4">
                {layout.tree.map((zone) => <LocationCard key={zone.id} node={zone} depth={0} />)}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-5 text-[10px] text-slate-500">
              {[
                ['bg-slate-900/60 border-slate-800', t('warehouseMap.legendEmpty')],
                ['bg-emerald-950/60 border-emerald-500/40', t('warehouseMap.legendLow')],
                ['bg-cyan-950/60 border-cyan-500/40', t('warehouseMap.legendMedium')],
                ['bg-amber-950/60 border-amber-500/40', t('warehouseMap.legendHigh')],
                ['bg-rose-950/60 border-rose-500/40', t('warehouseMap.legendFull')],
                ['bg-slate-800 border-slate-700', t('warehouseMap.legendUnknown')],
              ].map(([cls, label]) => (
                <span key={label} className="flex items-center gap-2">
                  <span className={`w-5 h-3 rounded border ${cls}`} /> {label}
                </span>
              ))}
            </div>
          </>
        )}

        {loading && <div className="glass-card p-12 text-center text-slate-500">{t('warehouseMap.loading')}</div>}
      </div>
    </div>
  );
}
