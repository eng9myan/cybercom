'use client';

import React from 'react';
import { FileDown, Plus } from 'lucide-react';
import { useCycomList, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';
import { useT } from '@/lib/i18n';
import { TRANSFER_STATE, statusTone, type StatusKey } from '@/lib/status';

type CycomPicking = {
  id: number;
  name?: string;
  location_id?: Many2One;
  location_dest_id?: Many2One;
  scheduled_date?: string;
  date_done?: string;
  state?: string;
  move_ids_without_package?: number[];
};

interface Transfer {
  rawId: number;
  id: string;
  from: string;
  to: string;
  date: string;
  itemsCount: number;
  statusKey: StatusKey;
  packed: boolean;
}

const mapPicking = (r: CycomPicking): Transfer => ({
  rawId: r.id,
  id: r.name || `WH/${r.id}`,
  from: m2oName(r.location_id, '—'),
  to: m2oName(r.location_dest_id, '—'),
  date: fmtDate(r.date_done || r.scheduled_date),
  itemsCount: r.move_ids_without_package?.length ?? 0,
  statusKey: TRANSFER_STATE[r.state ?? ''] || 'unknown',
  packed: r.state === 'done',
});

export default function StockTransfers() {
  const t = useT();
  const { rows: transfers, loading, error } = useCycomList<CycomPicking, Transfer>(
    'stock.picking',
    [['picking_type_id.code', '=', 'internal']],
    ['name', 'location_id', 'location_dest_id', 'scheduled_date', 'date_done', 'state', 'move_ids_without_package'],
    mapPicking,
    { limit: 200, order: 'scheduled_date desc' },
  );

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('transfers.title')}</h1>
          <p className="page-subtitle">{t('transfers.subtitle')}</p>
        </div>
        <button className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> {t('transfers.createTransfer')}</button>
      </div>

      <div className="glass-card p-6 border-emerald-500/20 bg-emerald-950/10 text-xs">
        <h3 className="text-sm font-bold text-white mb-2">{t('transfers.rulesHeading')}</h3>
        <p className="text-slate-400 leading-relaxed mb-4">{t('transfers.rulesBody')}</p>
      </div>

      {loading && <LoadingCard label={t('transfers.loading')} />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && transfers.length === 0 && <EmptyCard label={t('transfers.empty')} />}

      {!loading && !error && transfers.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('transfers.register')}</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('transfers.transferId')}</th>
                  <th>{t('transfers.sourceLocation')}</th>
                  <th>{t('transfers.destinationLocation')}</th>
                  <th>{t('transfers.totalItems')}</th>
                  <th>{t('transfers.departureDate')}</th>
                  <th>{t('transfers.packingList')}</th>
                  <th>{t('common.status')}</th>
                  <th>{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {transfers.map((tr) => (
                  <tr key={tr.rawId}>
                    <td className="font-mono text-xs font-bold text-slate-400">{tr.id}</td>
                    <td className="font-semibold text-slate-200">{tr.from}</td>
                    <td className="font-semibold text-slate-200">{tr.to}</td>
                    <td>{t('transfers.uniqueProducts', { n: tr.itemsCount })}</td>
                    <td>{tr.date}</td>
                    <td>
                      <span className={`badge ${tr.packed ? 'badge-green' : 'badge-yellow'}`}>
                        {tr.packed ? t('transfers.printed') : t('transfers.notPrinted')}
                      </span>
                    </td>
                    <td><span className={`badge ${statusTone(tr.statusKey)}`}>{t(`status.${tr.statusKey}`)}</span></td>
                    <td>
                      <div className="flex gap-2">
                        <button className="btn-secondary py-1 px-3 text-xs flex items-center gap-1 hover:bg-cyan-500/10 hover:text-cyan-400 hover:border-cyan-500/30 transition-colors">
                          <FileDown className="w-3.5 h-3.5" /> {t('transfers.printPackingSheet')}
                        </button>
                      </div>
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
