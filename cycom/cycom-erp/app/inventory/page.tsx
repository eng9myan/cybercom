'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useCycomList, m2oName, type Many2One } from '@/lib/cycomModels';
import { 
  Package, ArrowRight, ShieldAlert, CheckCircle2, AlertTriangle, 
  RefreshCw, Info, Lock, CheckCircle, FileSpreadsheet, PackageCheck
} from 'lucide-react';

interface StockTransfer {
  id: string;
  source: string;
  destination: string;
  item: string;
  sentQty: number;
  receivedQty: number;
  date: string;
  status: 'Pending' | 'Discrepancy' | 'Resolved' | 'Dispatched';
  discrepancyReason?: string;
}

interface UserWarehouse {
  userName: string;
  role: string;
  assignedWarehouse: string;
  restricted: boolean;
}

type CycomProduct = {
  id: number;
  name?: string;
  default_code?: string;
  qty_available?: number;
  virtual_available?: number;
  uom_id?: Many2One;
  categ_id?: Many2One;
};

const mapProduct = (r: CycomProduct): StockTransfer => ({
  id: r.default_code || `PROD-${r.id}`,
  source: m2oName(r.categ_id, '—'),
  destination: m2oName(r.uom_id, '—'),
  item: r.name || '—',
  sentQty: r.qty_available ?? 0,
  receivedQty: r.virtual_available ?? 0,
  date: '—',
  status: 'Pending',
});

const INITIAL_USERS: UserWarehouse[] = [
  { userName: 'Khaled Jaber', role: 'Amman Operator', assignedWarehouse: 'HQ Warehouse Amman', restricted: true },
  { userName: 'Lina Qudah', role: 'Zarqa Clerk', assignedWarehouse: 'Zarqa Outlet', restricted: true },
  { userName: 'Yousef Ali', role: 'Logistics Manager', assignedWarehouse: 'All Warehouses', restricted: false },
];

