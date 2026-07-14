'use client';

import React, { useState } from 'react';
import { Award, ShieldCheck, Heart, Users, Search, Plus, TrendingUp } from 'lucide-react';
import { useCycomList, m2oName, fmtCode, Many2One } from '@/lib/cycomModels';

// TODO: verify model name — may be hr.insurance in some backend versions
type BackendInsurance = {
  id: number;
  employee_id?: Many2One;
  name?: string;
  policy_number?: string | false;
  insurance_provider?: string | false;
  date_start?: string | false;
  date_end?: string | false;
  state?: string;
};

type ContractRow = {
  id: string;
  employee: string;
  grade: string;
  provider: string;
  dependentCount: number;
  premium: string;
  companyShare: string;
  employeeDeduction: string;
};

export default function HealthInsurance() {
  const { rows, loading } = useCycomList<BackendInsurance, ContractRow>(
    'hr.employee.insurance', // TODO: verify model name
    [],
    ['employee_id', 'name', 'policy_number', 'insurance_provider', 'date_start', 'date_end', 'state'],
    (r) => ({
      id: fmtCode('INS', r.id),
      employee: m2oName(r.employee_id),
      grade: r.name || '—',
      provider: (r.insurance_provider as string) || '—',
      dependentCount: 0,
      premium: '—',
      companyShare: '—',
      employeeDeduction: '—',
    }),
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Health Insurance Grades</h1>
          <p className="page-subtitle">Manage group health insurance schemes, coverage tiers, provider accounts, and monthly payroll integrations (hr_health_insurance).</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Contract
        </button>
      </div>

      {loading && (
        <div className="glass-card p-8 text-center text-slate-400 text-sm">
          Loading insurance data from backend…
        </div>
      )}

      {/* Insurance Grades Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-cyan-500/20 bg-cyan-950/10 space-y-4">
          <div className="flex justify-between items-start">
            <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl">
              <Award className="w-6 h-6" />
            </div>
            <span className="badge badge-cyan">Tier 1</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Grade A - Premium</h3>
            <p className="text-xs text-slate-400 mt-1">Full medical & dental network coverage. 75% company copay. Unlimited hospital network access.</p>
          </div>
          <div className="pt-2 flex justify-between text-xs border-t border-white/5 text-slate-400">
            <span>Active Enrollees:</span>
            <span className="font-bold text-white">45 Employees</span>
          </div>
        </div>

        <div className="glass-card p-6 border-purple-500/20 bg-purple-950/10 space-y-4">
          <div className="flex justify-between items-start">
            <div className="p-3 bg-purple-500/10 text-purple-400 rounded-xl">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <span className="badge badge-purple">Tier 2</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Grade B - Standard</h3>
            <p className="text-xs text-slate-400 mt-1">Primary network coverage, core dental. 85% company copay. Standard network hospital tier.</p>
          </div>
          <div className="pt-2 flex justify-between text-xs border-t border-white/5 text-slate-400">
            <span>Active Enrollees:</span>
            <span className="font-bold text-white">188 Employees</span>
          </div>
        </div>

        <div className="glass-card p-6 border-orange-500/20 bg-orange-950/10 space-y-4">
          <div className="flex justify-between items-start">
            <div className="p-3 bg-orange-500/10 text-orange-400 rounded-xl">
              <Heart className="w-6 h-6" />
            </div>
            <span className="badge badge-orange">Tier 3</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Grade C - Basic</h3>
            <p className="text-xs text-slate-400 mt-1">Emergency & basic clinic network. 90% company copay. Government & designated hospital tier.</p>
          </div>
          <div className="pt-2 flex justify-between text-xs border-t border-white/5 text-slate-400">
            <span>Active Enrollees:</span>
            <span className="font-bold text-white">109 Employees</span>
          </div>
        </div>
      </div>

      {/* Contracts Table */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Employee Insurance Ledger</h2>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Contract</th>
                <th>Employee Name</th>
                <th>Grade Tier</th>
                <th>Dependents</th>
                <th>Premium</th>
                <th>Company Share</th>
                <th>Deduction</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((contract) => (
                <tr key={contract.id}>
                  <td className="font-mono text-xs text-slate-400 font-bold">{contract.id}</td>
                  <td className="font-semibold text-slate-200">{contract.employee}</td>
                  <td>{contract.grade}</td>
                  <td>
                    <span className="badge badge-blue">{contract.dependentCount}</span>
                  </td>
                  <td>{contract.premium}</td>
                  <td>{contract.companyShare}</td>
                  <td className="font-bold text-cyan-400">{contract.employeeDeduction}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
