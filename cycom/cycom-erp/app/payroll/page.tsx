'use client';

import React, { useState } from 'react';
import {
  DollarSign, Clock, CheckCircle,
  XCircle, Calculator, FileSpreadsheet
} from 'lucide-react';
import { useCycomList, fmtCode, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { useT } from '@/lib/i18n';

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

const OT_STATUS_KEY: Record<OvertimeClaim['status'], string> = {
  pending: 'status.pendingApproval',
  approved: 'status.approved',
  rejected: 'status.declined',
};

const SLIP_STATUS_KEY: Record<GeneratedPayslip['status'], string> = {
  Draft: 'status.draft',
  Approved: 'status.approved',
  Paid: 'status.paid',
};

export default function PayrollDashboard() {
  const t = useT();
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

  const penaltyLabel =
    latenessMins <= 15 ? t('payrollDash.penaltyGrace') :
    latenessMins <= 30 ? t('payrollDash.penaltyHalf') :
    latenessMins <= 60 ? t('payrollDash.penaltyOne') :
    t('payrollDash.penaltyTwo');

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

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>{t('payrollDash.loading')}</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('payrollDash.title')}</h1>
          <p className="page-subtitle">{t('payrollDash.subtitle')}</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={exportToExcel}
            className="btn-secondary flex items-center gap-2"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" /> {t('payrollDash.exportXlsx')}
          </button>
          <button
            onClick={handleBulkApprovePayslips}
            className="btn-primary flex items-center gap-2"
          >
            <CheckCircle className="w-4 h-4" /> {t('payrollDash.bulkApprove')}
          </button>
        </div>
      </div>

      {/* Stats Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{t('payrollDash.totalMonthlyNet')}</span>
            <p className="text-2xl font-black text-white">JOD {payslips.reduce((acc, curr) => acc + curr.netSalary, 0).toLocaleString(undefined, {maximumFractionDigits: 2})}</p>
          </div>
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
            <DollarSign className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{t('payrollDash.pendingOt')}</span>
            <p className="text-2xl font-black text-[#F59E0B]">
              {t('payrollDash.requestsN', { n: otClaims.filter(c => c.status === 'pending').length })}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
            <Clock className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{t('payrollDash.latenessDeducted')}</span>
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
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{t('payrollDash.processedSlips')}</span>
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
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('payrollDash.generatorHeading')}</h2>
            <Calculator className="w-4 h-4 text-[#E67E22]" />
          </div>

          <form onSubmit={handleGeneratePayslip} className="space-y-4">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase">{t('payrollDash.employee')}</label>
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
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('payrollDash.baseSalary')}</label>
                <input
                  type="number"
                  value={baseSalary}
                  onChange={e => setBaseSalary(parseFloat(e.target.value) || 0)}
                  className="input-field"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('payrollDash.payPeriod')}</label>
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
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('payrollDash.otHours')}</label>
                <input
                  type="number"
                  value={otHours}
                  onChange={e => setOtHours(parseFloat(e.target.value) || 0)}
                  placeholder={t('payrollDash.otHoursPh')}
                  className="input-field"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('payrollDash.allowances')}</label>
                <input
                  type="number"
                  value={customAllowances}
                  onChange={e => setCustomAllowances(parseFloat(e.target.value) || 0)}
                  placeholder={t('payrollDash.allowancesPh')}
                  className="input-field"
                />
              </div>
            </div>

            {/* Lateness settings */}
            <div className="p-4 rounded-xl bg-white/3 border border-white/5 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">{t('payrollDash.latenessHeading')}</span>
                <span className="text-[9px] bg-red-500/20 text-[#EF4444] px-1.5 py-0.2 rounded font-bold">{t('payrollDash.latenessRules')}</span>
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] text-slate-500">{t('payrollDash.latenessMinutes')}</label>
                <input
                  type="number"
                  value={latenessMins}
                  onChange={e => setLatenessMins(parseInt(e.target.value) || 0)}
                  placeholder={t('payrollDash.latenessMinutesPh')}
                  className="input-field py-1"
                />
                <div className="text-[10px] text-slate-400 leading-relaxed pt-1 flex flex-col gap-0.5">
                  <span>{t('payrollDash.hourlyRate', { rate: `JOD ${hourlyRate.toFixed(2)}` })}</span>
                  <span>{t('payrollDash.penaltyAction', { action: penaltyLabel })}</span>
                </div>
              </div>
            </div>

            {/* Real-time Calculation Breakdown */}
            <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2 text-xs">
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">{t('payrollDash.baseWage')}</span>
                <span className="font-semibold text-slate-300">JOD {baseSalary.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">{t('payrollDash.otPay')}</span>
                <span className="font-semibold text-emerald-400">+JOD {otPaidValue.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">{t('payrollDash.allowancesLine')}</span>
                <span className="font-semibold text-emerald-400">+JOD {customAllowances.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-1">
                <span className="text-slate-500">{t('payrollDash.latenessPenalty')}</span>
                <span className="font-semibold text-red-400">-JOD {latenessDeduction.toFixed(2)}</span>
              </div>
              <div className="flex justify-between pt-1 font-bold text-sm">
                <span className="text-white">{t('payrollDash.estNet')}</span>
                <span className="text-[#E67E22]">JOD {calculatedNet.toFixed(2)}</span>
              </div>
            </div>

            <button type="submit" className="btn-primary w-full py-2">
              {t('payrollDash.generateBtn')}
            </button>
          </form>
        </div>

        {/* Right Column - Overtime wallet claims & Payslip Records */}
        <div className="lg:col-span-2 space-y-6">

          {/* Overtime Wallet approvals */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('payrollDash.otQueueHeading')}</h2>
              <span className="text-[10px] bg-[#F59E0B]/20 text-[#F59E0B] border border-[#F59E0B]/30 px-2 py-0.5 rounded font-bold">
                cycom_payroll_overtime
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('payrollDash.colId')}</th>
                    <th>{t('payrollDash.colEmployee')}</th>
                    <th>{t('payrollDash.colDate')}</th>
                    <th>{t('payrollDash.colHours')}</th>
                    <th>{t('payrollDash.colRate')}</th>
                    <th>{t('payrollDash.colMultiplier')}</th>
                    <th>{t('payrollDash.colTotal')}</th>
                    <th>{t('payrollDash.colStatus')}</th>
                    <th className="text-end">{t('payrollDash.colActions')}</th>
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
                        <td>{t('payrollDash.hoursN', { n: claim.hours })}</td>
                        <td>JOD {claim.ratePerHour.toFixed(2)}</td>
                        <td>{claim.multiplier}x</td>
                        <td className="font-bold text-white">JOD {totalVal.toFixed(2)}</td>
                        <td>
                          <span className={`badge text-[9px] ${
                            claim.status === 'approved' ? 'badge-green' :
                            claim.status === 'rejected' ? 'badge-red' : 'badge-yellow'
                          }`}>{t(OT_STATUS_KEY[claim.status])}</span>
                        </td>
                        <td className="text-end">
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
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('payrollDash.payslipLedgerHeading')}</h2>
              <span className="text-[10px] bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30 px-2 py-0.5 rounded font-bold">
                cycom_payslip_xlsx
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('payrollDash.slipId')}</th>
                    <th>{t('payrollDash.employeeName')}</th>
                    <th>{t('payrollDash.base')}</th>
                    <th>{t('payrollDash.otPaid')}</th>
                    <th>{t('payrollDash.latenessDed')}</th>
                    <th>{t('payrollDash.allowances')}</th>
                    <th>{t('payrollDash.netSalary')}</th>
                    <th>{t('payrollDash.period')}</th>
                    <th>{t('payrollDash.colStatus')}</th>
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
                        }`}>{t(SLIP_STATUS_KEY[ps.status])}</span>
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
