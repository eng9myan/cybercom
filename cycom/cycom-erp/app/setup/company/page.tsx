'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Building2, ChevronLeft, ChevronRight, CheckCircle2, AlertTriangle,
  Sparkles, Globe, Calendar, MapPin, Plus, Trash2, Layers, Wrench, Lightbulb,
} from 'lucide-react';
import {
  COUNTRIES,
  COUNTRY_CURRENCY,
  INDUSTRY_TEMPLATES,
  getIndustry,
  type IndustryKey,
} from '@/lib/setup/industry-templates';
import { applyCompanySetup, type CompanySetupBranch } from '@/lib/setup/companySetup';
import { useT } from '@/lib/i18n';

type StepIdx = 0 | 1 | 2 | 3;

export default function CompanySetupWizard() {
  const t = useT();
  const STEPS = [t('setupCompany.stepBasics'), t('setupCompany.stepFinancials'), t('setupCompany.stepSites'), t('setupWizard.stepReview')] as const;

  const PAYMENT_TERM_LABEL: Record<string, string> = {
    net_30: t('setupCompany.ptNet30'),
    net_15: t('setupCompany.ptNet15'),
    on_delivery: t('setupCompany.ptDelivery'),
    cash: t('setupCompany.ptCash'),
  };

  const MONTHS = [
    t('setupCompany.monthJan'), t('setupCompany.monthFeb'), t('setupCompany.monthMar'), t('setupCompany.monthApr'),
    t('setupCompany.monthMay'), t('setupCompany.monthJun'), t('setupCompany.monthJul'), t('setupCompany.monthAug'),
    t('setupCompany.monthSep'), t('setupCompany.monthOct'), t('setupCompany.monthNov'), t('setupCompany.monthDec'),
  ];

  const [step, setStep] = useState<StepIdx>(0);

  // Form state
  const [legalName, setLegalName] = useState('');
  const [shortName, setShortName] = useState('');
  const [industry, setIndustry] = useState<IndustryKey>('retail');

  const [countryCode, setCountryCode] = useState('JO');
  const [currency, setCurrency] = useState('JOD');
  const [fiscalYearStartMonth, setFiscalYearStartMonth] = useState(1);
  const [taxRegistrationNumber, setTaxRegistrationNumber] = useState('');
  const [paymentTerms, setPaymentTerms] = useState<'net_30' | 'net_15' | 'on_delivery' | 'cash'>('cash');
  const [pricingMode, setPricingMode] = useState<'tax_inclusive' | 'tax_exclusive'>('tax_inclusive');

  const [multiSite, setMultiSite] = useState(true);
  const [branches, setBranches] = useState<CompanySetupBranch[]>([
    { name: 'Branch 1', city: '' },
  ]);

  // Apply state
  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<
    | { ok: true; summary: string[]; warnings: string[]; parentCompanyId: number; branchIds: number[] }
    | { ok: false; error: string; warnings?: string[] }
    | null
  >(null);

  const industryTemplate = useMemo(() => getIndustry(industry), [industry]);

  // When industry changes, re-apply its defaults — but never clobber values the user already touched
  // in a way that would surprise them. We only apply on industry-change for fields that derive from it.
  const applyIndustryDefaults = (key: IndustryKey) => {
    const tmpl = getIndustry(key);
    setIndustry(key);
    setMultiSite(tmpl.defaults.multiSite);
    setBranches(Array.from({ length: tmpl.defaults.typicalSiteCount }, (_, i) => ({
      name: `Branch ${i + 1}`, city: '',
    })));
    setFiscalYearStartMonth(tmpl.defaults.fiscalYearStartMonth);
    setPaymentTerms(tmpl.defaults.paymentTerms);
    setPricingMode(tmpl.defaults.pricingMode);
  };

  const applyCountryDefaults = (code: string) => {
    setCountryCode(code);
    const ccy = COUNTRY_CURRENCY[code];
    if (ccy) setCurrency(ccy);
  };

  const canAdvance = (() => {
    if (step === 0) return legalName.trim().length > 0;
    if (step === 1) return Boolean(countryCode && currency);
    if (step === 2) return !multiSite || branches.every((b) => b.name.trim().length > 0);
    return true;
  })();

  const submit = async () => {
    setApplying(true);
    setResult(null);
    try {
      const res = await applyCompanySetup({
        legalName,
        shortName: shortName || undefined,
        industry,
        countryCode,
        currency,
        fiscalYearStartMonth,
        taxRegistrationNumber: taxRegistrationNumber || undefined,
        multiSite,
        branches: multiSite ? branches : [],
        paymentTerms,
        pricingMode,
      });
      setResult(res);
    } catch (e) {
      setResult({ ok: false, error: e instanceof Error ? e.message : 'Setup failed' });
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page header — same pattern as other Cycom pages */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <Building2 className="w-7 h-7 text-[#E67E22]" />
            {t('setupCompany.title')}
          </h1>
          <p className="page-subtitle">
            {t('setupCompany.subtitle')}
          </p>
        </div>
        <a
          href="/cycom/web#action=base.action_res_company_form"
          target="_blank"
          rel="noreferrer"
          className="btn-secondary flex items-center gap-2 text-xs"
          title="Drop into the raw Cycom Companies configuration page"
        >
          <Wrench className="w-3.5 h-3.5" /> {t('setupWizard.configureManually')}
        </a>
      </div>

      {/* Step indicator */}
      <div className="glass-card p-4 flex items-center gap-2">
        {STEPS.map((label, idx) => {
          const state = idx < step ? 'done' : idx === step ? 'active' : 'pending';
          return (
            <React.Fragment key={label}>
              <div className="flex items-center gap-2">
                <div
                  className={
                    'w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold border ' +
                    (state === 'done'
                      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                      : state === 'active'
                      ? 'bg-orange-500/15 text-[#E67E22] border-orange-500/40'
                      : 'bg-white/5 text-slate-500 border-white/10')
                  }
                >
                  {state === 'done' ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                </div>
                <span
                  className={
                    'text-xs font-bold uppercase tracking-widest ' +
                    (state === 'pending' ? 'text-slate-500' : 'text-white')
                  }
                >
                  {label}
                </span>
              </div>
              {idx < STEPS.length - 1 && <div className="flex-1 h-px bg-white/10" />}
            </React.Fragment>
          );
        })}
      </div>

      {/* Step body — never re-mount, just swap content */}
      <motion.div
        key={step}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18 }}
        className="space-y-6"
      >
        {step === 0 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupCompany.businessHeading')}</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCompany.legalName')} <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder={t('setupCompany.legalNamePh')}
                    className="input-field py-2.5"
                    value={legalName}
                    onChange={(e) => setLegalName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCompany.shortName')} <span className="text-slate-500 font-normal">{t('setupCompany.optional')}</span>
                  </label>
                  <input
                    type="text"
                    placeholder={t('setupCompany.shortNamePh')}
                    className="input-field py-2.5"
                    value={shortName}
                    onChange={(e) => setShortName(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('setupCompany.industryHeading')}</h2>
                <span className="badge badge-cyan font-mono text-[10px]">{t('setupCompany.industryBadge')}</span>
              </div>
              <p className="text-xs text-slate-500">
                {t('setupCompany.industryNote')}
              </p>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {INDUSTRY_TEMPLATES.map((tmpl) => {
                  const active = tmpl.key === industry;
                  return (
                    <button
                      key={tmpl.key}
                      type="button"
                      onClick={() => applyIndustryDefaults(tmpl.key)}
                      className={
                        'text-start p-4 rounded-xl border transition-all ' +
                        (active
                          ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white shadow-md shadow-orange-500/5'
                          : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10 hover:border-white/20')
                      }
                    >
                      <div className="text-sm font-bold mb-1">{tmpl.label}</div>
                      <div className="text-[11px] text-slate-400">{tmpl.blurb}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            <AdvisorPanel lines={industryTemplate.advisor} />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Globe className="w-4 h-4 text-cyan-400" /> {t('setupCompany.countryCurrencyHeading')}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCompany.country')} <span className="text-rose-400">*</span>
                  </label>
                  <select
                    className="input-field py-2.5"
                    value={countryCode}
                    onChange={(e) => applyCountryDefaults(e.target.value)}
                  >
                    {COUNTRIES.map((c) => (
                      <option key={c.code} value={c.code}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCompany.currency')} <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    maxLength={3}
                    placeholder={t('setupCompany.currencyPh')}
                    className="input-field py-2.5 uppercase"
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                    dir="ltr"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">
                    {t('setupCompany.currencyNote')}
                  </p>
                </div>
              </div>
            </div>

            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-purple-400" /> {t('setupCompany.fiscalHeading')}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCompany.fiscalYearStarts')}
                  </label>
                  <select
                    className="input-field py-2.5"
                    value={fiscalYearStartMonth}
                    onChange={(e) => setFiscalYearStartMonth(parseInt(e.target.value, 10))}
                  >
                    {MONTHS.map((m, i) => (
                      <option key={m} value={i + 1}>{m}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCompany.taxRegistration')} <span className="text-slate-500 font-normal">{t('setupCompany.optional')}</span>
                  </label>
                  <input
                    type="text"
                    placeholder={t('setupCompany.taxRegistrationPh')}
                    className="input-field py-2.5"
                    value={taxRegistrationNumber}
                    onChange={(e) => setTaxRegistrationNumber(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCompany.defaultPaymentTerms')}
                  </label>
                  <select
                    className="input-field py-2.5"
                    value={paymentTerms}
                    onChange={(e) => setPaymentTerms(e.target.value as typeof paymentTerms)}
                  >
                    <option value="cash">{t('setupCompany.ptCash')}</option>
                    <option value="on_delivery">{t('setupCompany.ptDelivery')}</option>
                    <option value="net_15">{t('setupCompany.ptNet15')}</option>
                    <option value="net_30">{t('setupCompany.ptNet30')}</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCompany.pricingMode')}
                  </label>
                  <select
                    className="input-field py-2.5"
                    value={pricingMode}
                    onChange={(e) => setPricingMode(e.target.value as typeof pricingMode)}
                  >
                    <option value="tax_inclusive">{t('setupCompany.pmInclusive')}</option>
                    <option value="tax_exclusive">{t('setupCompany.pmExclusive')}</option>
                  </select>
                </div>
              </div>
            </div>

            <AdvisorPanel
              lines={[
                t('setupCompany.financialsAdvisor', {
                  industry: industryTemplate.label,
                  country: COUNTRIES.find((c) => c.code === countryCode)?.name ?? countryCode,
                  currency,
                }),
                pricingMode === 'tax_inclusive'
                  ? t('setupCompany.inclusiveAdvisor')
                  : t('setupCompany.exclusiveAdvisor'),
              ]}
            />
          </>
        )}

        {step === 2 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-400" /> {t('setupCompany.locationsHeading')}
              </h2>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setMultiSite(false)}
                  className={
                    'flex-1 p-4 rounded-xl border text-start transition-all ' +
                    (!multiSite
                      ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white'
                      : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')
                  }
                >
                  <div className="font-bold text-sm">{t('setupCompany.singleLocation')}</div>
                  <div className="text-[11px] text-slate-400 mt-1">{t('setupCompany.singleLocationDesc')}</div>
                </button>
                <button
                  type="button"
                  onClick={() => setMultiSite(true)}
                  className={
                    'flex-1 p-4 rounded-xl border text-start transition-all ' +
                    (multiSite
                      ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white'
                      : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')
                  }
                >
                  <div className="font-bold text-sm">{t('setupCompany.multiBranch')}</div>
                  <div className="text-[11px] text-slate-400 mt-1">{t('setupCompany.multiBranchDesc')}</div>
                </button>
              </div>

              {multiSite && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{t('setupCompany.branches')}</span>
                    <button
                      type="button"
                      onClick={() => setBranches([...branches, { name: `Branch ${branches.length + 1}`, city: '' }])}
                      className="btn-secondary flex items-center gap-1.5 text-[10px] py-1.5 px-2.5"
                    >
                      <Plus className="w-3 h-3" /> {t('setupCompany.addBranch')}
                    </button>
                  </div>

                  <div className="space-y-2">
                    {branches.map((b, i) => (
                      <div key={i} className="flex gap-3 items-start bg-white/5 border border-white/8 rounded-xl p-3">
                        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-2">
                          <input
                            type="text"
                            placeholder={t('setupCompany.branchNamePh')}
                            className="input-field py-2 text-sm"
                            value={b.name}
                            onChange={(e) => {
                              const next = [...branches];
                              next[i] = { ...next[i], name: e.target.value };
                              setBranches(next);
                            }}
                          />
                          <input
                            type="text"
                            placeholder={t('setupCompany.cityPh')}
                            className="input-field py-2 text-sm"
                            value={b.city ?? ''}
                            onChange={(e) => {
                              const next = [...branches];
                              next[i] = { ...next[i], city: e.target.value };
                              setBranches(next);
                            }}
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => setBranches(branches.filter((_, j) => j !== i))}
                          className="p-2 rounded-lg text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition-colors"
                          title={t('setupCompany.removeBranch')}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <AdvisorPanel
              lines={[
                multiSite
                  ? t('setupCompany.multiSiteAdvisor', { company: legalName || t('setupCompany.yourCompany') })
                  : t('setupCompany.singleSiteAdvisor'),
              ]}
            />
          </>
        )}

        {step === 3 && (
          <>
            <div className="glass-card p-6 space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#E67E22]" /> {t('setupWizard.stepReview')}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <ReviewRow label={t('setupCompany.reviewLegalName')} value={legalName || '—'} />
                <ReviewRow label={t('setupCompany.reviewShortName')} value={shortName || '—'} />
                <ReviewRow label={t('setupCompany.reviewIndustry')} value={industryTemplate.label} />
                <ReviewRow label={t('setupCompany.reviewCountry')} value={COUNTRIES.find((c) => c.code === countryCode)?.name ?? countryCode} />
                <ReviewRow label={t('setupCompany.reviewCurrency')} value={currency} />
                <ReviewRow label={t('setupCompany.reviewFiscalStart')} value={MONTHS[fiscalYearStartMonth - 1]} />
                <ReviewRow label={t('setupCompany.reviewTaxReg')} value={taxRegistrationNumber || '—'} />
                <ReviewRow label={t('setupCompany.reviewPaymentTerms')} value={PAYMENT_TERM_LABEL[paymentTerms]} />
                <ReviewRow label={t('setupCompany.reviewPricingMode')} value={pricingMode === 'tax_inclusive' ? t('setupCompany.pmInclusive') : t('setupCompany.pmExclusive')} />
                <ReviewRow
                  label={t('setupCompany.reviewLocations')}
                  value={multiSite ? t('setupCompany.locationsSummary', { n: branches.length, names: branches.map((b) => b.name).join(', ') }) : t('setupCompany.singleLocationVal')}
                />
              </div>

              <div className="bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-4 text-xs text-cyan-200/90 flex items-start gap-3">
                <Sparkles className="w-4 h-4 text-cyan-300 flex-shrink-0 mt-0.5" />
                <div>
                  {t('setupCompany.applyNote')}
                </div>
              </div>
            </div>

            {result && result.ok && (
              <div className="glass-card p-6 border border-emerald-500/30 bg-emerald-500/5 space-y-3">
                <div className="flex items-center gap-2 text-emerald-300 font-bold">
                  <CheckCircle2 className="w-5 h-5" /> {t('setupCompany.companyConfigured')}
                </div>
                <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                  {result.summary.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
                {result.warnings.length > 0 && (
                  <div className="text-[11px] text-amber-300 space-y-1">
                    <div className="font-bold flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" /> {t('setupWizard.warnings')}
                    </div>
                    <ul className="list-disc list-inside ml-1">
                      {result.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="pt-2 flex gap-2">
                  <Link href="/setup" className="btn-secondary text-xs py-2 px-3">{t('setupCompany.continueNext')}</Link>
                  <Link href="/dashboard" className="btn-primary text-xs py-2 px-3">{t('setupCompany.goToDashboard')}</Link>
                </div>
              </div>
            )}

            {result && !result.ok && (
              <div className="glass-card p-6 border border-rose-500/30 bg-rose-500/5 space-y-2">
                <div className="flex items-center gap-2 text-rose-300 font-bold">
                  <AlertTriangle className="w-5 h-5" /> {t('setupWizard.setupFailed')}
                </div>
                <p className="text-xs text-rose-200">{result.error}</p>
                <p className="text-[10px] text-slate-500">
                  {t('setupWizard.recoveryHint')}
                </p>
              </div>
            )}
          </>
        )}
      </motion.div>

      {/* Footer nav */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          disabled={step === 0 || applying}
          onClick={() => setStep((s) => (Math.max(0, s - 1) as StepIdx))}
          className="btn-secondary flex items-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="w-4 h-4 rtl:-scale-x-100" /> {t('setupWizard.back')}
        </button>

        {step < 3 ? (
          <button
            type="button"
            disabled={!canAdvance}
            onClick={() => setStep((s) => (Math.min(3, s + 1) as StepIdx))}
            className="btn-primary flex items-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {t('setupWizard.next')} <ChevronRight className="w-4 h-4 rtl:-scale-x-100" />
          </button>
        ) : (
          <button
            type="button"
            onClick={submit}
            disabled={applying || (result?.ok ?? false)}
            className="btn-primary flex items-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {applying ? (
              <>
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                {t('setupWizard.applying')}
              </>
            ) : result?.ok ? (
              <>
                <CheckCircle2 className="w-4 h-4" /> {t('setupWizard.applied')}
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" /> {t('setupWizard.applySetup')}
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white/5 border border-white/8 rounded-xl p-3">
      <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">{label}</div>
      <div className="text-slate-200 font-semibold mt-0.5">{value}</div>
    </div>
  );
}

function AdvisorPanel({ lines }: { lines: string[] }) {
  const t = useT();
  return (
    <div className="glass-card p-5 border border-purple-500/20 bg-purple-500/5">
      <div className="flex items-center gap-2 mb-2">
        <Lightbulb className="w-4 h-4 text-purple-300" />
        <span className="text-xs font-bold uppercase tracking-wider text-purple-200">{t('setupWizard.aiRecommendation')}</span>
      </div>
      <ul className="space-y-1.5 text-xs text-slate-300">
        {lines.map((line, i) => (
          <li key={i} className="flex gap-2">
            <span className="text-purple-300/60">›</span>
            <span>{line}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
