'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCycomList, m2oName, fmtDate, type Many2One } from '@/lib/cycomModels';
import { 
  ShieldAlert, Plus, Trash2, CheckCircle2, AlertTriangle, 
  RefreshCw, Clipboard, CheckCircle, XCircle
} from 'lucide-react';

interface QualityCheck {
  id: string;
  productName: string;
  sku: string;
  parameter: 'Seal Test' | 'Weight Check' | 'Acidity / Purity' | 'Label Accuracy';
  inspector: string;
  dateChecked: string;
  status: 'Pending' | 'Passed' | 'Failed';
  notes: string;
}

type CycomQualityCheck = {
  id: number;
  name?: string;
  product_id?: Many2One;
  picking_id?: Many2One;
  quality_state?: string;
  create_date?: string;
};

const QUALITY_STATE_MAP: Record<string, QualityCheck['status']> = {
  pass: 'Passed', fail: 'Failed', none: 'Pending',
};

const mapQualityCheck = (r: CycomQualityCheck): QualityCheck => ({
  id: r.name || `QL-${r.id}`,
  productName: m2oName(r.product_id, '—'),
  sku: '—',
  parameter: 'Seal Test',
  inspector: '—',
  dateChecked: fmtDate(r.create_date),
  status: QUALITY_STATE_MAP[r.quality_state ?? ''] ?? 'Pending',
  notes: '',
});

