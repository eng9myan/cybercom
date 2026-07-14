'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useCycomList, m2oName, fmtDate, type Many2One } from '@/lib/cycomModels';
import { 
  CreditCard, TrendingUp, Users, Percent, Shield, ArrowUpRight, 
  Search, Sliders, CheckSquare, Square, RefreshCcw, DollarSign 
} from 'lucide-react';

interface Contract {
  id: string;
  customer: string;
  plan: 'Standard ERP' | 'Premium Cloud' | 'POS Dedicated Support' | 'Custom SLA';
  cost: number;
  renewal: string;
  status: 'Active' | 'Trial' | 'Suspended';
}

type CycomSaleOrder = {
  id: number;
  name?: string;
  partner_id?: Many2One;
  recurring_monthly?: number;
  stage_id?: Many2One;
  next_invoice_date?: string;
};

const mapSaleOrder = (r: CycomSaleOrder): Contract => {
  const stageName = m2oName(r.stage_id, '').toLowerCase();
  const status: Contract['status'] =
    stageName.includes('trial') ? 'Trial' :
    stageName.includes('suspend') || stageName.includes('cancel') ? 'Suspended' :
    'Active';
  return {
    id: r.name || `SUB-${r.id}`,
    customer: m2oName(r.partner_id, '—'),
    plan: 'Standard ERP',
    cost: r.recurring_monthly ?? 0,
    renewal: fmtDate(r.next_invoice_date),
    status,
  };
};

