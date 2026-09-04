'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Building2, Mail, ArrowRight, ArrowLeft, Check, Rocket, Sparkles,
  AlertCircle, Zap,
} from 'lucide-react';
import { useT } from '@/lib/i18n';

// Product this signup provisions. The backend supports many product_codes;
// cycom-erp signs customers up for the Cycom ERP product.
const PRODUCT_CODE = 'cycom';

type Result = {
  tenant_slug?: string;
  invoice_number?: string;
  amount?: string;
  currency?: string;
  due_date?: string;
  trial_ends_at?: string;
  username?: string;
  password?: string;
  realm_name?: string;
  provider?: string;
  checkout?: {
    provider: string;
    mode: string; // "manual" | "redirect" | "client_secret"
    reference?: string;
    url?: string;
    instructions?: Record<string, string>;
    error?: string;
  };
  detail?: string;
  contact_required?: boolean;
};

export default function SignupPage() {
  const t = useT();
  const [step, setStep] = useState(1);
  const [org, setOrg] = useState('');
  const [email, setEmail] = useState('');
  const [locale, setLocale] = useState<'en' | 'ar'>('en');
  const [tier, setTier] = useState('professional');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  const TIERS = [
    { id: 'starter', label: t('signupPage.tierStarterLabel'), desc: t('signupPage.tierStarterDesc'), price: t('signupPage.tierStarterPrice') },
    { id: 'professional', label: t('signupPage.tierProLabel'), desc: t('signupPage.tierProDesc'), price: t('signupPage.tierProPrice') },
    { id: 'enterprise', label: t('signupPage.tierEntLabel'), desc: t('signupPage.tierEntDesc'), price: t('signupPage.tierEntPrice') },
  ];

  async function submit(mode: 'demo' | 'register') {
    setLoading(true);
    setError(null);
    try {
      const body: Record<string, unknown> = { product_code: PRODUCT_CODE, email, org_name: org, locale };
      if (mode === 'register') body.tier = tier;
      const res = await fetch(`/api/cycom/signup/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = (await res.json()) as Result;
      if (!res.ok) throw new Error(data.detail || (data as any).error || `Signup failed (HTTP ${res.status})`);
      setResult(data);
      setStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('signupPage.signupFailed'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#030712] text-white flex flex-col justify-center items-center relative overflow-hidden p-6">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-[#E67E22]/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/3 w-[500px] h-[500px] bg-[#00F0FF]/5 rounded-full blur-[120px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md bg-[#0B0F19] border border-white/5 p-8 rounded-2xl shadow-2xl relative z-10 space-y-6"
      >
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#E67E22] to-[#D35400] flex items-center justify-center shadow-lg shadow-orange-500/20 mx-auto">
            <span className="text-white font-black text-xl">C</span>
          </div>
          <h1 className="text-2xl font-black tracking-wide">{t('signupPage.title')}</h1>
          <p className="text-[10px] text-[#E67E22] uppercase tracking-widest font-bold">{t('signupPage.subtitle')}</p>
        </div>

        {/* Step dots */}
        <div className="flex items-center gap-2">
          {[1, 2, 3].map((s, i) => (
            <React.Fragment key={s}>
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border transition shrink-0 ${
                step > s ? 'bg-[#E67E22] border-[#E67E22]' : step === s ? 'border-[#E67E22] text-[#E67E22]' : 'border-white/15 text-white/30'
              }`}>
                {step > s ? <Check className="w-3.5 h-3.5" /> : s}
              </div>
              {i < 2 && <div className="flex-1 h-px bg-white/10" />}
            </React.Fragment>
          ))}
        </div>

        {error && (
          <div className="flex items-start gap-2 p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /><span>{error}</span>
          </div>
        )}

        {/* Step 1 — Organization */}
        {step === 1 && (
          <form
            onSubmit={(e) => { e.preventDefault(); if (org && email) setStep(2); }}
            className="space-y-4"
          >
            <div>
              <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">{t('signupPage.orgNameLabel')}</label>
              <div className="relative">
                <Building2 className="w-4 h-4 absolute start-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input required value={org} onChange={(e) => setOrg(e.target.value)} placeholder={t('signupPage.orgNamePh')}
                  className="input-field w-full !ps-10" />
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">{t('signupPage.workEmailLabel')}</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute start-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t('signupPage.workEmailPh')}
                  className="input-field w-full !ps-10" autoComplete="email" dir="ltr" />
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">{t('signupPage.languageLabel')}</label>
              <select value={locale} onChange={(e) => setLocale(e.target.value as 'en' | 'ar')} className="input-field w-full">
                <option value="en">English</option>
                <option value="ar">العربية</option>
              </select>
            </div>
            <button className="btn-primary w-full flex items-center justify-center gap-2" disabled={!org || !email}>
              {t('signupPage.continueLabel')} <ArrowRight className="w-4 h-4 rtl:-scale-x-100" />
            </button>
          </form>
        )}

        {/* Step 2 — Plan */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="space-y-2">
              {TIERS.map((tr) => (
                <button key={tr.id} onClick={() => setTier(tr.id)}
                  className={`w-full text-start rounded-xl border p-3 transition ${
                    tier === tr.id ? 'border-[#E67E22] bg-[#E67E22]/10' : 'border-white/10 bg-white/5 hover:border-white/25'
                  }`}>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm">{tr.label}</span>
                    <span className="text-xs text-[#E67E22] font-semibold">{tr.price}</span>
                  </div>
                  <div className="text-xs text-white/50 mt-0.5">{tr.desc}</div>
                </button>
              ))}
            </div>

            <button onClick={() => submit('register')} disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
              {loading ? t('signupPage.creating') : <>{t('signupPage.createWorkspace')} <Rocket className="w-4 h-4" /></>}
            </button>

            <div className="flex items-center gap-3 text-white/30 text-xs">
              <div className="flex-1 h-px bg-white/10" /> {t('signupPage.orDivider')} <div className="flex-1 h-px bg-white/10" />
            </div>

            <button onClick={() => submit('demo')} disabled={loading}
              className="btn-secondary w-full flex items-center justify-center gap-2 disabled:opacity-50">
              <Zap className="w-4 h-4 text-[#00F0FF]" /> {t('signupPage.tryTrial')}
            </button>

            <button onClick={() => setStep(1)} className="w-full text-xs text-white/40 hover:text-white/70 flex items-center justify-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5 rtl:-scale-x-100" /> {t('signupPage.back')}
            </button>
          </div>
        )}

        {/* Step 3 — Result */}
        {step === 3 && result && (
          <div className="space-y-5">
            <div className="text-center space-y-1">
              <div className="w-12 h-12 mx-auto rounded-full bg-[#10B981]/15 border border-[#10B981]/30 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-[#10B981]" />
              </div>
              <h2 className="text-lg font-black">{t('signupPage.workspaceCreated')}</h2>
              <p className="text-xs text-white/50">{t('signupPage.tenantLabel')} <span className="font-mono text-white/80">{result.tenant_slug}</span></p>
            </div>

            <div className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-2 text-sm">
              {result.username && (
                <div className="flex justify-between"><span className="text-white/50">{t('signupPage.username')}</span><span className="font-mono">{result.username}</span></div>
              )}
              {result.password && (
                <div className="flex justify-between"><span className="text-white/50">{t('signupPage.password')}</span><span className="font-mono">{result.password}</span></div>
              )}
              {result.trial_ends_at && (
                <div className="flex justify-between"><span className="text-white/50">{t('signupPage.trialEnds')}</span><span>{new Date(result.trial_ends_at).toLocaleString()}</span></div>
              )}
              {result.invoice_number && (
                <>
                  <div className="flex justify-between"><span className="text-white/50">{t('signupPage.invoice')}</span><span className="font-mono">{result.invoice_number}</span></div>
                  <div className="flex justify-between"><span className="text-white/50">{t('signupPage.amountDue')}</span><span className="font-semibold">{result.amount} {result.currency}</span></div>
                  {result.due_date && <div className="flex justify-between"><span className="text-white/50">{t('signupPage.due')}</span><span>{new Date(result.due_date).toLocaleDateString()}</span></div>}
                </>
              )}
            </div>

            {/* Payment step — rendered from the provider-agnostic checkout the
                register endpoint returns. manual = bank instructions; redirect =
                send the browser to the gateway. */}
            {result.checkout && result.checkout.mode === 'manual' && (
              <div className="rounded-xl border border-[#00F0FF]/25 bg-[#00F0FF]/[0.04] p-4 space-y-2 text-sm">
                <div className="font-bold text-[#00F0FF] text-xs uppercase tracking-wider">{t('signupPage.payByBank')}</div>
                {Object.entries(result.checkout.instructions || {}).map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-4">
                    <span className="text-white/50 capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className="font-mono text-right break-all">{String(v)}</span>
                  </div>
                ))}
                <p className="text-xs text-white/40 pt-1">{t('signupPage.bankTransferNote')}</p>
              </div>
            )}

            {result.checkout && result.checkout.mode === 'redirect' && result.checkout.url && (
              <button
                onClick={() => { window.location.href = result.checkout!.url!; }}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {t('signupPage.payNow', { amount: result.amount ?? '', currency: result.currency ?? '' })} <ArrowRight className="w-4 h-4 rtl:-scale-x-100" />
              </button>
            )}

            <Link href="/login" className="btn-secondary w-full flex items-center justify-center gap-2">
              {t('signupPage.goToLogin')} <ArrowRight className="w-4 h-4 rtl:-scale-x-100" />
            </Link>
          </div>
        )}

        {step !== 3 && (
          <p className="text-center text-xs text-white/40">
            {t('signupPage.alreadyHaveWorkspace')}{' '}
            <Link href="/login" className="text-[#E67E22] font-semibold hover:underline">{t('signupPage.signIn')}</Link>
          </p>
        )}
      </motion.div>
    </div>
  );
}
