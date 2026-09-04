'use client';

import React from 'react';
import { FileSpreadsheet, FileDown, Plus } from 'lucide-react';
import { useCycomList, fmtCode, fmtMoney, fmtDate } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';
import { useT } from '@/lib/i18n';

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
  completed: boolean;
  totalGross: string;
  date: string;
}

const mapRun = (r: CycomPayslipRun): PayslipBatch => ({
  rawId: r.id,
  id: fmtCode('BATCH', r.id, 6),
  name: r.name || `Payroll batch ${r.id}`,
  count: r.slip_count ?? 0,
  completed: r.state === 'close',
  totalGross: fmtMoney(0, 'JOD'),
  date: fmtDate(r.date_end || r.date_start),
});

export default function PayslipBatches() {
  const t = useT();
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
          <h1 className="page-title text-white">{t('payslips.title')}</h1>
          <p className="page-subtitle">{t('payslips.subtitle')}</p>
        </div>
        <button className="btn-primary flex items-center gap-2"><Plus className="w-4 h-4" /> {t('payslips.createBatch')}</button>
      </div>

      {loading && <LoadingCard label={t('payslips.loading')} />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && batches.length === 0 && <EmptyCard label={t('payslips.empty')} />}

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
                <p className="text-xs text-slate-400 mt-0.5">{t('payslips.payDate', { date: b.date })} • {t('payslips.employeesIncluded', { n: b.count })}</p>
              </div>
            </div>
            <div className="flex flex-col md:items-end gap-2 text-right">
              <div>
                <span className="text-xs text-slate-500 block">{t('payslips.grossRollup')}</span>
                <span className="text-lg font-black text-white">{b.totalGross}</span>
              </div>
              <div className="flex gap-2">
                <span className={`badge ${b.completed ? 'badge-green' : 'badge-yellow'} self-center`}>
                  {b.completed ? t('status.completed') : t('status.draft')}
                </span>
                <button className="btn-secondary py-1 px-3 text-xs flex items-center gap-1.5 hover:bg-cyan-500/10 hover:text-cyan-400 hover:border-cyan-500/30 transition-colors">
                  <FileDown className="w-3.5 h-3.5" /> {t('payslips.exportXlsx')}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-white mb-3">{t('payslips.mappingHeading')}</h3>
        <p className="text-xs text-slate-400 leading-relaxed mb-4">{t('payslips.mappingBody')}</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-white/5 rounded-lg border border-white/5"><span className="text-slate-500 block">{t('payslips.bankOutput')}</span><span className="text-slate-200 font-semibold">CSV</span></div>
          <div className="p-3 bg-white/5 rounded-lg border border-white/5"><span className="text-slate-500 block">{t('payslips.fileFormat')}</span><span className="text-slate-200 font-semibold">Excel (xlsx)</span></div>
          <div className="p-3 bg-white/5 rounded-lg border border-white/5"><span className="text-slate-500 block">{t('payslips.deductionHooks')}</span><span className="text-slate-200 font-semibold">{t('payslips.automatic')}</span></div>
          <div className="p-3 bg-white/5 rounded-lg border border-white/5"><span className="text-slate-500 block">{t('payslips.workflowStage')}</span><span className="text-slate-200 font-semibold">{t('status.draft')} → {t('status.posted')}</span></div>
        </div>
      </div>
    </div>
  );
}
