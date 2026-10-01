'use client';

import React from 'react';
import { useT } from '@/lib/i18n';

/** One national e-invoicing field, as declared by the backend format's
 * FieldSpec (platform.einvoicing.national). Labels are the official
 * national terms (e.g. "Regime fiscale", "UsoCFDI") on purpose -- they're
 * what the taxpayer's accountant and the authority's docs call them. */
export interface EInvoiceFieldSpec {
  scope: 'seller' | 'buyer' | 'line' | 'document';
  key: string;
  label: string;
  required: boolean;
  pattern: string | null;
  choices: { value: string; label: string }[];
  help: string;
  conditional: boolean;
  default_from: string | null;
}

/** Translated label for a format mode, falling back to the backend label. */
export function useModeLabel() {
  const t = useT();
  return (mode: string | null | undefined, fallback?: string | null) => {
    if (!mode) return fallback || '';
    const key = `einvoicing.mode.${mode}`;
    const v = t(key);
    return v === key ? (fallback || mode) : v;
  };
}

export function EInvoiceFieldInput({
  spec, value, onChange, invalid, compact, mode,
}: {
  spec: EInvoiceFieldSpec; value: string; onChange: (v: string) => void; invalid?: boolean; compact?: boolean;
  mode?: string | null;
}) {
  const t = useT();
  const helpKey = mode ? `einvoicing.help.${mode}.${spec.scope}.${spec.key}` : '';
  const translatedHelp = helpKey ? t(helpKey) : '';
  const help = translatedHelp && translatedHelp !== helpKey ? translatedHelp : spec.help;
  const cls = `w-full bg-slate-950 border rounded-lg px-3 py-2 text-slate-200 outline-none text-xs ${
    invalid ? 'border-rose-500/60' : 'border-slate-850'
  }`;
  const patternOk = !value || !spec.pattern || new RegExp(`^(?:${spec.pattern})$`).test(value);
  return (
    <div>
      {!compact && (
        <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
          {spec.label}
          {spec.required && !spec.conditional && <span className="text-rose-400">*</span>}
          {spec.conditional && <span className="normal-case font-normal text-slate-600">({t('einvoicing.whenApplicable')})</span>}
        </label>
      )}
      {spec.choices.length > 0 ? (
        <select value={value} onChange={(e) => onChange(e.target.value)} className={`${cls} mt-0.5`}>
          <option value="">{t('einvoicing.selectPlaceholder')}</option>
          {spec.choices.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
        </select>
      ) : (
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          dir="ltr"
          className={`${cls} mt-0.5 ${patternOk ? '' : 'border-amber-500/60'}`}
        />
      )}
      {!compact && help && <p className="text-[10px] text-slate-500 mt-0.5">{help}</p>}
      {!patternOk && <p className="text-[10px] text-amber-400 mt-0.5">{t('einvoicing.formatHint')}</p>}
    </div>
  );
}
