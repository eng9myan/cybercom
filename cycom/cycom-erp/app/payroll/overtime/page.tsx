'use client';

import React from 'react';
import { Plus } from 'lucide-react';
import { useCycomList, fmtCode, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { useT } from '@/lib/i18n';

// --- Backend raw type ---
type CycomOvertimeRaw = {
  id: number;
  employee_id: Many2One;
  date: string;
  duration: number;
  state: string;
  reason: string;
};

// --- UI type ---
interface OvertimeEntry {
  id: string;
  employee: string;
  date: string;
  normalHours: number;
  holidayHours: number;
  multiplierNormal: string;
  multiplierHoliday: string;
  totalCalculated: string;
  status: 'approved' | 'declined' | 'pendingApproval';
}

// --- Mapper ---
const mapOvertime = (r: CycomOvertimeRaw): OvertimeEntry => ({
  id: fmtCode('OT', r.id),
  employee: m2oName(r.employee_id),
  date: fmtDate(r.date),
  normalHours: r.duration ?? 0,
  holidayHours: 0,
  multiplierNormal: '1.25x',
  multiplierHoliday: '1.50x',
  totalCalculated: '—',
  status:
    r.state === 'validated' ? 'approved' :
    r.state === 'refused' ? 'declined' :
    'pendingApproval',
});

export default function OvertimePayroll() {
  const t = useT();
  const { rows: entries, loading } = useCycomList<CycomOvertimeRaw, OvertimeEntry>(
    'hr.attendance.overtime',
    [],
    ['employee_id', 'date', 'duration', 'state', 'reason'],
    mapOvertime,
    { order: 'date desc' },
  );

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>{t('attendanceMain.loading')}</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('payrollOvertime.title')}</h1>
          <p className="page-subtitle">{t('payrollOvertime.subtitle')}</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> {t('payrollOvertime.logOvertime')}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-5 space-y-2">
          <span className="text-xs text-slate-500 font-bold uppercase">{t('payrollOvertime.totalOtHours')}</span>
          <p className="text-3xl font-black text-white">{t('payrollOvertime.hoursN', { n: 19 })}</p>
          <span className="text-xs text-slate-400">{t('payrollOvertime.recordedPeriod')}</span>
        </div>
        <div className="glass-card p-5 space-y-2">
          <span className="text-xs text-slate-500 font-bold uppercase">{t('payrollOvertime.calculatedOutflow')}</span>
          <p className="text-3xl font-black text-white">JOD 305.00</p>
          <span className="text-xs text-slate-400">{t('payrollOvertime.approvedPayout')}</span>
        </div>
        <div className="glass-card p-5 space-y-2">
          <span className="text-xs text-slate-500 font-bold uppercase">{t('payrollOvertime.rateConfig')}</span>
          <div className="flex justify-between items-center text-xs font-semibold text-slate-300 mt-2">
            <span>{t('payrollOvertime.normalRate')}</span>
            <span className="text-cyan-400 font-mono">1.25x</span>
          </div>
          <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
            <span>{t('payrollOvertime.holidayRate')}</span>
            <span className="text-purple-400 font-mono">1.50x</span>
          </div>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('payrollOvertime.ledgerHeading')}</h2>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('payrollOvertime.colEntry')}</th>
                <th>{t('payrollOvertime.colEmployeeName')}</th>
                <th>{t('payrollOvertime.colDate')}</th>
                <th>{t('payrollOvertime.colNormalHours')}</th>
                <th>{t('payrollOvertime.colHolidayHours')}</th>
                <th>{t('payrollOvertime.colCalculation')}</th>
                <th>{t('payrollOvertime.colTotalValue')}</th>
                <th>{t('payrollOvertime.colStatus')}</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td className="font-mono text-xs font-bold text-slate-400">{entry.id}</td>
                  <td className="font-semibold text-slate-200">{entry.employee}</td>
                  <td>{entry.date}</td>
                  <td>{t('payrollOvertime.hrMultiplier', { n: entry.normalHours, mult: entry.multiplierNormal })}</td>
                  <td>{t('payrollOvertime.hrMultiplier', { n: entry.holidayHours, mult: entry.multiplierHoliday })}</td>
                  <td className="text-xs text-slate-400">{t('payrollOvertime.normalPlusHoliday')}</td>
                  <td className="font-bold text-cyan-400">{entry.totalCalculated}</td>
                  <td>
                    <span className={`badge ${
                      entry.status === 'approved' ? 'badge-green' : 'badge-yellow'
                    }`}>{t(`status.${entry.status}`)}</span>
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
