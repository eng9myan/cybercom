'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, CheckCircle2, AlertTriangle, ShieldCheck, 
  Database, Play, Truck, X, Eye, PackageCheck, FileText
} from 'lucide-react';
import { useCycomList } from '@/lib/cycomModels';
import { call } from '@/lib/cycom';
import { LoadingCard } from '@/components/CycomEmptyStates';

interface WarehouseOrderRow {
  rawId: number;
  id: string;
  branch: string;
  requiredDate: string;
  priority: string;
  status: string;
  notes: string;
}

type CycomIO = {
  id: number;
  name: string;
  branch_id: number;
  required_date?: string;
  priority?: string;
  state: string;
  notes?: string;
};

const mapIO = (r: CycomIO): WarehouseOrderRow => ({
  rawId: r.id,
  id: r.name || `IO/${r.id}`,
  branch: `Branch #${r.branch_id}`,
  requiredDate: r.required_date || '—',
  priority: r.priority || 'normal',
  status: r.state || 'submitted',
  notes: r.notes || '—'
});

export default function WarehouseRequests() {
  const router = useRouter();
  const { rows: liveOrders, loading, error, reload } = useCycomList<CycomIO, WarehouseOrderRow>(
    'cy.internal.order',
    [['state', 'in', ['submitted', 'allocated']]],
    ['name', 'branch_id', 'required_date', 'priority', 'state', 'notes'],
    mapIO,
    { limit: 100 }
  );

  const [orders, setOrders] = useState<WarehouseOrderRow[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<WarehouseOrderRow | null>(null);
  const [lines, setLines] = useState<any[]>([]);
  const [allocations, setAllocations] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!loading && liveOrders) setOrders(liveOrders);
  }, [liveOrders, loading]);

  // Load Order Lines on Order Selection
  const handleSelectOrder = async (order: WarehouseOrderRow) => {
    setSelectedOrder(order);
    try {
      const lineData = await call<any[]>({
        model: 'cy.internal.order.line',
        method: 'search_read',
        args: [[['order_id', '=', order.rawId]]]
      });
      setLines(lineData || []);

      // Initialize allocations with requested_qty or already allocated_qty
      const initialAllocs: Record<string, number> = {};
      lineData?.forEach(l => {
        initialAllocs[l.id.toString()] = l.allocated_qty || l.requested_qty;
      });
      setAllocations(initialAllocs);
    } catch {}
  };

  const handleAllocChange = (lineId: number, qty: number) => {
    setAllocations({ ...allocations, [lineId.toString()]: Math.max(0, qty) });
  };

  // Submit allocation
  const handleSaveAllocations = async () => {
    if (!selectedOrder) return;
    setSaving(true);
    try {
      const res = await call<boolean>({
        model: 'cy.internal.order',
        method: 'allocate_items',
        args: [selectedOrder.rawId, allocations]
      });
      if (res) {
        alert('Stock allocated to branch request successfully!');
        // Refresh details
        handleSelectOrder(selectedOrder);
        reload();
      }
    } catch (err: any) {
      alert('Error allocating stock: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  // Dispatch shipment
  const handleDispatchOrder = async () => {
    if (!selectedOrder) return;
    setSaving(true);
    try {
      const res = await call<boolean>({
        model: 'cy.internal.order',
        method: 'dispatch_order',
        args: [selectedOrder.rawId]
      });
      if (res) {
        alert('Replenishment shipment dispatched successfully!');
        setSelectedOrder(null);
        reload();
      }
    } catch (err: any) {
      alert('Error dispatching replenishment order: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-5xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/inventory')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Warehouse Fulfillment Command
            </h1>
            <p className="text-xs text-slate-400 mt-1">Review, allocate quantities, and dispatch stock replenishment shipments to branches.</p>
          </div>
        </div>
      </div>

      {loading && <LoadingCard label="Loading branch requests…" />}
      {error && <div className="max-w-5xl mx-auto glass-card p-6 border-red-500/20 text-red-400">{error}</div>}
      
      {!loading && !error && orders.length === 0 && (
        <div className="max-w-5xl mx-auto glass-card p-12 text-center text-slate-500">
          No replenishment requests currently waiting in queue.
        </div>
      )}

      {!loading && !error && orders.length > 0 && (
        <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* List panel */}
          <div className="lg:col-span-1 glass-card p-4 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 border-b border-white/5 pb-2">
              Request Queue
            </h3>
            <div className="space-y-2">
              {orders.map((o) => (
                <div 
                  key={o.rawId} 
                  onClick={() => handleSelectOrder(o)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    selectedOrder?.rawId === o.rawId 
                      ? 'bg-indigo-600/10 border-indigo-500/40 text-slate-100' 
                      : 'bg-slate-950/40 border-slate-850 hover:bg-slate-900/40 text-slate-400'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold text-xs">{o.id}</span>
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-850">
                      {o.status}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500">{o.branch} • Required: {o.requiredDate}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Details & Action panel */}
          <div className="lg:col-span-2 space-y-6">
            {selectedOrder ? (
              <div className="glass-card p-6 space-y-6">
                {/* Order Summary */}
                <div className="flex justify-between items-start border-b border-white/5 pb-4">
                  <div>
                    <h2 className="text-lg font-bold text-white">{selectedOrder.id}</h2>
                    <p className="text-xs text-slate-400 mt-1">{selectedOrder.branch} • Status: <span className="text-indigo-400 uppercase font-semibold">{selectedOrder.status}</span></p>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={handleSaveAllocations}
                      disabled={saving}
                      className="flex items-center gap-1.5 px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition font-semibold"
                    >
                      <PackageCheck className="w-4 h-4 text-indigo-400" /> Allocate Stock
                    </button>
                    {selectedOrder.status === 'allocated' && (
                      <button 
                        onClick={handleDispatchOrder}
                        disabled={saving}
                        className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white font-semibold shadow-lg shadow-emerald-600/15 transition"
                      >
                        <Truck className="w-4 h-4" /> Dispatch Shipment
                      </button>
                    )}
                  </div>
                </div>

                {/* Line Items Table */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Replenishment Item Line allocation</h4>
                  <div className="border border-slate-850 rounded-xl overflow-hidden">
                    <table className="w-full border-collapse bg-slate-950/20 text-xs text-left">
                      <thead>
                        <tr className="bg-slate-950 text-slate-500 uppercase font-semibold border-b border-slate-850">
                          <th className="p-3">Product</th>
                          <th className="p-3 w-28 text-center">Requested</th>
                          <th className="p-3 w-28 text-center">Allocated</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {lines.map((line) => (
                          <tr key={line.id}>
                            <td className="p-3">
                              <div className="font-semibold text-slate-300">{line.product_name}</div>
                              <div className="text-[10px] text-slate-500">SKU: {line.product_code || '—'}</div>
                            </td>
                            <td className="p-3 text-center font-bold text-slate-300">{line.requested_qty}</td>
                            <td className="p-3 text-center">
                              <input 
                                type="number" min={0} max={line.requested_qty}
                                value={allocations[line.id.toString()] ?? 0}
                                onChange={e => handleAllocChange(line.id, parseInt(e.target.value))}
                                className="w-20 bg-slate-950 border border-slate-850 rounded px-2 py-1 text-slate-200 outline-none text-center"
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Notes */}
                {selectedOrder.notes && (
                  <div className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl">
                    <h5 className="text-[10px] font-bold text-slate-500 uppercase mb-1">Branch Request Notes</h5>
                    <p className="text-xs text-slate-300 leading-relaxed">{selectedOrder.notes}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="glass-card p-12 text-center text-slate-500">
                Select a replenishment request from the left panel to review and allocate stock.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
