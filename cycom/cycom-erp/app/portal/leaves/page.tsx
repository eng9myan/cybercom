'use client';

import React, { useState } from 'react';
import { useT } from '@/lib/i18n';

export default function MyLeavesPortal() {
  const t = useT();
  const [leaveType, setLeaveType] = useState('Annual Leave');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [notes, setNotes] = useState('');

  const BALANCES = [
    { type: t('portalLeaves.balAnnual'), total: 21, taken: 6.5, remaining: 14.5, color: 'border-cyan-500/20' },
    { type: t('portalLeaves.balSick'), total: 14, taken: 2, remaining: 12, color: 'border-purple-500/20' },
    { type: t('portalLeaves.balMaternity'), total: 90, taken: 0, remaining: 90, color: 'border-orange-500/20' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('portalLeaves.title')}</h1>
          <p className="page-subtitle">{t('portalLeaves.subtitle')}</p>
        </div>
      </div>

      {/* Leave Balances */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {BALANCES.map((b) => (
          <div key={b.type} className={`glass-card p-5 border ${b.color} space-y-3`}>
            <span className="text-xs text-slate-500 font-bold uppercase">{b.type}</span>
            <div className="flex justify-between items-end">
              <span className="text-3xl font-black text-white">{b.remaining} <span className="text-xs text-slate-400 font-normal">{t('portalLeaves.days')}</span></span>
              <div className="text-end text-[10px] text-slate-500">
                <span>{t('portalLeaves.totalTaken', { total: b.total, taken: b.taken })}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Form and History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Request Form */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('portalLeaves.requestHeading')}</h2>
          <div className="space-y-3 text-sm">
            <div>
              <label className="text-xs text-slate-400 block mb-1">{t('portalLeaves.leaveType')}</label>
              <select
                className="input-field"
                value={leaveType}
                onChange={(e) => setLeaveType(e.target.value)}
              >
                <option value="Annual Leave">{t('portalLeaves.optAnnual')}</option>
                <option value="Sick Leave">{t('portalLeaves.optSick')}</option>
                <option value="Unpaid Leave">{t('portalLeaves.optUnpaid')}</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">{t('portalLeaves.startDate')}</label>
                <input
                  type="date"
                  className="input-field font-mono"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">{t('portalLeaves.endDate')}</label>
                <input
                  type="date"
                  className="input-field font-mono"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">{t('portalLeaves.notesReason')}</label>
              <textarea
                className="input-field min-h-[80px]"
                placeholder={t('portalLeaves.notesPh')}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
            <button className="btn-primary w-full py-2.5">
              {t('portalLeaves.submitRequest')}
            </button>
          </div>
        </div>

        {/* History */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('portalLeaves.myApplicationsHeading')}</h2>
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-white/5 border border-white/5 flex justify-between items-center text-xs">
              <div className="space-y-1">
                <span className="font-bold text-slate-200 block">{t('portalLeaves.optAnnual')}</span>
                <span className="text-slate-500 block">{t('portalLeaves.annualLeaveDays')}</span>
              </div>
              <span className="badge badge-yellow">{t('status.pendingApproval')}</span>
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/5 flex justify-between items-center text-xs">
              <div className="space-y-1">
                <span className="font-bold text-slate-200 block">{t('portalLeaves.optSick')}</span>
                <span className="text-slate-500 block">{t('portalLeaves.sickLeaveDays')}</span>
              </div>
              <div className="text-end space-y-1">
                <span className="badge badge-red block">{t('status.declined')}</span>
                <span className="text-[10px] text-amber-500 block">{t('portalLeaves.fellBackUnpaid')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
