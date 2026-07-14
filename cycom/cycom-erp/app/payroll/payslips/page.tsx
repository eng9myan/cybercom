'use client';

import React from 'react';
import { FileSpreadsheet, FileDown, Plus } from 'lucide-react';
import { useCycomList, fmtCode, fmtMoney, fmtDate } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';

type CycomPayslipRun = {
  id: number;
  name?: string;
  date_start?: string;
  date_end?: string;
  state?: string;
  slip_count?: number;
};

interface PayslipBatch {
  id: string;
  rawId: number;
  name: string;
  count: number;
  status: string;
  totalGross: string;
  date: string;
}

const mapRun = (r: CycomPayslipRun): PayslipBatch => ({
  rawId: r.id,
  id: fmtCode('BATCH', r.id, 6),
  name: r.name || `Payroll batch ${r.id}`,
  count: r.slip_count ?? 0,
  status: r.state === 'close' ? 'Completed' : 'Draft',
  totalGross: fmtMoney(0, 'JOD'),
  date: fmtDate(r.date_end || r.date_start),
});

export default function PayslipBatches() {
  const { rows: batches, loading, error } = useCycomList<CycomPayslipRun, PayslipBatch>(
    'hr.payslip.run',
    [],
    ['name', 'date_start', 'date_end', 'state', 'slip_count'],
    mapRun,
    { limit: 100, order: 'date_end desc' },
  );

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Payslip Batches</h1>
          <p className="page-subtitle">Compile individual employee payslips into bulk cycles and generate XLSX spreadsheets (cycom_payslip_xlsx).</p>
        </div>
        <button className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> Create Batch</button>
      </div>

      {loading && <LoadingCard label="Loading payroll batches…" />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && batches.length === 0 && <EmptyCard label="No payroll batches yet. Create one to begin." />}

      <div className="space-y-4">
        {batches.map((b) => (
          <div key={b.id} className="glass-card p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl border border-cyan-500/10">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] font-mono font-bold text-cyan-400 bg-cyan-950/40 border border-cyan-800/30 px-2 py-0.5 rounded">{b.id}</span>
                <h3 className="text-lg font-bold text-white mt-1.5">{b.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">Pay Date: {b.date} • {b.count} Employees included</p>
              </div>
            </div>
            <div className="flex flex-col md:items-end gap-2 text-right">
              <div>
                <span className="text-xs text-slate-500 block">Gross Rollup</span>
                <span className="text-lg font-black text-white">{b.totalGross}</span>
              </div>
              <div className="flex gap-2">
                <span className={`badge ${b.status === 'Completed' ? 'badge-green' : 'badge-yellow'} self-center`}>{b.status}</span>
                <button className="btn-secondary py-1 px-3 text-xs flex items-center gap-1.5 hover:bg-cyan-500/10 hover:text-cyan-400 hover:border-cyan-500/30 transition-colors">
                  <FileDown className="w-3.5 h-3.5" /> Export XLSX
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-white mb-3">Cycom Excel Mapping Standard</h3>
        <p className="text-xs text-slate-400 leading-relaxed mb-4">
          Under Cycom accounting policies, generated Excel sheets map all salary items dynamically: Base Salary, Allowances (Transport, Housing), Overtime Hours &amp; Valuations, Lateness Deductions, Health Copays, and Net Payable.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-white/5 rounded-lg border border-white/5"><span className="text-slate-500 block">Bank Output</span><span className="text-slate-200 font-semibold">Standard CSV</span></div>
          <div className="p-3 bg-white/5 rounded-lg border border-white/5"><span className="text-slate-500 block">File Format</span><span className="text-slate-200 font-semibold">Excel (xlsx)</span></div>
          <div className="p-3 bg-white/5 rounded-lg border border-white/5"><span className="text-slate-500 block">Deduction Hooks</span><span className="text-slate-200 font-semibold">Automatic</span></div>
          <div className="p-3 bg-white/5 rounded-lg border border-white/5"><span className="text-slate-500 block">Workflow Stage</span><span className="text-slate-200 font-semibold">Draft → Post</span></div>
        </div>
      </div>
    </div>
  );
}
