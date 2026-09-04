'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Calculator, Globe, Percent, Layers, Wrench } from 'lucide-react';
import { COUNTRIES } from '@/lib/setup/industry-templates';
import { COA_COUNTRY_TEMPLATES, getCoaTemplate } from '@/lib/setup/coa-templates';
import { applyCoaSetup, fetchTenantPrefs } from '@/lib/setup/coaSetup';
import { StepIndicator } from '@/components/setup/StepIndicator';
import { WizardFooter } from '@/components/setup/WizardFooter';
import { AdvisorPanel } from '@/components/setup/AdvisorPanel';
import { ReviewRow } from '@/components/setup/ReviewRow';
import { ResultBanner } from '@/components/setup/ResultBanner';
import { useT } from '@/lib/i18n';

type StepIdx = 0 | 1 | 2;

export default function CoaWizard() {
  const t = useT();
  const STEPS = [t('setupCoa.localizationHeading'), t('setupCoa.taxHeading'), t('setupWizard.stepReview')] as const;
  const [step, setStep] = useState<StepIdx>(0);

  const [countryCode, setCountryCode] = useState('JO');
  const [l10nModule, setL10nModule] = useState('l10n_jo');
  const [salesTaxPct, setSalesTaxPct] = useState(16);
  const [purchaseTaxPct, setPurchaseTaxPct] = useState(16);
  const [prefsLoaded, setPrefsLoaded] = useState(false);

  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState<
    | { ok: true; summary: string[]; warnings: string[]; l10nModule: string; moduleId: number | null }
    | { ok: false; error: string; warnings?: string[] }
    | null
  >(null);

  // Inherit defaults from Company Setup
  useEffect(() => {
    fetchTenantPrefs()
      .then((prefs) => {
        if (prefs.countryCode) {
          setCountryCode(prefs.countryCode);
          const tmpl = getCoaTemplate(prefs.countryCode);
          setL10nModule(tmpl.l10nModule);
          setSalesTaxPct(tmpl.defaultSalesTaxPct);
          setPurchaseTaxPct(tmpl.defaultPurchaseTaxPct);
        }
      })
      .finally(() => setPrefsLoaded(true));
  }, []);

  const template = useMemo(() => getCoaTemplate(countryCode), [countryCode]);

  const onCountryChange = (code: string) => {
    setCountryCode(code);
    const tmpl = getCoaTemplate(code);
    setL10nModule(tmpl.l10nModule);
    setSalesTaxPct(tmpl.defaultSalesTaxPct);
    setPurchaseTaxPct(tmpl.defaultPurchaseTaxPct);
  };

  const submit = async () => {
    setApplying(true);
    setResult(null);
    try {
      setResult(await applyCoaSetup({ countryCode, l10nModule, salesTaxPct, purchaseTaxPct }));
    } catch (e) {
      setResult({ ok: false, error: e instanceof Error ? e.message : 'Setup failed' });
    } finally {
      setApplying(false);
    }
  };

  const canAdvance = (() => {
    if (step === 0) return Boolean(countryCode && l10nModule.trim());
    if (step === 1) return salesTaxPct >= 0 && purchaseTaxPct >= 0;
    return true;
  })();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white flex items-center gap-3">
            <Calculator className="w-7 h-7 text-[#E67E22]" />
            {t('setupCoa.title')}
          </h1>
          <p className="page-subtitle">
            {t('setupCoa.subtitle')}
          </p>
        </div>
        <a
          href="/cycom/cycom/action-account.action_account_form"
          target="_blank"
          rel="noreferrer"
          className="btn-secondary flex items-center gap-2 text-xs"
          title="Drop into the raw Cycom Accounts configuration page"
        >
          <Wrench className="w-3.5 h-3.5" /> {t('setupWizard.configureManually')}
        </a>
      </div>

      <StepIndicator steps={STEPS} current={step} />

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
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Globe className="w-4 h-4 text-cyan-400" /> {t('setupCoa.localizationHeading')}
              </h2>

              {!prefsLoaded && (
                <p className="text-[11px] text-slate-500">{t('setupCoa.loadingPrefs')}</p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">{t('setupCoa.country')}</label>
                  <select
                    className="input-field py-2.5"
                    value={countryCode}
                    onChange={(e) => onCountryChange(e.target.value)}
                  >
                    {COUNTRIES.map((c) => (
                      <option key={c.code} value={c.code}>
                        {c.name} {COA_COUNTRY_TEMPLATES[c.code] ? t('setupCoa.dedicatedChart') : t('setupCoa.genericChart')}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCoa.l10nModule')}
                  </label>
                  <input
                    type="text"
                    className="input-field py-2.5 font-mono"
                    value={l10nModule}
                    onChange={(e) => setL10nModule(e.target.value)}
                    dir="ltr"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">
                    {t('setupCoa.l10nModuleNote')}
                  </p>
                </div>
              </div>
            </div>

            <AdvisorPanel
              lines={[
                template.advisor,
                t('setupCoa.localizationAdvisorNote1'),
                t('setupCoa.localizationAdvisorNote2'),
              ]}
            />
          </>
        )}

        {step === 1 && (
          <>
            <div className="glass-card p-6 space-y-5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Percent className="w-4 h-4 text-emerald-400" /> {t('setupCoa.taxHeading')}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCoa.salesVat')}
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min={0}
                    max={50}
                    className="input-field py-2.5"
                    value={salesTaxPct}
                    onChange={(e) => setSalesTaxPct(parseFloat(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">
                    {t('setupCoa.purchaseVat')}
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min={0}
                    max={50}
                    className="input-field py-2.5"
                    value={purchaseTaxPct}
                    onChange={(e) => setPurchaseTaxPct(parseFloat(e.target.value) || 0)}
                  />
                </div>
              </div>

              <p className="text-[11px] text-slate-500">
                {t('setupCoa.taxMatrixNote')}
              </p>
            </div>

            <AdvisorPanel
              lines={[
                t('setupCoa.taxAdvisor', { country: COUNTRIES.find((c) => c.code === countryCode)?.name ?? countryCode, rate: template.defaultSalesTaxPct }),
                salesTaxPct === 0 && purchaseTaxPct === 0
                  ? t('setupCoa.zeroTaxNote')
                  : t('setupCoa.exportTaxNote'),
              ]}
            />
          </>
        )}

        {step === 2 && (
          <>
            <div className="glass-card p-6 space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#E67E22]" /> {t('setupWizard.stepReview')}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <ReviewRow label={t('setupCoa.reviewCountry')} value={COUNTRIES.find((c) => c.code === countryCode)?.name ?? countryCode} />
                <ReviewRow label={t('setupCoa.reviewL10nModule')} value={l10nModule} />
                <ReviewRow label={t('setupCoa.reviewSalesVat')} value={`${salesTaxPct}%`} />
                <ReviewRow label={t('setupCoa.reviewPurchaseVat')} value={`${purchaseTaxPct}%`} />
              </div>

              <p className="text-[11px] text-slate-500">
                {t('setupCoa.applyNote')}
              </p>
            </div>

            {result && <ResultBanner result={result} />}
          </>
        )}
      </motion.div>

      <WizardFooter
        step={step}
        totalSteps={STEPS.length}
        canAdvance={canAdvance}
        applying={applying}
        applied={Boolean(result?.ok)}
        onBack={() => setStep((s) => (Math.max(0, s - 1) as StepIdx))}
        onNext={() => setStep((s) => (Math.min(STEPS.length - 1, s + 1) as StepIdx))}
        onApply={submit}
        applyLabel={t('setupCoa.applyLabel')}
      />
    </div>
  );
}
