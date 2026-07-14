'use client';

import React from 'react';

export function ToggleRow({
  label, description, on, setOn,
}: {
  label: string;
  description: string;
  on: boolean;
  setOn: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => setOn(!on)}
      className={
        'w-full text-left flex items-center gap-3 p-3 rounded-xl border transition-all ' +
        (on
          ? 'bg-gradient-to-br from-emerald-500/10 to-cyan-500/5 border-emerald-500/30'
          : 'bg-white/5 border-white/10 hover:bg-white/10')
      }
    >
      <div className={'w-9 h-5 rounded-full relative transition-colors ' + (on ? 'bg-emerald-500/60' : 'bg-white/10')}>
        <div className={'absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ' + (on ? 'left-4' : 'left-0.5')} />
      </div>
      <div className="flex-1">
        <div className="text-sm font-bold text-white">{label}</div>
        <div className="text-[11px] text-slate-400">{description}</div>
      </div>
    </button>
  );
}
