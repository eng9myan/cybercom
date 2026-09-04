'use client';

import React from 'react';
import { Settings } from 'lucide-react';
import { useCycomList, fmtCode, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { useT } from '@/lib/i18n';

// --- Backend raw type ---
type CycomPayslipLineRaw = {
  id: number;
  employee_id: Many2One;
  name: string;
  amount: number;
  date: string;
  slip_id: Many2One;
  code: string;
};

// --- UI type ---
interface DeductionEntry {
  id: string;
  employee: string;
  date: string;
  delayMinutes: number;
  calcKey: 'latenessDeduction' | 'absenceDeduction' | 'generalDeduction';
  deduction: string;
  status: 'stApplied';
}

// --- Mapper ---
const mapDeduction = (r: CycomPayslipLineRaw): DeductionEntry => ({
  id: fmtCode('DED', r.id),
  employee: m2oName(r.employee_id),
  date: fmtDate(r.date),
  delayMinutes: 0,
  calcKey:
    r.code === 'LATE' ? 'latenessDeduction' :
    r.code === 'ABSENCE' ? 'absenceDeduction' :
    'generalDeduction',
  deduction: `JOD ${Math.abs(r.amount ?? 0).toFixed(2)}`,
  status: 'stApplied',
});

export default function LatenessDeductions() {
  const t = useT();
  const { rows: list, loading } = useCycomList<CycomPayslipLineRaw, DeductionEntry>(
    'hr.payslip.line',
    [['code', 'in', ['DED', 'ABSENCE', 'LATE']]],
    ['employee_id', 'name', 'amount', 'date', 'slip_id', 'code'],
    mapDeduction,
  );

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>{t('payrollDeductions.loading')}</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('payrollDeductions.title')}</h1>
          <p className="page-subtitle">{t('payrollDeductions.subtitle')}</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <Settings className="w-4 h-4" /> {t('payrollDeductions.graceSettings')}
        </button>
      </div>

      {/* Settings Summary Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-5 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-500 font-bold uppercase">{t('payrollDeductions.gracePeriod')}</span>
            <span className="badge badge-cyan">{t('payrollDeductions.active')}</span>
          </div>
          <p className="text-2xl font-black text-white">{t('payrollDeductions.minutesN', { n: 15 })}</p>
          <p className="text-xs text-slate-400">{t('payrollDeductions.graceNote')}</p>
        </div>

        <div className="glass-card p-5 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-500 font-bold uppercase">{t('payrollDeductions.latenessMultiplier')}</span>
            <span className="badge badge-purple">{t('payrollDeductions.standard')}</span>
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <div className="flex justify-between">
              <span>{t('payrollDeductions.first15to30')}</span>
              <span className="font-mono font-bold text-white">{t('payrollDeductions.x1Hourly')}</span>
            </div>
            <div className="flex justify-between">
              <span>{t('payrollDeductions.range30to60')}</span>
              <span className="font-mono font-bold text-white">{t('payrollDeductions.x15Hourly')}</span>
            </div>
            <div className="flex justify-between">
              <span>{t('payrollDeductions.over60')}</span>
              <span className="font-mono font-bold text-white">{t('payrollDeductions.x2Hourly')}</span>
            </div>
          </div>
        </div>

        <div className="glass-card p-5 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-500 font-bold uppercase">{t('payrollDeductions.totalDeductions')}</span>
            <span className="badge badge-red">{t('payrollDeductions.thisCycle')}</span>
          </div>
          <p className="text-2xl font-black text-white">JOD 65.00</p>
          <p className="text-xs text-slate-400">{t('payrollDeductions.totalDeductionsNote')}</p>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('payrollDeductions.ledgerHeading')}</h2>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('payrollDeductions.colEntry')}</th>
                <th>{t('payrollDeductions.colEmployeeName')}</th>
                <th>{t('payrollDeductions.colInfractionDate')}</th>
                <th>{t('payrollDeductions.colDelayDuration')}</th>
                <th>{t('payrollDeductions.colFormulaApplied')}</th>
                <th>{t('payrollDeductions.colDeductionAmount')}</th>
                <th>{t('payrollDeductions.colStatus')}</th>
              </tr>
            </thead>
            <tbody>
              {list.map((d) => (
                <tr key={d.id}>
                  <td className="font-mono text-xs font-bold text-slate-400">{d.id}</td>
                  <td className="font-semibold text-slate-200">{d.employee}</td>
                  <td>{d.date}</td>
                  <td>{t('payrollDeductions.minsN', { n: d.delayMinutes })}</td>
                  <td>{t(`payrollDeductions.${d.calcKey}`)}</td>
                  <td className={d.deduction !== 'JOD 0.00' ? 'font-bold text-rose-400' : 'text-slate-400'}>{d.deduction}</td>
                  <td>
                    <span className="badge badge-red">{t('payrollDeductions.stApplied')}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
