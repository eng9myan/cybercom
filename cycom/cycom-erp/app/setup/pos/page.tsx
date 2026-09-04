'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ShoppingCart, Layers, Wrench, Banknote } from 'lucide-react';
import { fetchTenantPrefs } from '@/lib/setup/coaSetup';
import { PAYMENT_MIX_LABEL, getPosDefaults, type PaymentMix } from '@/lib/setup/pos-templates';
import { applyPosSetup, type PosSetupResult } from '@/lib/setup/posSetup';
import { StepIndicator } from '@/components/setup/StepIndicator';
import { WizardFooter } from '@/components/setup/WizardFooter';
import { AdvisorPanel } from '@/components/setup/AdvisorPanel';
import { ReviewRow } from '@/components/setup/ReviewRow';
import { ResultBanner } from '@/components/setup/ResultBanner';
import { ToggleRow } from '@/components/setup/ToggleRow';
import { useT } from '@/lib/i18n';

type StepIdx = 0 | 1 | 2;

export default function PosWizard() {
  const t = useT();
  const STEPS = [t('setupPos.paymentMixHeading'), t('setupWizard.stepModules'), t('setupWizard.stepReview')] as const;
  const [step, setStep] = useState<StepIdx>(0);
  const [industry, setIndustry] = useState<string | undefined>();

  const [paymentMix, setPaymentMix] = useState<PaymentMix>('split');
  const [dailyCashCloseout, setDailyCashCloseout] = useState(true);
  const [enableAdvanceOrder, setEnableAdvanceOrder] = useState(false);
  const [enablePledge, setEnablePledge] = useState(false);
  const [enableRefundBuyer, setEnableRefundBuyer] = useState(false);
  const [enableCashMoveAccess, setEnableCashMoveAccess] = useState(false);
  const [enablePredefinedDiscounts, setEnablePredefinedDiscounts] = useState(false);
  const [enablePosRounding, setEnablePosRounding] = useState(false);

  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<PosSetupResult | null>(null);

  useEffect(() => {
    fetchTenantPrefs().then((prefs) => {
      setIndustry(prefs.industry);
      const d = getPosDefaults(prefs.industry);
      setPaymentMix(d.paymentMix);
      setDailyCashCloseout(d.dailyCashCloseout);
      setEnableAdvanceOrder(d.enableAdvanceOrder);
      setEnablePledge(d.enablePledge);
      setEnableRefundBuyer(d.enableRefundBuyer);
      setEnableCashMoveAccess(d.enableCashMoveAccess);
      setEnablePredefinedDiscounts(d.enablePredefinedDiscounts);
      setEnablePosRounding(d.enablePosRounding);
    });
  }, []);

  const submit = async () => {
    setApplying(true);
    setResult(await applyPosSetup({
      paymentMix, dailyCashCloseout,
      enableAdvanceOrder, enablePledge, enableRefundBuyer, enableCashMoveAccess,
      enablePredefinedDiscounts, enablePosRounding,
    }));
    setApplying(false);
  };

  const onOff = (v: boolean) => v ? t('setupWizard.on') : t('setupWizard.off');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <ShoppingCart className="w-7 h-7 text-[#E67E22]" /> {t('setupPos.title')}
          </h1>
          <p className="page-subtitle">{t('setupPos.subtitle')}</p>
        </div>
        <a href="/cycom/cycom/action-point_of_sale.action_pos_config_kanban" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> {t('setupWizard.configureManually')}
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Banknote className="w-4 h-4 text-emerald-400" /> {t('setupPos.paymentMixHeading')}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(['cash_heavy', 'split', 'card_heavy'] as PaymentMix[]).map((m) => (
                  <button key={m} type="button" onClick={() => setPaymentMix(m)} className={'text-start p-4 rounded-xl border transition-all ' + (m === paymentMix ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')}>
                    <div className="text-sm font-bold">{PAYMENT_MIX_LABEL[m]}</div>
                  </button>
                ))}
              </div>
              <div className="pt-1">
                <ToggleRow label={t('setupPos.closeoutLabel')}
                  description={t('setupPos.closeoutDesc')}
                  on={dailyCashCloseout} setOn={setDailyCashCloseout} />
              </div>
            </div>
            <AdvisorPanel lines={[
              industry ? t('setupPos.mixAdvisor', { industry }) : t('setupWizard.runCompanyFirst'),
              t('setupPos.mixAdvisorNote'),
            ]} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupPos.extensionsHeading')}</h2>
              <ToggleRow label={t('setupPos.advanceLabel')}
                description={t('setupPos.advanceDesc')} on={enableAdvanceOrder} setOn={setEnableAdvanceOrder} />
              <ToggleRow label={t('setupPos.pledgeLabel')}
                description={t('setupPos.pledgeDesc')} on={enablePledge} setOn={setEnablePledge} />
              <ToggleRow label={t('setupPos.refundLabel')}
                description={t('setupPos.refundDesc')} on={enableRefundBuyer} setOn={setEnableRefundBuyer} />
              <ToggleRow label={t('setupPos.cashMoveLabel')}
                description={t('setupPos.cashMoveDesc')} on={enableCashMoveAccess} setOn={setEnableCashMoveAccess} />
              <ToggleRow label={t('setupPos.discountsLabel')}
                description={t('setupPos.discountsDesc')} on={enablePredefinedDiscounts} setOn={setEnablePredefinedDiscounts} />
              <ToggleRow label={t('setupPos.roundingLabel')}
                description={t('setupPos.roundingDesc')} on={enablePosRounding} setOn={setEnablePosRounding} />
            </div>
            <AdvisorPanel lines={[
              t('setupPos.extensionsAdvisor'),
              t('setupPos.extensionsAdvisorNote'),
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
                <ReviewRow label={t('setupPos.reviewMix')} value={PAYMENT_MIX_LABEL[paymentMix]} />
                <ReviewRow label={t('setupPos.reviewCloseout')} value={onOff(dailyCashCloseout)} />
                <ReviewRow label={t('setupPos.reviewAdvance')} value={onOff(enableAdvanceOrder)} />
                <ReviewRow label={t('setupPos.reviewPledge')} value={onOff(enablePledge)} />
                <ReviewRow label={t('setupPos.reviewRefund')} value={onOff(enableRefundBuyer)} />
                <ReviewRow label={t('setupPos.reviewCashMove')} value={onOff(enableCashMoveAccess)} />
                <ReviewRow label={t('setupPos.reviewDiscounts')} value={onOff(enablePredefinedDiscounts)} />
                <ReviewRow label={t('setupPos.reviewRounding')} value={onOff(enablePosRounding)} />
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
        onApply={submit} applyLabel={t('setupPos.applyLabel')} />
    </div>
  );
}