export default function QualityPage() {
  const { rows: liveChecks, loading } = useCycomList<CycomQualityCheck, QualityCheck>(
    'quality.check', [], ['name', 'product_id', 'picking_id', 'quality_state', 'create_date'],
    mapQualityCheck,
  );
  const [checks, setChecks] = useState<QualityCheck[]>([]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setChecks(liveChecks); }, [loading]);

  // New check form
  const [product, setProduct] = useState('Premium Olive Oil 1L');
  const [param, setParam] = useState<'Seal Test' | 'Weight Check' | 'Acidity / Purity' | 'Label Accuracy'>('Seal Test');
  const [inspector, setInspector] = useState('Khaled Jaber');
  const [notes, setNotes] = useState('');
  const [status, setStatus] = useState<'Pending' | 'Passed' | 'Failed'>('Pending');

  const handleCreateCheck = (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes) return;

    const newCheck: QualityCheck = {
      id: `QL-${Math.floor(904 + Math.random() * 90)}`,
      productName: product,
      sku: product === 'Premium Olive Oil 1L' ? 'OLIVE-OIL-1L' : 'MILK-POW-400G',
      parameter: param,
      inspector: inspector,
      dateChecked: new Date().toISOString().split('T')[0],
      status: status,
      notes: notes
    };

    setChecks([newCheck, ...checks]);
    setNotes('');
  };

  const handlePassCheck = (id: string) => {
    setChecks(checks.map(c => c.id === id ? { ...c, status: 'Passed' } : c));
  };

  const handleFailCheck = (id: string) => {
    setChecks(checks.map(c => c.id === id ? { ...c, status: 'Failed' } : c));
  };

  const handleDeleteCheck = (id: string) => {
    setChecks(checks.filter(c => c.id !== id));
  };

  // Stats
  const totalChecked = checks.filter(c => c.status !== 'Pending').length;
  const passedCount = checks.filter(c => c.status === 'Passed').length;
  const passRate = totalChecked > 0 ? Math.round((passedCount / totalChecked) * 100) : 100;

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Quality Control (QC)</h1>
          <p className="page-subtitle">Standard Cycom Quality Control Points. Record batch audit checklists, inspect items, and monitor validation rates.</p>
        </div>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Audits</span>
            <p className="text-2xl font-black text-white">{checks.length} checks</p>
          </div>
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400">
            <Clipboard className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">QC Pass Rate</span>
            <p className="text-2xl font-black text-[#10B981]">{passRate}%</p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Failed Audits</span>
            <p className="text-2xl font-black text-[#EF4444]">
              {checks.filter(c => c.status === 'Failed').length} batches
            </p>
          </div>
          <div className="p-3 rounded-xl bg-red-500/10 text-red-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Pending Checks</span>
            <p className="text-2xl font-black text-[#F59E0B]">
              {checks.filter(c => c.status === 'Pending').length} audits
            </p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
            <RefreshCw className="w-5 h-5 animate-spin-slow" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - Form */}
        <div className="glass-card p-5 space-y-4 h-fit">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Record Quality Audit Check</h2>
            <Plus className="w-4 h-4 text-[#EF4444]" />
          </div>

          <form onSubmit={handleCreateCheck} className="space-y-3 text-xs">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Product Item</label>
              <select value={product} onChange={e => setProduct(e.target.value)} className="input-field">
                <option value="Premium Olive Oil 1L">Premium Olive Oil 1L</option>
                <option value="Cycom Milk Powder 400g">Cycom Milk Powder 400g</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Parameter Test</label>
                <select value={param} onChange={e => setParam(e.target.value as any)} className="input-field">
                  <option value="Seal Test">Seal Integrity</option>
                  <option value="Weight Check">Weight Tolerance</option>
                  <option value="Acidity / Purity">Acidity / Purity</option>
                  <option value="Label Accuracy">Label Accuracy</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Inspector</label>
                <select value={inspector} onChange={e => setInspector(e.target.value)} className="input-field">
                  <option value="Khaled Jaber">Khaled Jaber</option>
                  <option value="Ahmad Masri">Ahmad Masri</option>
                  <option value="Rami Khasawneh">Rami Khasawneh</option>
                </select>
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Audit Result Status</label>
              <select value={status} onChange={e => setStatus(e.target.value as any)} className="input-field font-semibold text-emerald-400">
                <option value="Pending" className="text-amber-400">Pending</option>
                <option value="Passed" className="text-emerald-400">Passed (Pass)</option>
                <option value="Failed" className="text-red-400">Failed (Fail)</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Inspection Notes</label>
              <input 
                type="text" 
                required 
                placeholder="Log physical measurement values..." 
                value={notes}
                onChange={e => setNotes(e.target.value)}
                className="input-field"
              />
            </div>
            <button type="submit" className="btn-primary w-full py-2">
              Log QC Audit Point
            </button>
          </form>
        </div>

        {/* Right Column - Audits grid list */}
        <div className="lg:col-span-2 glass-card p-5 space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">Quality Control Logs</h2>
          <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
            {checks.map(c => (
              <div key={c.id} className="p-4 rounded-xl bg-white/3 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-black text-white">{c.id}</span>
                    <span className="text-[10px] text-slate-500">{c.dateChecked}</span>
                    <span className="text-[9px] bg-white/5 px-2 py-0.2 rounded border border-white/10 text-slate-400 font-bold uppercase">{c.parameter}</span>
                    <span className={`badge text-[9px] ${
                      c.status === 'Passed' ? 'badge-green' :
                      c.status === 'Failed' ? 'badge-red' : 'badge-yellow'
                    }`}>{c.status}</span>
                  </div>
                  <p className="text-xs text-slate-200 font-bold">{c.productName}</p>
                  <p className="text-[11px] text-slate-400 leading-normal">Inspector: <strong>{c.inspector}</strong> · Detail: {c.notes}</p>
                </div>

                <div className="flex gap-1.5 flex-shrink-0">
                  {c.status === 'Pending' && (
                    <>
                      <button 
                        onClick={() => handlePassCheck(c.id)}
                        className="p-1 px-2 text-[10px] font-bold rounded bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/25 text-[#10B981] flex items-center gap-1"
                      >
                        <CheckCircle className="w-3.5 h-3.5" /> Pass
                      </button>
                      <button 
                        onClick={() => handleFailCheck(c.id)}
                        className="p-1 px-2 text-[10px] font-bold rounded bg-red-500/10 hover:bg-red-500/20 border border-red-500/25 text-[#EF4444] flex items-center gap-1"
                      >
                        <XCircle className="w-3.5 h-3.5" /> Fail
                      </button>
                    </>
                  )}
                  <button 
                    onClick={() => handleDeleteCheck(c.id)}
                    className="p-1 rounded hover:bg-red-500/20 text-[#EF4444]"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
