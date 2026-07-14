'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ArrowLeft, Search, RefreshCw, FileText, CheckCircle2, 
  HelpCircle, AlertCircle, Percent, Sparkles, Brain
} from 'lucide-react';

export default function AIReconciliation() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  // Mock bank statement lines
  const [bankLines, setBankLines] = useState([
    { id: 101, description: 'CYCOM SWEETS AMMAN', amount: 1500.00 },
    { id: 102, description: 'HABIB CO JOD', amount: 850.50 },
    { id: 103, description: 'MISC CASH DEPOSIT', amount: 200.00 }
  ]);

  // Mock open invoices
  const [invoices, setInvoices] = useState([
    { id: 201, number: 'INV/2026/0043', partner_name: 'Cycom Sweets', amount_total: 1500.00 },
    { id: 202, number: 'INV/2026/0044', partner_name: 'Habib & Sons', amount_total: 850.50 },
    { id: 203, number: 'INV/2026/0045', partner_name: 'Al-Masri Trading', amount_total: 620.00 }
  ]);

  const handleRunReconciliation = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8888/api/enterprise/reconcile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bank_lines: bankLines,
          open_invoices: invoices
        })
      });
      if (res.ok) {
        const data = await res.json();
        setResults(data.matches || []);
      }
    } catch {
      alert('Reconciliation matching failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      {/* Header */}
      <div className="max-w-5xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/accounting')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-indigo-400" /> AI-Powered Bank Reconciliation
            </h1>
            <p className="text-xs text-slate-400 mt-1">Automatically match bank statement items to outstanding customer/supplier invoices using NLP string similarity.</p>
          </div>
        </div>

        <button 
          onClick={handleRunReconciliation}
          disabled={loading}
          className="btn-primary flex items-center gap-2"
        >
          <Brain className="w-4 h-4" /> Run AI Matching Engine
        </button>
      </div>

      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Bank Lines */}
        <div className="glass-card p-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 border-b border-white/5 pb-2">
            Bank Statement Entries
          </h3>
          <div className="space-y-2">
            {bankLines.map(l => (
              <div key={l.id} className="p-3 bg-slate-950/40 border border-slate-850 rounded-xl flex justify-between items-center">
                <div>
                  <div className="font-semibold text-slate-300">{l.description}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Line ID: {l.id}</div>
                </div>
                <div className="font-mono text-slate-200 font-bold">{l.amount.toFixed(2)} JOD</div>
              </div>
            ))}
          </div>
        </div>

        {/* Invoices */}
        <div className="glass-card p-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 border-b border-white/5 pb-2">
            Outstanding Accounts Receivable
          </h3>
          <div className="space-y-2">
            {invoices.map(i => (
              <div key={i.id} className="p-3 bg-slate-950/40 border border-slate-850 rounded-xl flex justify-between items-center">
                <div>
                  <div className="font-semibold text-slate-300">{i.partner_name}</div>
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5">{i.number}</div>
                </div>
                <div className="font-mono text-slate-200 font-bold">{i.amount_total.toFixed(2)} JOD</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Results grid */}
      {results.length > 0 && (
        <div className="max-w-5xl mx-auto glass-card p-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 border-b border-white/5 pb-2">
            Reconciliation Recommendations
          </h3>
          <div className="overflow-x-auto">
            <table className="data-table w-full text-left">
              <thead>
                <tr className="border-b border-white/5 text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  <th className="pb-3">Bank Line ID</th>
                  <th className="pb-3">Matched Invoice</th>
                  <th className="pb-3">Partner Name</th>
                  <th className="pb-3">Amount</th>
                  <th className="pb-3">AI Confidence Score</th>
                  <th className="pb-3">Matching Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {results.map((r, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.01]">
                    <td className="py-3 font-mono text-slate-400">{r.statement_line_id}</td>
                    <td className="py-3 font-mono text-slate-200 font-bold">{r.invoice_number || '—'}</td>
                    <td className="py-3 text-slate-300">{r.partner_name || '—'}</td>
                    <td className="py-3 font-mono text-slate-200 font-semibold">{r.amount.toFixed(2)} JOD</td>
                    <td className="py-3 font-semibold text-slate-300">
                      {r.confidence_score > 0 ? (
                        <div className="flex items-center gap-1">
                          <div className="w-12 h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500" style={{ width: `${r.confidence_score * 100}%` }}></div>
                          </div>
                          <span className="font-mono">{(r.confidence_score * 100).toFixed(0)}%</span>
                        </div>
                      ) : '—'}
                    </td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                        r.status === 'matched' 
                          ? 'bg-emerald-950/40 text-emerald-400 border-emerald-500/20' 
                          : r.status === 'suggested' 
                            ? 'bg-amber-950/40 text-amber-400 border-amber-500/20 animate-pulse' 
                            : 'bg-slate-800 text-slate-400 border-slate-700/50'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
