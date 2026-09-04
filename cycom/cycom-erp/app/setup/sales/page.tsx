'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Layers, Wrench, Shield } from 'lucide-react';
import { fetchTenantPrefs } from '@/lib/setup/coaSetup';
import { MOTION_LABEL, getSalesDefaults, type SalesMotion } from '@/lib/setup/sales-templates';
import { applySalesSetup, type SalesSetupResult } from '@/lib/setup/salesSetup';
import { StepIndicator } from '@/components/setup/StepIndicator';
import { WizardFooter } from '@/components/setup/WizardFooter';
import { AdvisorPanel } from '@/components/setup/AdvisorPanel';
import { ReviewRow } from '@/components/setup/ReviewRow';
import { ResultBanner } from '@/components/setup/ResultBanner';
import { ToggleRow } from '@/components/setup/ToggleRow';
import { useT } from '@/lib/i18n';

type StepIdx = 0 | 1 | 2;

export default function SalesWizard() {
  const t = useT();
  const STEPS = [t('setupSales.motionHeading'), t('setupWizard.stepModules'), t('setupWizard.stepReview')] as const;
  const [step, setStep] = useState<StepIdx>(0);
  const [industry, setIndustry] = useState<string | undefined>();

  const [salesMotion, setSalesMotion] = useState<SalesMotion>('mixed');
  const [freeDiscountLimitPct, setFreeDiscountLimitPct] = useState(5);
  const [managerDiscountLimitPct, setManagerDiscountLimitPct] = useState(10);
  const [dualApprovalThresholdPct, setDualApprovalThresholdPct] = useState(20);
  const [enableDiscountExceptionApproval, setEnableDiscountExceptionApproval] = useState(true);
  const [enableLineLevelApproval, setEnableLineLevelApproval] = useState(false);
  const [enablePricingControl, setEnablePricingControl] = useState(false);
  const [enableSaleFiscalKeepPrice, setEnableSaleFiscalKeepPrice] = useState(false);

  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<SalesSetupResult | null>(null);

  useEffect(() => {
    fetchTenantPrefs().then((prefs) => {
      setIndustry(prefs.industry);
      const d = getSalesDefaults(prefs.industry);
      setSalesMotion(d.motion);
      setFreeDiscountLimitPct(d.freeDiscountLimitPct);
      setManagerDiscountLimitPct(d.managerDiscountLimitPct);
      setDualApprovalThresholdPct(d.dualApprovalThresholdPct);
      setEnableDiscountExceptionApproval(d.enableDiscountExceptionApproval);
      setEnableLineLevelApproval(d.enableLineLevelApproval);
      setEnablePricingControl(d.enablePricingControl);
      setEnableSaleFiscalKeepPrice(d.enableSaleFiscalKeepPrice);
    });
  }, []);

  const submit = async () => {
    setApplying(true);
    setResult(await applySalesSetup({
      motion: salesMotion, freeDiscountLimitPct, managerDiscountLimitPct, dualApprovalThresholdPct,
      enableDiscountExceptionApproval, enableLineLevelApproval, enablePricingControl, enableSaleFiscalKeepPrice,
    }));
    setApplying(false);
  };

  const onOff = (v: boolean) => v ? t('setupWizard.on') : t('setupWizard.off');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <TrendingUp className="w-7 h-7 text-[#E67E22]" /> {t('setupSales.title')}
          </h1>
          <p className="page-subtitle">{t('setupSales.subtitle')}</p>
        </div>
        <a href="/cycom/cycom/action-sale.action_orders" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> {t('setupWizard.configureManually')}
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupSales.motionHeading')}</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(['b2c', 'b2b', 'mixed'] as SalesMotion[]).map((m) => (
                  <button key={m} type="button" onClick={() => setSalesMotion(m)} className={'text-start p-4 rounded-xl border transition-all ' + (m === salesMotion ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')}>
                    <div className="text-sm font-bold">{MOTION_LABEL[m]}</div>
                  </button>
                ))}
              </div>
            </div>
            <AdvisorPanel lines={[
              industry ? t('setupSales.motionAdvisor', { industry, motion: MOTION_LABEL[getSalesDefaults(industry).motion] }) : t('setupWizard.runCompanyFirst'),
              t('setupSales.motionAdvisorNote'),
            ]} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Shield className="w-4 h-4 text-rose-400" /> {t('setupSales.ceilingsHeading')}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Pct label={t('setupSales.freeLimitLabel')} desc={t('setupSales.freeLimitDesc')} value={freeDiscountLimitPct} setValue={setFreeDiscountLimitPct} />
                <Pct label={t('setupSales.managerLimitLabel')} desc={t('setupSales.managerLimitDesc')} value={managerDiscountLimitPct} setValue={setManagerDiscountLimitPct} />
                <Pct label={t('setupSales.dualThresholdLabel')} desc={t('setupSales.dualThresholdDesc')} value={dualApprovalThresholdPct} setValue={setDualApprovalThresholdPct} />
              </div>

              <div className="space-y-3 pt-1">
                <ToggleRow label={t('setupSales.exceptionApprovalLabel')}
                  description={t('setupSales.exceptionApprovalDesc')} on={enableDiscountExceptionApproval} setOn={setEnableDiscountExceptionApproval} />
                <ToggleRow label={t('setupSales.lineApprovalLabel')}
                  description={t('setupSales.lineApprovalDesc')} on={enableLineLevelApproval} setOn={setEnableLineLevelApproval} />
                <ToggleRow label={t('setupSales.pricingControlLabel')}
                  description={t('setupSales.pricingControlDesc')} on={enablePricingControl} setOn={setEnablePricingControl} />
                <ToggleRow label={t('setupSales.fiscalKeepLabel')}
                  description={t('setupSales.fiscalKeepDesc')} on={enableSaleFiscalKeepPrice} setOn={setEnableSaleFiscalKeepPrice} />
              </div>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <div className="glass-card p-6 space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#E67E22]" /> {t('setupWizard.stepReview')}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <ReviewRow label={t('setupSales.reviewMotion')} value={MOTION_LABEL[salesMotion]} />
                <ReviewRow label={t('setupSales.reviewFreeUpTo')} value={`${freeDiscountLimitPct}%`} />
                <ReviewRow label={t('setupSales.reviewManagerUpTo')} value={`${managerDiscountLimitPct}%`} />
                <ReviewRow label={t('setupSales.reviewDualOver')} value={`${dualApprovalThresholdPct}%`} />
                <ReviewRow label={t('setupSales.reviewExceptionApproval')} value={onOff(enableDiscountExceptionApproval)} />
                <ReviewRow label={t('setupSales.reviewLineApproval')} value={onOff(enableLineLevelApproval)} />
                <ReviewRow label={t('setupSales.reviewPricingControl')} value={onOff(enablePricingControl)} />
                <ReviewRow label={t('setupSales.reviewFiscalKeep')} value={onOff(enableSaleFiscalKeepPrice)} />
              </div>
            </div>
            {result && <ResultBanner result={result} />}
          </>
        )}
      </motion.div>

      <WizardFooter step={step} totalSteps={STEPS.length} canAdvance={true}
        applying={applying} applied={Boolean(result?.ok)}
        onBack={() => setStep((s) => (Math.max(0, s - 1) as StepIdx))}
        onNext={() => setStep((s) => (Math.min(STEPS.length - 1, s + 1) as StepIdx))}
        onApply={submit} applyLabel={t('setupSales.applyLabel')} />
    </div>
  );
}

function Pct({ label, desc, value, setValue }: { label: string; desc: string; value: number; setValue: (n: number) => void }) {
  return (
    <div>
      <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">{label}</label>
      <input type="number" min={0} max={100} step="0.5" className="input-field py-2.5" value={value} onChange={(e) => setValue(parseFloat(e.target.value) || 0)} />
      <p className="text-[10px] text-slate-500 mt-1">{desc}</p>
    </div>
  );
}
