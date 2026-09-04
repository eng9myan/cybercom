'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  FileText, CheckCircle2, RefreshCw,
  ShieldAlert, CheckCircle, Calculator, FileSpreadsheet
} from 'lucide-react';
import { useCycomList, m2oName, fmtCode, Many2One } from '@/lib/cycomModels';
import { useT } from '@/lib/i18n';

interface JournalEntry {
  id: string;
  ref: string;
  date: string;
  journal: 'Bank' | 'Cash' | 'General';
  partner: string;
  debit: number;
  credit: number;
  status: 'Posted' | 'Draft';
  reconciled: boolean;
}

interface BankStatementLine {
  id: string;
  date: string;
  label: string;
  amount: number;
  matchedEntryId: string | null;
}

const INITIAL_BANK_LINES: BankStatementLine[] = [
  { id: 'STMT-TX-101', date: '2026-06-14', label: 'DEPOSIT FRM JORDAN HYPERMARKETS', amount: 4200, matchedEntryId: null },
  { id: 'STMT-TX-102', date: '2026-06-13', label: 'TRANSFER TO SAMER WHOLESALE EST', amount: -1250, matchedEntryId: null },
  { id: 'STMT-TX-103', date: '2026-06-11', label: 'RENT PAYMENT DIRECT DEBIT HQ', amount: -2000, matchedEntryId: null },
  { id: 'STMT-TX-104', date: '2026-06-14', label: 'CASH SALE DEP COUNTER A', amount: 180, matchedEntryId: 'MOVE/2026/06/002' },
];

type BackendMove = {
  id: number;
  name?: string;
  date?: string;
  journal_id?: Many2One;
  partner_id?: Many2One;
  amount_total?: number;
  state?: string;
};

const VALID_JOURNALS = ['Bank', 'Cash', 'General'] as const;
function resolveJournal(name: string): 'Bank' | 'Cash' | 'General' {
  if (VALID_JOURNALS.includes(name as any)) return name as 'Bank' | 'Cash' | 'General';
  return 'General';
}

const JOURNAL_STATUS_KEY: Record<JournalEntry['status'], string> = {
  Posted: 'status.posted',
  Draft: 'status.draft',
};

