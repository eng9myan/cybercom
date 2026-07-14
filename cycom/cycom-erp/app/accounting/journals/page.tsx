'use client';

import React, { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { useCycomList, fmtCode, fmtMoney, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { write } from '@/lib/cycom';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';

type CycomMove = {
  id: number;
  name?: string;
  ref?: string | false;
  journal_id?: Many2One;
  partner_id?: Many2One;
  invoice_date?: string;
  date?: string;
  amount_total?: number;
  state?: string;
  currency_id?: Many2One;
};

interface JournalEntry {
  rawId: number;
  id: string;
  journal: string;
  date: string;
  partner: string;
  account: string;
  amount: string;
  status: string;
  selected: boolean;
}

const mapMove = (r: CycomMove): JournalEntry => ({
  rawId: r.id,
  id: r.name && r.name !== '/' ? r.name : fmtCode('MOVE', r.id, 5),
  journal: `${m2oName(r.journal_id, 'General')}${r.ref ? ` (${r.ref})` : ''}`,
  date: fmtDate(r.invoice_date || r.date),
  partner: m2oName(r.partner_id, '—'),
  account: '—',
  amount: fmtMoney(r.amount_total ?? 0, m2oName(r.currency_id, '')),
  status: r.state === 'posted' ? 'Posted' : r.state === 'draft' ? 'Draft' : (r.state || '—'),
  selected: false,
});

export default function JournalEntries() {
  const { rows: server, loading, error, reload } = useCycomList<CycomMove, JournalEntry>(
    'account.move',
    [],
    ['name', 'ref', 'journal_id', 'partner_id', 'invoice_date', 'date', 'amount_total', 'state', 'currency_id'],
    mapMove,
    { limit: 200, order: 'date desc' },
  );
  const [overrides, setOverrides] = useState<Record<number, Partial<JournalEntry>>>({});

  const list = server.map((s) => ({ ...s, ...(overrides[s.rawId] || {}) }));

  const toggleSelect = (rawId: number) => {
    setOverrides((prev) => ({ ...prev, [rawId]: { ...(prev[rawId] || {}), selected: !(prev[rawId]?.selected ?? false) } }));
  };

  const handleBulkDraft = async () => {
    const selected = list.filter((e) => e.selected).map((e) => e.rawId);
    if (!selected.length) return;
    try {
      await write('account.move', selected, { state: 'draft' });
      const next: Record<number, Partial<JournalEntry>> = {};
      selected.forEach((id) => { next[id] = { selected: false, status: 'Draft' }; });
      setOverrides({ ...overrides, ...next });
    } catch {
      // best-effort — backend will tell us via error state on reload
      reload();
    }
  };

  const selectedCount = list.filter((item) => item.selected).length;

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Journal Entries Ledger</h1>
          <p className="page-subtitle">Post or audit accounting moves, verify cash/bank account restrictions, and perform bulk draft overrides (account_move_bulk_set_draft).</p>
        </div>
        <div className="flex gap-3">
          {selectedCount > 0 && (
            <button
              onClick={handleBulkDraft}
              className="px-3 py-2 text-xs font-bold bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 rounded-md transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-4 h-4" /> Reset ({selectedCount}) to Draft
            </button>
          )}
        </div>
      </div>

      <div className="glass-card p-6 border-cyan-500/20 bg-cyan-950/10 text-xs">
        <h3 className="text-sm font-bold text-white mb-2">Journal Domain Restrictions</h3>
        <p className="text-slate-400 leading-relaxed mb-4">
          <strong>custom_cash_bank_journal_account_domain:</strong> restricts cash and bank journal account selection to predefined chart of accounts domains (e.g. cash journals can only post to Cash-in-Hand accounts, and bank journals to Liquid Bank assets). Prevents ledger accounting errors.
        </p>
      </div>

      {loading && <LoadingCard label="Loading journal entries…" />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && list.length === 0 && <EmptyCard label="No journal entries yet. Post or import a few to populate this register." />}

      {!loading && !error && list.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Journal Entries Register</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-10">Select</th>
                  <th>Entry Code</th>
                  <th>Journal Code</th>
                  <th>Partner</th>
                  <th>Date</th>
                  <th>Total Value</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {list.map((item) => (
                  <tr key={item.rawId}>
                    <td>
                      <input type="checkbox" checked={item.selected} onChange={() => toggleSelect(item.rawId)} className="cursor-pointer" />
                    </td>
                    <td className="font-mono text-xs font-bold text-slate-400">{item.id}</td>
                    <td className="font-semibold text-slate-200">{item.journal}</td>
                    <td>{item.partner}</td>
                    <td className="text-slate-400">{item.date}</td>
                    <td className="font-bold text-white">{item.amount}</td>
                    <td>
                      <span className={`badge ${item.status === 'Posted' ? 'badge-green' : 'badge-yellow'}`}>{item.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
