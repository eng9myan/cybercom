'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, Plus, Send, RefreshCw, FileText, CheckCircle2, 
  AlertTriangle, Truck, Clock, X, Search, Trash2
} from 'lucide-react';
import { useCycomList, fmtCode } from '@/lib/cycomModels';
import { call } from '@/lib/cycom';
import { LoadingCard } from '@/components/CycomEmptyStates';

interface InternalOrderRow {
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

const mapIO = (r: CycomIO): InternalOrderRow => ({
  rawId: r.id,
  id: r.name || `IO/${r.id}`,
  branch: `Branch #${r.branch_id}`,
  requiredDate: r.required_date || '—',
  priority: r.priority || 'normal',
  status: r.state || 'draft',
  notes: r.notes || '—'
});

const STATUS_BADGE: Record<string, string> = {
  draft: 'bg-slate-800 text-slate-400 border border-slate-700',
  submitted: 'bg-blue-950/40 text-blue-400 border border-blue-500/20',
  allocated: 'bg-indigo-950/40 text-indigo-400 border border-indigo-500/20',
  dispatched: 'bg-purple-950/40 text-purple-400 border border-purple-500/20 animate-pulse',
  received: 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/20',
  partially_received: 'bg-amber-950/40 text-amber-400 border border-amber-500/20',
  cancelled: 'bg-rose-950/40 text-rose-400 border border-rose-500/20'
};

export default function BranchOrders() {
  const router = useRouter();
  const { rows: liveOrders, loading, error, reload } = useCycomList<CycomIO, InternalOrderRow>(
    'cy.internal.order',
    [],
    ['name', 'branch_id', 'required_date', 'priority', 'state', 'notes'],
    mapIO,
    { limit: 100 }
  );

  const [orders, setOrders] = useState<InternalOrderRow[]>([]);
  const [showModal, setShowModal] = useState(false);
  
  // Search & Selector for products in wizard
  const [searchTerm, setSearchTerm] = useState('');
  const [products, setProducts] = useState<any[]>([]);
  const [cart, setCart] = useState<Array<{ id: number; name: string; code: string; qty: number }>>([]);
  const [requiredDate, setRequiredDate] = useState('');
  const [priority, setPriority] = useState('normal');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (!loading && liveOrders) setOrders(liveOrders);
  }, [liveOrders, loading]);

  // Fetch product catalog on modal open
  useEffect(() => {
    if (showModal) {
      const fetchCatalog = async () => {
        try {
          const res = await call<any[]>({
            model: 'inventory.product',
            method: 'search_read',
            args: [[['name', 'like', `%${searchTerm}%`]], ['name', 'code']]
          });
          setProducts(res || []);
        } catch {}
      };
      const debounce = setTimeout(fetchCatalog, 300);
      return () => clearTimeout(debounce);
    }
  }, [showModal, searchTerm]);

  const addToCart = (p: any) => {
    if (cart.find(x => x.id === p.id)) return;
    setCart([...cart, { id: p.id, name: p.name, code: p.code || '—', qty: 1 }]);
  };

  const updateCartQty = (idx: number, qty: number) => {
    const next = [...cart];
    next[idx].qty = Math.max(1, qty);
    setCart(next);
  };

  const removeFromCart = (idx: number) => {
    setCart(cart.filter((_, i) => i !== idx));
  };

  // Submit Order Creation
  const handleSubmitOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cart.length === 0) {
      alert('Cart is empty. Please add at least one product.');
      return;
    }

    try {
      const ioId = await call<number>({
        model: 'cy.internal.order',
        method: 'create',
        args: [{
          name: `IO/${new Date().getFullYear()}/BR1/${Math.floor(1000 + Math.random() * 9000)}`,
          branch_id: 1,
          required_date: requiredDate || null,
          priority,
          notes,
          state: 'draft'
        }]
      });

      if (ioId) {
        // Create order lines
        for (const item of cart) {
          await call({
            model: 'cy.internal.order.line',
            method: 'create',
            args: [{
              order_id: ioId,
              product_id: item.id,
              product_name: item.name,
              product_code: item.code,
              requested_qty: item.qty,
              allocated_qty: 0,
              shipped_qty: 0,
              received_qty: 0,
              line_state: 'pending'
            }]
          });
        }

        // Submit for review
        await call({
          model: 'cy.internal.order',
          method: 'submit_for_review',
          args: [ioId]
        });

        alert('Replenishment request submitted successfully!');
        setShowModal(false);
        setCart([]);
        setNotes('');
        reload();
      }
    } catch (err: any) {
      alert('Error creating internal order: ' + err.message);
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
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
              Branch Replenishment Requests
            </h1>
            <p className="text-xs text-slate-400 mt-1">Request stock transfers from the central warehouse and receive inventory packages.</p>
          </div>
        </div>

        <button 
          onClick={() => setShowModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> New Replenishment Request
        </button>
      </div>

      {loading && <LoadingCard label="Loading replenishment logs…" />}
      {error && <div className="max-w-5xl mx-auto glass-card p-6 border-red-500/20 text-red-400">{error}</div>}
      
      {!loading && !error && orders.length === 0 && (
        <div className="max-w-5xl mx-auto glass-card p-12 text-center text-slate-500">
          No replenishment requests logged yet. Click 'New Replenishment Request' to create one.
        </div>
      )}

      {!loading && !error && orders.length > 0 && (
        <div className="max-w-5xl mx-auto glass-card p-6">
          <div className="overflow-x-auto">
            <table className="data-table w-full border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  <th className="pb-3 text-left">Order Reference</th>
                  <th className="pb-3 text-left">Branch</th>
                  <th className="pb-3 text-left">Required Date</th>
                  <th className="pb-3 text-left">Priority</th>
                  <th className="pb-3 text-left">Fulfillment Status</th>
                  <th className="pb-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {orders.map((o) => (
                  <tr key={o.rawId} className="hover:bg-white/[0.01] transition-all">
                    <td className="py-4 font-mono text-slate-300 font-bold">{o.id}</td>
                    <td className="py-4 text-slate-400">{o.branch}</td>
                    <td className="py-4 text-slate-400">{o.requiredDate}</td>
                    <td className="py-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                        o.priority === 'urgent' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {o.priority}
                      </span>
                    </td>
                    <td className="py-4">
                      <span className={`px-2.5 py-1 text-[10px] font-bold uppercase rounded-md tracking-wider ${STATUS_BADGE[o.status] || STATUS_BADGE['draft']}`}>
                        {o.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-4 text-right">
                      {o.status === 'dispatched' && (
                        <Link 
                          href={`/inventory/branch-orders/${o.rawId}/receive`}
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded text-xs font-semibold text-white transition flex items-center gap-1.5 inline-flex"
                        >
                          <Truck className="w-3.5 h-3.5" /> Confirm Receipt
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* New Request Modal */}
      <AnimatePresence>
        {showModal && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-2xl shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h3 className="font-bold text-slate-200">New Replenishment Request</h3>
                <button onClick={() => setShowModal(false)} className="p-1 hover:bg-slate-800 rounded-lg transition">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleSubmitOrder} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs text-slate-400">Required Date</label>
                    <input 
                      type="date" required
                      value={requiredDate} onChange={e => setRequiredDate(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-slate-400">Priority</label>
                    <select 
                      value={priority} onChange={e => setPriority(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    >
                      <option value="low">Low</option>
                      <option value="normal">Normal</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                </div>

                {/* Product Search & Cart */}
                <div className="space-y-2 border-t border-white/5 pt-3">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Add Items to Replenish</label>
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input 
                      type="text" placeholder="Search catalog by name or code..."
                      value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg pl-9 pr-3 py-2 text-slate-200 outline-none"
                    />
                  </div>

                  {/* Search Results list */}
                  {searchTerm && products.length > 0 && (
                    <div className="bg-slate-950 border border-slate-850 rounded-lg max-h-40 overflow-y-auto divide-y divide-white/5">
                      {products.map(p => (
                        <div 
                          key={p.id} onClick={() => addToCart(p)}
                          className="p-2.5 flex items-center justify-between cursor-pointer hover:bg-slate-900/60"
                        >
                          <div>
                            <span className="font-semibold text-slate-300">{p.name}</span>
                            <span className="text-[10px] text-slate-500 ml-2">SKU: {p.code || '—'}</span>
                          </div>
                          <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded">Add</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Cart list */}
                {cart.length > 0 && (
                  <div className="border border-slate-850 rounded-xl overflow-hidden">
                    <table className="w-full border-collapse bg-slate-950/20 text-xs">
                      <thead>
                        <tr className="bg-slate-950 text-slate-500 uppercase font-semibold border-b border-slate-850">
                          <th className="p-3 text-left">Product</th>
                          <th className="p-3 text-left w-24">Qty Requested</th>
                          <th className="p-3 text-right w-16">Remove</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {cart.map((item, idx) => (
                          <tr key={item.id}>
                            <td className="p-3">
                              <div className="font-semibold text-slate-300">{item.name}</div>
                              <div className="text-[10px] text-slate-500">SKU: {item.code}</div>
                            </td>
                            <td className="p-3">
                              <input 
                                type="number" min={1} required
                                value={item.qty} onChange={e => updateCartQty(idx, parseInt(e.target.value))}
                                className="w-full bg-slate-950 border border-slate-850 rounded px-2 py-1 text-slate-200 outline-none text-center"
                              />
                            </td>
                            <td className="p-3 text-right">
                              <button 
                                type="button" onClick={() => removeFromCart(idx)}
                                className="p-1 hover:bg-red-500/10 rounded text-rose-400"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Request Notes</label>
                  <textarea 
                    rows={3} placeholder="Provide any extra details or instructions..."
                    value={notes} onChange={e => setNotes(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg p-3 text-slate-200 outline-none"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-white/5">
                  <button 
                    type="button" onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition text-xs font-semibold"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-semibold shadow-lg shadow-blue-600/15 transition text-xs"
                  >
                    <Send className="w-4 h-4" /> Send Replenishment Request
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
