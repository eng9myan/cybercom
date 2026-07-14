'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, CheckCircle2, AlertTriangle, ShieldCheck, 
  Database, Play, Truck, X, FileText, CheckCircle
} from 'lucide-react';
import { call } from '@/lib/cycom';
import { LoadingCard } from '@/components/CycomEmptyStates';

interface OrderDetails {
  id: number;
  name: string;
  branch_id: number;
  required_date?: string;
  notes?: string;
  state: string;
}

interface OrderLine {
  id: number;
  product_name: string;
  product_code: string;
  requested_qty: number;
  shipped_qty: number;
}

export default function ReceiveReplenishment() {
  const router = useRouter();
  const params = useParams();
  const idStr = params?.id as string;
  const orderId = parseInt(idStr);

  const [order, setOrder] = useState<OrderDetails | null>(null);
  const [lines, setLines] = useState<OrderLine[]>([]);
  const [loading, setLoading] = useState(true);
  const [receipts, setReceipts] = useState<Record<string, { received_qty: number; reason: string }>>({});
  const [saving, setSaving] = useState(false);

  // Fetch order details & lines
  useEffect(() => {
    const fetchOrderDetails = async () => {
      if (!orderId) return;
      try {
        const oData = await call<any>({
          model: 'cy.internal.order',
          method: 'read',
          args: [orderId]
        });

        const lineData = await call<any[]>({
          model: 'cy.internal.order.line',
          method: 'search_read',
          args: [[['order_id', '=', orderId]]]
        });

        if (oData) {
          setOrder(oData);
          setLines(lineData || []);

          // Initialize receipts state
          const initialReceipts: Record<string, { received_qty: number; reason: string }> = {};
          lineData?.forEach(l => {
            initialReceipts[l.id.toString()] = { received_qty: l.shipped_qty, reason: '' };
          });
          setReceipts(initialReceipts);
        }
      } catch (err: any) {
        alert('Error loading order details: ' + err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchOrderDetails();
  }, [orderId]);

  const handleQtyChange = (lineId: number, qty: number, maxQty: number) => {
    const key = lineId.toString();
    const current = receipts[key] || { received_qty: maxQty, reason: '' };
    const nextQty = Math.max(0, Math.min(maxQty, qty));
    setReceipts({
      ...receipts,
      [key]: { ...current, received_qty: nextQty }
    });
  };

  const handleReasonChange = (lineId: number, reason: string) => {
    const key = lineId.toString();
    const current = receipts[key] || { received_qty: 0, reason: '' };
    setReceipts({
      ...receipts,
      [key]: { ...current, reason }
    });
  };

  // Submit Receipt
  const handleConfirmReceipt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderId) return;
    setSaving(true);
    try {
      const res = await call<boolean>({
        model: 'cy.internal.order',
        method: 'receive_order',
        args: [orderId, receipts]
      });
      if (res) {
        alert('Stock receipt confirmed successfully!');
        router.push('/inventory/branch-orders');
      }
    } catch (err: any) {
      alert('Error confirming receipt: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8"><LoadingCard label="Loading replenishment logs…" /></div>;
  if (!order) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-center text-slate-400 font-medium">Request record not found.</div>;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      {/* Header */}
      <div className="max-w-4xl mx-auto flex items-center gap-4 mb-8">
        <button 
          onClick={() => router.push('/inventory/branch-orders')}
          className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
        >
          <ArrowLeft className="w-5 h-5 text-slate-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            Confirm Replenishment Receipt: {order.name}
          </h1>
          <p className="text-xs text-slate-400 mt-1">Branch #{order.branch_id} • Status: <span className="text-purple-400 uppercase font-semibold">{order.state}</span></p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto bg-slate-900/40 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl">
        <form onSubmit={handleConfirmReceipt} className="space-y-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 border-b border-white/5 pb-2">
            Verify Dispatched Packages
          </h3>

          <div className="border border-slate-850 rounded-xl overflow-hidden">
            <table className="w-full border-collapse bg-slate-950/20 text-xs text-left">
              <thead>
                <tr className="bg-slate-950 text-slate-500 uppercase font-semibold border-b border-slate-850">
                  <th className="p-3">Product</th>
                  <th className="p-3 w-28 text-center">Shipped Qty</th>
                  <th className="p-3 w-28 text-center">Received Qty</th>
                  <th className="p-3 text-left">Discrepancy Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {lines.map((line) => {
                  const lineKey = line.id.toString();
                  const recData = receipts[lineKey] || { received_qty: line.shipped_qty, reason: '' };
                  const hasDiscrepancy = recData.received_qty < line.shipped_qty;

                  return (
                    <tr key={line.id}>
                      <td className="p-3">
                        <div className="font-semibold text-slate-300">{line.product_name}</div>
                        <div className="text-[10px] text-slate-500">SKU: {line.product_code || '—'}</div>
                      </td>
                      <td className="p-3 text-center font-bold text-slate-400">{line.shipped_qty}</td>
                      <td className="p-3 text-center">
                        <input 
                          type="number" min={0} max={line.shipped_qty} required
                          value={recData.received_qty}
                          onChange={e => handleQtyChange(line.id, parseInt(e.target.value), line.shipped_qty)}
                          className="w-20 bg-slate-950 border border-slate-850 rounded px-2 py-1 text-slate-200 outline-none text-center"
                        />
                      </td>
                      <td className="p-3">
                        {hasDiscrepancy ? (
                          <input 
                            type="text" required
                            placeholder="e.g. Broken packaging, missing items"
                            value={recData.reason}
                            onChange={e => handleReasonChange(line.id, e.target.value)}
                            className="w-full bg-slate-950 border border-rose-500/20 rounded px-3 py-1.5 text-slate-200 outline-none focus:border-rose-500/50"
                          />
                        ) : (
                          <span className="text-slate-500 italic">No discrepancy</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {order.notes && (
            <div className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl text-xs">
              <h5 className="text-[10px] font-bold text-slate-500 uppercase mb-1">Request Notes</h5>
              <p className="text-slate-300 leading-relaxed">{order.notes}</p>
            </div>
          )}

          <div className="flex justify-end gap-3 border-t border-white/5 pt-6">
            <button 
              type="button" onClick={() => router.push('/inventory/branch-orders')}
              className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition font-semibold"
            >
              Cancel
            </button>
            <button 
              type="submit" disabled={saving}
              className="flex items-center gap-1.5 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white font-semibold shadow-lg shadow-emerald-600/15 transition disabled:opacity-50"
            >
              <CheckCircle className="w-4 h-4" /> Confirm & Log Receipt
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
