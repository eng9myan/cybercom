'use client';

import React, { useState } from 'react';
import { ShoppingBag, ShieldCheck, Printer, ArrowRightLeft } from 'lucide-react';
import { useT } from '@/lib/i18n';

type SessionState = 'closed' | 'opening' | 'open';

export default function POSRegisterSession() {
  const t = useT();
  const [openingBalance, setOpeningBalance] = useState('0.00');
  const [sessionState, setSessionState] = useState<SessionState>('closed');
  const [cashTransactions] = useState([
    { type: 'Cash In', amount: 'JOD 100.00', reason: 'Float replenishment', user: 'Wajih Masri' },
    { type: 'Cash Out', amount: 'JOD 50.00', reason: 'Cash withdrawal for office supplies', user: 'Rami Khasawneh' },
  ]);

  const openSession = () => {
    setSessionState('opening');
    setTimeout(() => setSessionState('open'), 1000);
  };

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('posSession.title')}</h1>
          <p className="page-subtitle">{t('posSession.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('posSession.sessionManagement')}</h2>

          {sessionState === 'closed' && (
            <div className="space-y-4 text-sm">
              <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {t('posSession.openingLockNote')}
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">{t('posSession.confirmOpeningBalance')}</label>
                <input
                  type="text"
                  className="input-field font-mono"
                  value={openingBalance}
                  onChange={(e) => setOpeningBalance(e.target.value)}
                />
              </div>
              <button onClick={openSession} className="btn-primary w-full py-2.5 flex items-center justify-center gap-2">
                <ShoppingBag className="w-4 h-4" /> {t('posSession.openSession')}
              </button>
            </div>
          )}

          {sessionState === 'opening' && (
            <div className="flex flex-col items-center justify-center text-center p-8 space-y-3">
              <div className="w-8 h-8 border-4 border-[#E67E22]/20 border-t-[#E67E22] rounded-full animate-spin" />
              <p className="text-xs text-slate-400">{t('posSession.validating')}</p>
            </div>
          )}

          {sessionState === 'open' && (
            <div className="space-y-4 text-sm">
              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 flex-shrink-0" />
                <span>{t('posSession.sessionActive', { name: 'Rami Khasawneh' })}</span>
              </div>
              <div className="flex gap-2">
                <button className="btn-secondary flex-1 flex items-center justify-center gap-2">
                  <ArrowRightLeft className="w-4 h-4 text-cyan-400" /> {t('posSession.cashInOut')}
                </button>
                <button className="btn-secondary flex-1 flex items-center justify-center gap-2">
                  <Printer className="w-4 h-4 text-purple-400" /> {t('posSession.receiptAudit')}
                </button>
              </div>
              <button
                onClick={() => setSessionState('closed')}
                className="w-full py-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 rounded-md font-bold transition-colors"
              >
                {t('posSession.closeAndPost')}
              </button>
            </div>
          )}
        </div>

        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('posSession.cashMoveLedger')}</h2>
          <div className="space-y-3">
            {cashTransactions.map((tx, idx) => (
              <div key={idx} className="flex justify-between items-center p-3 rounded-lg bg-white/5 border border-white/5 text-xs">
                <div className="space-y-1">
                  <span className="font-bold text-slate-200 block">{tx.type} ({tx.amount})</span>
                  <span className="text-slate-500 block">{t('posSession.reasonLine', { reason: tx.reason })}</span>
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
