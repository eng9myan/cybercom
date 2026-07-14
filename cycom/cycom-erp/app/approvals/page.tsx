'use client';

import React, { useState, useEffect } from 'react';
import { Check, X, Shield, FileText, ShoppingCart, Loader2 } from 'lucide-react';
import { CyGlassCard } from '@/components/CyGlassCard';

interface HITLAction {
  id: number;
  type: 'purchase_order' | 'journal_entry';
  title: string;
  description: string;
  tenant_id: number;
  company_id: number;
  payload: any;
}

export default function ApprovalsPage() {
  const [actions, setActions] = useState<HITLAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueue = async () => {
    try {
      const res = await fetch('/api/cycom/hitl/queue');
      if (!res.ok) {
        throw new Error('Failed to fetch approval queue');
      }
      const data = await res.json();
      setActions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleApprove = async (id: number) => {
    try {
      const res = await fetch(`/api/cycom/hitl/approve/${id}`, { method: 'POST' });
      if (!res.ok) throw new Error('Approval request failed');
      setActions((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      alert('Failed to approve draft action.');
    }
  };

  const handleReject = async (id: number) => {
    try {
      const res = await fetch(`/api/cycom/hitl/reject/${id}`, { method: 'POST' });
      if (!res.ok) throw new Error('Rejection request failed');
      setActions((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      alert('Failed to reject action.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="page-title text-white">Autonomous Approval Queue</h1>
          <p className="page-subtitle">
            CFO Human-in-the-Loop review terminal for AI-suggested supply chain buffers and financial adjustments.
          </p>
        </div>
        <span className="badge badge-purple flex items-center gap-1.5 px-3 py-1 text-xs">
          <Shield className="w-3.5 h-3.5" /> Human-in-the-Loop Enabled
        </span>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-[#A855F7]" />
          <span className="text-sm">Fetching queue from Cycom Micro-Kernel...</span>
        </div>
      )}

      {error && (
        <div className="glass-card p-6 border border-rose-500/30 bg-rose-500/5 text-sm text-center">
          <p className="text-rose-300 font-semibold mb-1">Queue Synchronisation Error</p>
          <p className="text-rose-400/80 text-xs">{error}</p>
          <p className="text-slate-500 text-[10px] mt-2">Confirm the micro-kernel backend is running.</p>
        </div>
      )}

      {!loading && !error && actions.length === 0 && (
        <div className="glass-card py-20 text-center text-slate-500 text-sm border border-dashed border-white/10">
          <p className="font-semibold text-slate-400">All Clear</p>
          <p className="text-xs text-slate-500 mt-1">No autonomous actions pending CFO approval.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {actions.map((act) => (
          <CyGlassCard
            key={act.id}
            className="border-purple-500/10 hover:border-purple-500/20 flex flex-col justify-between h-full bg-[#0A0E1A]/80"
          >
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div
                  className={`
                    p-2.5 rounded-xl border
                    ${
                      act.type === 'purchase_order'
                        ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    }
                  `}
                >
                  {act.type === 'purchase_order' ? (
                    <ShoppingCart className="w-5 h-5" />
                  ) : (
                    <FileText className="w-5 h-5" />
                  )}
                </div>
                <div>
                  <h3 className="text-base font-bold text-white leading-tight">{act.title}</h3>
                  <span className="text-[9px] font-mono font-bold text-slate-500 uppercase tracking-wider block mt-1">
                    Tenant #{act.tenant_id} · Company #{act.company_id}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed mb-6">{act.description}</p>
            </div>

            <div className="flex gap-3 border-t border-white/5 pt-4 mt-auto">
              <button
                onClick={() => handleApprove(act.id)}
                className="btn-primary flex-1 py-2 flex items-center justify-center gap-1.5 text-xs bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg"
              >
                <Check className="w-4 h-4" /> Approve Draft
              </button>
              <button
                onClick={() => handleReject(act.id)}
                className="
                  btn-secondary flex-1 py-2 flex items-center justify-center gap-1.5 text-xs
                  text-rose-400 border border-rose-500/10 hover:border-rose-500/25 hover:bg-rose-500/5 font-semibold rounded-lg
                "
              >
                <X className="w-4 h-4" /> Reject & Discard
              </button>
            </div>
          </CyGlassCard>
        ))}
      </div>
    </div>
  );
}
