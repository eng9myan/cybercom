'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Factory, Layers, Wrench } from 'lucide-react';
import { fetchTenantPrefs } from '@/lib/setup/coaSetup';
import { MFG_TYPE_LABEL, getManufacturingDefaults, type ManufacturingType } from '@/lib/setup/manufacturing-templates';
import { applyManufacturingSetup, type ManufacturingSetupResult } from '@/lib/setup/manufacturingSetup';
import { StepIndicator } from '@/components/setup/StepIndicator';
import { WizardFooter } from '@/components/setup/WizardFooter';
import { AdvisorPanel } from '@/components/setup/AdvisorPanel';
import { ReviewRow } from '@/components/setup/ReviewRow';
import { ResultBanner } from '@/components/setup/ResultBanner';
import { ToggleRow } from '@/components/setup/ToggleRow';
import { useT } from '@/lib/i18n';

type StepIdx = 0 | 1 | 2;

export default function ManufacturingWizard() {
  const t = useT();
  const STEPS = [t('setupWizard.stepType'), t('setupWizard.stepModules'), t('setupWizard.stepReview')] as const;
  const [step, setStep] = useState<StepIdx>(0);
  const [industry, setIndustry] = useState<string | undefined>();

  const [mfgType, setMfgType] = useState<ManufacturingType>('none');
  const [enableMrp, setEnableMrp] = useState(false);
  const [enableWorkorders, setEnableWorkorders] = useState(false);
  const [enableMaintenance, setEnableMaintenance] = useState(false);
  const [enableQuality, setEnableQuality] = useState(false);
  const [enablePlm, setEnablePlm] = useState(false);

  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<ManufacturingSetupResult | null>(null);

  useEffect(() => {
    fetchTenantPrefs().then((prefs) => {
      setIndustry(prefs.industry);
      const d = getManufacturingDefaults(prefs.industry);
      setMfgType(d.mfgType);
      setEnableMrp(d.enableMrp);
      setEnableWorkorders(d.enableWorkorders);
      setEnableMaintenance(d.enableMaintenance);
      setEnableQuality(d.enableQuality);
      setEnablePlm(d.enablePlm);
    });
  }, []);

  const submit = async () => {
    setApplying(true);
    setResult(await applyManufacturingSetup({
      mfgType, enableMrp, enableWorkorders, enableMaintenance, enableQuality, enablePlm,
    }));
    setApplying(false);
  };

  const onOff = (v: boolean) => v ? t('setupWizard.on') : t('setupWizard.off');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <Factory className="w-7 h-7 text-[#E67E22]" /> {t('setupMfg.title')}
          </h1>
          <p className="page-subtitle">{t('setupMfg.subtitle')}</p>
        </div>
        <a href="/cycom/cycom/action-mrp.mrp_production_action" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> {t('setupWizard.configureManually')}
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupMfg.typeHeading')}</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(['none', 'discrete', 'process', 'food', 'pharma'] as ManufacturingType[]).map((m) => (
                  <button key={m} type="button" onClick={() => setMfgType(m)} className={'text-start p-4 rounded-xl border transition-all ' + (m === mfgType ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')}>
                    <div className="text-sm font-bold">{MFG_TYPE_LABEL[m]}</div>
                  </button>
                ))}
              </div>
            </div>
            <AdvisorPanel lines={[
              industry ? t('setupMfg.typeAdvisor', { industry, type: MFG_TYPE_LABEL[getManufacturingDefaults(industry).mfgType] }) : t('setupWizard.runCompanyFirst'),
              t('setupMfg.typeAdvisorNote'),
            ]} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupMfg.modulesHeading')}</h2>
              <ToggleRow label={t('setupMfg.mrpLabel')} description={t('setupMfg.mrpDesc')} on={enableMrp} setOn={setEnableMrp} />
              <ToggleRow label={t('setupMfg.workordersLabel')} description={t('setupMfg.workordersDesc')} on={enableWorkorders} setOn={setEnableWorkorders} />
              <ToggleRow label={t('setupMfg.maintenanceLabel')} description={t('setupMfg.maintenanceDesc')} on={enableMaintenance} setOn={setEnableMaintenance} />
              <ToggleRow label={t('setupMfg.qualityLabel')} description={t('setupMfg.qualityDesc')} on={enableQuality} setOn={setEnableQuality} />
              <ToggleRow label={t('setupMfg.plmLabel')} description={t('setupMfg.plmDesc')} on={enablePlm} setOn={setEnablePlm} />
            </div>
            <AdvisorPanel lines={[
              t('setupMfg.modulesAdvisor'),
              t('setupMfg.modulesAdvisorNote'),
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
                <ReviewRow label={t('setupMfg.reviewType')} value={MFG_TYPE_LABEL[mfgType]} />
                <ReviewRow label={t('setupMfg.reviewMrp')} value={onOff(enableMrp)} />
                <ReviewRow label={t('setupMfg.reviewWorkorders')} value={onOff(enableWorkorders)} />
                <ReviewRow label={t('setupMfg.reviewMaintenance')} value={onOff(enableMaintenance)} />
                <ReviewRow label={t('setupMfg.reviewQuality')} value={onOff(enableQuality)} />
                <ReviewRow label={t('setupMfg.reviewPlm')} value={onOff(enablePlm)} />
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
        onApply={submit} applyLabel={t('setupMfg.applyLabel')} />
    </div>
  );
}
