'use client';

import React from 'react';
import { FileSignature, DollarSign, CheckCircle2 } from 'lucide-react';
import { useCycomList, fmtCode, fmtDate, fmtMoney, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';

type CycomExpense = {
  id: number;
  name?: string;
  employee_id?: Many2One;
  product_id?: Many2One;
  total_amount?: number;
  date?: string;
  description?: string | false;
  state?: string;
  currency_id?: Many2One;
};

interface ExpenseClaim {
  rawId: number;
  id: string;
  employeeName: string;
  item: string;
  category: string;
  amountFmt: string;
  amount: number;
  date: string;
  description: string;
  status: string;
}

const STATE_LABEL: Record<string, string> = {
  draft: 'Submitted',
  reported: 'Submitted',
  approved: 'Approved',
  done: 'Reimbursed',
  cancel: 'Declined',
  refused: 'Declined',
};

const mapExpense = (e: CycomExpense): ExpenseClaim => ({
  rawId: e.id,
  id: fmtCode('EXP', e.id, 3),
  employeeName: m2oName(e.employee_id, '—'),
  item: e.name || `Expense ${e.id}`,
  category: m2oName(e.product_id, 'Other'),
  amount: Number(e.total_amount ?? 0),
  amountFmt: fmtMoney(e.total_amount ?? 0, m2oName(e.currency_id, '')),
  date: fmtDate(e.date),
  description: (e.description as string) || '—',
  status: STATE_LABEL[e.state ?? ''] || (e.state || 'Submitted'),
});

export default function ExpensesPage() {
  const { rows: expenses, loading, error } = useCycomList<CycomExpense, ExpenseClaim>(
    'hr.expense',
    [],
    ['name', 'employee_id', 'product_id', 'total_amount', 'date', 'description', 'state', 'currency_id'],
    mapExpense,
    { limit: 200, order: 'date desc' },
  );

  const totalSubmitted = expenses.filter((e) => e.status === 'Submitted').reduce((acc, e) => acc + e.amount, 0);
  const totalReimbursed = expenses.filter((e) => e.status === 'Reimbursed').reduce((acc, e) => acc + e.amount, 0);
  const pendingCount = expenses.filter((e) => e.status === 'Submitted').length;

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Expense Claims</h1>
          <p className="page-subtitle">Employee expense submissions, approvals, and reimbursements.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Stat label="Pending approval" value={pendingCount} icon={<FileSignature className="w-5 h-5" />} tone="amber" />
        <Stat label="Total submitted" value={fmtMoney(totalSubmitted, '')} icon={<DollarSign className="w-5 h-5" />} tone="cyan" />
        <Stat label="Total reimbursed" value={fmtMoney(totalReimbursed, '')} icon={<CheckCircle2 className="w-5 h-5" />} tone="emerald" />
      </div>

      {loading && <LoadingCard label="Loading expense claims…" />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && expenses.length === 0 && <EmptyCard label="No expense claims yet." />}

      {!loading && !error && expenses.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Claims Register</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr><th>Claim</th><th>Employee</th><th>Description</th><th>Category</th><th>Amount</th><th>Date</th><th>Status</th></tr>
              </thead>
              <tbody>
                {expenses.map((e) => (
                  <tr key={e.rawId}>
                    <td className="font-mono text-xs font-bold text-slate-400">{e.id}</td>
                    <td className="font-semibold text-slate-200">{e.employeeName}</td>
                    <td>{e.item}</td>
                    <td><span className="badge badge-purple">{e.category}</span></td>
                    <td className="font-bold text-white">{e.amountFmt}</td>
                    <td className="text-slate-400">{e.date}</td>
                    <td><span className={`badge ${e.status === 'Reimbursed' || e.status === 'Approved' ? 'badge-green' : e.status === 'Declined' ? 'badge-red' : 'badge-yellow'}`}>{e.status}</span></td>
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

function Stat({ label, value, icon, tone }: { label: string; value: number | string; icon: React.ReactNode; tone: 'cyan' | 'amber' | 'emerald' }) {
  const colors = {
    cyan: 'bg-cyan-500/10 text-cyan-400',
    amber: 'bg-amber-500/10 text-amber-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
  }[tone];
  return (
    <div className="stat-card flex items-center justify-between">
      <div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{label}</span>
        <p className="text-2xl font-black text-white">{value}</p>
      </div>
      <div className={`p-3 rounded-xl ${colors}`}>{icon}</div>
    </div>
  );
}
