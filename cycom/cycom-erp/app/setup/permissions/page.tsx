'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Layers, Wrench } from 'lucide-react';
import { fetchTenantPrefs } from '@/lib/setup/coaSetup';
import { ROLE_TEMPLATE_LABEL, getPermissionDefaults, type RoleTemplate } from '@/lib/setup/permissions-templates';
import { applyPermissionsSetup, type PermissionsSetupResult } from '@/lib/setup/permissionsSetup';
import { StepIndicator } from '@/components/setup/StepIndicator';
import { WizardFooter } from '@/components/setup/WizardFooter';
import { AdvisorPanel } from '@/components/setup/AdvisorPanel';
import { ReviewRow } from '@/components/setup/ReviewRow';
import { ResultBanner } from '@/components/setup/ResultBanner';
import { ToggleRow } from '@/components/setup/ToggleRow';
import { useT } from '@/lib/i18n';

type StepIdx = 0 | 1 | 2;

export default function PermissionsWizard() {
  const t = useT();
  const STEPS = [t('setupPermissions.roleHeading'), t('setupPermissions.sensitivityHeading'), t('setupWizard.stepReview')] as const;
  const [step, setStep] = useState<StepIdx>(0);
  const [industry, setIndustry] = useState<string | undefined>();

  const [roleTemplate, setRoleTemplate] = useState<RoleTemplate>('standard');
  const [financeRestricted, setFinanceRestricted] = useState(true);
  const [payrollRestricted, setPayrollRestricted] = useState(true);
  const [inventoryRestricted, setInventoryRestricted] = useState(false);
  const [posRestricted, setPosRestricted] = useState(false);
  const [createCycomManagerGroup, setCreateCycomManagerGroup] = useState(true);

  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<PermissionsSetupResult | null>(null);

  useEffect(() => {
    fetchTenantPrefs().then((prefs) => {
      setIndustry(prefs.industry);
      const d = getPermissionDefaults(prefs.industry);
      setRoleTemplate(d.roleTemplate);
      setFinanceRestricted(d.financeRestricted);
      setPayrollRestricted(d.payrollRestricted);
      setInventoryRestricted(d.inventoryRestricted);
      setPosRestricted(d.posRestricted);
      setCreateCycomManagerGroup(d.createCycomManagerGroup);
    });
  }, []);

  const submit = async () => {
    setApplying(true);
    setResult(await applyPermissionsSetup({
      roleTemplate, financeRestricted, payrollRestricted, inventoryRestricted, posRestricted, createCycomManagerGroup,
    }));
    setApplying(false);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <Shield className="w-7 h-7 text-[#E67E22]" /> {t('setupPermissions.title')}
          </h1>
          <p className="page-subtitle">{t('setupPermissions.subtitle')}</p>
        </div>
        <a href="/cycom/cycom/action-base.action_res_groups" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> {t('setupWizard.configureManually')}
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupPermissions.roleHeading')}</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(['strict', 'standard', 'open'] as RoleTemplate[]).map((m) => (
                  <button key={m} type="button" onClick={() => setRoleTemplate(m)} className={'text-start p-4 rounded-xl border transition-all ' + (m === roleTemplate ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')}>
                    <div className="text-sm font-bold">{ROLE_TEMPLATE_LABEL[m]}</div>
                  </button>
                ))}
              </div>
              <ToggleRow label={t('setupPermissions.createGroupLabel')}
                description={t('setupPermissions.createGroupDesc')} on={createCycomManagerGroup} setOn={setCreateCycomManagerGroup} />
            </div>
            <AdvisorPanel lines={[
              industry ? t('setupPermissions.roleAdvisor', { industry, template: ROLE_TEMPLATE_LABEL[getPermissionDefaults(industry).roleTemplate] }) : t('setupWizard.runCompanyFirst'),
              t('setupPermissions.roleAdvisorNote'),
            ]} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupPermissions.sensitivityHeading')}</h2>
              <ToggleRow label={t('setupPermissions.financeLabel')} description={t('setupPermissions.financeDesc')} on={financeRestricted} setOn={setFinanceRestricted} />
              <ToggleRow label={t('setupPermissions.payrollLabel')} description={t('setupPermissions.payrollDesc')} on={payrollRestricted} setOn={setPayrollRestricted} />
              <ToggleRow label={t('setupPermissions.inventoryLabel')} description={t('setupPermissions.inventoryDesc')} on={inventoryRestricted} setOn={setInventoryRestricted} />
              <ToggleRow label={t('setupPermissions.posLabel')} description={t('setupPermissions.posDesc')} on={posRestricted} setOn={setPosRestricted} />
            </div>
            <AdvisorPanel lines={[
              t('setupPermissions.sensitivityAdvisor'),
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
                <ReviewRow label={t('setupPermissions.reviewRoleTemplate')} value={ROLE_TEMPLATE_LABEL[roleTemplate]} />
                <ReviewRow label={t('setupPermissions.reviewManagerGroup')} value={createCycomManagerGroup ? t('setupWizard.created') : t('setupWizard.skipped')} />
                <ReviewRow label={t('setupPermissions.reviewFinance')} value={financeRestricted ? t('setupPermissions.restricted') : t('setupPermissions.open')} />
                <ReviewRow label={t('setupPermissions.reviewPayroll')} value={payrollRestricted ? t('setupPermissions.restricted') : t('setupPermissions.open')} />
                <ReviewRow label={t('setupPermissions.reviewInventory')} value={inventoryRestricted ? t('setupPermissions.inventoryRestrictedVal') : t('setupPermissions.open')} />
                <ReviewRow label={t('setupPermissions.reviewPos')} value={posRestricted ? t('setupPermissions.posRestrictedVal') : t('setupPermissions.open')} />
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
        onApply={submit} applyLabel={t('setupPermissions.applyLabel')} />
    </div>
  );
}
