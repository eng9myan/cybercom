'use client';

import React from 'react';

export function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white/5 border border-white/8 rounded-xl p-3">
      <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">{label}</div>
      <div className="text-slate-200 font-semibold mt-0.5">{value}</div>
    </div>
  );
}
