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

const STEPS = ['Role template', 'Sensitivity', 'Review'] as const;
type StepIdx = 0 | 1 | 2;

export default function PermissionsWizard() {
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
            <Shield className="w-7 h-7 text-[#E67E22]" /> Permissions & Roles
          </h1>
          <p className="page-subtitle">Role template + module sensitivity. Detailed per-user access stays available in Cycom.</p>
        </div>
        <a href="/cycom/cycom/action-base.action_res_groups" target="_blank" rel="noreferrer" className="btn-secondary flex items-center gap-2 text-xs">
          <Wrench className="w-3.5 h-3.5" /> Configure manually
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

      <motion.div key={step} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="space-y-6">
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Role template</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(['strict', 'standard', 'open'] as RoleTemplate[]).map((m) => (
                  <button key={m} type="button" onClick={() => setRoleTemplate(m)} className={'text-left p-4 rounded-xl border transition-all ' + (m === roleTemplate ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')}>
                    <div className="text-sm font-bold">{ROLE_TEMPLATE_LABEL[m]}</div>
                  </button>
                ))}
              </div>
              <ToggleRow label="Create a Cycom Manager group"
                description="Adds a res.groups record you can assign to module managers. Doesn't auto-add anyone." on={createCycomManagerGroup} setOn={setCreateCycomManagerGroup} />
            </div>
            <AdvisorPanel lines={[
              industry ? `"${industry}" tenants typically run the "${ROLE_TEMPLATE_LABEL[getPermissionDefaults(industry).roleTemplate]}" template.` : 'Run Company Setup first.',
              'Strict suits regulated manufacturing; open suits small services teams; standard is the right default for most.',
            ]} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Module sensitivity</h2>
              <ToggleRow label="Finance restricted" description="Only Finance team can see GL, AP, AR." on={financeRestricted} setOn={setFinanceRestricted} />
              <ToggleRow label="Payroll restricted" description="Only Payroll team can see payslips, salary structures." on={payrollRestricted} setOn={setPayrollRestricted} />
              <ToggleRow label="Inventory restricted (per warehouse)" description="warehouse_restriction_for_user — operators only see their warehouse." on={inventoryRestricted} setOn={setInventoryRestricted} />
              <ToggleRow label="POS restricted (per terminal)" description="Cashiers only see their POS session and cash drawer." on={posRestricted} setOn={setPosRestricted} />
            </div>
            <AdvisorPanel lines={[
              'These toggles persist as ir.config_parameter values for now; detailed access rules can be tightened per group later under Settings → Users & Companies → Groups.',
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
                <ReviewRow label="Role template" value={ROLE_TEMPLATE_LABEL[roleTemplate]} />
                <ReviewRow label="Cycom Manager group" value={createCycomManagerGroup ? 'Created' : 'Skipped'} />
                <ReviewRow label="Finance" value={financeRestricted ? 'Restricted' : 'Open'} />
                <ReviewRow label="Payroll" value={payrollRestricted ? 'Restricted' : 'Open'} />
                <ReviewRow label="Inventory" value={inventoryRestricted ? 'Restricted per warehouse' : 'Open'} />
                <ReviewRow label="POS" value={posRestricted ? 'Restricted per terminal' : 'Open'} />
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
        onApply={submit} applyLabel="Configure permissions" />
    </div>
  );
}
