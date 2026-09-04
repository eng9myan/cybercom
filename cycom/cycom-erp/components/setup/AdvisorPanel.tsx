'use client';

import React from 'react';
import { Lightbulb } from 'lucide-react';
import { useT } from '@/lib/i18n';

export function AdvisorPanel({ lines }: { lines: string[] }) {
  const t = useT();
  return (
    <div className="glass-card p-5 border border-purple-500/20 bg-purple-500/5">
      <div className="flex items-center gap-2 mb-2">
        <Lightbulb className="w-4 h-4 text-purple-300" />
        <span className="text-xs font-bold uppercase tracking-wider text-purple-200">{t('setupWizard.aiRecommendation')}</span>
      </div>
      <ul className="space-y-1.5 text-xs text-slate-300">
        {lines.map((line, i) => (
          <li key={i} className="flex gap-2">
            <span className="text-purple-300/60">›</span>
            <span>{line}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
