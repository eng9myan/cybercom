'use client';

import React from 'react';

export function LoadingCard({ label = 'Loading from Cycom backend…' }: { label?: string }) {
  return <div className="glass-card p-8 text-center text-slate-400 text-sm">{label}</div>;
}

export function ErrorCard({ error, hint }: { error: string; hint?: string }) {
  return (
    <div className="glass-card p-6 border border-rose-500/30 bg-rose-500/5 text-sm">
      <p className="text-rose-300 font-semibold mb-1">Couldn't load data</p>
      <p className="text-rose-400/80 text-xs">{error}</p>
      <p className="text-slate-500 text-[10px] mt-2">
        {hint ?? "Confirm cycom-platform is running (docker compose up) and you're logged in."}
      </p>
    </div>
  );
}

export function EmptyCard({ label = 'No records found.' }: { label?: string }) {
  return <div className="glass-card p-8 text-center text-slate-500 text-sm">{label}</div>;
}