export default function InventoryDashboard() {
  const { rows: liveProducts, loading } = useCycomList<CycomProduct, StockTransfer>(
    'product.product',
    [['type', '=', 'product']],
    ['name', 'default_code', 'qty_available', 'virtual_available', 'uom_id', 'categ_id'],
    mapProduct,
  );
  const [transfers, setTransfers] = useState<StockTransfer[]>([]);
  const [users, setUsers] = useState<UserWarehouse[]>(INITIAL_USERS);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setTransfers(liveProducts); }, [loading]);
  const [negBlockActive, setNegBlockActive] = useState(true);

  // Dispatch transfer states
  const [sourceWh, setSourceWh] = useState('HQ Warehouse Amman');
  const [destWh, setDestWh] = useState('Amman Store North');
  const [transferItem, setTransferItem] = useState('Cycom Milk Powder 400g');
  const [transferQty, setTransferQty] = useState('');
  const [currentUser, setCurrentUser] = useState('Khaled Jaber'); // restricted to HQ Warehouse

  // Mock Stock quantities in source warehouse
  const [stockQuantities, setStockQuantities] = useState<Record<string, number>>({
    'Cycom Milk Powder 400g': 120,
    'Premium Olive Oil 1L': 0, // Out of stock to test block!
    'Canned Hummus 24-Pack': 15,
    'Dry Yeast 500g': 80,
  });

  // Discrepancy modal state
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [selectedTransferId, setSelectedTransferId] = useState<string | null>(null);
  const [discReason, setDiscReason] = useState('Damaged in Transit');

  const activeUser = users.find(u => u.userName === currentUser) || users[0];

  const handleDispatch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!transferQty) return;
    const qty = parseInt(transferQty);

    // 1. Warehouse Access Restriction check
    if (activeUser.restricted && activeUser.assignedWarehouse !== sourceWh) {
      alert(`Access Violation: Operator ${activeUser.userName} is restricted to ${activeUser.assignedWarehouse}. You cannot dispatch transfers from ${sourceWh}.`);
      return;
    }

    // 2. Negative stock block check
    const currentStock = stockQuantities[transferItem] || 0;
    if (negBlockActive && qty > currentStock) {
      alert(`Transfer Blocked: Negative Stock Guard is ACTIVE. Requested quantity (${qty}) exceeds available stock (${currentStock}) of ${transferItem} in ${sourceWh}.`);
      return;
    }

    // Process Transfer dispatch
    const newTransfer: StockTransfer = {
      id: `WH-TR-${Math.floor(406 + Math.random() * 500)}`,
      source: sourceWh,
      destination: destWh,
      item: transferItem,
      sentQty: qty,
      receivedQty: 0,
      date: new Date().toISOString().split('T')[0],
      status: 'Pending'
    };

    setTransfers([newTransfer, ...transfers]);
    // Deduct stock
    setStockQuantities({
      ...stockQuantities,
      [transferItem]: currentStock - qty
    });
    setTransferQty('');
  };

  const handleResolveDiscrepancy = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTransferId) return;

    setTransfers(transfers.map(tr => {
      if (tr.id === selectedTransferId) {
        return {
          ...tr,
          status: 'Resolved',
          receivedQty: tr.sentQty, // Norm to match sent after adjustment
          discrepancyReason: discReason
        };
      }
      return tr;
    }));

    setShowResolveModal(false);
    setSelectedTransferId(null);
  };

  const toggleUserRestriction = (userName: string) => {
    setUsers(users.map(u => u.userName === userName ? { ...u, restricted: !u.restricted } : u));
  };

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Inventory & Stock Command</h1>
          <p className="page-subtitle">Track inter-warehouse stock transfers, audit item discrepancies, configure warehouse user access, and enforce negative stock blocks.</p>
        </div>
        <div className="flex gap-3">
          <Link href="/inventory/branch-orders" className="btn-primary flex items-center gap-2">
            <RefreshCw className="w-4 h-4" /> Replenishment Requests
          </Link>
          <Link href="/inventory/warehouse-requests" className="btn-secondary flex items-center gap-2">
            <PackageCheck className="w-4 h-4 text-indigo-400" /> Warehouse Fulfillment
          </Link>
          <Link href="/inventory/import" className="btn-secondary flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-emerald-500" /> Import Products
          </Link>
          <button 
            onClick={() => setNegBlockActive(!negBlockActive)}
            className={`btn-${negBlockActive ? 'primary' : 'secondary'} flex items-center gap-2`}
          >
            <Lock className="w-4 h-4" />
            {negBlockActive ? 'Negative Stock Block Active' : 'Negative Stock Allowed'}
          </button>
        </div>
      </div>

      {/* Grid Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Warehouses</span>
            <p className="text-2xl font-black text-white">4 Locations</p>
          </div>
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
            <Package className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Open Discrepancies</span>
            <p className="text-2xl font-black text-[#EF4444]">
              {transfers.filter(t => t.status === 'Discrepancy').length} transfers
            </p>
          </div>
          <div className="p-3 rounded-xl bg-red-500/10 text-red-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Negative Stock Block</span>
            <p className="text-xl font-black text-[#10B981] mt-1 flex items-center gap-1.5">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-ping" />
              {negBlockActive ? 'ENFORCED' : 'DISABLED'}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Transfers today</span>
            <p className="text-2xl font-black text-[#5DADE2]">{transfers.length}</p>
          </div>
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400">
            <RefreshCw className="w-5 h-5" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - Stock dispatch & Negative block simulator */}
        <div className="space-y-6">
          
          {/* Dispatch Stock Form */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Dispatch Stock Transfer</h2>
              <span className="text-[10px] bg-red-500/20 text-[#EF4444] border border-red-500/30 px-2 py-0.5 rounded font-bold">
                stock_location_negative_block
              </span>
            </div>

            <form onSubmit={handleDispatch} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Operator Session</label>
                  <select 
                    value={currentUser} 
                    onChange={e => setCurrentUser(e.target.value)}
                    className="input-field"
                  >
                    {users.map(u => (
                      <option key={u.userName} value={u.userName}>{u.userName} ({u.role})</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Product SKU</label>
                  <select 
                    value={transferItem} 
                    onChange={e => setTransferItem(e.target.value)}
                    className="input-field"
                  >
                    <option value="Cycom Milk Powder 400g">Milk Powder (Stock: {stockQuantities['Cycom Milk Powder 400g']})</option>
                    <option value="Premium Olive Oil 1L">Olive Oil (Stock: {stockQuantities['Premium Olive Oil 1L']})</option>
                    <option value="Canned Hummus 24-Pack">Hummus 24P (Stock: {stockQuantities['Canned Hummus 24-Pack']})</option>
                    <option value="Dry Yeast 500g">Dry Yeast (Stock: {stockQuantities['Dry Yeast 500g']})</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Source Location</label>
                  <select 
                    value={sourceWh} 
                    onChange={e => setSourceWh(e.target.value)}
                    className="input-field font-semibold"
                  >
                    <option value="HQ Warehouse Amman">HQ Warehouse Amman</option>
                    <option value="Amman Store North">Amman Store North</option>
                    <option value="Zarqa Outlet">Zarqa Outlet</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Dest. Location</label>
                  <select 
                    value={destWh} 
                    onChange={e => setDestWh(e.target.value)}
                    className="input-field"
                  >
                    <option value="Amman Store North">Amman Store North</option>
                    <option value="Zarqa Outlet">Zarqa Outlet</option>
                    <option value="Irbid Depot">Irbid Depot</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Dispatch Quantity</label>
                <input 
                  type="number" 
                  required 
                  placeholder="e.g. 25" 
                  value={transferQty}
                  onChange={e => setTransferQty(e.target.value)}
                  className="input-field font-mono"
                />
              </div>

              {/* Warnings indicators */}
              <div className="space-y-2">
                {activeUser.assignedWarehouse !== sourceWh && activeUser.restricted && (
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-[#EF4444] text-[10px] leading-relaxed">
                    Access Violation Warning: User is restricted to {activeUser.assignedWarehouse}. Submission will be blocked on dispatch.
                  </div>
                )}
                {stockQuantities[transferItem] <= 0 && (
                  <div className={`p-3 rounded-lg text-[10px] leading-relaxed border ${
                    negBlockActive ? 'bg-red-500/10 border-red-500/20 text-[#EF4444]' : 'bg-amber-500/10 border-amber-500/20 text-[#F59E0B]'
                  }`}>
                    {negBlockActive 
                      ? 'STOCK BLOCKED: Zero inventory. Negative Stock Guard is active and will reject this dispatch.'
                      : 'STOCK WARNING: Zero inventory. Negative stock is enabled; transfer will generate negative balance.'}
                  </div>
                )}
              </div>

              <button type="submit" className="btn-primary w-full py-2">
                Dispatch Transfer Stock
              </button>
            </form>
          </div>

        </div>

        {/* Right Column - Discrepancy transfers & User-Warehouse restrictions */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Transfers Table with Discrepancy Action */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Transfer Discrepancy Manager</h2>
              <span className="text-[10px] bg-red-500/20 text-[#EF4444] border border-red-500/30 px-2 py-0.5 rounded font-bold">
                stock_transfer_discrepancy_new
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Transfer ID</th>
                    <th>Product Item</th>
                    <th>Source ➔ Dest</th>
                    <th>Qty Sent</th>
                    <th>Qty Received</th>
                    <th>Diff</th>
                    <th>Status</th>
                    <th className="text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {transfers.map(tr => {
                    const diff = tr.sentQty - tr.receivedQty;
                    return (
                      <tr key={tr.id}>
                        <td className="font-mono text-xs">{tr.id}</td>
                        <td className="font-bold text-slate-300">{tr.item}</td>
                        <td className="text-xs text-slate-400">{tr.source.split(' ')[0]} ➔ {tr.destination.split(' ')[0]}</td>
                        <td className="font-mono text-slate-300">{tr.sentQty}</td>
                        <td className="font-mono text-slate-300">{tr.receivedQty}</td>
                        <td className="font-mono font-bold">
                          {tr.status === 'Discrepancy' ? (
                            <span className="text-red-400">-{diff}</span>
                          ) : (
                            <span className="text-slate-500">0</span>
                          )}
                        </td>
                        <td>
                          <span className={`badge text-[9px] ${
                            tr.status === 'Resolved' ? 'badge-green' :
                            tr.status === 'Discrepancy' ? 'badge-red' : 'badge-yellow'
                          }`}>{tr.status}</span>
                        </td>
                        <td className="text-right">
                          {tr.status === 'Discrepancy' && (
                            <button 
                              onClick={() => { setSelectedTransferId(tr.id); setShowResolveModal(true); }}
                              className="p-1 px-2 text-[10px] font-bold rounded bg-red-500/10 hover:bg-red-500/20 border border-red-500/25 text-[#EF4444]"
                            >
                              Resolve
                            </button>
                          )}
                          {tr.status === 'Resolved' && tr.discrepancyReason && (
                            <span className="text-[10px] text-slate-500 italic font-medium">{tr.discrepancyReason}</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* User Warehouse Access Limits */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Warehouse Access Restrictions</h2>
              <span className="text-[10px] bg-blue-500/20 text-[#5DADE2] border border-blue-500/30 px-2 py-0.5 rounded font-bold">
                warehouse_restriction_for_user
              </span>
            </div>

            <div className="space-y-3">
              {users.map(user => (
                <div key={user.userName} className="p-3.5 rounded-xl bg-white/3 border border-white/5 flex items-center justify-between hover:border-white/10 transition-colors">
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-white">{user.userName}</p>
                    <p className="text-[10px] text-slate-400">{user.role} · Allowed Node: <strong className="text-slate-200">{user.assignedWarehouse}</strong></p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`badge text-[9px] ${user.restricted ? 'badge-orange' : 'badge-cyan'}`}>
                      {user.restricted ? 'Restricted' : 'Universal'}
                    </span>
                    <button 
                      onClick={() => toggleUserRestriction(user.userName)}
                      className="p-1 px-2 text-[10px] rounded hover:bg-white/5 border border-white/10 text-slate-300 font-bold"
                    >
                      Toggle Lock
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

      {/* Discrepancy Resolution Modal */}
      <AnimatePresence>
        {showResolveModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-[#0b0f19] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-5"
            >
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Resolve Stock Discrepancy</h3>
                <button onClick={() => setShowResolveModal(false)} className="text-slate-500 hover:text-white text-xs">Cancel</button>
              </div>

              <form onSubmit={handleResolveDiscrepancy} className="space-y-4 text-xs">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Adjustment Reason</label>
                  <select 
                    value={discReason} 
                    onChange={e => setDiscReason(e.target.value)}
                    className="input-field"
                  >
                    <option value="Damaged in Transit">Damaged in Transit (Writedown)</option>
                    <option value="Stock Shortage Supplier">Stock Shortage from Supplier</option>
                    <option value="Corrected Mismatch">Corrected Scan Mismatch</option>
                    <option value="Other">Other Adjustment</option>
                  </select>
                </div>
                <p className="text-[10px] text-slate-500 leading-normal">
                  Note: Resolving discrepancy adjusts physical inventory records at the destination warehouse to match the validated quantity and logs an accounting variance line.
                </p>
                <div className="flex justify-end gap-3 pt-3 border-t border-white/5">
                  <button 
                    type="button" 
                    onClick={() => setShowResolveModal(false)} 
                    className="btn-secondary py-1.5"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="btn-primary py-1.5"
                  >
                    Resolve Discrepancy
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
