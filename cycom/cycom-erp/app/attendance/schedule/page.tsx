'use client';

import React from 'react';
import { Info, Settings } from 'lucide-react';
import { useT } from '@/lib/i18n';

const SHIFTS = [
  { id: 'SHIFT-01', name: 'HQ General Shift', start: '08:00 AM', end: '04:00 PM', grace: '15 mins', workDays: 'Sunday - Thursday', normalizationType: 'Fixed Shift Rounding' },
  { id: 'SHIFT-02', name: 'Warehouse Zarqa Shift', start: '07:00 AM', end: '03:00 PM', grace: '15 mins', workDays: 'Saturday - Thursday', normalizationType: 'Split Shift Normalization' },
  { id: 'SHIFT-03', name: 'Retail Store Shift', start: '10:00 AM', end: '08:00 PM', grace: '10 mins', workDays: 'Saturday - Thursday', normalizationType: 'Flexible Rounding' },
];

export default function ScheduleNormalization() {
  const t = useT();
  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('schedule.title')}</h1>
          <p className="page-subtitle">{t('schedule.subtitle')}</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Settings className="w-4 h-4" /> {t('schedule.shiftSettings')}
        </button>
      </div>

      <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 flex gap-4 text-purple-300">
        <Info className="w-6 h-6 flex-shrink-0" />
        <div className="text-xs space-y-1">
          <h4 className="font-bold text-white">{t('schedule.whyHeading')}</h4>
          <p className="leading-relaxed">{t('schedule.whyBody')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {SHIFTS.map((shift) => (
          <div key={shift.id} className="glass-card p-6 space-y-4">
            <div className="flex justify-between items-start">
              <span className="text-[10px] font-mono font-bold text-cyan-400 bg-cyan-950/40 border border-cyan-800/30 px-2 py-0.5 rounded">
                {shift.id}
              </span>
              <span className="badge badge-purple">{shift.normalizationType}</span>
            </div>
            <div>
              <h3 className="text-base font-bold text-white">{shift.name}</h3>
              <p className="text-xs text-slate-400 mt-1">{shift.workDays}</p>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs bg-black/30 p-3 rounded-lg border border-white/5 font-mono text-slate-300">
              <div>
                <span className="text-slate-500 block">{t('schedule.shiftStart')}</span>
                <span className="font-bold text-white">{shift.start}</span>
              </div>
              <div>
                <span className="text-slate-500 block">{t('schedule.shiftEnd')}</span>
                <span className="font-bold text-white">{shift.end}</span>
              </div>
              <div className="col-span-2 pt-2 border-t border-white/5">
                <span className="text-slate-500 block">{t('schedule.graceLimit')}</span>
                <span className="font-semibold text-cyan-400">{shift.grace}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
