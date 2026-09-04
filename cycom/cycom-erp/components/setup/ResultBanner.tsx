'use client';

import React from 'react';
import Link from 'next/link';
import { CheckCircle2, AlertTriangle } from 'lucide-react';
import { useT } from '@/lib/i18n';

type Ok = { ok: true; summary: string[]; warnings?: string[] };
type Err = { ok: false; error: string; warnings?: string[] };

export function ResultBanner({
  result,
  successCta,
  recoveryHint,
}: {
  result: Ok | Err;
  successCta?: { href: string; label: string };
  recoveryHint?: string;
}) {
  const t = useT();
  const cta = successCta ?? { href: '/setup', label: t('setupWizard.continueNext') };
  const hint = recoveryHint ?? t('setupWizard.recoveryHint');
  if (result.ok) {
    return (
      <div className="glass-card p-6 border border-emerald-500/30 bg-emerald-500/5 space-y-3">
        <div className="flex items-center gap-2 text-emerald-300 font-bold">
          <CheckCircle2 className="w-5 h-5" /> {t('setupWizard.setupApplied')}
        </div>
        <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
          {result.summary.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
        {result.warnings && result.warnings.length > 0 && (
          <div className="text-[11px] text-amber-300 space-y-1">
            <div className="font-bold flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" /> {t('setupWizard.warnings')}
            </div>
            <ul className="list-disc list-inside ml-1">
              {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        )}
        <div className="pt-2">
          <Link href={cta.href} className="btn-secondary text-xs py-2 px-3">{cta.label}</Link>
        </div>
      </div>
    );
  }
  return (
    <div className="glass-card p-6 border border-rose-500/30 bg-rose-500/5 space-y-2">
      <div className="flex items-center gap-2 text-rose-300 font-bold">
        <AlertTriangle className="w-5 h-5" /> {t('setupWizard.setupFailed')}
      </div>
      <p className="text-xs text-rose-200">{result.error}</p>
      <p className="text-[10px] text-slate-500">{hint}</p>
    </div>
  );
}
