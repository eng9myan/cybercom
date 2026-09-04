'use client';

import React from 'react';
import { useCycomList, fmtCode, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { Check, X } from 'lucide-react';
import { useT } from '@/lib/i18n';

type CycomOvertime = {
  id: number;
  employee_id: Many2One;
  date?: string;
  duration?: number;
  state?: string;
};

type OvertimeReq = {
  id: string;
  employee: string;
  week: string;
  overtimeHours: number;
  eligibility: 'Eligible' | 'Requires Review';
  rateType: string;
  reason: string;
};

const mapOvertime = (r: CycomOvertime): OvertimeReq => ({
  id: fmtCode('OT-REQ', r.id, 4),
  employee: m2oName(r.employee_id),
  week: fmtDate(r.date),
  overtimeHours: r.duration ?? 0,
  eligibility: r.state === 'validated' ? 'Eligible' : 'Requires Review',
  rateType: '1.25x (Normal)',
  reason: '—',
});

export default function OvertimeApprovalFlow() {
  const t = useT();
  const { rows: requests, loading } = useCycomList<CycomOvertime, OvertimeReq>(
    'hr.attendance.overtime', // TODO: verify model name
    [],
    ['employee_id', 'date', 'duration', 'state'],
    mapOvertime,
    { limit: 100, order: 'date desc' },
  );

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>{t('attendanceMain.loading')}</div>;

  const handleAction = (_id: string, _action: 'Approved' | 'Rejected') => {
    // TODO: call Backend write API to update state, then reload
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('attendanceOvertime.title')}</h1>
          <p className="page-subtitle">{t('attendanceOvertime.subtitle')}</p>
        </div>
      </div>

      {/* Info Rules Box */}
      <div className="glass-card p-6 border-cyan-500/20 bg-cyan-950/10 text-xs">
        <h3 className="text-sm font-bold text-white mb-2">{t('attendanceOvertime.rulesHeading')}</h3>
        <p className="text-slate-400 leading-relaxed mb-4">
          {t('attendanceOvertime.rulesDesc')}
        </p>
        <div className="flex gap-4 font-mono text-[11px] text-slate-300">
          <div>
            <span className="text-slate-500 block">{t('attendanceOvertime.hqRegularHours')}</span>
            <span className="font-bold">{t('attendanceOvertime.hoursPerWeek', { n: 40 })}</span>
          </div>
          <div>
            <span className="text-slate-500 block">{t('attendanceOvertime.warehouseRegularHours')}</span>
            <span className="font-bold">{t('attendanceOvertime.hoursPerWeek', { n: 48 })}</span>
          </div>
          <div>
            <span className="text-slate-500 block">{t('attendanceOvertime.eligibilityCheck')}</span>
            <span className="text-emerald-400 font-semibold">{t('attendanceOvertime.automaticCheck')}</span>
          </div>
        </div>
      </div>

      {/* Requests Queue */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('attendanceOvertime.queueHeading')}</h2>
        {requests.length === 0 ? (
          <div className="glass-card p-8 text-center text-slate-500 text-xs font-semibold">
            {t('attendanceOvertime.emptyQueue')}
          </div>
        ) : (
          requests.map((r) => (
            <div key={r.id} className="glass-card p-5 space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] font-mono font-bold text-cyan-400 bg-cyan-950/40 border border-cyan-800/30 px-2 py-0.5 rounded">
                    {r.id}
                  </span>
                  <h3 className="text-base font-bold text-white mt-1.5">{r.employee}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{r.week}</p>
                </div>
                <div className="text-end space-y-1">
                  <span className={`badge ${
                    r.eligibility === 'Eligible' ? 'badge-green' : 'badge-yellow'
                  }`}>{r.eligibility === 'Eligible' ? t('attendanceOvertime.eligibleVal') : t('attendanceOvertime.reviewVal')}</span>
                  <span className="text-xs text-[#E67E22] font-semibold block">{r.rateType}</span>
                </div>
              </div>

              <div className="bg-black/30 p-3 rounded-lg border border-white/5 text-xs text-slate-300">
                <span className="text-slate-500 block text-[10px] uppercase font-bold">{t('attendanceOvertime.reasonPurpose')}</span>
                &quot;{r.reason}&quot;
              </div>

              <div className="flex justify-between items-center pt-2 border-t border-white/5">
                <span className="text-xs text-slate-400">{t('attendanceOvertime.proposed')} <strong className="text-white">{t('attendanceOvertime.hoursVal', { n: r.overtimeHours })}</strong></span>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleAction(r.id, 'Rejected')}
                    className="p-1.5 text-xs font-bold border border-red-500/20 text-red-400 bg-red-500/5 hover:bg-red-500/10 rounded-md transition-colors flex items-center gap-1"
                  >
                    <X className="w-3.5 h-3.5" /> {t('attendanceOvertime.deny')}
                  </button>
                  <button
                    onClick={() => handleAction(r.id, 'Approved')}
                    className="p-1.5 text-xs font-bold bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 rounded-md transition-colors flex items-center gap-1"
                  >
                    <Check className="w-3.5 h-3.5" /> {t('attendanceOvertime.approve')}
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
