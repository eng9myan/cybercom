'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Play, Settings, ShieldAlert, Cpu } from 'lucide-react';
import { useT } from '@/lib/i18n';

export default function WorkflowBuilder() {
  const t = useT();
  const router = useRouter();

  // Rule Config
  const [field, setField] = useState('amount_total');
  const [operator, setOperator] = useState('>');
  const [value, setValue] = useState('1000');

  // Test Context
  const [ctxVal, setCtxVal] = useState('1500');

  // Results
  const [evalResult, setEvalResult] = useState<boolean | null>(null);

  // Pure client-side condition evaluation -- no engine anywhere in cycom
  // actually wires this rule shape into real business events, so this is
  // a standalone "test a condition" sandbox, not a connected workflow
  // trigger. Numeric operators compare as numbers when both sides parse
  // as one, otherwise fall back to string comparison.
  const handleEvaluate = (e: React.FormEvent) => {
    e.preventDefault();
    const ctx = ctxVal;
    const numCtx = parseFloat(ctx);
    const numVal = parseFloat(value);
    const bothNumeric = !Number.isNaN(numCtx) && !Number.isNaN(numVal);

    let matched: boolean;
    switch (operator) {
      case '>':
        matched = bothNumeric ? numCtx > numVal : ctx > value;
        break;
      case '<':
        matched = bothNumeric ? numCtx < numVal : ctx < value;
        break;
      case '==':
        matched = bothNumeric ? numCtx === numVal : ctx === value;
        break;
      case 'contains':
        matched = ctx.toLowerCase().includes(value.toLowerCase());
        break;
      default:
        matched = false;
    }
    setEvalResult(matched);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex items-center gap-4 mb-8">
        <button
          onClick={() => router.push('/settings')}
          className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
        >
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            {t('settingsWorkflows.title')}
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('settingsWorkflows.subtitle')}</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Rule Editor */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-2">
            <Settings className="w-4 h-4 text-blue-400" /> {t('settingsWorkflows.editorHeading')}
          </h3>
          <form onSubmit={handleEvaluate} className="space-y-4">
            <div className="space-y-1">
              <label className="text-slate-400">{t('settingsWorkflows.contextField')}</label>
              <select
                value={field} onChange={e => setField(e.target.value)}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
              >
                <option value="amount_total">amount_total (Purchase/Sales Total)</option>
                <option value="items_count">items_count (Total items in transfer)</option>
                <option value="supplier_risk">supplier_risk (low/medium/high)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-slate-400">{t('settingsWorkflows.operator')}</label>
                <select
                  value={operator} onChange={e => setOperator(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                >
                  <option value=">">{t('settingsWorkflows.gt')}</option>
                  <option value="<">{t('settingsWorkflows.lt')}</option>
                  <option value="==">{t('settingsWorkflows.eq')}</option>
                  <option value="contains">{t('settingsWorkflows.contains')}</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-slate-400">{t('settingsWorkflows.ruleValue')}</label>
                <input
                  type="text" value={value} onChange={e => setValue(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                />
              </div>
            </div>

            <div className="space-y-3 border-t border-white/5 pt-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">{t('settingsWorkflows.simulateHeading')}</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-slate-500 font-bold uppercase">{t('settingsWorkflows.field')}</label>
                  <div className="w-full bg-slate-950/60 border border-slate-900 rounded-lg px-3 py-2 text-slate-400 font-mono text-xs">{field}</div>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-slate-500 font-bold uppercase">{t('settingsWorkflows.value')}</label>
                  <input
                    type="text" value={ctxVal} onChange={e => setCtxVal(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none font-bold"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-semibold shadow-lg shadow-blue-600/15 transition flex items-center justify-center gap-2"
            >
              <Play className="w-4 h-4" /> {t('settingsWorkflows.evaluateBtn')}
            </button>
          </form>
        </div>

        {/* Rule Output */}
        <div className="glass-card p-6 flex flex-col justify-center items-center text-center space-y-4">
          {evalResult !== null ? (
            <>
              <div className={`w-16 h-16 rounded-full flex items-center justify-center border transition ${
                evalResult
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                  : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
              }`}>
                {evalResult ? <ShieldAlert className="w-8 h-8 animate-pulse" /> : <Cpu className="w-8 h-8" />}
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-100">
                  {evalResult ? t('settingsWorkflows.triggerFired') : t('settingsWorkflows.conditionNotMatched')}
                </h3>
                <p className="text-xs text-slate-400 mt-2 max-w-xs leading-relaxed">
                  {evalResult
                    ? t('settingsWorkflows.matchedNote', { field, val: ctxVal, op: operator, rule: value })
                    : t('settingsWorkflows.notMatchedNote', { field, val: ctxVal, op: operator, rule: value })}
                </p>
              </div>
            </>
          ) : (
            <div className="text-slate-500 max-w-xs">
              <Cpu className="w-8 h-8 mx-auto text-slate-600 mb-2" />
              {t('settingsWorkflows.emptyState')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
