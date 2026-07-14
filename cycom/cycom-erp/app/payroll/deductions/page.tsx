'use client';

import React from 'react';
import { Percent, Clock, AlertTriangle, ShieldCheck, Settings, Plus } from 'lucide-react';
import { useCycomList, fmtCode, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';

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
  calculation: string;
  deduction: string;
  status: string;
}

// --- Mapper ---
const mapDeduction = (r: CycomPayslipLineRaw): DeductionEntry => ({
  id: fmtCode('DED', r.id),
  employee: m2oName(r.employee_id),
  date: fmtDate(r.date),
  delayMinutes: 0,
  calculation:
    r.code === 'LATE' ? 'Lateness Deduction' :
    r.code === 'ABSENCE' ? 'Absence Deduction' :
    'General Deduction',
  deduction: `JOD ${Math.abs(r.amount ?? 0).toFixed(2)}`,
  status: 'Applied',
});

export default function LatenessDeductions() {
  const { rows: list, loading } = useCycomList<CycomPayslipLineRaw, DeductionEntry>(
    'hr.payslip.line',
    [['code', 'in', ['DED', 'ABSENCE', 'LATE']]],
    ['employee_id', 'name', 'amount', 'date', 'slip_id', 'code'],
    mapDeduction,
  );

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Lateness & Deductions</h1>
          <p className="page-subtitle">Track employee delay logs synched from ZK biometric devices, and calculate deductions based on company grace configurations (latness_deduction).</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <Settings className="w-4 h-4" /> Grace Settings
        </button>
      </div>

      {/* Settings Summary Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-5 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-500 font-bold uppercase">Grace Period</span>
            <span className="badge badge-cyan">Active</span>
          </div>
          <p className="text-2xl font-black text-white">15 Minutes</p>
          <p className="text-xs text-slate-400">Delays under 15 mins incur no penalty up to 3 times/month.</p>
        </div>

        <div className="glass-card p-5 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-500 font-bold uppercase">Lateness Multiplier</span>
            <span className="badge badge-purple">Standard</span>
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <div className="flex justify-between">
              <span>First 15-30m delay:</span>
              <span className="font-mono font-bold text-white">1.0x Hourly</span>
            </div>
            <div className="flex justify-between">
              <span>30-60m delay:</span>
              <span className="font-mono font-bold text-white">1.5x Hourly</span>
            </div>
            <div className="flex justify-between">
              <span>&gt;60m delay:</span>
              <span className="font-mono font-bold text-white">2.0x Hourly</span>
            </div>
          </div>
        </div>

        <div className="glass-card p-5 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-500 font-bold uppercase">Total deductions</span>
            <span className="badge badge-red">This Cycle</span>
          </div>
          <p className="text-2xl font-black text-white">JOD 65.00</p>
          <p className="text-xs text-slate-400">Total processed deduction deductions applied to salary bills.</p>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Deductions Ledger</h2>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Entry</th>
                <th>Employee Name</th>
                <th>Infraction Date</th>
                <th>Delay Duration</th>
                <th>Formula Applied</th>
                <th>Deduction Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {list.map((d) => (
                <tr key={d.id}>
                  <td className="font-mono text-xs font-bold text-slate-400">{d.id}</td>
                  <td className="font-semibold text-slate-200">{d.employee}</td>
                  <td>{d.date}</td>
                  <td>{d.delayMinutes} mins</td>
                  <td>{d.calculation}</td>
                  <td className={d.deduction !== 'JOD 0.00' ? 'font-bold text-rose-400' : 'text-slate-400'}>{d.deduction}</td>
                  <td>
                    <span className={`badge ${
                      d.status === 'Applied' ? 'badge-red' :
                      d.status === 'Pending Review' ? 'badge-yellow' :
                      'badge-green'
                    }`}>{d.status}</span>
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
