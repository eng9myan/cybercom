'use client';

import React from 'react';
import { ChevronLeft, ChevronRight, CheckCircle2, Sparkles } from 'lucide-react';
import { useT } from '@/lib/i18n';

type Props = {
  step: number;
  totalSteps: number;
  canAdvance: boolean;
  applying: boolean;
  applied: boolean;
  onBack: () => void;
  onNext: () => void;
  onApply: () => void;
  applyLabel?: string;
};

export function WizardFooter({
  step, totalSteps, canAdvance, applying, applied, onBack, onNext, onApply, applyLabel,
}: Props) {
  const t = useT();
  const isLast = step === totalSteps - 1;
  return (
    <div className="flex items-center justify-between pt-2">
      <button
        type="button"
        disabled={step === 0 || applying}
        onClick={onBack}
        className="btn-secondary flex items-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <ChevronLeft className="w-4 h-4 rtl:-scale-x-100" /> {t('setupWizard.back')}
      </button>

      {!isLast ? (
        <button
          type="button"
          disabled={!canAdvance}
          onClick={onNext}
          className="btn-primary flex items-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {t('setupWizard.next')} <ChevronRight className="w-4 h-4 rtl:-scale-x-100" />
        </button>
      ) : (
        <button
          type="button"
          onClick={onApply}
          disabled={applying || applied}
          className="btn-primary flex items-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {applying ? (
            <>
              <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              {t('setupWizard.applying')}
            </>
          ) : applied ? (
            <>
              <CheckCircle2 className="w-4 h-4" /> {t('setupWizard.applied')}
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" /> {applyLabel ?? t('setupWizard.applySetup')}
            </>
          )}
        </button>
      )}
    </div>
  );
}
