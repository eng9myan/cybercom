'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Package, Settings2, Layers, Wrench } from 'lucide-react';
import { fetchTenantPrefs } from '@/lib/setup/coaSetup';
import { COSTING_LABEL, getWarehouseDefaults, type CostingMethod } from '@/lib/setup/warehouse-templates';
import { applyWarehouseSetup, type WarehouseSetupResult } from '@/lib/setup/warehouseSetup';
import { StepIndicator } from '@/components/setup/StepIndicator';
import { WizardFooter } from '@/components/setup/WizardFooter';
import { AdvisorPanel } from '@/components/setup/AdvisorPanel';
import { ReviewRow } from '@/components/setup/ReviewRow';
import { ResultBanner } from '@/components/setup/ResultBanner';
import { useT } from '@/lib/i18n';

type StepIdx = 0 | 1 | 2;

export default function WarehouseWizard() {
  const t = useT();
  const STEPS = [t('setupWarehouse.costingHeading'), t('setupWarehouse.policyHeading'), t('setupWizard.stepReview')] as const;
  const [step, setStep] = useState<StepIdx>(0);
  const [industry, setIndustry] = useState<string | undefined>();

  const [costingMethod, setCostingMethod] = useState<CostingMethod>('fifo');
  const [negativeStockGuard, setNegativeStockGuard] = useState(true);
  const [lowStockThreshold, setLowStockThreshold] = useState(10);
  const [enableWarehouseRestriction, setEnableWarehouseRestriction] = useState(false);
  const [enableDiscrepancyWorkflow, setEnableDiscrepancyWorkflow] = useState(true);

  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<WarehouseSetupResult | null>(null);

  useEffect(() => {
    fetchTenantPrefs().then((prefs) => {
      setIndustry(prefs.industry);
      const d = getWarehouseDefaults(prefs.industry);
      setCostingMethod(d.costingMethod);
      setNegativeStockGuard(d.negativeStockGuard);
      setLowStockThreshold(d.lowStockThreshold);
      setEnableWarehouseRestriction(d.enableWarehouseRestriction);
      setEnableDiscrepancyWorkflow(d.enableDiscrepancyWorkflow);
    });
  }, []);

  const submit = async () => {
    setApplying(true);
    setResult(await applyWarehouseSetup({
      costingMethod, negativeStockGuard, lowStockThreshold,
      enableWarehouseRestriction, enableDiscrepancyWorkflow,
    }));
    setApplying(false);
  };

  const onOff = (v: boolean) => v ? t('setupWizard.on') : t('setupWizard.off');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <Package className="w-7 h-7 text-[#E67E22]" /> {t('setupWarehouse.title')}
          </h1>
          <p className="page-subtitle">{t('setupWarehouse.subtitle')}</p>
        </div>
        <a href="/cycom/cycom/action-stock.action_warehouse_form" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> {t('setupWizard.configureManually')}
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Settings2 className="w-4 h-4 text-cyan-400" /> {t('setupWarehouse.costingHeading')}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(['standard', 'fifo', 'average'] as CostingMethod[]).map((m) => (
                  <button key={m} type="button" onClick={() => setCostingMethod(m)} className={'text-start p-4 rounded-xl border transition-all ' + (m === costingMethod ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')}>
                    <div className="text-sm font-bold">{COSTING_LABEL[m]}</div>
                  </button>
                ))}
              </div>
            </div>
            <AdvisorPanel lines={[
              industry ? t('setupWarehouse.costingAdvisor', { industry }) : t('setupWizard.runCompanyFirst'),
              t('setupWarehouse.costingAdvisorNote'),
            ]} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupWarehouse.policyHeading')}</h2>

              <div className="space-y-3">
                <ToggleRow label={t('setupWarehouse.negativeGuardLabel')}
                  description={t('setupWarehouse.negativeGuardDesc')}
                  on={negativeStockGuard} setOn={setNegativeStockGuard} />
                <ToggleRow label={t('setupWarehouse.warehouseRestrictionLabel')}
                  description={t('setupWarehouse.warehouseRestrictionDesc')}
                  on={enableWarehouseRestriction} setOn={setEnableWarehouseRestriction} />
                <ToggleRow label={t('setupWarehouse.discrepancyLabel')}
                  description={t('setupWarehouse.discrepancyDesc')}
                  on={enableDiscrepancyWorkflow} setOn={setEnableDiscrepancyWorkflow} />
              </div>

              <div className="pt-2">
                <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">{t('setupWarehouse.lowStockLabel')}</label>
                <input type="number" min={0} className="input-field py-2.5 max-w-[200px]"
                  value={lowStockThreshold} onChange={(e) => setLowStockThreshold(parseFloat(e.target.value) || 0)} />
                <p className="text-[10px] text-slate-500 mt-1">{t('setupWarehouse.lowStockNote')}</p>
              </div>
            </div>
            <AdvisorPanel lines={[
              t('setupWarehouse.policyAdvisor'),
              t('setupWarehouse.policyAdvisorNote'),
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
                <ReviewRow label={t('setupWarehouse.reviewCosting')} value={COSTING_LABEL[costingMethod]} />
                <ReviewRow label={t('setupWarehouse.reviewNegGuard')} value={onOff(negativeStockGuard)} />
                <ReviewRow label={t('setupWarehouse.reviewWhRestriction')} value={onOff(enableWarehouseRestriction)} />
                <ReviewRow label={t('setupWarehouse.reviewDiscrepancy')} value={onOff(enableDiscrepancyWorkflow)} />
                <ReviewRow label={t('setupWarehouse.reviewLowStock')} value={t('setupWarehouse.unitsN', { n: lowStockThreshold })} />
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
        onApply={submit} applyLabel={t('setupWarehouse.applyLabel')} />
    </div>
  );
}

function ToggleRow({ label, description, on, setOn }: { label: string; description: string; on: boolean; setOn: (v: boolean) => void }) {
  return (
    <button type="button" onClick={() => setOn(!on)} className={'w-full text-start flex items-center gap-3 p-3 rounded-xl border transition-all ' + (on ? 'bg-gradient-to-br from-emerald-500/10 to-cyan-500/5 border-emerald-500/30' : 'bg-white/5 border-white/10 hover:bg-white/10')}>
      <div className={'w-9 h-5 rounded-full relative transition-colors ' + (on ? 'bg-emerald-500/60' : 'bg-white/10')}>
        <div className={'absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ' + (on ? 'start-4' : 'start-0.5')} />
      </div>
      <div className="flex-1">
        <div className="text-sm font-bold text-white">{label}</div>
        <div className="text-[11px] text-slate-400">{description}</div>
      </div>
    </button>
  );
}
