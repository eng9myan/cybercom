'use client';

import React, { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { useCycomList, fmtCode, fmtMoney, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { write } from '@/lib/cycom';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';
import { useT } from '@/lib/i18n';

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

type MoveStatusKey = 'posted' | 'draft' | 'unknown';

interface JournalEntry {
  rawId: number;
  id: string;
  journal: string;
  date: string;
  partner: string;
  amount: string;
  statusKey: MoveStatusKey;
  selected: boolean;
}

const mapMove = (r: CycomMove): JournalEntry => ({
  rawId: r.id,
  id: r.name && r.name !== '/' ? r.name : fmtCode('MOVE', r.id, 5),
  journal: `${m2oName(r.journal_id, 'General')}${r.ref ? ` (${r.ref})` : ''}`,
  date: fmtDate(r.invoice_date || r.date),
  partner: m2oName(r.partner_id, '—'),
  amount: fmtMoney(r.amount_total ?? 0, m2oName(r.currency_id, '')),
  statusKey: r.state === 'posted' ? 'posted' : r.state === 'draft' ? 'draft' : 'unknown',
  selected: false,
});

export default function JournalEntries() {
  const t = useT();
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
      selected.forEach((id) => { next[id] = { selected: false, statusKey: 'draft' }; });
      setOverrides({ ...overrides, ...next });
    } catch {
      reload();
    }
  };

  const selectedCount = list.filter((item) => item.selected).length;
  const badgeTone = (k: MoveStatusKey) => (k === 'posted' ? 'badge-green' : 'badge-yellow');

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('journals.title')}</h1>
          <p className="page-subtitle">{t('journals.subtitle')}</p>
        </div>
        <div className="flex gap-3">
          {selectedCount > 0 && (
            <button
              onClick={handleBulkDraft}
              className="px-3 py-2 text-xs font-bold bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 rounded-md transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-4 h-4" /> {t('journals.resetToDraft', { n: selectedCount })}
            </button>
          )}
        </div>
      </div>

      <div className="glass-card p-6 border-cyan-500/20 bg-cyan-950/10 text-xs">
        <h3 className="text-sm font-bold text-white mb-2">{t('journals.restrictionsHeading')}</h3>
        <p className="text-slate-400 leading-relaxed mb-4">{t('journals.restrictionsBody')}</p>
      </div>

      {loading && <LoadingCard label={t('journals.loading')} />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && list.length === 0 && <EmptyCard label={t('journals.empty')} />}

      {!loading && !error && list.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('journals.register')}</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-10">{t('journals.select')}</th>
                  <th>{t('journals.entryCode')}</th>
                  <th>{t('journals.journalCode')}</th>
                  <th>{t('journals.partner')}</th>
                  <th>{t('common.date')}</th>
                  <th>{t('journals.totalValue')}</th>
                  <th>{t('common.status')}</th>
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
                    <td><span className={`badge ${badgeTone(item.statusKey)}`}>{t(`status.${item.statusKey}`)}</span></td>
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
