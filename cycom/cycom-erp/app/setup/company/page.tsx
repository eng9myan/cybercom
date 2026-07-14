'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Building2, ChevronLeft, ChevronRight, CheckCircle2, AlertTriangle,
  Sparkles, Globe, Coins, Calendar, MapPin, Plus, Trash2, Layers, Wrench, Lightbulb,
} from 'lucide-react';
import {
  COUNTRIES,
  COUNTRY_CURRENCY,
  INDUSTRY_TEMPLATES,
  getIndustry,
  type IndustryKey,
} from '@/lib/setup/industry-templates';
import { applyCompanySetup, type CompanySetupBranch } from '@/lib/setup/companySetup';

const STEPS = ['Basics', 'Financials', 'Sites', 'Review'] as const;
type StepIdx = 0 | 1 | 2 | 3;

const PAYMENT_TERM_LABEL: Record<string, string> = {
  net_30: 'Net 30',
  net_15: 'Net 15',
  on_delivery: 'On delivery',
  cash: 'Cash on sale',
};

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export default function CompanySetupWizard() {
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
    const t = getIndustry(key);
    setIndustry(key);
    setMultiSite(t.defaults.multiSite);
    setBranches(Array.from({ length: t.defaults.typicalSiteCount }, (_, i) => ({
      name: `Branch ${i + 1}`, city: '',
    })));
    setFiscalYearStartMonth(t.defaults.fiscalYearStartMonth);
    setPaymentTerms(t.defaults.paymentTerms);
    setPricingMode(t.defaults.pricingMode);
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
            Company Setup
          </h1>
          <p className="page-subtitle">
            Answer a few business questions. Cycom configures your tenant — no ERP knowledge required.
          </p>
        </div>
        <a
          href="/cycom/web#action=base.action_res_company_form"
          target="_blank"
          rel="noreferrer"
          className="btn-secondary flex items-center gap-2 text-xs"
          title="Drop into the raw Cycom Companies configuration page"
        >
          <Wrench className="w-3.5 h-3.5" /> Configure manually
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
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Your business</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    Legal name <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Cycom Retail Co."
                    className="input-field py-2.5"
                    value={legalName}
                    onChange={(e) => setLegalName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    Short name <span className="text-slate-500 font-normal">(optional)</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Cycom Retail"
                    className="input-field py-2.5"
                    value={shortName}
                    onChange={(e) => setShortName(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Industry</h2>
                <span className="badge badge-cyan font-mono text-[10px]">Cycom Industry Templates</span>
              </div>
              <p className="text-xs text-slate-500">
                Pick the closest match. Cycom uses this to pre-fill the next steps with sensible defaults.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {INDUSTRY_TEMPLATES.map((t) => {
                  const active = t.key === industry;
                  return (
                    <button
                      key={t.key}
                      type="button"
                      onClick={() => applyIndustryDefaults(t.key)}
                      className={
                        'text-left p-4 rounded-xl border transition-all ' +
                        (active
                          ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white shadow-md shadow-orange-500/5'
                          : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10 hover:border-white/20')
                      }
                    >
                      <div className="text-sm font-bold mb-1">{t.label}</div>
                      <div className="text-[11px] text-slate-400">{t.blurb}</div>
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
                <Globe className="w-4 h-4 text-cyan-400" /> Country &amp; currency
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    Country <span className="text-rose-400">*</span>
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
                    Currency <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    maxLength={3}
                    placeholder="JOD"
                    className="input-field py-2.5 uppercase"
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                  />
                  <p className="text-[10px] text-slate-500 mt-1">
                    Pre-filled from the country. Override if your reporting currency differs.
                  </p>
                </div>
              </div>
            </div>

            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-purple-400" /> Fiscal &amp; commercial defaults
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    Fiscal year starts
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
                    Tax registration <span className="text-slate-500 font-normal">(optional)</span>
                  </label>
                  <input
                    type="text"
                    placeholder="VAT / Tax ID"
                    className="input-field py-2.5"
                    value={taxRegistrationNumber}
                    onChange={(e) => setTaxRegistrationNumber(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    Default payment terms
                  </label>
                  <select
                    className="input-field py-2.5"
                    value={paymentTerms}
                    onChange={(e) => setPaymentTerms(e.target.value as typeof paymentTerms)}
                  >
                    <option value="cash">Cash on sale</option>
                    <option value="on_delivery">On delivery</option>
                    <option value="net_15">Net 15</option>
                    <option value="net_30">Net 30</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    Pricing mode
                  </label>
                  <select
                    className="input-field py-2.5"
                    value={pricingMode}
                    onChange={(e) => setPricingMode(e.target.value as typeof pricingMode)}
                  >
                    <option value="tax_inclusive">Tax-inclusive (shelf price = paid price)</option>
                    <option value="tax_exclusive">Tax-exclusive (tax shown as line)</option>
                  </select>
                </div>
              </div>
            </div>

            <AdvisorPanel
              lines={[
                `${industryTemplate.label} businesses in ${COUNTRIES.find((c) => c.code === countryCode)?.name ?? 'this country'} typically use ${currency} as their primary currency.`,
                pricingMode === 'tax_inclusive'
                  ? 'Tax-inclusive is the right default for retail and hospitality — the shelf label is the price the customer pays.'
                  : 'Tax-exclusive is the right default for B2B sales — invoices show tax as a separate line and customers can reclaim it.',
              ]}
            />
          </>
        )}

        {step === 2 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-400" /> Locations
              </h2>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setMultiSite(false)}
                  className={
                    'flex-1 p-4 rounded-xl border text-left transition-all ' +
                    (!multiSite
                      ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white'
                      : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')
                  }
                >
                  <div className="font-bold text-sm">Single location</div>
                  <div className="text-[11px] text-slate-400 mt-1">One office, one warehouse, one POS terminal.</div>
                </button>
                <button
                  type="button"
                  onClick={() => setMultiSite(true)}
                  className={
                    'flex-1 p-4 rounded-xl border text-left transition-all ' +
                    (multiSite
                      ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border-orange-500/40 text-white'
                      : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10')
                  }
                >
                  <div className="font-bold text-sm">Multiple branches</div>
                  <div className="text-[11px] text-slate-400 mt-1">Each branch will be created as a child company.</div>
                </button>
              </div>

              {multiSite && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Branches</span>
                    <button
                      type="button"
                      onClick={() => setBranches([...branches, { name: `Branch ${branches.length + 1}`, city: '' }])}
                      className="btn-secondary flex items-center gap-1.5 text-[10px] py-1.5 px-2.5"
                    >
                      <Plus className="w-3 h-3" /> Add branch
                    </button>
                  </div>

                  <div className="space-y-2">
                    {branches.map((b, i) => (
                      <div key={i} className="flex gap-3 items-start bg-white/5 border border-white/8 rounded-xl p-3">
                        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-2">
                          <input
                            type="text"
                            placeholder="Branch name"
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
                            placeholder="City (optional)"
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
                          title="Remove branch"
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
                  ? `Each branch will be created as a child of "${legalName || 'your company'}" in Cycom (res.company.parent_id). Inter-branch transfers and consolidated reporting will work out of the box.`
                  : 'Single-location tenants skip the multi-company setup entirely — everything posts to one company ledger.',
              ]}
            />
          </>
        )}

        {step === 3 && (
          <>
            <div className="glass-card p-6 space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#E67E22]" /> Review
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <ReviewRow label="Legal name" value={legalName || '—'} />
                <ReviewRow label="Short name" value={shortName || '—'} />
                <ReviewRow label="Industry" value={industryTemplate.label} />
                <ReviewRow label="Country" value={COUNTRIES.find((c) => c.code === countryCode)?.name ?? countryCode} />
                <ReviewRow label="Currency" value={currency} />
                <ReviewRow label="Fiscal year starts" value={MONTHS[fiscalYearStartMonth - 1]} />
                <ReviewRow label="Tax registration" value={taxRegistrationNumber || '—'} />
                <ReviewRow label="Payment terms" value={PAYMENT_TERM_LABEL[paymentTerms]} />
                <ReviewRow label="Pricing mode" value={pricingMode === 'tax_inclusive' ? 'Tax-inclusive' : 'Tax-exclusive'} />
                <ReviewRow
                  label="Locations"
                  value={multiSite ? `${branches.length} branches: ${branches.map((b) => b.name).join(', ')}` : 'Single location'}
                />
              </div>

              <div className="bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-4 text-xs text-cyan-200/90 flex items-start gap-3">
                <Sparkles className="w-4 h-4 text-cyan-300 flex-shrink-0 mt-0.5" />
                <div>
                  When you click <strong className="text-white">Apply</strong>, Cycom will create the company (and branches) in Cycom,
                  activate the currency if needed, and persist your industry + commercial defaults so the next setup wizard
                  (Chart of Accounts) inherits them. No manual Cycom configuration is required.
                </div>
              </div>
            </div>

            {result && result.ok && (
              <div className="glass-card p-6 border border-emerald-500/30 bg-emerald-500/5 space-y-3">
                <div className="flex items-center gap-2 text-emerald-300 font-bold">
                  <CheckCircle2 className="w-5 h-5" /> Company configured
                </div>
                <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                  {result.summary.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
                {result.warnings.length > 0 && (
                  <div className="text-[11px] text-amber-300 space-y-1">
                    <div className="font-bold flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" /> Warnings
                    </div>
                    <ul className="list-disc list-inside ml-1">
                      {result.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="pt-2 flex gap-2">
                  <Link href="/setup" className="btn-secondary text-xs py-2 px-3">Continue to next wizard</Link>
                  <Link href="/dashboard" className="btn-primary text-xs py-2 px-3">Go to dashboard</Link>
                </div>
              </div>
            )}

            {result && !result.ok && (
              <div className="glass-card p-6 border border-rose-500/30 bg-rose-500/5 space-y-2">
                <div className="flex items-center gap-2 text-rose-300 font-bold">
                  <AlertTriangle className="w-5 h-5" /> Setup failed
                </div>
                <p className="text-xs text-rose-200">{result.error}</p>
                <p className="text-[10px] text-slate-500">
                  Confirm cycom-platform is running and you're logged in. You can re-run the wizard once the issue is fixed.
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
          <ChevronLeft className="w-4 h-4" /> Back
        </button>

        {step < 3 ? (
          <button
            type="button"
            disabled={!canAdvance}
            onClick={() => setStep((s) => (Math.min(3, s + 1) as StepIdx))}
            className="btn-primary flex items-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next <ChevronRight className="w-4 h-4" />
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
                Applying…
              </>
            ) : result?.ok ? (
              <>
                <CheckCircle2 className="w-4 h-4" /> Applied
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" /> Apply setup
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
  return (
    <div className="glass-card p-5 border border-purple-500/20 bg-purple-500/5">
      <div className="flex items-center gap-2 mb-2">
        <Lightbulb className="w-4 h-4 text-purple-300" />
        <span className="text-xs font-bold uppercase tracking-wider text-purple-200">Cycom AI Recommendation</span>
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
