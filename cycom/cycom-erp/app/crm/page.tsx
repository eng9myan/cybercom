'use client';

import React, { useEffect, useState } from 'react';
import {
  DollarSign, Plus, ArrowRight, ArrowLeft, Trash2,
  Sparkles, Star, Award,
} from 'lucide-react';
import { searchRead, create, write, unlink } from '@/lib/cycom';
import { fmtCode, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';

interface LeadCard {
  id: string;
  rawId: number;
  clientName: string;
  expectedRevenue: number;
  probability: number;
  stage: 'New' | 'Qualified' | 'Proposition' | 'Won' | 'Lost';
  contact: string;
}

type CycomLead = {
  id: number;
  partner_name?: string | false;
  contact_name?: string | false;
  expected_revenue?: number;
  probability?: number;
  stage_id?: Many2One;
  email_from?: string | false;
};

const STAGES: Array<'New' | 'Qualified' | 'Proposition' | 'Won' | 'Lost'> = [
  'New', 'Qualified', 'Proposition', 'Won', 'Lost',
];

const STAGE_BG_STYLES = {
  New: 'border-slate-500/25 bg-slate-500/3',
  Qualified: 'border-cyan-500/25 bg-cyan-500/3',
  Proposition: 'border-purple-500/25 bg-purple-500/3',
  Won: 'border-emerald-500/25 bg-emerald-500/3',
  Lost: 'border-red-500/25 bg-red-500/3',
};

function cycomStageToCycom(cycomStage: string): LeadCard['stage'] {
  const s = cycomStage.toLowerCase();
  if (s.includes('won')) return 'Won';
  if (s.includes('lost') || s.includes('dead')) return 'Lost';
  if (s.includes('propos') || s.includes('quot')) return 'Proposition';
  if (s.includes('qualif')) return 'Qualified';
  return 'New';
}

function mapLead(r: CycomLead): LeadCard {
  return {
    rawId: r.id,
    id: fmtCode('LD', r.id, 3),
    clientName: (r.partner_name as string) || (r.contact_name as string) || `Lead ${r.id}`,
    expectedRevenue: Number(r.expected_revenue || 0),
    probability: Math.round(Number(r.probability || 0)),
    stage: r.stage_id ? cycomStageToCycom(m2oName(r.stage_id)) : 'New',
    contact: (r.email_from as string) || 'no-reply@lead.com',
  };
}

export default function CRMPage() {
  const [leads, setLeads] = useState<LeadCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New lead form
  const [client, setClient] = useState('');
  const [revenue, setRevenue] = useState('');
  const [prob, setProb] = useState('50');
  const [contact, setContact] = useState('');

  const loadLeads = () => {
    setLoading(true);
    setError(null);
    searchRead<CycomLead>(
      'crm.lead',
      [['type', '=', 'lead']],
      ['partner_name', 'contact_name', 'expected_revenue', 'probability', 'stage_id', 'email_from'],
      { limit: 200, order: 'id desc' },
    )
      .then((rows) => setLeads(rows.map(mapLead)))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load CRM leads'))
      .finally(() => setLoading(false));
  };

  useEffect(loadLeads, []);

  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!client || !revenue) return;
    try {
      const id = await create('crm.lead', {
        type: 'lead',
        partner_name: client,
        expected_revenue: parseFloat(revenue),
        probability: parseFloat(prob),
        email_from: contact || false,
      });
      setLeads([
        { rawId: id, id: fmtCode('LD', id, 3), clientName: client, expectedRevenue: parseFloat(revenue), probability: parseFloat(prob), stage: 'New', contact: contact || 'no-reply@lead.com' },
        ...leads,
      ]);
      setClient(''); setRevenue(''); setContact('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create lead');
    }
  };

  const promoteLead = async (rawId: number) => {
    const ld = leads.find((l) => l.rawId === rawId);
    if (!ld) return;
    const currIdx = STAGES.indexOf(ld.stage);
    const nextIdx = Math.min(currIdx + 1, STAGES.length - 1);
    const newStage = STAGES[nextIdx];
    const newProb = newStage === 'Won' ? 100 : newStage === 'Lost' ? 0 : newStage === 'Proposition' ? 75 : ld.probability;
    setLeads(leads.map((l) => (l.rawId === rawId ? { ...l, stage: newStage, probability: newProb } : l)));
    try { await write('crm.lead', [rawId], { probability: newProb }); } catch { /* swallow — UI already moved */ }
  };

  const demoteLead = async (rawId: number) => {
    const ld = leads.find((l) => l.rawId === rawId);
    if (!ld) return;
    const currIdx = STAGES.indexOf(ld.stage);
    const nextIdx = Math.max(currIdx - 1, 0);
    const newStage = STAGES[nextIdx];
    const newProb = newStage === 'New' ? 10 : newStage === 'Qualified' ? 40 : ld.probability;
    setLeads(leads.map((l) => (l.rawId === rawId ? { ...l, stage: newStage, probability: newProb } : l)));
    try { await write('crm.lead', [rawId], { probability: newProb }); } catch { /* swallow */ }
  };

  const deleteLead = async (rawId: number) => {
    setLeads(leads.filter((l) => l.rawId !== rawId));
    try { await unlink('crm.lead', [rawId]); } catch { /* swallow */ }
  };

  // Calculate stats
  const totalPipeline = leads.filter((l) => l.stage !== 'Lost').reduce((acc, curr) => acc + curr.expectedRevenue, 0);
  const weightedPipeline = leads.filter((l) => l.stage !== 'Lost').reduce((acc, curr) => acc + (curr.expectedRevenue * (curr.probability / 100)), 0);

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">CRM &amp; Opportunity Pipeline</h1>
          <p className="page-subtitle">Drag/promote opportunities, adjust probabilities, and evaluate pipeline values.</p>
        </div>
      </div>

      {loading && <LoadingCard label="Loading leads…" />}
      {error && <ErrorCard error={error} />}

      {!loading && !error && (
        <>
          {/* KPI Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="stat-card flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Pipeline Value</span>
                <p className="text-2xl font-black text-white">JOD {totalPipeline.toLocaleString()}</p>
              </div>
              <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400"><DollarSign className="w-5 h-5" /></div>
            </div>
            <div className="stat-card flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Weighted Forecast</span>
                <p className="text-2xl font-black text-[#10B981]">JOD {weightedPipeline.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400"><Sparkles className="w-5 h-5" /></div>
            </div>
            <div className="stat-card flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Open Opportunities</span>
                <p className="text-2xl font-black text-[#F59E0B]">{leads.filter((l) => l.stage !== 'Won' && l.stage !== 'Lost').length} leads</p>
              </div>
              <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400"><Star className="w-5 h-5" /></div>
            </div>
            <div className="stat-card flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Won Deals</span>
                <p className="text-2xl font-black text-[#10B981]">{leads.filter((l) => l.stage === 'Won').length} closed</p>
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400"><Award className="w-5 h-5" /></div>
            </div>
          </div>

          {leads.length === 0 && <EmptyCard label="No leads yet — create one on the left." />}

          {/* Main Workspace */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Left creator */}
            <div className="glass-card p-5 space-y-4 h-fit">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Add New Lead Opportunity</h2>
                <Plus className="w-4 h-4 text-[#A855F7]" />
              </div>

              <form onSubmit={handleCreateLead} className="space-y-3 text-xs">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Opportunity / Customer</label>
                  <input type="text" required placeholder="e.g. Zarqa Outlet Store" value={client} onChange={(e) => setClient(e.target.value)} className="input-field" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Expected JOD</label>
                    <input type="number" required placeholder="e.g. 5000" value={revenue} onChange={(e) => setRevenue(e.target.value)} className="input-field font-mono" />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Prob %</label>
                    <input type="number" min="0" max="100" value={prob} onChange={(e) => setProb(e.target.value)} className="input-field font-mono" />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Contact Email</label>
                  <input type="email" placeholder="e.g. client@domain.jo" value={contact} onChange={(e) => setContact(e.target.value)} className="input-field" />
                </div>
                <button type="submit" className="btn-primary w-full py-2">Insert into Pipeline</button>
              </form>
            </div>

            {/* Kanban */}
            <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-5 gap-3.5 items-start">
              {STAGES.map((stage) => {
                const stageLeads = leads.filter((l) => l.stage === stage);
                const stageRevenueSum = stageLeads.reduce((acc, curr) => acc + curr.expectedRevenue, 0);
                return (
                  <div key={stage} className={`p-3 rounded-2xl border ${STAGE_BG_STYLES[stage]} space-y-3 min-h-[460px] flex flex-col`}>
                    <div className="border-b border-white/5 pb-2">
                      <div className="flex justify-between items-center">
                        <span className="text-[11px] font-bold text-white uppercase">{stage}</span>
                        <span className="text-[9px] bg-white/5 px-2 py-0.2 rounded font-mono font-bold text-slate-400">{stageLeads.length}</span>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-1 font-bold">JOD {stageRevenueSum.toLocaleString()}</p>
                    </div>
                    <div className="space-y-2 flex-1 overflow-y-auto pr-1">
                      {stageLeads.map((ld) => (
                        <div key={ld.id} className="p-3 rounded-xl bg-[#0B0F19]/90 border border-white/5 hover:border-white/12 shadow-sm space-y-2 group transition-all">
                          <div className="flex justify-between items-start">
                            <span className="text-[11px] font-bold text-white group-hover:text-[#E67E22] transition-colors leading-normal break-words max-w-[80%]">{ld.clientName}</span>
                            <button onClick={() => deleteLead(ld.rawId)} className="p-0.5 rounded hover:bg-red-500/10 text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                            <span>JOD {ld.expectedRevenue}</span>
                            <span className="font-bold">{ld.probability}%</span>
                          </div>
                          <div className="text-[9px] text-slate-500 truncate">{ld.contact}</div>
                          <div className="flex justify-between border-t border-white/5 pt-2 mt-2">
                            {STAGES.indexOf(stage) > 0 ? (
                              <button onClick={() => demoteLead(ld.rawId)} className="p-1 rounded bg-white/3 hover:bg-white/8 text-slate-400"><ArrowLeft className="w-2.5 h-2.5" /></button>
                            ) : <div />}
                            {STAGES.indexOf(stage) < STAGES.length - 1 ? (
                              <button onClick={() => promoteLead(ld.rawId)} className="p-1 rounded bg-white/3 hover:bg-white/8 text-slate-400"><ArrowRight className="w-2.5 h-2.5" /></button>
                            ) : <div />}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
