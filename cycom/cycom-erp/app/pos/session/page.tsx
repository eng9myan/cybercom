'use client';

import React, { useState } from 'react';
import { ShoppingBag, Lock, ShieldCheck, Printer, ArrowRightLeft } from 'lucide-react';

export default function POSRegisterSession() {
  const [openingBalance, setOpeningBalance] = useState('0.00');
  const [sessionState, setSessionState] = useState<'Closed' | 'Opening' | 'Open'>('Closed');
  const [cashTransactions, setCashTransactions] = useState([
    { type: 'Cash In', amount: 'JOD 100.00', reason: 'Float replenishment', user: 'Wajih Masri' },
    { type: 'Cash Out', amount: 'JOD 50.00', reason: 'Cash withdrawal for office supplies', user: 'Rami Khasawneh' },
  ]);

  const openSession = () => {
    setSessionState('Opening');
    setTimeout(() => {
      setSessionState('Open');
    }, 1000);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">POS Session Control</h1>
          <p className="page-subtitle">Open or close register sessions, log cash inputs or cash-outs, and print cash drawer summaries.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Opening Controls */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Register Session Management</h2>
          
          {sessionState === 'Closed' && (
            <div className="space-y-4 text-sm">
              <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                <strong>Opening Balance Lock:</strong> Under company policy, cashiers must establish a zero-cash beginning register float unless authorized.
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Confirm Opening Cash Balance (JOD)</label>
                <input 
                  type="text" 
                  className="input-field font-mono" 
                  value={openingBalance}
                  onChange={(e) => setOpeningBalance(e.target.value)}
                />
              </div>
              <button 
                onClick={openSession}
                className="btn-primary w-full py-2.5 flex items-center justify-center gap-2"
              >
                <ShoppingBag className="w-4 h-4" /> Open Register Session
              </button>
            </div>
          )}

          {sessionState === 'Opening' && (
            <div className="flex flex-col items-center justify-center text-center p-8 space-y-3">
              <div className="w-8 h-8 border-4 border-[#E67E22]/20 border-t-[#E67E22] rounded-full animate-spin" />
              <p className="text-xs text-slate-400">Validating zero-float check & cashier permissions...</p>
            </div>
          )}

          {sessionState === 'Open' && (
            <div className="space-y-4 text-sm">
              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 flex-shrink-0" />
                <span>Register Session is <strong>Active & Open</strong>. Assigned to: <strong>Rami Khasawneh</strong>.</span>
              </div>
              <div className="flex gap-2">
                <button className="btn-secondary flex-1 flex items-center justify-center gap-2">
                  <ArrowRightLeft className="w-4 h-4 text-cyan-400" /> Cash Input / Out
                </button>
                <button className="btn-secondary flex-1 flex items-center justify-center gap-2">
                  <Printer className="w-4 h-4 text-purple-400" /> Receipt Audit
                </button>
              </div>
              <button 
                onClick={() => setSessionState('Closed')}
                className="w-full py-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 rounded-md font-bold transition-colors"
              >
                Close & Post Session
              </button>
            </div>
          )}
        </div>

        {/* Right Column - Cash Drawer / Transactions */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Cash Move Ledger (pos_cash_move_access)</h2>
          <div className="space-y-3">
            {cashTransactions.map((tx, idx) => (
              <div key={idx} className="flex justify-between items-center p-3 rounded-lg bg-white/5 border border-white/5 text-xs">
                <div className="space-y-1">
                  <span className="font-bold text-slate-200 block">{tx.type} ({tx.amount})</span>
                  <span className="text-slate-500 block">Reason: {tx.reason}</span>
                </div>
                <div className="text-right">
                  <span className="badge badge-purple">{tx.user}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
