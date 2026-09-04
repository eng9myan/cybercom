'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ShoppingBag, Layers, Wrench, Shield } from 'lucide-react';
import { fetchTenantPrefs } from '@/lib/setup/coaSetup';
import { APPROVAL_POLICY_LABEL, getProcurementDefaults, type ApprovalPolicy } from '@/lib/setup/procurement-templates';
import { applyProcurementSetup, type ProcurementSetupResult } from '@/lib/setup/procurementSetup';
import { StepIndicator } from '@/components/setup/StepIndicator';
import { WizardFooter } from '@/components/setup/WizardFooter';
import { AdvisorPanel } from '@/components/setup/AdvisorPanel';
import { ReviewRow } from '@/components/setup/ReviewRow';
import { ResultBanner } from '@/components/setup/ResultBanner';
import { ToggleRow } from '@/components/setup/ToggleRow';
import { useT } from '@/lib/i18n';

type StepIdx = 0 | 1 | 2;

export default function ProcurementWizard() {
  const t = useT();
  const STEPS = [t('setupProcurement.approvalHeading'), t('setupProcurement.rfqHeading'), t('setupWizard.stepReview')] as const;
  const [step, setStep] = useState<StepIdx>(0);
  const [industry, setIndustry] = useState<string | undefined>();

  const [approvalPolicy, setApprovalPolicy] = useState<ApprovalPolicy>('single');
  const [approvalThresholdAmount, setApprovalThresholdAmount] = useState(1000);
  const [rfqValidityDays, setRfqValidityDays] = useState(14);
  const [defaultLeadTimeDays, setDefaultLeadTimeDays] = useState(7);
  const [enableAltanmyaExtension, setEnableAltanmyaExtension] = useState(false);
  const [enableApprovalContact, setEnableApprovalContact] = useState(true);

  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<ProcurementSetupResult | null>(null);

  useEffect(() => {
    fetchTenantPrefs().then((prefs) => {
      setIndustry(prefs.industry);
      const d = getProcurementDefaults(prefs.industry);
      setApprovalPolicy(d.approvalPolicy);
      setApprovalThresholdAmount(d.approvalThresholdAmount);
      setRfqValidityDays(d.rfqValidityDays);
      setDefaultLeadTimeDays(d.defaultLeadTimeDays);
      setEnableAltanmyaExtension(d.enableAltanmyaExtension);
      setEnableApprovalContact(d.enableApprovalContact);
    });
  }, []);

  const submit = async () => {
    setApplying(true);
    setResult(await applyProcurementSetup({
      approvalPolicy, approvalThresholdAmount, rfqValidityDays, defaultLeadTimeDays,
      enableAltanmyaExtension, enableApprovalContact,
    }));
    setApplying(false);
  };

  const onOff = (v: boolean) => v ? t('setupWizard.on') : t('setupWizard.off');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <ShoppingBag className="w-7 h-7 text-[#E67E22]" /> {t('setupProcurement.title')}
          </h1>
          <p className="page-subtitle">{t('setupProcurement.subtitle')}</p>
        </div>
        <a href="/cycom/cycom/action-purchase.purchase_rfq" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> {t('setupWizard.configureManually')}
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Shield className="w-4 h-4 text-rose-400" /> {t('setupProcurement.approvalHeading')}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(['auto', 'single', 'dual'] as ApprovalPolicy[]).map((m) => (
                  <button key={m} type="button" onClick={() => setApprovalPolicy(m)} className={'text-start p-4 rounded-xl border transition-all ' + (m === approvalPolicy ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')}>
                    <div className="text-sm font-bold">{APPROVAL_POLICY_LABEL[m]}</div>
                  </button>
                ))}
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">{t('setupProcurement.thresholdLabel')}</label>
                <input type="number" min={0} className="input-field py-2.5 max-w-[240px]" value={approvalThresholdAmount} onChange={(e) => setApprovalThresholdAmount(parseFloat(e.target.value) || 0)} />
                <p className="text-[10px] text-slate-500 mt-1">{t('setupProcurement.thresholdNote')}</p>
              </div>
              <div className="space-y-3 pt-1">
                <ToggleRow label={t('setupProcurement.altanmyaLabel')} description={t('setupProcurement.altanmyaDesc')} on={enableAltanmyaExtension} setOn={setEnableAltanmyaExtension} />
                <ToggleRow label={t('setupProcurement.approvalContactLabel')} description={t('setupProcurement.approvalContactDesc')} on={enableApprovalContact} setOn={setEnableApprovalContact} />
              </div>
            </div>
            <AdvisorPanel lines={[
              industry ? t('setupProcurement.approvalAdvisor', { policy: APPROVAL_POLICY_LABEL[getProcurementDefaults(industry).approvalPolicy], industry }) : t('setupWizard.runCompanyFirst'),
              t('setupProcurement.approvalAdvisorNote'),
            ]} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupProcurement.rfqHeading')}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">{t('setupProcurement.rfqValidityLabel')}</label>
                  <input type="number" min={1} max={120} className="input-field py-2.5" value={rfqValidityDays} onChange={(e) => setRfqValidityDays(parseInt(e.target.value, 10) || 0)} />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">{t('setupProcurement.leadTimeLabel')}</label>
                  <input type="number" min={0} max={365} className="input-field py-2.5" value={defaultLeadTimeDays} onChange={(e) => setDefaultLeadTimeDays(parseInt(e.target.value, 10) || 0)} />
                </div>
              </div>
            </div>
            <AdvisorPanel lines={[
              t('setupProcurement.rfqAdvisor'),
              t('setupProcurement.rfqAdvisorNote'),
            ]} />
          </>
        )}

        {step === 2 && (
          <>
            <div className="glass-card p-6 space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#E67E22]" /> {t('setupWizard.stepReview')}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <ReviewRow label={t('setupProcurement.reviewPolicy')} value={APPROVAL_POLICY_LABEL[approvalPolicy]} />
                <ReviewRow label={t('setupProcurement.reviewThreshold')} value={String(approvalThresholdAmount)} />
                <ReviewRow label={t('setupProcurement.reviewValidity')} value={t('setupProcurement.daysN', { n: rfqValidityDays })} />
                <ReviewRow label={t('setupProcurement.reviewLeadTime')} value={t('setupProcurement.daysN', { n: defaultLeadTimeDays })} />
                <ReviewRow label={t('setupProcurement.reviewAltanmya')} value={onOff(enableAltanmyaExtension)} />
                <ReviewRow label={t('setupProcurement.reviewApprovalContact')} value={onOff(enableApprovalContact)} />
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
        onApply={submit} applyLabel={t('setupProcurement.applyLabel')} />
    </div>
  );
}
