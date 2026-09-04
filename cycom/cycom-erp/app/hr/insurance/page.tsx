'use client';

import React from 'react';
import { Award, ShieldCheck, Heart, Plus } from 'lucide-react';
import { useCycomList, m2oName, fmtCode, Many2One } from '@/lib/cycomModels';
import { useT } from '@/lib/i18n';

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
  const t = useT();
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
          <h1 className="page-title text-white">{t('hrInsurance.title')}</h1>
          <p className="page-subtitle">{t('hrInsurance.subtitle')}</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> {t('hrInsurance.addContract')}
        </button>
      </div>

      {loading && (
        <div className="glass-card p-8 text-center text-slate-400 text-sm">
          {t('hrInsurance.loading')}
        </div>
      )}

      {/* Insurance Grades Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-cyan-500/20 bg-cyan-950/10 space-y-4">
          <div className="flex justify-between items-start">
            <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl">
              <Award className="w-6 h-6" />
            </div>
            <span className="badge badge-cyan">{t('hrInsurance.tier1')}</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{t('hrInsurance.gradeATitle')}</h3>
            <p className="text-xs text-slate-400 mt-1">{t('hrInsurance.gradeADesc')}</p>
          </div>
          <div className="pt-2 flex justify-between text-xs border-t border-white/5 text-slate-400">
            <span>{t('hrInsurance.activeEnrollees')}</span>
            <span className="font-bold text-white">{t('hrInsurance.employeesN', { n: 45 })}</span>
          </div>
        </div>

        <div className="glass-card p-6 border-purple-500/20 bg-purple-950/10 space-y-4">
          <div className="flex justify-between items-start">
            <div className="p-3 bg-purple-500/10 text-purple-400 rounded-xl">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <span className="badge badge-purple">{t('hrInsurance.tier2')}</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{t('hrInsurance.gradeBTitle')}</h3>
            <p className="text-xs text-slate-400 mt-1">{t('hrInsurance.gradeBDesc')}</p>
          </div>
          <div className="pt-2 flex justify-between text-xs border-t border-white/5 text-slate-400">
            <span>{t('hrInsurance.activeEnrollees')}</span>
            <span className="font-bold text-white">{t('hrInsurance.employeesN', { n: 188 })}</span>
          </div>
        </div>

        <div className="glass-card p-6 border-orange-500/20 bg-orange-950/10 space-y-4">
          <div className="flex justify-between items-start">
            <div className="p-3 bg-orange-500/10 text-orange-400 rounded-xl">
              <Heart className="w-6 h-6" />
            </div>
            <span className="badge badge-orange">{t('hrInsurance.tier3')}</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{t('hrInsurance.gradeCTitle')}</h3>
            <p className="text-xs text-slate-400 mt-1">{t('hrInsurance.gradeCDesc')}</p>
          </div>
          <div className="pt-2 flex justify-between text-xs border-t border-white/5 text-slate-400">
            <span>{t('hrInsurance.activeEnrollees')}</span>
            <span className="font-bold text-white">{t('hrInsurance.employeesN', { n: 109 })}</span>
          </div>
        </div>
      </div>

      {/* Contracts Table */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('hrInsurance.ledgerHeading')}</h2>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('hrInsurance.colContract')}</th>
                <th>{t('hrInsurance.colEmployeeName')}</th>
                <th>{t('hrInsurance.colGradeTier')}</th>
                <th>{t('hrInsurance.colDependents')}</th>
                <th>{t('hrInsurance.colPremium')}</th>
                <th>{t('hrInsurance.colCompanyShare')}</th>
                <th>{t('hrInsurance.colDeduction')}</th>
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
