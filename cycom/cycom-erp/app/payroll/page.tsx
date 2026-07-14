'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  DollarSign, Clock, Download, Plus, CheckCircle,
  XCircle, Calculator, FileSpreadsheet, Eye, RefreshCw
} from 'lucide-react';
import { useCycomList, fmtCode, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';

// --- Backend raw types ---
type CycomOvertimeRaw = {
  id: number;
  employee_id: Many2One;
  date: string;
  duration: number;
  state: string;
};

type CycomPayslipRaw = {
  id: number;
  employee_id: Many2One;
  date_from: string;
  date_to: string;
  net_wage: number;
  state: string;
};

// --- UI types ---
interface OvertimeClaim {
  id: string;
  employeeName: string;
  hours: number;
  ratePerHour: number;
  multiplier: number;
  date: string;
  status: 'pending' | 'approved' | 'rejected';
}

interface GeneratedPayslip {
  id: string;
  employeeName: string;
  baseSalary: number;
  overtimePaid: number;
  latenessDeductions: number;
  allowances: number;
  netSalary: number;
  period: string;
  status: 'Draft' | 'Approved' | 'Paid';
}

// --- Mappers ---
const mapOvertimeClaim = (r: CycomOvertimeRaw): OvertimeClaim => ({
  id: fmtCode('OT', r.id),
  employeeName: m2oName(r.employee_id),
  hours: r.duration ?? 0,
  ratePerHour: 0,
  multiplier: 1.5,
  date: fmtDate(r.date),
  status: r.state === 'validated' ? 'approved' : r.state === 'refused' ? 'rejected' : 'pending',
});

const fmtPeriod = (s?: string): string => {
  if (!s) return '—';
  const d = new Date(s);
  if (isNaN(d.getTime())) return s;
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
};

const mapPayslip = (r: CycomPayslipRaw): GeneratedPayslip => ({
  id: fmtCode('PS', r.id),
  employeeName: m2oName(r.employee_id),
  baseSalary: 0,
  overtimePaid: 0,
  latenessDeductions: 0,
  allowances: 0,
  netSalary: r.net_wage ?? 0,
  period: fmtPeriod(r.date_from),
  status: r.state === 'done' ? 'Paid' : r.state === 'verify' ? 'Approved' : 'Draft',
});

export default function PayrollDashboard() {
  const { rows: otClaims, loading: loadingOT } = useCycomList<CycomOvertimeRaw, OvertimeClaim>(
    'hr.attendance.overtime',
    [],
    ['employee_id', 'date', 'duration', 'state'],
    mapOvertimeClaim,
  );
  const { rows: payslips, loading: loadingPayslips } = useCycomList<CycomPayslipRaw, GeneratedPayslip>(
    'hr.payslip',
    [],
    ['employee_id', 'date_from', 'date_to', 'net_wage', 'state'],
    mapPayslip,
    { order: 'date_from desc' },
  );
  const loading = loadingOT || loadingPayslips;

  // Payslip Generator states
  const [selectedEmp, setSelectedEmp] = useState('Ahmad Masri');
  const [baseSalary, setBaseSalary] = useState(750);
  const [otHours, setOtHours] = useState(0);
  const [latenessMins, setLatenessMins] = useState(0);
  const [customAllowances, setCustomAllowances] = useState(0);
  const [slipPeriod, setSlipPeriod] = useState('June 2026');

  // Lateness Calculator helper
  // Rule: 1-15 min = 0, 16-30 min = 0.5 hour deduction, 31-60 min = 1 hour deduction, 60+ min = 2 hours deduction
  const calculateLatenessDeduction = (mins: number, hourlyRate: number) => {
    if (mins <= 15) return 0;
    if (mins <= 30) return 0.5 * hourlyRate;
    if (mins <= 60) return 1.0 * hourlyRate;
    return 2.0 * hourlyRate; // 60+ min
  };

  // Derived Values
  const hourlyRate = baseSalary / 176; // 22 working days * 8 hours
  const latenessDeduction = calculateLatenessDeduction(latenessMins, hourlyRate);
  const otPaidValue = otHours * hourlyRate * 1.5;
  const calculatedNet = baseSalary + otPaidValue + customAllowances - latenessDeduction;

  const handleGeneratePayslip = (e: React.FormEvent) => {
    e.preventDefault();
    // Payslip creation requires a backend write; local addition disabled after live data wiring.
  };

  const handleApproveOT = (_id: string) => {
    // OT approval requires a backend write; local mutation disabled after live data wiring.
  };

  const handleRejectOT = (_id: string) => {
    // OT rejection requires a backend write; local mutation disabled after live data wiring.
  };

  const handleBulkApprovePayslips = () => {
    // Bulk approval requires a backend write; local mutation disabled after live data wiring.
  };

  // Excel csv export simulation
  const exportToExcel = () => {
    const headers = ['Payslip ID,Employee,Base Salary,OT Paid,Lateness Deductions,Allowances,Net Salary,Period,Status\n'];
    const rows = payslips.map(ps =>
      `${ps.id},"${ps.employeeName}",${ps.baseSalary},${ps.overtimePaid},${ps.latenessDeductions},${ps.allowances},${ps.netSalary},"${ps.period}",${ps.status}\n`
    );
    const blob = new Blob([...headers, ...rows], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `Cycom_Group_Payslips_${slipPeriod.replace(' ', '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Payroll & Compensation Command</h1>
          <p className="page-subtitle">Process monthly wages, calculate lateness deductions, manage overtime approvals, and export financial summaries.</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={exportToExcel}
            className="btn-secondary flex items-center gap-2"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" /> Export XLSX Summary
          </button>
          <button
            onClick={handleBulkApprovePayslips}
            className="btn-primary flex items-center gap-2"
          >
            <CheckCircle className="w-4 h-4" /> Bulk Approve Drafts
          </button>
        </div>
      </div>

      {/* Stats Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Monthly Net</span>
            <p className="text-2xl font-black text-white">JOD {payslips.reduce((acc, curr) => acc + curr.netSalary, 0).toLocaleString(undefined, {maximumFractionDigits: 2})}</p>
          </div>
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
            <DollarSign className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Pending OT approvals</span>
            <p className="text-2xl font-black text-[#F59E0B]">
              {otClaims.filter(c => c.status === 'pending').length} requests
            </p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
            <Clock className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Lateness Deducted</span>
            <p className="text-2xl font-black text-[#EF4444]">
              JOD {payslips.reduce((acc, curr) => acc + curr.latenessDeductions, 0).toFixed(2)}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-red-500/10 text-red-400">
            <Calculator className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Processed Slips</span>
            <p className="text-2xl font-black text-[#10B981]">{payslips.length}</p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <CheckCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column - Payslip Calculator Form */}
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Payslip Generator Engine</h2>
            <Calculator className="w-4 h-4 text-[#E67E22]" />
          </div>

          <form onSubmit={handleGeneratePayslip} className="space-y-4">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Employee</label>
              <select
                value={selectedEmp}
                onChange={e => {
                  setSelectedEmp(e.target.value);
                  setBaseSalary(e.target.value === 'Sara Haddad' ? 950 : e.target.value === 'Rami Khasawneh' ? 600 : 750);
                }}
                className="input-field"
              >
                <option value="Ahmad Masri">Ahmad Masri (EMP-029)</option>
                <option value="Sara Haddad">Sara Haddad (EMP-034)</option>
                <option value="Rami Khasawneh">Rami Khasawneh (EMP-088)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Base Salary (JOD)</label>
                <input
                  type="number"
                  value={baseSalary}
                  onChange={e => setBaseSalary(parseFloat(e.target.value) || 0)}
                  className="input-field"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Pay Period</label>
                <input
                  type="text"
                  value={slipPeriod}
                  onChange={e => setSlipPeriod(e.target.value)}
                  className="input-field"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">OT Hours</label>
                <input
                  type="number"
                  value={otHours}
                  onChange={e => setOtHours(parseFloat(e.target.value) || 0)}
                  placeholder="e.g. 5"
                  className="input-field"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Allowances (JOD)</label>
                <input
                  type="number"
                  value={customAllowances}
                  onChange={e => setCustomAllowances(parseFloat(e.target.value) || 0)}
                  placeholder="e.g. 100"
                  className="input-field"
                />
              </div>
            </div>

            {/* Lateness settings */}
            <div className="p-4 rounded-xl bg-white/3 border border-white/5 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Lateness Deduction</span>
                <span className="text-[9px] bg-red-500/20 text-[#EF4444] px-1.5 py-0.2 rounded font-bold">Cycom Rules</span>
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] text-slate-500">Lateness Minutes this month:</label>
                <input
                  type="number"
                  value={latenessMins}
                  onChange={e => setLatenessMins(parseInt(e.target.value) || 0)}
                  placeholder="e.g. 45 min"
                  className="input-field py-1"
                />
                <div className="text-[10px] text-slate-400 leading-relaxed pt-1 flex flex-col gap-0.5">
                  <span>Calculated Hourly Rate: <strong>JOD {hourlyRate.toFixed(2)}/hr</strong></span>
                  <span>Penalty Action: <strong>{latenessMins <= 15 ? 'Grace Period (0 hrs)' : latenessMins <= 30 ? 'Deduct 0.5 hrs' : latenessMins <= 60 ? 'Deduct 1.0 hrs' : 'Deduct 2.0 hrs'}</strong></span>
                </div>
              </div>
            </div>

            {/* Real-time Calculation Breakdown */}
            <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2 text-xs">
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">Base Wage:</span>
                <span className="font-semibold text-slate-300">JOD {baseSalary.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">OT Pay (1.5x):</span>
                <span className="font-semibold text-emerald-400">+JOD {otPaidValue.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">Allowances:</span>
                <span className="font-semibold text-emerald-400">+JOD {customAllowances.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">Lateness Penalty:</span>
                <span className="font-semibold text-red-400">-JOD {latenessDeduction.toFixed(2)}</span>
              </div>
              <div className="flex justify-between pt-1 font-bold text-sm">
                <span className="text-white">Est. Net Net:</span>
                <span className="text-[#E67E22]">JOD {calculatedNet.toFixed(2)}</span>
              </div>
            </div>

            <button type="submit" className="btn-primary w-full py-2">
              Generate & Record Payslip
            </button>
          </form>
        </div>

        {/* Right Column - Overtime wallet claims & Payslip Records */}
        <div className="lg:col-span-2 space-y-6">

          {/* Overtime Wallet approvals */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Overtime Wallet Approval Queue</h2>
              <span className="text-[10px] bg-[#F59E0B]/20 text-[#F59E0B] border border-[#F59E0B]/30 px-2 py-0.5 rounded font-bold">
                cycom_payroll_overtime
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Employee</th>
                    <th>Date</th>
                    <th>Hours</th>
                    <th>Rate</th>
                    <th>Multiplier</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {otClaims.map(claim => {
                    const totalVal = claim.hours * claim.ratePerHour * claim.multiplier;
                    return (
                      <tr key={claim.id}>
                        <td className="font-mono text-xs">{claim.id}</td>
                        <td className="font-semibold text-slate-300">{claim.employeeName}</td>
                        <td>{claim.date}</td>
                        <td>{claim.hours} hrs</td>
                        <td>JOD {claim.ratePerHour.toFixed(2)}</td>
                        <td>{claim.multiplier}x</td>
                        <td className="font-bold text-white">JOD {totalVal.toFixed(2)}</td>
                        <td>
                          <span className={`badge text-[9px] ${
                            claim.status === 'approved' ? 'badge-green' :
                            claim.status === 'rejected' ? 'badge-red' : 'badge-yellow'
                          }`}>{claim.status}</span>
                        </td>
                        <td className="text-right">
                          {claim.status === 'pending' && (
                            <div className="flex gap-1 justify-end">
                              <button
                                onClick={() => handleApproveOT(claim.id)}
                                className="p-1 rounded hover:bg-emerald-500/20 text-[#10B981]"
                              >
                                <CheckCircle className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleRejectOT(claim.id)}
                                className="p-1 rounded hover:bg-red-500/20 text-[#EF4444]"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Payslip Records */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Processed Payslips Ledger</h2>
              <span className="text-[10px] bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30 px-2 py-0.5 rounded font-bold">
                cycom_payslip_xlsx
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Slip ID</th>
                    <th>Employee Name</th>
                    <th>Base</th>
                    <th>OT Paid</th>
                    <th>Lateness Ded.</th>
                    <th>Allowances</th>
                    <th>Net Salary</th>
                    <th>Period</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {payslips.map(ps => (
                    <tr key={ps.id}>
                      <td className="font-mono text-xs">{ps.id}</td>
                      <td className="font-semibold text-slate-300">{ps.employeeName}</td>
                      <td>JOD {ps.baseSalary}</td>
                      <td className="text-emerald-400">+JOD {ps.overtimePaid}</td>
                      <td className="text-red-400">-JOD {ps.latenessDeductions}</td>
                      <td className="text-emerald-400">+JOD {ps.allowances}</td>
                      <td className="font-black text-white">JOD {ps.netSalary}</td>
                      <td>{ps.period}</td>
                      <td>
                        <span className={`badge text-[9px] ${
                          ps.status === 'Paid' ? 'badge-green' :
                          ps.status === 'Approved' ? 'badge-blue' : 'badge-yellow'
                        }`}>{ps.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
