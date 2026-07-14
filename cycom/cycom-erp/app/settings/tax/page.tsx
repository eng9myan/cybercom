'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ArrowLeft, Percent, Calculator, Globe, FileText, CheckCircle
} from 'lucide-react';

export default function TaxSettings() {
  const router = useRouter();
  const [amount, setAmount] = useState('1000');
  const [vatRate, setVatRate] = useState('0.16');
  const [whtRate, setWhtRate] = useState('0.02');
  const [applyWht, setApplyWht] = useState(true);

  // Result state
  const [calcResult, setCalcResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8888/api/enterprise/tax/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: parseFloat(amount),
          vat_rate: parseFloat(vatRate),
          wht_rate: parseFloat(whtRate),
          apply_wht: applyWht
        })
      });
      if (res.ok) {
        const data = await res.json();
        setCalcResult(data);
      } else {
        alert('Calculation error');
      }
    } catch (err: any) {
      alert('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex items-center gap-4 mb-8">
        <button 
          onClick={() => router.push('/settings')}
          className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
        >
          <ArrowLeft className="w-5 h-5 text-slate-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Global Tax & JoFotara E-Invoicing
          </h1>
          <p className="text-xs text-slate-400 mt-1">Configure VAT, Withholding Tax (WHT), and preview legal e-invoice XML schemas.</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Settings Form */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-2">
            <Percent className="w-4 h-4 text-blue-400" /> Taxation Configuration
          </h3>
          <form onSubmit={handleCalculate} className="space-y-4">
            <div className="space-y-1">
              <label className="text-slate-400">Default VAT Rate (Jordan standard is 0.16)</label>
              <input 
                type="number" step="0.01" value={vatRate} onChange={e => setVatRate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-slate-400">Default WHT Rate (Jordan standard is 0.02)</label>
              <input 
                type="number" step="0.01" value={whtRate} onChange={e => setWhtRate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
              />
            </div>
            <div className="flex items-center gap-2 pt-2">
              <input 
                type="checkbox" id="wht" checked={applyWht} onChange={e => setApplyWht(e.target.checked)}
                className="rounded border-slate-800 bg-slate-950 text-blue-600 focus:ring-0"
              />
              <label htmlFor="wht" className="text-slate-300">Apply Withholding Tax (WHT) deductions</label>
            </div>

            <div className="space-y-1 border-t border-white/5 pt-3">
              <label className="text-slate-400 font-bold block mb-1">Test Transaction Value (JOD)</label>
              <input 
                type="number" value={amount} onChange={e => setAmount(e.target.value)}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none font-bold"
              />
            </div>

            <button 
              type="submit" disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-semibold shadow-lg shadow-blue-600/15 transition flex items-center justify-center gap-2"
            >
              <Calculator className="w-4 h-4" /> Calculate & Format JoFotara XML
            </button>
          </form>
        </div>

        {/* Calculation Result & XML View */}
        <div className="space-y-6">
          {calcResult ? (
            <>
              {/* Totals */}
              <div className="glass-card p-6 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-2">
                  Taxation breakdown
                </h3>
                <div className="space-y-1.5 text-xs font-medium">
                  <div className="flex justify-between"><span className="text-slate-500">Base Amount</span><span className="text-slate-200">{calcResult.base_amount.toFixed(2)} JOD</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">VAT ({calcResult.vat_rate * 100}%)</span><span className="text-slate-200">+{calcResult.vat_amount.toFixed(2)} JOD</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">WHT ({calcResult.wht_rate * 100}%)</span><span className="text-rose-400">-{calcResult.wht_amount.toFixed(2)} JOD</span></div>
                  <div className="flex justify-between border-t border-white/5 pt-2 font-bold text-sm"><span className="text-white">Payable Total</span><span className="text-cyan-400">{calcResult.total_amount.toFixed(2)} JOD</span></div>
                </div>
              </div>

              {/* JoFotara UBL XML */}
              <div className="glass-card p-6 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-2">
                  <FileText className="w-4 h-4 text-emerald-400" /> JoFotara XML Envelope Preview
                </h3>
                <pre className="bg-slate-950 p-4 border border-slate-850 rounded-lg text-[10px] font-mono text-emerald-400 overflow-x-auto select-all max-h-48 whitespace-pre">
                  {calcResult.jofotara_xml}
                </pre>
              </div>
            </>
          ) : (
            <div className="glass-card p-12 text-center text-slate-500">
              Input a transaction value and click calculate to preview taxation values and UBL-compliant invoice envelopes.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
