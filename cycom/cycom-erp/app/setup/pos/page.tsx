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

const STEPS = ['Operating model', 'Features', 'Review'] as const;
type StepIdx = 0 | 1 | 2;

export default function PosWizard() {
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

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <ShoppingCart className="w-7 h-7 text-[#E67E22]" /> POS Configuration
          </h1>
          <p className="page-subtitle">Sessions, pricelists, and Cycom POS features. One terminal per company is created automatically.</p>
        </div>
        <a href="/cycom/cycom/action-point_of_sale.action_pos_config_kanban" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> Configure manually
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Banknote className="w-4 h-4 text-emerald-400" /> Payment mix
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(['cash_heavy', 'split', 'card_heavy'] as PaymentMix[]).map((m) => (
                  <button key={m} type="button" onClick={() => setPaymentMix(m)} className={'text-left p-4 rounded-xl border transition-all ' + (m === paymentMix ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')}>
                    <div className="text-sm font-bold">{PAYMENT_MIX_LABEL[m]}</div>
                  </button>
                ))}
              </div>
              <div className="pt-1">
                <ToggleRow label="Daily cash closeout"
                  description="pos_opening_cash_zero — force cash drawer to zero at start of each session."
                  on={dailyCashCloseout} setOn={setDailyCashCloseout} />
              </div>
            </div>
            <AdvisorPanel lines={[
              industry ? `Cycom pre-filled the typical POS mix for "${industry}".` : 'Run Company Setup first.',
              'Cash-heavy operations should keep daily closeout on; card-heavy can skip it.',
            ]} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Cycom POS extensions</h2>
              <ToggleRow label="Advance orders (two-cashier flow)"
                description="pos_advance_order — order today, pay/collect later." on={enableAdvanceOrder} setOn={setEnableAdvanceOrder} />
              <ToggleRow label="Pledge / Rahn management"
                description="pos_pledge + pos_pledge_order — collateralized lending workflow with dual receipts." on={enablePledge} setOn={setEnablePledge} />
              <ToggleRow label="Buyer-aware refunds"
                description="cycom_jo_pos_refund_buyer — refund to the original payment method/customer." on={enableRefundBuyer} setOn={setEnableRefundBuyer} />
              <ToggleRow label="Restricted cash-in/cash-out"
                description="cycom_pos_cash_move_access — only nominated cashiers can move cash." on={enableCashMoveAccess} setOn={setEnableCashMoveAccess} />
              <ToggleRow label="Predefined discount buttons"
                description="pos_predefined_discounts — fixed discount tiles in the POS UI." on={enablePredefinedDiscounts} setOn={setEnablePredefinedDiscounts} />
              <ToggleRow label="Price rounding"
                description="pos_rounding — round final total to the nearest cash denomination." on={enablePosRounding} setOn={setEnablePosRounding} />
            </div>
            <AdvisorPanel lines={[
              'Retail tenants typically enable advance orders, pledge, and rounding.',
              'Hospitality enables rounding, refunds, and cash-move restrictions; usually no advance/pledge.',
            ]} />
          </>
        )}

        {step === 2 && (
          <>
            <div className="glass-card p-6 space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#E67E22]" /> Review
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <ReviewRow label="Payment mix" value={PAYMENT_MIX_LABEL[paymentMix]} />
                <ReviewRow label="Daily cash closeout" value={dailyCashCloseout ? 'On' : 'Off'} />
                <ReviewRow label="Advance orders" value={enableAdvanceOrder ? 'On' : 'Off'} />
                <ReviewRow label="Pledge management" value={enablePledge ? 'On' : 'Off'} />
                <ReviewRow label="Buyer-aware refunds" value={enableRefundBuyer ? 'On' : 'Off'} />
                <ReviewRow label="Cash-move access control" value={enableCashMoveAccess ? 'On' : 'Off'} />
                <ReviewRow label="Predefined discounts" value={enablePredefinedDiscounts ? 'On' : 'Off'} />
                <ReviewRow label="Price rounding" value={enablePosRounding ? 'On' : 'Off'} />
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
        onApply={submit} applyLabel="Configure POS" />
    </div>
  );
}