export default function SubscriptionsPage() {
  const { rows: liveContracts, loading } = useCycomList<CycomSaleOrder, Contract>(
    'sale.order',
    [['is_subscription', '=', true]],
    ['name', 'partner_id', 'recurring_monthly', 'stage_id', 'next_invoice_date'],
    mapSaleOrder,
  );
  const [contracts, setContracts] = useState<Contract[]>([]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setContracts(liveContracts); }, [loading]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('All');
  
  // Interactive Simulator variables
  const [simUsers, setSimUsers] = useState<number>(15);
  const [simNodes, setSimNodes] = useState<number>(4);
  const [hasSLA, setHasSLA] = useState<boolean>(true);

  // Math totals
  const totalMRR = contracts
    .filter(c => c.status === 'Active' || c.status === 'Trial')
    .reduce((sum, c) => sum + c.cost, 0);

  const activeCount = contracts.filter(c => c.status === 'Active').length;
  const trialCount = contracts.filter(c => c.status === 'Trial').length;

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    const visibleIds = filteredContracts.map(c => c.id);
    const allSelected = visibleIds.every(id => selectedIds.includes(id));
    if (allSelected) {
      setSelectedIds(prev => prev.filter(id => !visibleIds.includes(id)));
    } else {
      setSelectedIds(prev => Array.from(new Set([...prev, ...visibleIds])));
    }
  };

  // Bulk simulation action
  const handleBulkRenew = () => {
    if (selectedIds.length === 0) return;
    setContracts(prev => prev.map(c => {
      if (selectedIds.includes(c.id)) {
        return {
          ...c,
          status: 'Active',
          renewal: '2026-08-01'
        };
      }
      return c;
    }));
    setSelectedIds([]);
  };

  const handleBulkSuspend = () => {
    if (selectedIds.length === 0) return;
    setContracts(prev => prev.map(c => {
      if (selectedIds.includes(c.id)) {
        return {
          ...c,
          status: 'Suspended'
        };
      }
      return c;
    }));
    setSelectedIds([]);
  };

  // Pricing calculator logic
  const calcBasePrice = () => {
    const userPrice = simUsers * 15; // 15 JOD per user
    const nodePrice = simNodes * 45; // 45 JOD per POS node
    const slaFee = hasSLA ? 250 : 0;
    return userPrice + nodePrice + slaFee;
  };

  const filteredContracts = contracts.filter(c => {
    if (filterStatus === 'All') return true;
    return c.status === filterStatus;
  });

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>Loading...</div>;

  return (
    <div className="space-y-6 max-w-[1200px] mx-auto">
      {/* Page Header */}
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title text-white">Subscriptions & Contract Billing</h1>
          <p className="page-subtitle">Manage customer recurring services, monthly active licenses, and SaaS contracts.</p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs text-slate-500">
          <Shield className="w-3.5 h-3.5 text-[#E67E22]" />
          <span>Secured Ledger Sync</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 space-y-1 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-[#E67E22]/30 to-transparent" />
          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">MONTHLY RECURRING REV (MRR)</span>
          <p className="text-xl font-black text-white">JOD {totalMRR.toLocaleString()}</p>
          <span className="text-[10px] text-emerald-400 font-bold inline-flex items-center gap-0.5">
            <TrendingUp className="w-3 h-3" /> +8.4% this month
          </span>
        </div>

        <div className="glass-card p-4 space-y-1">
          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">ACTIVE LICENSES</span>
          <p className="text-xl font-black text-white">{activeCount}</p>
          <span className="text-[10px] text-slate-500">Excluding trial accounts</span>
        </div>

        <div className="glass-card p-4 space-y-1">
          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">TRIAL CONTRACTS</span>
          <p className="text-xl font-black text-[#5DADE2]">{trialCount}</p>
          <span className="text-[10px] text-slate-500">Expires in 30 days max</span>
        </div>

        <div className="glass-card p-4 space-y-1">
          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">ANNUAL CHURN RATE</span>
          <p className="text-xl font-black text-[#EF4444]">1.2%</p>
          <span className="text-[10px] text-emerald-400 font-bold">Below industry average (2.5%)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        
        {/* Subscriptions List Table */}
        <div className="glass-card p-5 lg:col-span-2 space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-white/5">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">RECURRING CLIENTS LIST</h2>
            
            {/* Filter buttons */}
            <div className="flex items-center gap-1.5 bg-black/20 p-1 border border-white/5 rounded-xl text-[10px] font-semibold text-slate-400">
              {['All', 'Active', 'Trial', 'Suspended'].map(st => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    filterStatus === st ? 'bg-[#E67E22] text-white' : 'hover:text-white'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Bulk actions */}
          {selectedIds.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-between px-3 py-2 bg-orange-500/10 border border-orange-500/20 rounded-xl"
            >
              <span className="text-xs font-medium text-slate-300">
                {selectedIds.length} subscription{selectedIds.length > 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center gap-2">
                <button 
                  onClick={handleBulkRenew}
                  className="px-2.5 py-1 rounded bg-[#E67E22] hover:bg-orange-600 text-white text-[10px] font-bold transition-all"
                >
                  Renew Active / Sync
                </button>
                <button 
                  onClick={handleBulkSuspend}
                  className="px-2.5 py-1 rounded bg-[#EF4444] hover:bg-red-600 text-white text-[10px] font-bold transition-all"
                >
                  Pause Billing
                </button>
              </div>
            </motion.div>
          )}

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-slate-500 uppercase tracking-widest text-[9px] font-bold">
                  <th className="py-2.5 px-3 w-8">
                    <button onClick={toggleAll} className="text-slate-400 hover:text-white">
                      {filteredContracts.every(c => selectedIds.includes(c.id)) ? (
                        <CheckSquare className="w-4 h-4 text-[#E67E22]" />
                      ) : (
                        <Square className="w-4 h-4" />
                      )}
                    </button>
                  </th>
                  <th className="py-2.5 px-3">Contract Ref</th>
                  <th className="py-2.5 px-3">Customer</th>
                  <th className="py-2.5 px-3">Service Tier</th>
                  <th className="py-2.5 px-3 text-right">Cost (JOD)</th>
                  <th className="py-2.5 px-3">Renewal</th>
                  <th className="py-2.5 px-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-sans">
                {filteredContracts.map(c => {
                  const isSel = selectedIds.includes(c.id);
                  return (
                    <tr 
                      key={c.id}
                      className={`hover:bg-white/2 transition-colors ${isSel ? 'bg-orange-500/3' : ''}`}
                    >
                      <td className="py-2.5 px-3">
                        <button onClick={() => toggleSelect(c.id)} className="text-slate-400 hover:text-white">
                          {isSel ? (
                            <CheckSquare className="w-4 h-4 text-[#E67E22]" />
                          ) : (
                            <Square className="w-4 h-4" />
                          )}
                        </button>
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-400">{c.id}</td>
                      <td className="py-2.5 px-3 font-semibold text-slate-200">{c.customer}</td>
                      <td className="py-2.5 px-3 text-slate-400">{c.plan}</td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-white">JOD {c.cost}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{c.renewal}</td>
                      <td className="py-2.5 px-3 text-center">
                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${
                          c.status === 'Active' 
                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                            : c.status === 'Trial'
                              ? 'bg-blue-500/10 border-blue-500/20 text-[#5DADE2]'
                              : 'bg-red-500/10 border-red-500/20 text-red-400'
                        }`}>
                          {c.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pricing Estimator Tool */}
        <div className="glass-card p-5 space-y-4">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider pb-3 border-b border-white/5 flex items-center gap-1.5">
            <Sliders className="w-4 h-4 text-[#E67E22]" />
            PROJECTION CALCULATOR
          </h2>

          <div className="space-y-4">
            {/* Users slider */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Total Users</span>
                <span className="text-white font-bold">{simUsers} Seats</span>
              </div>
              <input
                type="range"
                min="5"
                max="100"
                value={simUsers}
                onChange={(e) => setSimUsers(parseInt(e.target.value))}
                className="w-full accent-[#E67E22] bg-white/10 h-1 rounded-lg outline-none cursor-pointer"
              />
              <span className="text-[8px] text-slate-500 block">JOD 15 per active user / month</span>
            </div>

            {/* POS Nodes slider */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">POS Nodes / Registers</span>
                <span className="text-white font-bold">{simNodes} Terminals</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={simNodes}
                onChange={(e) => setSimNodes(parseInt(e.target.value))}
                className="w-full accent-[#5DADE2] bg-white/10 h-1 rounded-lg outline-none cursor-pointer"
              />
              <span className="text-[8px] text-slate-500 block">JOD 45 per active POS terminal / month</span>
            </div>

            {/* SLA toggle */}
            <div className="flex items-center justify-between py-2 border-y border-white/5">
              <div className="text-left">
                <span className="text-xs text-slate-300 font-semibold block">Custom Cloud SLA</span>
                <span className="text-[9px] text-slate-500">24/7 technical callout engineer</span>
              </div>
              <button
                onClick={() => setHasSLA(!hasSLA)}
                className={`w-10 h-5 rounded-full p-0.5 transition-colors ${
                  hasSLA ? 'bg-[#E67E22]' : 'bg-white/10'
                }`}
              >
                <div className={`w-4 h-4 rounded-full bg-white transition-transform ${
                  hasSLA ? 'translate-x-5' : 'translate-x-0'
                }`} />
              </button>
            </div>

            {/* Recalculated total */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-orange-500/10 to-transparent border border-orange-500/25 text-center space-y-1">
              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">ESTIMATED MONTHLY FEE</span>
              <p className="text-2xl font-black text-white">JOD {calcBasePrice().toLocaleString()}</p>
              <span className="text-[9px] text-slate-500">Recalculated in real-time</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
