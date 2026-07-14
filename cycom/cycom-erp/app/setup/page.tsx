'use client';

import React, { useState } from 'react';
import { ArrowRight, Check, Loader2 } from 'lucide-react';
import { CyGlassCard } from '@/components/CyGlassCard';

export default function SetupWizard() {
  const [step, setStep] = useState(1);
  const [companyName, setCompanyName] = useState('');
  const [vertical, setVertical] = useState('manufacturing');
  const [region, setRegion] = useState('JO');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const res = await fetch('/api/cycom/setup/bootstrap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: companyName,
          vertical,
          region,
        }),
      });

      if (res.ok) {
        setSuccess(true);
      } else {
        alert('Setup failed to provision database tables and schemas.');
      }
    } catch {
      alert('Failed to connect to bootstrapping API server.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-6 pt-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white mb-2">Cycom Setup Wizard</h1>
        <p className="text-xs text-slate-400">
          Onboard your B2B enterprise company, config ledgers, and seed compliance matrices.
        </p>
      </div>

      <CyGlassCard className="bg-[#0C0F19]/80 border-purple-500/10">
        {success ? (
          <div className="text-center py-6 space-y-4">
            <div className="w-12 h-12 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full flex items-center justify-center mx-auto">
              <Check className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white">System Provisioned Successfully!</h3>
            <p className="text-xs text-slate-400 leading-relaxed max-w-sm mx-auto">
              Dynamic B2B apps, chart of accounts, ESG ledger databases, and local fiscal compliance configurations have been bootstrapped and seeded.
            </p>
            <div className="pt-2">
              <a
                href="/approvals"
                className="inline-flex items-center gap-2 text-xs text-purple-400 hover:text-purple-300 font-semibold transition-colors"
              >
                Go to Approvals Queue <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {step === 1 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-2">
                    Company Legal Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Cycom Advanced Materials Ltd."
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="
                      w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3
                      text-sm text-white outline-none focus:border-purple-500/40 transition-colors
                    "
                  />
                </div>
                <button
                  disabled={!companyName.trim()}
                  onClick={() => setStep(2)}
                  className="
                    w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50
                    text-white font-semibold text-sm rounded-xl flex items-center justify-center gap-2 transition-all
                  "
                >
                  Continue <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-2">
                    Industry Vertical
                  </label>
                  <select
                    value={vertical}
                    onChange={(e) => setVertical(e.target.value)}
                    className="
                      w-full bg-[#0A0D16] border border-white/10 rounded-xl px-4 py-3
                      text-sm text-white outline-none focus:border-purple-500/40 transition-colors
                    "
                  >
                    <option value="manufacturing">Manufacturing & Assembly (MRP, ESG Carbon Ledger)</option>
                    <option value="law">Legal & Professional Services (Projects, Timesheets)</option>
                    <option value="education">Schools & Educational Institutes (Administration, CRM)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-2">
                    Primary Region (Fiscal Compliance Model)
                  </label>
                  <select
                    value={region}
                    onChange={(e) => setRegion(e.target.value)}
                    className="
                      w-full bg-[#0A0D16] border border-white/10 rounded-xl px-4 py-3
                      text-sm text-white outline-none focus:border-purple-500/40 transition-colors
                    "
                  >
                    <option value="JO">Jordan (JoFotara ISTD E-Invoicing)</option>
                    <option value="SA">Saudi Arabia (ZATCA Phase 2 E-Invoicing)</option>
                    <option value="US">United States / Europe (Peppol BIS UBL XML)</option>
                  </select>
                </div>

                <div className="flex gap-4 pt-2">
                  <button
                    onClick={() => setStep(1)}
                    className="
                      flex-1 py-3 border border-white/10 rounded-xl text-sm font-semibold
                      text-slate-300 hover:bg-white/5 transition-all
                    "
                  >
                    Back
                  </button>
                  <button
                    disabled={isSubmitting}
                    onClick={handleSubmit}
                    className="
                      flex-1 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50
                      text-white font-semibold text-sm rounded-xl flex items-center justify-center gap-2 transition-all
                    "
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" /> Provisioning...
                      </>
                    ) : (
                      'Complete Setup'
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </CyGlassCard>
    </div>
  );
}
