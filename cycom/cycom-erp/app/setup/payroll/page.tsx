'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { DollarSign, Clock, Layers, Wrench } from 'lucide-react';
import { fetchTenantPrefs } from '@/lib/setup/coaSetup';
import {
  FREQUENCY_LABEL,
  getPayrollDefaults,
  type PayFrequency,
} from '@/lib/setup/payroll-templates';
import { applyPayrollSetup, type PayrollSetupResult } from '@/lib/setup/payrollSetup';
import { StepIndicator } from '@/components/setup/StepIndicator';
import { WizardFooter } from '@/components/setup/WizardFooter';
import { AdvisorPanel } from '@/components/setup/AdvisorPanel';
import { ReviewRow } from '@/components/setup/ReviewRow';
import { ResultBanner } from '@/components/setup/ResultBanner';

const STEPS = ['Frequency & hours', 'OT & lateness', 'Review'] as const;
type StepIdx = 0 | 1 | 2;

export default function PayrollWizard() {
  const [step, setStep] = useState<StepIdx>(0);
  const [industry, setIndustry] = useState<string | undefined>();
  const [frequency, setFrequency] = useState<PayFrequency>('monthly');
  const [weeklyHours, setWeeklyHours] = useState(48);
  const [otMultiplier, setOtMultiplier] = useState(1.5);
  const [latenessGraceMinutes, setLatenessGraceMinutes] = useState(15);
  const [enableCycomOvertime, setEnableCycomOvertime] = useState(true);
  const [enableMassReconciliation, setEnableMassReconciliation] = useState(true);

  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<PayrollSetupResult | null>(null);

  useEffect(() => {
    fetchTenantPrefs().then((prefs) => {
      setIndustry(prefs.industry);
      const d = getPayrollDefaults(prefs.industry);
      setFrequency(d.frequency);
      setWeeklyHours(d.weeklyHours);
      setOtMultiplier(d.otMultiplier);
      setLatenessGraceMinutes(d.latenessGraceMinutes);
    });
  }, []);

  const submit = async () => {
    setApplying(true);
    setResult(null);
    setResult(await applyPayrollSetup({
      frequency, weeklyHours, otMultiplier, latenessGraceMinutes,
      enableCycomOvertime, enableMassReconciliation,
    }));
    setApplying(false);
  };

  const canAdvance = useMemo(() => {
    if (step === 0) return weeklyHours > 0;
    if (step === 1) return otMultiplier >= 1 && latenessGraceMinutes >= 0;
    return true;
  }, [step, weeklyHours, otMultiplier, latenessGraceMinutes]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <DollarSign className="w-7 h-7 text-[#E67E22]" /> Payroll Structure
          </h1>
          <p className="page-subtitle">Pay frequency, working hours, overtime, lateness. Cycom builds the rules so you don't open salary-rule XML.</p>
        </div>
        <a href="/cycom/cycom/action-hr_payroll.action_hr_payroll_structure_type_list_view" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> Configure manually
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" /> Pay cycle
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(Object.keys(FREQUENCY_LABEL) as PayFrequency[]).map((f) => (
                  <button
                    key={f}
                    type="button"
                    onClick={() => setFrequency(f)}
                    className={
                      'text-left p-4 rounded-xl border transition-all ' +
                      (f === frequency
                        ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white'
                        : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10 hover:border-white/20')
                    }
                  >
                    <div className="text-sm font-bold">{FREQUENCY_LABEL[f]}</div>
                  </button>
                ))}
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                  Working hours per week
                </label>
                <input
                  type="number" min={1} max={84}
                  className="input-field py-2.5"
                  value={weeklyHours}
                  onChange={(e) => setWeeklyHours(parseFloat(e.target.value) || 0)}
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  Common values: 40 (services), 45 (wholesale), 48 (retail / manufacturing), 54 (hospitality).
                </p>
              </div>
            </div>

            <AdvisorPanel
              lines={[
                industry ? `Cycom pre-filled values typical for "${industry}" tenants.` : 'Run Company Setup first so Cycom can tailor these defaults to your industry.',
                'Pay frequency drives the work-entry generation cadence and the payslip date range.',
              ]}
            />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Overtime & lateness</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">Overtime multiplier</label>
                  <input type="number" step="0.1" min={1} max={3} className="input-field py-2.5" value={otMultiplier} onChange={(e) => setOtMultiplier(parseFloat(e.target.value) || 1)} />
                  <p className="text-[10px] text-slate-500 mt-1">Most jurisdictions: 1.5× weekday, 2× weekend/holiday.</p>
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">Lateness grace minutes</label>
                  <input type="number" min={0} max={120} className="input-field py-2.5" value={latenessGraceMinutes} onChange={(e) => setLatenessGraceMinutes(parseInt(e.target.value, 10) || 0)} />
                </div>
              </div>

              <div className="space-y-3 pt-1">
                <ToggleRow
                  label="Cycom overtime engine"
                  description="cycom_payroll_overtime + extra_hours_enhancement — pays OT from payslip inputs."
                  on={enableCycomOvertime}
                  setOn={setEnableCycomOvertime}
                />
                <ToggleRow
                  label="Mass reconciliation (OT-first lateness cover)"
                  description="mass_reconciliation + latness_deduction — covers lateness via OT bucket then annual leave."
                  on={enableMassReconciliation}
                  setOn={setEnableMassReconciliation}
                />
              </div>
            </div>

            <AdvisorPanel
              lines={[
                'The Cycom modules are battle-tested in Cycom payroll operations. Leave them on unless you have a hard reason to opt out.',
                'Disable only if you already have a third-party OT/lateness engine and want to avoid two systems calculating the same numbers.',
              ]}
            />
          </>
        )}

        {step === 2 && (
          <>
            <div className="glass-card p-6 space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#E67E22]" /> Review
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <ReviewRow label="Pay frequency" value={FREQUENCY_LABEL[frequency]} />
                <ReviewRow label="Weekly hours" value={`${weeklyHours} h`} />
                <ReviewRow label="OT multiplier" value={`×${otMultiplier}`} />
                <ReviewRow label="Lateness grace" value={`${latenessGraceMinutes} min`} />
                <ReviewRow label="Cycom OT engine" value={enableCycomOvertime ? 'Enabled' : 'Off'} />
                <ReviewRow label="Mass reconciliation" value={enableMassReconciliation ? 'Enabled' : 'Off'} />
              </div>
            </div>
            {result && <ResultBanner result={result} />}
          </>
        )}
      </motion.div>

      <WizardFooter
        step={step} totalSteps={STEPS.length} canAdvance={canAdvance}
        applying={applying} applied={Boolean(result?.ok)}
        onBack={() => setStep((s) => (Math.max(0, s - 1) as StepIdx))}
        onNext={() => setStep((s) => (Math.min(STEPS.length - 1, s + 1) as StepIdx))}
        onApply={submit}
        applyLabel="Configure payroll"
      />
    </div>
  );
}

function ToggleRow({ label, description, on, setOn }: { label: string; description: string; on: boolean; setOn: (v: boolean) => void }) {
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
