'use client';

import React from 'react';
import { Clock, CheckCircle2, ShieldAlert, Award, FileSpreadsheet, Plus } from 'lucide-react';
import { useCycomList, fmtCode, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';

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
  status: string;
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
    r.state === 'validated' ? 'Approved' :
    r.state === 'refused' ? 'Rejected' :
    'Pending Approval',
});

export default function OvertimePayroll() {
  const { rows: entries, loading } = useCycomList<CycomOvertimeRaw, OvertimeEntry>(
    'hr.attendance.overtime',
    [],
    ['employee_id', 'date', 'duration', 'state', 'reason'],
    mapOvertime,
    { order: 'date desc' },
  );

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Overtime Compensation</h1>
          <p className="page-subtitle">Track overtime hours synched from attendance, calculate compensations using custom multipliers, and process approvals (cycom_payroll_overtime).</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Log Overtime
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-5 space-y-2">
          <span className="text-xs text-slate-500 font-bold uppercase">Total Overtime Hours</span>
          <p className="text-3xl font-black text-white">19 Hours</p>
          <span className="text-xs text-slate-400">Recorded this period</span>
        </div>
        <div className="glass-card p-5 space-y-2">
          <span className="text-xs text-slate-500 font-bold uppercase">Calculated Outflow</span>
          <p className="text-3xl font-black text-white">JOD 305.00</p>
          <span className="text-xs text-slate-400">Total approved OT payout</span>
        </div>
        <div className="glass-card p-5 space-y-2">
          <span className="text-xs text-slate-500 font-bold uppercase">Rate Config</span>
          <div className="flex justify-between items-center text-xs font-semibold text-slate-300 mt-2">
            <span>Normal Rate:</span>
            <span className="text-cyan-400 font-mono">1.25x</span>
          </div>
          <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
            <span>Holiday Rate:</span>
            <span className="text-purple-400 font-mono">1.50x</span>
          </div>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Overtime Ledger</h2>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Entry</th>
                <th>Employee Name</th>
                <th>Date</th>
                <th>Normal Hours</th>
                <th>Holiday Hours</th>
                <th>Calculation</th>
                <th>Total Value</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td className="font-mono text-xs font-bold text-slate-400">{entry.id}</td>
                  <td className="font-semibold text-slate-200">{entry.employee}</td>
                  <td>{entry.date}</td>
                  <td>{entry.normalHours} hr ({entry.multiplierNormal})</td>
                  <td>{entry.holidayHours} hr ({entry.multiplierHoliday})</td>
                  <td className="text-xs text-slate-400">Normal + Holiday multipliers</td>
                  <td className="font-bold text-cyan-400">{entry.totalCalculated}</td>
                  <td>
                    <span className={`badge ${
                      entry.status === 'Approved' ? 'badge-green' : 'badge-yellow'
                    }`}>{entry.status}</span>
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
