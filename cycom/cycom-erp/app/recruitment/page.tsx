'use client';

import React from 'react';
import { Star, Briefcase, ArrowRight, ArrowLeft } from 'lucide-react';
import { useCycomList, fmtCode, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';

type CycomApplicant = {
  id: number;
  partner_name?: string | false;
  name?: string;
  email_from?: string | false;
  job_id?: Many2One;
  priority?: string;
  kanban_state?: string;
  stage_id?: Many2One;
  create_date?: string;
};

interface Candidate {
  rawId: number;
  id: string;
  name: string;
  email: string;
  position: string;
  rating: number;
  stage: 'Applied' | 'Phone Screen' | 'Interview' | 'Offer' | 'Hired';
  dateApplied: string;
}

const STAGES: Array<'Applied' | 'Phone Screen' | 'Interview' | 'Offer' | 'Hired'> = [
  'Applied', 'Phone Screen', 'Interview', 'Offer', 'Hired',
];

const STAGE_COLORS = {
  Applied: 'border-slate-500/20 bg-slate-500/2',
  'Phone Screen': 'border-cyan-500/20 bg-cyan-500/2',
  Interview: 'border-purple-500/20 bg-purple-500/2',
  Offer: 'border-amber-500/20 bg-amber-500/2',
  Hired: 'border-emerald-500/20 bg-emerald-500/2',
};

function stageFromCycom(name: string): Candidate['stage'] {
  const s = (name || '').toLowerCase();
  if (s.includes('hire')) return 'Hired';
  if (s.includes('offer') || s.includes('contract')) return 'Offer';
  if (s.includes('interview') || s.includes('second')) return 'Interview';
  if (s.includes('phone') || s.includes('initial') || s.includes('first')) return 'Phone Screen';
  return 'Applied';
}

const mapApplicant = (a: CycomApplicant): Candidate => ({
  rawId: a.id,
  id: fmtCode('CAN', a.id, 3),
  name: (a.partner_name as string) || (a.name as string) || `Applicant ${a.id}`,
  email: (a.email_from as string) || '—',
  position: m2oName(a.job_id, 'Unspecified'),
  rating: Math.min(5, Math.max(0, parseInt(a.priority || '0', 10))),
  stage: a.stage_id ? stageFromCycom(m2oName(a.stage_id)) : 'Applied',
  dateApplied: fmtDate(a.create_date),
});

export default function RecruitmentPage() {
  const { rows: candidates, loading, error } = useCycomList<CycomApplicant, Candidate>(
    'hr.applicant',
    [],
    ['partner_name', 'name', 'email_from', 'job_id', 'priority', 'kanban_state', 'stage_id', 'create_date'],
    mapApplicant,
    { limit: 200, order: 'create_date desc' },
  );

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Recruitment Pipeline</h1>
          <p className="page-subtitle">Applicants from open positions to hire, with stage transitions.</p>
        </div>
      </div>

      {loading && <LoadingCard label="Loading candidates…" />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && candidates.length === 0 && <EmptyCard label="No applicants yet — open a position in the Cycom backend to start receiving them." />}

      {!loading && !error && candidates.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3.5 items-start">
          {STAGES.map((stage) => {
            const stageCands = candidates.filter((c) => c.stage === stage);
            return (
              <div key={stage} className={`p-3 rounded-2xl border ${STAGE_COLORS[stage]} space-y-3 min-h-[420px] flex flex-col`}>
                <div className="border-b border-white/5 pb-2 flex justify-between items-center">
                  <span className="text-[11px] font-bold text-white uppercase">{stage}</span>
                  <span className="text-[9px] bg-white/5 px-2 py-0.5 rounded font-mono font-bold text-slate-400">{stageCands.length}</span>
                </div>
                <div className="space-y-2 flex-1 overflow-y-auto pr-1">
                  {stageCands.map((c) => (
                    <div key={c.rawId} className="p-3 rounded-xl bg-[#0B0F19]/90 border border-white/5 hover:border-white/12 shadow-sm space-y-2 group transition-all">
                      <div className="flex justify-between items-start gap-2">
                        <span className="text-[11px] font-bold text-white">{c.name}</span>
                        <div className="flex gap-0.5">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <Star key={i} className={`w-2.5 h-2.5 ${i < c.rating ? 'fill-amber-400 text-amber-400' : 'text-slate-600'}`} />
                          ))}
                        </div>
                      </div>
                      <div className="text-[10px] text-slate-500 flex items-center gap-1.5 truncate">
                        <Briefcase className="w-3 h-3" /> {c.position}
                      </div>
                      <div className="text-[9px] text-slate-500 truncate">{c.email}</div>
                      <div className="text-[9px] text-slate-600 border-t border-white/5 pt-1.5">Applied {c.dateApplied}</div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
