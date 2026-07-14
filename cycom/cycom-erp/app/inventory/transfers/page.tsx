'use client';

import React from 'react';
import { FileDown, Plus } from 'lucide-react';
import { useCycomList, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';

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
  status: string;
  packingList: string;
}

const STATE_LABEL: Record<string, string> = {
  draft: 'Draft',
  waiting: 'Waiting',
  confirmed: 'Confirmed',
  assigned: 'Ready',
  done: 'Completed',
  cancel: 'Cancelled',
};

const mapPicking = (r: CycomPicking): Transfer => ({
  rawId: r.id,
  id: r.name || `WH/${r.id}`,
  from: m2oName(r.location_id, '—'),
  to: m2oName(r.location_dest_id, '—'),
  date: fmtDate(r.date_done || r.scheduled_date),
  itemsCount: r.move_ids_without_package?.length ?? 0,
  status: STATE_LABEL[r.state ?? ''] || r.state || '—',
  packingList: r.state === 'done' ? 'Printed' : 'Not Printed',
});

export default function StockTransfers() {
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
          <h1 className="page-title text-white">Stock Transfers</h1>
          <p className="page-subtitle">Initiate internal warehouse transfers, verify negative stock block rules, and generate Excel packing list reports (stock_picking_catalog).</p>
        </div>
        <button className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Create Stock Transfer</button>
      </div>

      <div className="glass-card p-6 border-emerald-500/20 bg-emerald-950/10 text-xs">
        <h3 className="text-sm font-bold text-white mb-2">Stock Transfer Rules</h3>
        <p className="text-slate-400 leading-relaxed mb-4">
          <strong>stock_location_negative_block:</strong> Validates stock levels at source location before confirming transfer. If request exceeds local bin levels, submission is blocked.
          <strong>cycom_packing_list:</strong> Prints a custom cargo delivery sheet.
        </p>
      </div>

      {loading && <LoadingCard label="Loading transfers…" />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && transfers.length === 0 && <EmptyCard label="No internal transfers yet. Create one to begin moving stock between warehouses." />}

      {!loading && !error && transfers.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Transfer Register</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Transfer ID</th>
                  <th>Source Location</th>
                  <th>Destination Location</th>
                  <th>Total Items</th>
                  <th>Departure Date</th>
                  <th>Packing list</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {transfers.map((t) => (
                  <tr key={t.rawId}>
                    <td className="font-mono text-xs font-bold text-slate-400">{t.id}</td>
                    <td className="font-semibold text-slate-200">{t.from}</td>
                    <td className="font-semibold text-slate-200">{t.to}</td>
                    <td>{t.itemsCount} unique products</td>
                    <td>{t.date}</td>
                    <td>
                      <span className={`badge ${t.packingList === 'Printed' ? 'badge-green' : 'badge-yellow'}`}>{t.packingList}</span>
                    </td>
                    <td>
                      <span className={`badge ${t.status === 'Completed' ? 'badge-green' : t.status === 'Cancelled' ? 'badge-red' : 'badge-cyan'}`}>{t.status}</span>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button className="btn-secondary py-1 px-3 text-xs flex items-center gap-1 hover:bg-cyan-500/10 hover:text-cyan-400 hover:border-cyan-500/30 transition-colors">
                          <FileDown className="w-3.5 h-3.5" /> Print Packing Sheet
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
