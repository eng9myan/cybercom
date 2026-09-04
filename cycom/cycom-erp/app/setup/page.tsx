'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight, ArrowLeft, Check, Loader2, Building2, Globe, Layers,
  Users, ShieldCheck, Upload, ClipboardList, Sparkles, Factory, Store,
  HardHat, Briefcase, Truck, Home, Wrench, GraduationCap, HeartHandshake, Hospital,
} from 'lucide-react';
import { useT } from '@/lib/i18n';

type IndustryTemplate = {
  key: string; name: string; department_pack_keys: string[];
  approval_matrix: { document_type: string; name: string; tiers: { min: number; max: number | null; role: string }[] }[];
  import_templates: { entity: string; columns: string[] }[];
  default_config?: { roles?: { name: string; description?: string }[] };
};

export default function ReadyErpWizard() {
  const t = useT();

  // ── Wizard chrome built from the live catalog (translated labels + descs) ──
  const SETUP_LEVELS = [
    { id: 'express', label: t('readyErp.levelExpressLabel'), desc: t('readyErp.levelExpressDesc') },
    { id: 'professional', label: t('readyErp.levelProfessionalLabel'), desc: t('readyErp.levelProfessionalDesc') },
    { id: 'enterprise', label: t('readyErp.levelEnterpriseLabel'), desc: t('readyErp.levelEnterpriseDesc') },
  ];

  const COUNTRIES = [
    { code: 'JO', name: t('readyErp.countryJoName'), detail: t('readyErp.countryJoDetail') },
    { code: 'SA', name: t('readyErp.countrySaName'), detail: t('readyErp.countrySaDetail') },
    { code: 'AE', name: t('readyErp.countryAeName'), detail: t('readyErp.countryAeDetail') },
    { code: 'US', name: t('readyErp.countryUsName'), detail: t('readyErp.countryUsDetail') },
  ];

  const INDUSTRIES = [
    { key: 'construction', name: t('readyErp.indConstructionName'), icon: HardHat, status: 'ready', desc: t('readyErp.indConstructionDesc') },
    { key: 'trading', name: t('readyErp.indTradingName'), icon: Store, status: 'ready', desc: t('readyErp.indTradingDesc') },
    { key: 'manufacturing', name: t('readyErp.indManufacturingName'), icon: Factory, status: 'ready', desc: t('readyErp.indManufacturingDesc') },
    { key: 'services', name: t('readyErp.indServicesName'), icon: Briefcase, status: 'ready', desc: t('readyErp.indServicesDesc') },
    { key: 'logistics', name: t('readyErp.indLogisticsName'), icon: Truck, status: 'ready', desc: t('readyErp.indLogisticsDesc') },
    { key: 'realestate', name: t('readyErp.indRealestateName'), icon: Home, status: 'ready', desc: t('readyErp.indRealestateDesc') },
    { key: 'facility', name: t('readyErp.indFacilityName'), icon: Wrench, status: 'ready', desc: t('readyErp.indFacilityDesc') },
    { key: 'education', name: t('readyErp.indEducationName'), icon: GraduationCap, status: 'ready', desc: t('readyErp.indEducationDesc') },
    { key: 'retailgroup', name: t('readyErp.indRetailgroupName'), icon: Store, status: 'ready', desc: t('readyErp.indRetailgroupDesc') },
    { key: 'healthcare', name: t('readyErp.indHealthcareName'), icon: Hospital, status: 'ready', desc: t('readyErp.indHealthcareDesc') },
    { key: 'nonprofit', name: t('readyErp.indNonprofitName'), icon: HeartHandshake, status: 'ready', desc: t('readyErp.indNonprofitDesc') },
  ];

  const SIZES = [
    { id: 'micro', label: t('readyErp.sizeMicroLabel'), desc: t('readyErp.sizeMicroDesc') },
    { id: 'small', label: t('readyErp.sizeSmallLabel'), desc: t('readyErp.sizeSmallDesc') },
    { id: 'medium', label: t('readyErp.sizeMediumLabel'), desc: t('readyErp.sizeMediumDesc') },
    { id: 'large', label: t('readyErp.sizeLargeLabel'), desc: t('readyErp.sizeLargeDesc') },
    { id: 'enterprise', label: t('readyErp.sizeEnterpriseLabel'), desc: t('readyErp.sizeEnterpriseDesc') },
  ];

  const BUSINESS_OPS = [
    { id: 'buys_products', label: t('readyErp.opBuysProducts') },
    { id: 'manufactures', label: t('readyErp.opManufactures') },
    { id: 'provides_services', label: t('readyErp.opProvidesServices') },
    { id: 'manages_projects', label: t('readyErp.opManagesProjects') },
    { id: 'operates_branches', label: t('readyErp.opOperatesBranches') },
    { id: 'imports', label: t('readyErp.opImports') },
    { id: 'exports', label: t('readyErp.opExports') },
    { id: 'field_sales', label: t('readyErp.opFieldSales') },
    { id: 'ecommerce', label: t('readyErp.opEcommerce') },
    { id: 'retail_pos', label: t('readyErp.opRetailPos') },
  ];

  const STEPS = [
    t('readyErp.stepLevel'), t('readyErp.stepCountry'), t('readyErp.stepIndustry'), t('readyErp.stepStructure'),
    t('readyErp.stepSize'), t('readyErp.stepOperations'), t('readyErp.stepApprovals'), t('readyErp.stepRoles'),
    t('readyErp.stepImport'), t('readyErp.stepReview'),
  ];

  const FALLBACK_APPROVALS = [
    { document_type: 'purchase_request', name: t('readyErp.fallbackApprovalPurchase'), tiers: [
      { min: 0, max: 500, role: t('readyErp.roleDeptManager') }, { min: 500, max: 5000, role: t('readyErp.roleProcurementManager') }, { min: 5000, max: null, role: t('readyErp.roleGeneralManager') }] },
    { document_type: 'payment', name: t('readyErp.fallbackApprovalPayment'), tiers: [
      { min: 0, max: 10000, role: t('readyErp.roleFinanceManager') }, { min: 10000, max: null, role: t('readyErp.roleGeneralManager') }] },
  ];
  const FALLBACK_IMPORTS = [
    { entity: 'employees', columns: ['employee_number', 'full_name', 'department', 'salary'] },
    { entity: 'chart_of_accounts', columns: ['code', 'name', 'account_type', 'parent'] },
  ];
  const FALLBACK_ROLES = [t('readyErp.fallbackRoleGm'), t('readyErp.fallbackRoleSiteEngineer'), t('readyErp.fallbackRoleQs')];

  const [step, setStep] = useState(0);
  const [templates, setTemplates] = useState<Record<string, IndustryTemplate>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [aiText, setAiText] = useState('');
  const [aiBusy, setAiBusy] = useState(false);
  const [aiResult, setAiResult] = useState<any>(null);

  const [form, setForm] = useState({
    setup_level: 'express',
    company_name: '',
    country_code: 'JO',
    industry_key: 'construction',
    size: 'medium',
    business_ops: ['manages_projects'] as string[],
    selected_department_packs: [] as string[],
    companies: 1, branches: 1, warehouses: 1, factories: 0, projects: 3,
  });

  useEffect(() => {
    fetch('/api/cycom/provisioning/industry-templates')
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => {
        const rows = (data.results || data) as IndustryTemplate[];
        const map: Record<string, IndustryTemplate> = {};
        rows.forEach((tpl) => (map[tpl.key] = tpl));
        setTemplates(map);
      })
      .catch(() => setTemplates({})); // backend down → previews fall back below
  }, []);

  const tpl = templates[form.industry_key];
  const rolesPreview = useMemo(() => {
    if (tpl) {
      const packRoles = tpl.department_pack_keys || [];
      const cfg = tpl.default_config?.roles?.map((r) => r.name) || [];
      return { packs: packRoles, industryRoles: cfg };
    }
    return { packs: ['finance', 'procurement', 'hr', 'inventory', 'projects'], industryRoles: FALLBACK_ROLES };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tpl]);

  const set = (patch: Partial<typeof form>) => setForm((f) => ({ ...f, ...patch }));
  const toggleOp = (id: string) =>
    set({ business_ops: form.business_ops.includes(id) ? form.business_ops.filter((o) => o !== id) : [...form.business_ops, id] });

  async function proposeFromAi() {
    setAiBusy(true);
    setAiResult(null);
    try {
      const res = await fetch('/api/cycom/provisioning/ai-propose/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: aiText }),
      });
      const data = await res.json();
      setAiResult(data);
      if (data.matched) {
        set({
          industry_key: data.industry_key,
          selected_department_packs: data.extra_department_packs || [],
        });
      }
    } catch {
      setAiResult({ matched: false, message: t('readyErp.aiUnavailable') });
    } finally {
      setAiBusy(false);
    }
  }

  const canNext = () => {
    if (step === 0) return form.company_name.trim().length > 0;
    return true;
  };

  async function createCompany() {
    setSubmitting(true);
    setError(null);
    try {
      const createRes = await fetch('/api/cycom/provisioning/blueprints/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!createRes.ok) throw new Error((await createRes.json())?.detail || `Create failed (${createRes.status})`);
      const bp = await createRes.json();
      const provRes = await fetch(`/api/cycom/provisioning/blueprints/${bp.id}/provision/`, { method: 'POST' });
      if (!provRes.ok) throw new Error((await provRes.json())?.detail || `Provision failed (${provRes.status})`);
      setResult(await provRes.json());
    } catch (e: any) {
      setError(e.message || t('readyErp.genericError'));
    } finally {
      setSubmitting(false);
    }
  }

  // ── Success screen ────────────────────────────────────────────────────────
  if (result) {
    const s = result.summary || {};
    const industryName = INDUSTRIES.find((i) => i.key === form.industry_key)?.name || form.industry_key;
    return (
      <div className="max-w-3xl mx-auto py-10 px-4">
        <div className="glass-card p-8 text-center">
          <div className="w-14 h-14 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
            <Check className="w-7 h-7" />
          </div>
          <h1 className="page-title">{t('readyErp.successTitle', { company: result.company_name })}</h1>
          <p className="page-subtitle mb-6">{t('readyErp.successSubtitle', { industry: industryName })}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-start">
            <Stat label={t('readyErp.statModules')} value={(s.enabled_modules || []).length} />
            <Stat label={t('readyErp.statAccounts')} value={s.accounts_created ?? '—'} />
            <Stat label={t('readyErp.statRoles')} value={(s.roles || []).length} />
            <Stat label={t('readyErp.statApprovals')} value={(s.approval_policies || []).length} />
          </div>
          <div className="mt-6 flex gap-3 justify-center">
            <a href="/dashboard" className="btn-primary inline-flex items-center gap-2">{t('readyErp.openDashboard')} <ArrowRight className="w-4 h-4 rtl:-scale-x-100" /></a>
            <a href="/hr/employees/import" className="btn-secondary inline-flex items-center gap-2"><Upload className="w-4 h-4" /> {t('readyErp.importData')}</a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <header className="mb-6">
        <h1 className="page-title flex items-center gap-2"><Sparkles className="w-5 h-5 text-[var(--cy-orange)]" /> {t('readyErp.title')}</h1>
        <p className="page-subtitle">{t('readyErp.subtitle')}</p>
      </header>

      {/* Progress */}
      <div className="flex items-center gap-1.5 mb-6 overflow-x-auto">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-1.5 shrink-0">
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[0.7rem] font-semibold border ${
              i === step ? 'bg-[var(--cy-orange)]/15 text-[var(--cy-orange)] border-[var(--cy-orange)]/30'
              : i < step ? 'text-emerald-400 border-emerald-500/20' : 'text-slate-500 border-white/5'}`}>
              {i < step ? <Check className="w-3 h-3" /> : <span>{i + 1}</span>}{label}
            </div>
          </div>
        ))}
      </div>

      <div className="glass-card p-6 min-h-[340px]">
        {step === 0 && (
          <Section icon={Building2} title={t('readyErp.companySetupHeading')}>
            <label className="block text-xs font-bold text-slate-400 uppercase mb-2">{t('readyErp.companyNameLabel')}</label>
            <input className="input-field mb-5" placeholder={t('readyErp.companyNamePh')} value={form.company_name}
              onChange={(e) => set({ company_name: e.target.value })} />
            <div className="grid gap-3">
              {SETUP_LEVELS.map((l) => (
                <Choice key={l.id} active={form.setup_level === l.id} onClick={() => set({ setup_level: l.id })} title={l.label} desc={l.desc} />
              ))}
            </div>
          </Section>
        )}

        {step === 1 && (
          <Section icon={Globe} title={t('readyErp.countryHeading')}>
            <div className="grid gap-3">
              {COUNTRIES.map((c) => (
                <Choice key={c.code} active={form.country_code === c.code} onClick={() => set({ country_code: c.code })} title={c.name} desc={c.detail} />
              ))}
            </div>
          </Section>
        )}

        {step === 2 && (
          <Section icon={Factory} title={t('readyErp.industryHeading')}>
            {/* AI-guided configuration: describe the company in plain language */}
            <div className="mb-4 p-3 rounded-xl border border-[var(--cy-blue)]/20 bg-[var(--cy-blue)]/5">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-3.5 h-3.5 text-[var(--cy-blue)]" />
                <span className="text-xs font-bold text-slate-300 uppercase">{t('readyErp.aiHeading')}</span>
              </div>
              <div className="flex gap-2">
                <input className="input-field flex-1" placeholder={t('readyErp.aiPh')}
                  value={aiText} onChange={(e) => setAiText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && aiText.trim().length >= 10 && proposeFromAi()} />
                <button onClick={proposeFromAi} disabled={aiBusy || aiText.trim().length < 10}
                  className="btn-secondary shrink-0 inline-flex items-center gap-1.5 disabled:opacity-40">
                  {aiBusy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />} {t('readyErp.aiPropose')}
                </button>
              </div>
              {aiResult && (
                <div className="mt-2 text-xs">
                  {aiResult.matched ? (
                    <p className="text-emerald-300">
                      {t('readyErp.aiProposedLine', { industry: aiResult.industry_name, confidence: aiResult.confidence, rationale: aiResult.rationale })}
                    </p>
                  ) : (
                    <p className="text-amber-300">{aiResult.message}</p>
                  )}
                </div>
              )}
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              {INDUSTRIES.map((ind) => {
                const Icon = ind.icon;
                return (
                  <button key={ind.key} onClick={() => set({ industry_key: ind.key })}
                    className={`text-start p-3 rounded-xl border transition-all ${form.industry_key === ind.key
                      ? 'border-[var(--cy-orange)]/40 bg-[var(--cy-orange)]/8' : 'border-white/8 hover:border-white/15 bg-white/[0.02]'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4 text-[var(--cy-blue)]" />
                      <span className="text-sm font-semibold text-white">{ind.name}</span>
                      {ind.status === 'ready'
                        ? <span className="badge badge-green">{t('readyErp.statusReady')}</span>
                        : <span className="badge badge-orange">{t('readyErp.statusPreview')}</span>}
                    </div>
                    <p className="text-xs text-slate-400">{ind.desc}</p>
                  </button>
                );
              })}
            </div>
          </Section>
        )}

        {step === 3 && (
          <Section icon={Layers} title={t('readyErp.structureHeading')}>
            <div className="grid grid-cols-2 gap-4">
              <NumberField label={t('readyErp.fieldCompanies')} value={form.companies} onChange={(v) => set({ companies: v })} />
              <NumberField label={t('readyErp.fieldBranches')} value={form.branches} onChange={(v) => set({ branches: v })} />
              <NumberField label={t('readyErp.fieldWarehouses')} value={form.warehouses} onChange={(v) => set({ warehouses: v })} />
              <NumberField label={t('readyErp.fieldFactories')} value={form.factories} onChange={(v) => set({ factories: v })} />
              <NumberField label={t('readyErp.fieldProjects')} value={form.projects} onChange={(v) => set({ projects: v })} />
            </div>
          </Section>
        )}

        {step === 4 && (
          <Section icon={Building2} title={t('readyErp.sizeHeading')}>
            <div className="grid gap-3">
              {SIZES.map((s) => (
                <Choice key={s.id} active={form.size === s.id} onClick={() => set({ size: s.id })} title={s.label} desc={s.desc} />
              ))}
            </div>
            <p className="text-xs text-slate-500 mt-4">{t('readyErp.sizeNote')}</p>
          </Section>
        )}

        {step === 5 && (
          <Section icon={ClipboardList} title={t('readyErp.opsHeading')}>
            <div className="grid sm:grid-cols-2 gap-2">
              {BUSINESS_OPS.map((op) => (
                <button key={op.id} onClick={() => toggleOp(op.id)}
                  className={`flex items-center gap-2 text-start p-2.5 rounded-lg border text-sm transition-all ${
                    form.business_ops.includes(op.id) ? 'border-[var(--cy-blue)]/40 bg-[var(--cy-blue)]/8 text-white' : 'border-white/8 text-slate-300 hover:border-white/15'}`}>
                  <span className={`w-4 h-4 rounded border flex items-center justify-center ${form.business_ops.includes(op.id) ? 'bg-[var(--cy-blue)] border-[var(--cy-blue)]' : 'border-white/20'}`}>
                    {form.business_ops.includes(op.id) && <Check className="w-3 h-3 text-black" />}
                  </span>
                  {op.label}
                </button>
              ))}
            </div>
          </Section>
        )}

        {step === 6 && (
          <Section icon={ShieldCheck} title={t('readyErp.approvalsHeading')}>
            <p className="text-xs text-slate-400 mb-4">{t('readyErp.approvalsNote')}</p>
            <div className="space-y-4">
              {(tpl?.approval_matrix || FALLBACK_APPROVALS).map((p) => (
                <div key={p.document_type}>
                  <div className="text-sm font-semibold text-white mb-1.5">{p.name}</div>
                  <div className="flex flex-wrap gap-2">
                    {p.tiers.map((tier, i) => (
                      <span key={i} className="badge badge-cyan">
                        {tier.max === null ? t('readyErp.approvalOver', { min: tier.min }) : t('readyErp.approvalRange', { min: tier.min, max: tier.max })} → {tier.role}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {step === 7 && (
          <Section icon={Users} title={t('readyErp.rolesHeading')}>
            <p className="text-xs text-slate-400 mb-4">{t('readyErp.rolesNote')}</p>
            <div className="mb-3">
              <div className="text-xs font-bold text-slate-400 uppercase mb-1.5">{t('readyErp.deptPacksLabel')}</div>
              <div className="flex flex-wrap gap-2">{rolesPreview.packs.map((p) => <span key={p} className="badge badge-orange">{p}</span>)}</div>
            </div>
            <div>
              <div className="text-xs font-bold text-slate-400 uppercase mb-1.5">{t('readyErp.industryRolesLabel')}</div>
              <div className="flex flex-wrap gap-2">{rolesPreview.industryRoles.map((r) => <span key={r} className="badge badge-purple">{r}</span>)}</div>
            </div>
          </Section>
        )}

        {step === 8 && (
          <Section icon={Upload} title={t('readyErp.importHeading')}>
            <p className="text-xs text-slate-400 mb-4">{t('readyErp.importNote')}</p>
            <div className="grid sm:grid-cols-2 gap-2">
              {(tpl?.import_templates || FALLBACK_IMPORTS).map((it) => (
                <div key={it.entity} className="p-2.5 rounded-lg border border-white/8 bg-white/[0.02]">
                  <div className="text-sm font-semibold text-white capitalize">{it.entity.replace(/_/g, ' ')}</div>
                  <div className="text-[0.7rem] text-slate-500 truncate" dir="ltr">{it.columns.join(', ')}</div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {step === 9 && (
          <Section icon={Check} title={t('readyErp.reviewHeading')}>
            <div className="space-y-2 text-sm">
              <Row k={t('readyErp.reviewCompany')} v={form.company_name || '—'} />
              <Row k={t('readyErp.reviewCountry')} v={COUNTRIES.find((c) => c.code === form.country_code)?.name || form.country_code} />
              <Row k={t('readyErp.reviewIndustry')} v={INDUSTRIES.find((i) => i.key === form.industry_key)?.name || form.industry_key} />
              <Row k={t('readyErp.reviewSizeLevel')} v={`${form.size} · ${form.setup_level}`} />
              <Row k={t('readyErp.reviewStructure')} v={t('readyErp.structureSummary', { companies: form.companies, branches: form.branches, warehouses: form.warehouses, projects: form.projects })} />
              <Row k={t('readyErp.reviewOperations')} v={form.business_ops.join(', ') || '—'} />
            </div>
            {error && <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs">{error}</div>}
          </Section>
        )}
      </div>

      {/* Nav */}
      <div className="flex justify-between mt-5">
        <button onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}
          className="btn-secondary inline-flex items-center gap-2 disabled:opacity-40"><ArrowLeft className="w-4 h-4 rtl:-scale-x-100" /> {t('readyErp.back')}</button>
        {step < STEPS.length - 1 ? (
          <button onClick={() => canNext() && setStep((s) => s + 1)} disabled={!canNext()}
            className="btn-primary inline-flex items-center gap-2 disabled:opacity-40">{t('readyErp.continue')} <ArrowRight className="w-4 h-4 rtl:-scale-x-100" /></button>
        ) : (
          <button onClick={createCompany} disabled={submitting}
            className="btn-primary inline-flex items-center gap-2 disabled:opacity-60">
            {submitting ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('readyErp.building')}</> : <>{t('readyErp.createCompany')} <Sparkles className="w-4 h-4" /></>}
          </button>
        )}
      </div>
    </div>
  );
}

function Section({ icon: Icon, title, children }: { icon: any; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-4"><Icon className="w-4 h-4 text-[var(--cy-orange)]" /><h2 className="text-base font-bold text-white">{title}</h2></div>
      {children}
    </div>
  );
}
function Choice({ active, onClick, title, desc }: { active: boolean; onClick: () => void; title: string; desc: string }) {
  return (
    <button onClick={onClick} className={`text-start p-3 rounded-xl border transition-all ${active ? 'border-[var(--cy-orange)]/40 bg-[var(--cy-orange)]/8' : 'border-white/8 hover:border-white/15 bg-white/[0.02]'}`}>
      <div className="text-sm font-semibold text-white">{title}</div>
      <div className="text-xs text-slate-400 mt-0.5">{desc}</div>
    </button>
  );
}
function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <label className="block text-xs font-bold text-slate-400 uppercase mb-2">{label}</label>
      <input type="number" min={0} className="input-field" value={value} onChange={(e) => onChange(Math.max(0, parseInt(e.target.value || '0', 10)))} />
    </div>
  );
}
function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return <div className="p-3 rounded-xl border border-white/8 bg-white/[0.02]"><div className="text-2xl font-black text-[var(--cy-blue)]">{value}</div><div className="text-[0.7rem] uppercase text-slate-500 font-bold">{label}</div></div>;
}
function Row({ k, v }: { k: string; v: string }) {
  return <div className="flex justify-between border-b border-white/5 pb-1.5"><span className="text-slate-400">{k}</span><span className="text-white font-medium text-end">{v}</span></div>;
}
