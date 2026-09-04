'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Users, Layers, Wrench, Plus, Trash2 } from 'lucide-react';
import { fetchTenantPrefs } from '@/lib/setup/coaSetup';
import { ORG_SIZE_LABEL, getHrDefaults, type OrgSize } from '@/lib/setup/hr-templates';
import { applyHrSetup, type HrSetupResult } from '@/lib/setup/hrSetup';
import { StepIndicator } from '@/components/setup/StepIndicator';
import { WizardFooter } from '@/components/setup/WizardFooter';
import { AdvisorPanel } from '@/components/setup/AdvisorPanel';
import { ReviewRow } from '@/components/setup/ReviewRow';
import { ResultBanner } from '@/components/setup/ResultBanner';
import { ToggleRow } from '@/components/setup/ToggleRow';
import { useT } from '@/lib/i18n';

type StepIdx = 0 | 1 | 2;

export default function HrWizard() {
  const t = useT();
  const STEPS = [t('setupHr.orgSizeHeading'), t('setupHr.featuresHeading'), t('setupWizard.stepReview')] as const;
  const [step, setStep] = useState<StepIdx>(0);
  const [industry, setIndustry] = useState<string | undefined>();

  const [orgSize, setOrgSize] = useState<OrgSize>('medium');
  const [departments, setDepartments] = useState<string[]>(['General']);
  const [enableBiometricZk, setEnableBiometricZk] = useState(false);
  const [enableSingleDeviceBinding, setEnableSingleDeviceBinding] = useState(false);
  const [enableGeofence, setEnableGeofence] = useState(false);
  const [enableHealthInsurance, setEnableHealthInsurance] = useState(false);
  const [enableEmployeeCode, setEnableEmployeeCode] = useState(false);
  const [enableEmployeeSpouse, setEnableEmployeeSpouse] = useState(false);
  const [enableAutoPortal, setEnableAutoPortal] = useState(false);
  const [enableDocumentExpiry, setEnableDocumentExpiry] = useState(false);
  const [enableEmployeeRequest, setEnableEmployeeRequest] = useState(false);

  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<HrSetupResult | null>(null);

  useEffect(() => {
    fetchTenantPrefs().then((prefs) => {
      setIndustry(prefs.industry);
      const d = getHrDefaults(prefs.industry);
      setOrgSize(d.orgSize);
      setDepartments(d.seedDepartments);
      setEnableBiometricZk(d.enableBiometricZk);
      setEnableSingleDeviceBinding(d.enableSingleDeviceBinding);
      setEnableGeofence(d.enableGeofence);
      setEnableHealthInsurance(d.enableHealthInsurance);
      setEnableEmployeeCode(d.enableEmployeeCode);
      setEnableEmployeeSpouse(d.enableEmployeeSpouse);
      setEnableAutoPortal(d.enableAutoPortal);
      setEnableDocumentExpiry(d.enableDocumentExpiry);
      setEnableEmployeeRequest(d.enableEmployeeRequest);
    });
  }, []);

  const submit = async () => {
    setApplying(true);
    setResult(await applyHrSetup({
      orgSize, departments,
      enableBiometricZk, enableSingleDeviceBinding, enableGeofence, enableHealthInsurance,
      enableEmployeeCode, enableEmployeeSpouse, enableAutoPortal, enableDocumentExpiry, enableEmployeeRequest,
    }));
    setApplying(false);
  };

  const onOff = (v: boolean) => v ? t('setupWizard.on') : t('setupWizard.off');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <Users className="w-7 h-7 text-[#E67E22]" /> {t('setupHr.title')}
          </h1>
          <p className="page-subtitle">{t('setupHr.subtitle')}</p>
        </div>
        <a href="/cycom/cycom/action-hr.open_view_department_form" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> {t('setupWizard.configureManually')}
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupHr.orgSizeHeading')}</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(['small', 'medium', 'large'] as OrgSize[]).map((m) => (
                  <button key={m} type="button" onClick={() => setOrgSize(m)} className={'text-start p-4 rounded-xl border transition-all ' + (m === orgSize ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')}>
                    <div className="text-sm font-bold">{ORG_SIZE_LABEL[m]}</div>
                  </button>
                ))}
              </div>

              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{t('setupHr.initialDepts')}</span>
                  <button type="button" onClick={() => setDepartments([...departments, ''])} className="btn-secondary flex items-center gap-1.5 text-[10px] py-1.5 px-2.5">
                    <Plus className="w-3 h-3" /> {t('setupHr.add')}
                  </button>
                </div>
                {departments.map((d, i) => (
                  <div key={i} className="flex gap-2 items-center bg-white/5 border border-white/8 rounded-xl p-2">
                    <input type="text" className="input-field py-2 text-sm flex-1" placeholder={t('setupHr.deptPh')} value={d} onChange={(e) => { const next = [...departments]; next[i] = e.target.value; setDepartments(next); }} />
                    <button type="button" onClick={() => setDepartments(departments.filter((_, j) => j !== i))} className="p-2 rounded-lg text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
            <AdvisorPanel lines={[
              industry ? t('setupHr.orgAdvisor', { industry }) : t('setupWizard.runCompanyFirst'),
              t('setupHr.orgAdvisorNote'),
            ]} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupHr.featuresHeading')}</h2>
              <ToggleRow label={t('setupHr.zkLabel')} description={t('setupHr.zkDesc')} on={enableBiometricZk} setOn={setEnableBiometricZk} />
              <ToggleRow label={t('setupHr.singleDeviceLabel')} description={t('setupHr.singleDeviceDesc')} on={enableSingleDeviceBinding} setOn={setEnableSingleDeviceBinding} />
              <ToggleRow label={t('setupHr.geofenceLabel')} description={t('setupHr.geofenceDesc')} on={enableGeofence} setOn={setEnableGeofence} />
              <ToggleRow label={t('setupHr.healthInsuranceLabel')} description={t('setupHr.healthInsuranceDesc')} on={enableHealthInsurance} setOn={setEnableHealthInsurance} />
              <ToggleRow label={t('setupHr.employeeCodeLabel')} description={t('setupHr.employeeCodeDesc')} on={enableEmployeeCode} setOn={setEnableEmployeeCode} />
              <ToggleRow label={t('setupHr.spouseLabel')} description={t('setupHr.spouseDesc')} on={enableEmployeeSpouse} setOn={setEnableEmployeeSpouse} />
              <ToggleRow label={t('setupHr.autoPortalLabel')} description={t('setupHr.autoPortalDesc')} on={enableAutoPortal} setOn={setEnableAutoPortal} />
              <ToggleRow label={t('setupHr.docExpiryLabel')} description={t('setupHr.docExpiryDesc')} on={enableDocumentExpiry} setOn={setEnableDocumentExpiry} />
              <ToggleRow label={t('setupHr.empRequestLabel')} description={t('setupHr.empRequestDesc')} on={enableEmployeeRequest} setOn={setEnableEmployeeRequest} />
            </div>
            <AdvisorPanel lines={[
              t('setupHr.featuresAdvisor'),
              t('setupHr.featuresAdvisorNote'),
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
                <ReviewRow label={t('setupHr.reviewOrgSize')} value={ORG_SIZE_LABEL[orgSize]} />
                <ReviewRow label={t('setupHr.reviewDepartments')} value={departments.filter(Boolean).join(', ') || '—'} />
                <ReviewRow label={t('setupHr.reviewZk')} value={onOff(enableBiometricZk)} />
                <ReviewRow label={t('setupHr.reviewSingleDevice')} value={onOff(enableSingleDeviceBinding)} />
                <ReviewRow label={t('setupHr.reviewGeofence')} value={onOff(enableGeofence)} />
                <ReviewRow label={t('setupHr.reviewHealthInsurance')} value={onOff(enableHealthInsurance)} />
                <ReviewRow label={t('setupHr.reviewEmployeeCode')} value={onOff(enableEmployeeCode)} />
                <ReviewRow label={t('setupHr.reviewSpouse')} value={onOff(enableEmployeeSpouse)} />
                <ReviewRow label={t('setupHr.reviewAutoPortal')} value={onOff(enableAutoPortal)} />
                <ReviewRow label={t('setupHr.reviewDocExpiry')} value={onOff(enableDocumentExpiry)} />
                <ReviewRow label={t('setupHr.reviewEmpRequest')} value={onOff(enableEmployeeRequest)} />
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
        onApply={submit} applyLabel={t('setupHr.applyLabel')} />
    </div>
  );
}
