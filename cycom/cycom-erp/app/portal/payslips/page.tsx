'use client';

import React from 'react';
import { FileDown, FileText } from 'lucide-react';
import { useCycomList, type Many2One } from '@/lib/cycomModels';
import { useT } from '@/lib/i18n';

type CycomPayslip = {
  id: number;
  employee_id?: Many2One;
  date_from?: string;
  date_to?: string;
  net_wage?: number;
  state?: string;
};

interface Payslip {
  id: string;
  period: string;
  basic: string;
  allowance: string;
  deduction: string;
  net: string;
  status: 'released' | 'pendingApproval';
}

const mapPayslip = (r: CycomPayslip): Payslip => {
  const dateFrom = r.date_from ? new Date(r.date_from) : null;
  const period = dateFrom
    ? dateFrom.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : '—';
  return {
    id: `PAY-${String(r.id).padStart(4, '0')}`,
    period,
    basic: '—',
    allowance: '—',
    deduction: '—',
    net: `JOD ${(r.net_wage ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
    status: r.state === 'done' ? 'released' : 'pendingApproval',
  };
};

export default function MyPayslipsPortal() {
  const t = useT();
  const { rows: payslips, loading } = useCycomList<CycomPayslip, Payslip>(
    'hr.payslip',
    [['state', '=', 'done']],
    ['employee_id', 'date_from', 'date_to', 'net_wage', 'state'],
    mapPayslip,
  );

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>{t('portalPayslips.loading')}</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('portalPayslips.title')}</h1>
          <p className="page-subtitle">{t('portalPayslips.subtitle')}</p>
        </div>
      </div>

      {/* Ledger */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('portalPayslips.historyHeading')}</h2>
        <div className="space-y-4">
          {payslips.map((p) => (
            <div key={p.id} className="flex flex-col md:flex-row justify-between items-start md:items-center p-4 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-cyan-500/10 text-cyan-400 rounded-lg">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">{p.period}</h3>
                  <span className="text-[10px] font-mono text-slate-500">{t('portalPayslips.idLabel', { id: p.id })}</span>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-6 text-xs text-start">
                <div>
                  <span className="text-slate-500 block">{t('portalPayslips.basic')}</span>
                  <span className="font-semibold text-slate-200">{p.basic}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">{t('portalPayslips.allowances')}</span>
                  <span className="font-semibold text-emerald-400">{p.allowance}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">{t('portalPayslips.deductions')}</span>
                  <span className="font-semibold text-rose-400">{p.deduction}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">{t('portalPayslips.netPayable')}</span>
                  <span className="font-black text-white">{p.net}</span>
                </div>
              </div>

              <div className="flex gap-2 items-center">
                <span className={`badge ${p.status === 'released' ? 'badge-green' : 'badge-yellow'}`}>
                  {p.status === 'released' ? t('status.released') : t('status.pendingApproval')}
                </span>
                {p.status === 'released' && (
                  <button className="p-1.5 rounded bg-white/5 border border-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors">
                    <FileDown className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