export default function AccountingDashboard() {
  const t = useT();
  const { rows: liveEntries, loading } = useCycomList<BackendMove, JournalEntry>(
    'account.move',
    [['move_type', '=', 'entry']],
    ['name', 'date', 'journal_id', 'partner_id', 'amount_total', 'state'],
    (r) => {
      const amt = r.amount_total ?? 0;
      return {
        id: r.name || fmtCode('MOVE', r.id),
        ref: r.name || '—',
        date: r.date || '',
        journal: resolveJournal(m2oName(r.journal_id)),
        partner: m2oName(r.partner_id),
        debit: amt > 0 ? amt : 0,
        credit: amt < 0 ? Math.abs(amt) : 0,
        status: r.state === 'posted' ? 'Posted' : 'Draft',
        reconciled: false,
      };
    },
    { limit: 100, order: 'date desc' },
  );

  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [bankLines, setBankLines] = useState<BankStatementLine[]>(INITIAL_BANK_LINES);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  useEffect(() => {
    if (liveEntries.length > 0) setEntries(liveEntries);
  }, [liveEntries]);

  // Payment Validation states
  const [payAmount, setPayAmount] = useState('');
  const [payPartner, setPayPartner] = useState('');
  const [payJournal, setPayJournal] = useState<'Bank' | 'Cash'>('Bank');
  const [paymentSuccess, setPaymentSuccess] = useState(false);

  // Reconcilation Selection states
  const [reconcileSelectBankId, setReconcileSelectBankId] = useState<string | null>(null);
  const [reconcileSelectEntryId, setReconcileSelectEntryId] = useState<string | null>(null);

  // Checkbox select
  const toggleSelectEntry = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(x => x !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  // Bulk Draft Action (Cycom: account_move_bulk_set_draft)
  const handleBulkDraft = () => {
    if (selectedIds.length === 0) return;
    setEntries(entries.map(ent =>
      selectedIds.includes(ent.id)
        ? { ...ent, status: 'Draft', reconciled: false }
        : ent
    ));
    // Reset selections
    setSelectedIds([]);
  };

  // Auto Match engine (Cycom: mass_reconciliation)
  const handleAutoReconcile = () => {
    let updatedEntries = [...entries];
    let updatedLines = bankLines.map(line => {
      if (line.matchedEntryId) return line; // already done

      // Attempt match on absolute values
      const targetAmount = Math.abs(line.amount);
      const match = updatedEntries.find(ent =>
        !ent.reconciled &&
        (ent.debit === targetAmount || ent.credit === targetAmount)
      );

      if (match) {
        // Mark match
        updatedEntries = updatedEntries.map(e => e.id === match.id ? { ...e, reconciled: true } : e);
        return {
          ...line,
          matchedEntryId: match.id
        };
      }
      return line;
    });

    setEntries(updatedEntries);
    setBankLines(updatedLines);
  };

  // Manual reconcile
  const handleManualReconcile = () => {
    if (!reconcileSelectBankId || !reconcileSelectEntryId) return;

    setBankLines(bankLines.map(line =>
      line.id === reconcileSelectBankId
        ? { ...line, matchedEntryId: reconcileSelectEntryId }
        : line
    ));

    setEntries(entries.map(ent =>
      ent.id === reconcileSelectEntryId
        ? { ...ent, reconciled: true }
        : ent
    ));

    setReconcileSelectBankId(null);
    setReconcileSelectEntryId(null);
  };

  // Payment post with validation check (Cycom: payment_non_zero_confirm)
  const handlePostPayment = (e: React.FormEvent) => {
    e.preventDefault();
    const amt = parseFloat(payAmount) || 0;

    if (amt <= 0) {
      alert(`Posting Refused: Payment amount must be a NON-ZERO, positive JOD value. You cannot post a payment of JOD ${amt.toFixed(2)}.`);
      return;
    }

    // Process payment
    const newEntry: JournalEntry = {
      id: `MOVE/2026/06/00${entries.length + 1}`,
      ref: `PYMT-POST-MOCK-${Math.floor(1000 + Math.random() * 9000)}`,
      date: new Date().toISOString().split('T')[0],
      journal: payJournal,
      partner: payPartner || 'Miscellaneous Vendor',
      debit: 0,
      credit: amt,
      status: 'Posted',
      reconciled: false
    };

    setEntries([newEntry, ...entries]);
    setPaymentSuccess(true);
    setPayAmount('');
    setPayPartner('');
    setTimeout(() => setPaymentSuccess(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('acctDash.title')}</h1>
          <p className="page-subtitle">{t('acctDash.subtitle')}</p>
        </div>
        <div className="flex gap-3">
          <Link href="/accounting/reconciliation" className="btn-primary flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-indigo-400" /> {t('acctDash.aiReconciler')}
          </Link>
          <Link href="/accounting/import" className="btn-secondary flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-emerald-500" /> {t('acctDash.importEntries')}
          </Link>
          <button
            onClick={handleAutoReconcile}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4 text-cyan-400" /> {t('acctDash.runAutoReconcile')}
          </button>
          <button
            onClick={handleBulkDraft}
            disabled={selectedIds.length === 0}
            className="btn-secondary flex items-center gap-2 disabled:opacity-50"
          >
            <CheckCircle className="w-4 h-4" /> {t('acctDash.setDraftN', { n: selectedIds.length })}
          </button>
        </div>
      </div>

      {loading && (
        <div className="glass-card p-8 text-center text-slate-400 text-sm">
          {t('acctDash.loading')}
        </div>
      )}

      {/* Grid Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{t('acctDash.journalBalance')}</span>
            <p className="text-2xl font-black text-[#10B981]">JOD 4,200.00</p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <Calculator className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{t('acctDash.unreconciledLines')}</span>
            <p className="text-2xl font-black text-[#F59E0B]">
              {t('acctDash.transactionsN', { n: bankLines.filter(l => !l.matchedEntryId).length })}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
            <RefreshCw className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{t('acctDash.bulkDraftControl')}</span>
            <span className="badge badge-cyan text-[8px] mt-1.5">account_move_bulk_set_draft</span>
          </div>
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
            <FileText className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{t('acctDash.postProtection')}</span>
            <span className="badge badge-orange text-[8px] mt-1.5">payment_non_zero_confirm</span>
          </div>
          <div className="p-3 rounded-xl bg-orange-500/10 text-[#E67E22]">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column - Payment Creator */}
        <div className="space-y-6">

          {/* Post Payment */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('acctDash.postPaymentHeading')}</h2>
              <span className="text-[10px] bg-orange-500/20 text-[#E67E22] border border-[#E67E22]/30 px-2 py-0.5 rounded font-bold">
                payment_non_zero_confirm
              </span>
            </div>

            {paymentSuccess ? (
              <div className="h-[180px] flex flex-col items-center justify-center text-center space-y-3 text-xs text-emerald-400">
                <CheckCircle2 className="w-10 h-10 animate-bounce" />
                <div>
                  <p className="font-bold">{t('acctDash.paymentPostedSuccess')}</p>
                  <p className="text-[10px] text-slate-500 mt-1">{t('acctDash.paymentPostedNote')}</p>
                </div>
              </div>
            ) : (
              <form onSubmit={handlePostPayment} className="space-y-4 text-xs">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('acctDash.vendorPartner')}</label>
                  <input
                    type="text"
                    required
                    placeholder={t('acctDash.vendorPartnerPh')}
                    value={payPartner}
                    onChange={e => setPayPartner(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">{t('acctDash.journalMode')}</label>
                    <select
                      value={payJournal}
                      onChange={e => setPayJournal(e.target.value as any)}
                      className="input-field"
                    >
                      <option value="Bank">{t('acctDash.bankAccount')}</option>
                      <option value="Cash">{t('acctDash.cashDrawer')}</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">{t('acctDash.amount')}</label>
                    <input
                      type="number"
                      placeholder={t('acctDash.amountPh')}
                      value={payAmount}
                      onChange={e => setPayAmount(e.target.value)}
                      className="input-field font-mono"
                    />
                  </div>
                </div>
                <p className="text-[9px] text-slate-500">
                  {t('acctDash.validationNote')}
                </p>
                <button type="submit" className="btn-primary w-full py-2">
                  {t('acctDash.postPaymentBtn')}
                </button>
              </form>
            )}
          </div>

          {/* Mass Reconciliation Manual Selector */}
          {reconcileSelectBankId && (
            <div className="glass-card p-5 bg-[#E67E22]/5 border-[#E67E22]/20 space-y-3 text-xs animate-slide-up">
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="font-bold text-[#E67E22]">{t('acctDash.manualMatchLock')}</span>
                <button onClick={() => { setReconcileSelectBankId(null); setReconcileSelectEntryId(null); }} className="text-slate-500">{t('acctDash.cancel')}</button>
              </div>
              <p className="text-slate-400">{t('acctDash.matchStatementLine', { id: reconcileSelectBankId })}</p>
              <select
                value={reconcileSelectEntryId || ''}
                onChange={e => setReconcileSelectEntryId(e.target.value)}
                className="input-field"
              >
                <option value="">{t('acctDash.selectMatchingEntry')}</option>
                {entries.filter(e => !e.reconciled).map(e => (
                  <option key={e.id} value={e.id}>
                    {e.id} - {e.partner} (JOD {e.debit || e.credit})
                  </option>
                ))}
              </select>
              <button
                onClick={handleManualReconcile}
                disabled={!reconcileSelectEntryId}
                className="btn-primary w-full py-1.5 disabled:opacity-50"
              >
                {t('acctDash.confirmMatch')}
              </button>
            </div>
          )}

        </div>

        {/* Right Column - Statement Matcher & Journal Entries Grid */}
        <div className="lg:col-span-2 space-y-6">

          {/* Statement Reconciliation Panel */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('acctDash.statementHeading')}</h2>
              <span className="text-[10px] bg-cyan-500/20 text-[#00F0FF] border border-[#00F0FF]/30 px-2 py-0.5 rounded font-bold">
                mass_reconciliation
              </span>
            </div>

            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {bankLines.map(line => (
                <div key={line.id} className="p-3.5 rounded-xl bg-white/3 border border-white/5 flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-white">{line.label}</p>
                    <p className="text-[10px] text-slate-500">{line.date} · <span className="font-mono">{line.id}</span></p>
                  </div>
                  <div className="text-end flex items-center gap-4">
                    <div>
                      <p className={`text-xs font-mono font-bold ${line.amount > 0 ? 'text-emerald-400' : 'text-slate-300'}`}>
                        {line.amount > 0 ? '+' : ''}JOD {line.amount}
                      </p>
                      {line.matchedEntryId && (
                        <p className="text-[9px] text-emerald-500 font-bold font-mono">{t('acctDash.matched', { ref: line.matchedEntryId.split('/').pop() ?? '' })}</p>
                      )}
                    </div>
                    {!line.matchedEntryId ? (
                      <button
                        onClick={() => setReconcileSelectBankId(line.id)}
                        className="p-1 px-2 text-[10px] font-bold rounded bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/25 text-[#00F0FF]"
                      >
                        {t('acctDash.match')}
                      </button>
                    ) : (
                      <span className="text-emerald-400"><CheckCircle2 className="w-5 h-5" /></span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Journal Entries List */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('acctDash.ledgerHeading')}</h2>
              <span className="text-[10px] bg-red-500/20 text-[#EF4444] border border-red-500/30 px-2 py-0.5 rounded font-bold">
                account_move_bulk_set_draft
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="w-8">
                      <input
                        type="checkbox"
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedIds(entries.map(x => x.id));
                          } else {
                            setSelectedIds([]);
                          }
                        }}
                        checked={entries.length > 0 && selectedIds.length === entries.length}
                        className="rounded bg-white/5 border-white/10 accent-[#E67E22]"
                      />
                    </th>
                    <th>{t('acctDash.colIdMove')}</th>
                    <th>{t('acctDash.colRef')}</th>
                    <th>{t('acctDash.colPartner')}</th>
                    <th>{t('acctDash.colJournal')}</th>
                    <th>{t('acctDash.colDebit')}</th>
                    <th>{t('acctDash.colCredit')}</th>
                    <th>{t('acctDash.colStatus')}</th>
                    <th>{t('acctDash.colRecon')}</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map(ent => (
                    <tr key={ent.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(ent.id)}
                          onChange={() => toggleSelectEntry(ent.id)}
                          className="rounded bg-white/5 border-white/10 accent-[#E67E22]"
                        />
                      </td>
                      <td className="font-mono text-[11px] text-slate-300">{ent.id}</td>
                      <td className="font-bold text-slate-400">{ent.ref}</td>
                      <td>{ent.partner}</td>
                      <td>
                        <span className={`badge text-[9px] ${
                          ent.journal === 'Bank' ? 'badge-cyan' :
                          ent.journal === 'Cash' ? 'badge-orange' : 'badge-purple'
                        }`}>{ent.journal}</span>
                      </td>
                      <td className="font-mono">{ent.debit > 0 ? `JOD ${ent.debit}` : '-'}</td>
                      <td className="font-mono">{ent.credit > 0 ? `JOD ${ent.credit}` : '-'}</td>
                      <td>
                        <span className={`badge text-[9px] ${ent.status === 'Posted' ? 'badge-green' : 'badge-yellow'}`}>
                          {t(JOURNAL_STATUS_KEY[ent.status])}
                        </span>
                      </td>
                      <td>
                        <span className={`w-2 h-2 rounded-full inline-block ${ent.reconciled ? 'bg-[#10B981]' : 'bg-[#EF4444]'}`} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
