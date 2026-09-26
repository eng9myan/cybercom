'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft, Landmark, RefreshCw, Plus, X, Scale
} from 'lucide-react';
import { useT } from '@/lib/i18n';

interface Account {
  id: string;
  code: string;
  name: string;
  account_type: string;
}

interface PendingLine {
  statement_date: string;
  description: string;
  amount: string;
}

interface LedgerLine {
  id: string;
  date: string;
  reference: string;
  description: string;
  amount: number;
}

interface StatementLine {
  id: string;
  date: string;
  description: string;
  amount: number;
}

interface Summary {
  ledger_balance: number;
  cleared_balance: number;
  outstanding_journal_lines: LedgerLine[];
  outstanding_total: number;
  unmatched_statement_lines: StatementLine[];
  unmatched_statement_total: number;
  has_open_items: boolean;
  statement_ending_balance: number | null;
  difference: number | null;
  is_balanced: boolean | null;
}

export default function BankReconciliation() {
  const t = useT();
  const router = useRouter();

  const [accounts, setAccounts] = useState<Account[]>([]);
  const [bankAccountId, setBankAccountId] = useState('');
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [endingBalance, setEndingBalance] = useState('');

  const [pending, setPending] = useState<PendingLine[]>([]);
  const [newDate, setNewDate] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newAmount, setNewAmount] = useState('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<{ kind: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetch('/api/cycom/rest/accounting/accounts/', { credentials: 'include' })
      .then((r) => r.json())
      .then((data) => {
        const rows = (data.results || data) as Account[];
        setAccounts(rows.filter((a) => a.account_type === 'asset'));
      })
      .catch(() => {});
  }, []);

  const loadSummary = useCallback(async () => {
    if (!bankAccountId) {
      setSummary(null);
      return;
    }
    setLoading(true);
    try {
      const qs = new URLSearchParams({ bank_account: bankAccountId });
      if (endingBalance) qs.set('statement_ending_balance', endingBalance);
      const res = await fetch(`/api/cycom/rest/accounting/reports/bank-reconciliation/?${qs}`, { credentials: 'include' });
      if (res.ok) setSummary(await res.json());
    } catch {
      setStatus({ kind: 'error', text: t('accountingReconciliation.loadFailed') });
    } finally {
      setLoading(false);
    }
  }, [bankAccountId, endingBalance, t]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  const addPendingLine = () => {
    if (!newDate || !newDesc || !newAmount) return;
    setPending((p) => [...p, { statement_date: newDate, description: newDesc, amount: newAmount }]);
    setNewDate('');
    setNewDesc('');
    setNewAmount('');
  };

  const removePendingLine = (idx: number) => {
    setPending((p) => p.filter((_, i) => i !== idx));
  };

  const handleImport = async () => {
    if (!bankAccountId || pending.length === 0) return;
    setBusy(true);
    try {
      const res = await fetch('/api/cycom/rest/accounting/bank-statement-lines/import/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          bank_account: bankAccountId,
          rows: pending.map((p) => ({ ...p, amount: parseFloat(p.amount) })),
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setStatus({ kind: 'success', text: t('accountingReconciliation.importSuccess', {
          created: String((data.created || []).length),
          skipped: String(data.skipped_duplicates ?? 0),
        }) });
        setPending([]);
        await loadSummary();
      } else {
        setStatus({ kind: 'error', text: t('accountingReconciliation.importFailed', { msg: data.detail || res.statusText }) });
      }
    } catch (err: any) {
      setStatus({ kind: 'error', text: t('accountingReconciliation.importFailed', { msg: err.message }) });
    } finally {
      setBusy(false);
    }
  };

  const handleAutoMatch = async () => {
    if (!bankAccountId) return;
    setBusy(true);
    try {
      const res = await fetch('/api/cycom/rest/accounting/bank-statement-lines/auto-match/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ bank_account: bankAccountId }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setStatus({ kind: 'success', text: t('accountingReconciliation.autoMatchResult', {
          matched: String(data.matched), ambiguous: String(data.ambiguous), remaining: String(data.remaining_unmatched),
        }) });
        await loadSummary();
      } else {
        setStatus({ kind: 'error', text: t('accountingReconciliation.autoMatchFailed', { msg: data.detail || res.statusText }) });
      }
    } catch (err: any) {
      setStatus({ kind: 'error', text: t('accountingReconciliation.autoMatchFailed', { msg: err.message }) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      {/* Header */}
      <div className="max-w-5xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/accounting')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent flex items-center gap-2">
              <Landmark className="w-6 h-6 text-indigo-400" /> {t('accountingReconciliation.title')}
            </h1>
            <p className="text-xs text-slate-400 mt-1">{t('accountingReconciliation.subtitle')}</p>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto space-y-6">
        {status && (
          <div className={`flex items-center justify-between px-4 py-3 rounded-lg border text-xs font-medium ${
            status.kind === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/20 text-emerald-400'
              : 'bg-rose-950/40 border-rose-500/20 text-rose-400'
          }`}>
            <span>{status.text}</span>
            <button onClick={() => setStatus(null)} className="p-1 hover:bg-white/5 rounded transition">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Account selector */}
        <div className="glass-card p-6">
          <label className="text-xs text-slate-400 block mb-1">{t('accountingReconciliation.selectAccount')}</label>
          <select
            value={bankAccountId} onChange={(e) => setBankAccountId(e.target.value)}
            className="w-full max-w-md bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
          >
            <option value="">{t('accountingReconciliation.selectAccountPh')}</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>{a.code} -- {a.name}</option>
            ))}
          </select>
          {accounts.length === 0 && (
            <p className="text-[10px] text-amber-400 mt-2">{t('accountingReconciliation.noAccounts')}</p>
          )}
        </div>

        {!bankAccountId ? (
          <div className="glass-card p-12 text-center text-slate-500">
            {t('accountingReconciliation.emptyState')}
          </div>
        ) : (
          <>
            {/* Add statement lines */}
            <div className="glass-card p-6 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 pb-2">
                {t('accountingReconciliation.addLineHeading')}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <input
                  type="date" value={newDate} onChange={(e) => setNewDate(e.target.value)}
                  className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                />
                <input
                  type="text" placeholder={t('accountingReconciliation.description')}
                  value={newDesc} onChange={(e) => setNewDesc(e.target.value)}
                  className="md:col-span-2 bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                />
                <input
                  type="number" step="0.01" placeholder={t('accountingReconciliation.amount')}
                  value={newAmount} onChange={(e) => setNewAmount(e.target.value)}
                  className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                />
              </div>
              <button
                onClick={addPendingLine}
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg transition"
              >
                <Plus className="w-4 h-4" /> {t('accountingReconciliation.addLine')}
              </button>

              {pending.length > 0 && (
                <div className="space-y-2 border-t border-white/5 pt-3">
                  <h4 className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                    {t('accountingReconciliation.pendingLines', { n: String(pending.length) })}
                  </h4>
                  {pending.map((p, idx) => (
                    <div key={idx} className="flex items-center justify-between gap-4 p-2.5 bg-slate-950/40 border border-slate-850 rounded-lg">
                      <div className="flex items-center gap-4 text-slate-300">
                        <span className="text-slate-500">{p.statement_date}</span>
                        <span>{p.description}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-mono font-semibold">{parseFloat(p.amount).toFixed(2)}</span>
                        <button onClick={() => removePendingLine(idx)} className="p-1 hover:bg-slate-800 rounded transition">
                          <X className="w-3.5 h-3.5 text-slate-500" />
                        </button>
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={handleImport} disabled={busy}
                    className="btn-primary flex items-center gap-2 disabled:opacity-50"
                  >
                    {t('accountingReconciliation.importLines')}
                  </button>
                </div>
              )}
            </div>

            {/* Auto-match + summary */}
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  {t('accountingReconciliation.summaryHeading')}
                </h3>
                <button
                  onClick={handleAutoMatch} disabled={busy}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-white font-medium transition"
                >
                  <RefreshCw className={`w-4 h-4 ${busy ? 'animate-spin' : ''}`} /> {t('accountingReconciliation.runAutoMatch')}
                </button>
              </div>

              {loading ? (
                <div className="text-center py-6 text-slate-500">...</div>
              ) : summary && (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('accountingReconciliation.clearedBalance')}</label>
                      <div className="text-emerald-400 font-mono font-bold mt-0.5">{summary.cleared_balance.toFixed(2)}</div>
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('accountingReconciliation.outstandingTotal')}</label>
                      <div className="text-slate-200 font-mono font-bold mt-0.5">{summary.outstanding_total.toFixed(2)}</div>
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('accountingReconciliation.unmatchedTotal')}</label>
                      <div className="text-slate-200 font-mono font-bold mt-0.5">{summary.unmatched_statement_total.toFixed(2)}</div>
                    </div>
                  </div>

                  <div className="flex items-end gap-4 border-t border-white/5 pt-4">
                    <div className="space-y-1">
                      <label className="text-xs text-slate-400">{t('accountingReconciliation.statementEndingBalance')}</label>
                      <input
                        type="number" step="0.01" placeholder={t('accountingReconciliation.statementEndingBalancePh')}
                        value={endingBalance} onChange={(e) => setEndingBalance(e.target.value)}
                        className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none w-48"
                      />
                    </div>
                    {summary.difference !== null && (
                      <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${
                        summary.is_balanced
                          ? 'bg-emerald-950/40 border-emerald-500/20 text-emerald-400'
                          : 'bg-rose-950/40 border-rose-500/20 text-rose-400'
                      }`}>
                        <Scale className="w-4 h-4" />
                        <span className="font-semibold">
                          {summary.is_balanced ? t('accountingReconciliation.balanced') : t('accountingReconciliation.notBalanced')}
                        </span>
                        <span className="font-mono">({summary.difference.toFixed(2)})</span>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>

            {summary && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card p-6">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 border-b border-white/5 pb-2">
                    {t('accountingReconciliation.outstandingJournalHeading')}
                  </h3>
                  {summary.outstanding_journal_lines.length === 0 ? (
                    <div className="text-center py-6 text-slate-500">{t('accountingReconciliation.noOutstanding')}</div>
                  ) : (
                    <div className="space-y-2">
                      {summary.outstanding_journal_lines.map((l) => (
                        <div key={l.id} className="p-3 bg-slate-950/40 border border-slate-850 rounded-xl flex justify-between items-center">
                          <div>
                            <div className="font-semibold text-slate-300">{l.description}</div>
                            <div className="text-[10px] text-slate-500 mt-0.5">{l.date} -- {l.reference}</div>
                          </div>
                          <div className="font-mono text-slate-200 font-bold">{l.amount.toFixed(2)}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="glass-card p-6">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 border-b border-white/5 pb-2">
                    {t('accountingReconciliation.unmatchedStatementHeading')}
                  </h3>
                  {summary.unmatched_statement_lines.length === 0 ? (
                    <div className="text-center py-6 text-slate-500">{t('accountingReconciliation.noUnmatched')}</div>
                  ) : (
                    <div className="space-y-2">
                      {summary.unmatched_statement_lines.map((l) => (
                        <div key={l.id} className="p-3 bg-slate-950/40 border border-slate-850 rounded-xl flex justify-between items-center">
                          <div>
                            <div className="font-semibold text-slate-300">{l.description}</div>
                            <div className="text-[10px] text-slate-500 mt-0.5">{l.date}</div>
                          </div>
                          <div className="font-mono text-slate-200 font-bold">{l.amount.toFixed(2)}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
