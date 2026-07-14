'use client';

import React from 'react';
import { CheckCircle2 } from 'lucide-react';

export function StepIndicator({ steps, current }: { steps: readonly string[]; current: number }) {
  return (
    <div className="glass-card p-4 flex items-center gap-2">
      {steps.map((label, idx) => {
        const state = idx < current ? 'done' : idx === current ? 'active' : 'pending';
        return (
          <React.Fragment key={label}>
            <div className="flex items-center gap-2">
              <div
                className={
                  'w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold border ' +
                  (state === 'done'
                    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                    : state === 'active'
                    ? 'bg-orange-500/15 text-[#E67E22] border-orange-500/40'
                    : 'bg-white/5 text-slate-500 border-white/10')
                }
              >
                {state === 'done' ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
              </div>
              <span
                className={
                  'text-xs font-bold uppercase tracking-widest ' +
                  (state === 'pending' ? 'text-slate-500' : 'text-white')
                }
              >
                {label}
              </span>
            </div>
            {idx < steps.length - 1 && <div className="flex-1 h-px bg-white/10" />}
          </React.Fragment>
        );
      })}
    </div>
  );
}
