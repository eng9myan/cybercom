'use client';

import React from 'react';
import { Star, Briefcase } from 'lucide-react';
import { useCycomList, fmtCode, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';
import { useT } from '@/lib/i18n';

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

type StageKey = 'applied' | 'phoneScreen' | 'interview' | 'offer' | 'hired';

interface Candidate {
  rawId: number;
  id: string;
  name: string;
  email: string;
  position: string;
  rating: number;
  stage: StageKey;
  dateApplied: string;
}

const STAGES: StageKey[] = ['applied', 'phoneScreen', 'interview', 'offer', 'hired'];

const STAGE_COLORS: Record<StageKey, string> = {
  applied: 'border-slate-500/20 bg-slate-500/2',
  phoneScreen: 'border-cyan-500/20 bg-cyan-500/2',
  interview: 'border-purple-500/20 bg-purple-500/2',
  offer: 'border-amber-500/20 bg-amber-500/2',
  hired: 'border-emerald-500/20 bg-emerald-500/2',
};

function stageFromCycom(name: string): StageKey {
  const s = (name || '').toLowerCase();
  if (s.includes('hire')) return 'hired';
  if (s.includes('offer') || s.includes('contract')) return 'offer';
  if (s.includes('interview') || s.includes('second')) return 'interview';
  if (s.includes('phone') || s.includes('initial') || s.includes('first')) return 'phoneScreen';
  return 'applied';
}

const mapApplicant = (a: CycomApplicant): Candidate => ({
  rawId: a.id,
  id: fmtCode('CAN', a.id, 3),
  name: (a.partner_name as string) || (a.name as string) || `Applicant ${a.id}`,
  email: (a.email_from as string) || '—',
  position: m2oName(a.job_id, 'Unspecified'),
  rating: Math.min(5, Math.max(0, parseInt(a.priority || '0', 10))),
  stage: a.stage_id ? stageFromCycom(m2oName(a.stage_id)) : 'applied',
  dateApplied: fmtDate(a.create_date),
});

export default function RecruitmentPage() {
  const t = useT();
  const { rows: candidates, loading, error } = useCycomList<CycomApplicant, Candidate>(
    'hr.applicant',
    [],
    ['partner_name', 'name', 'email_from', 'job_id', 'priority', 'kanban_state', 'stage_id', 'create_date'],
    mapApplicant,
    { limit: 200, order: 'create_date desc' },
  );

  const stageLabel: Record<StageKey, string> = {
    applied: t('recruitment.stageApplied'),
    phoneScreen: t('recruitment.stagePhoneScreen'),
    interview: t('recruitment.stageInterview'),
    offer: t('recruitment.stageOffer'),
    hired: t('recruitment.stageHired'),
  };

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('recruitment.title')}</h1>
          <p className="page-subtitle">{t('recruitment.subtitle')}</p>
        </div>
      </div>

      {loading && <LoadingCard label={t('recruitment.loading')} />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && candidates.length === 0 && <EmptyCard label={t('recruitment.empty')} />}

      {!loading && !error && candidates.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3.5 items-start">
          {STAGES.map((stage) => {
            const stageCands = candidates.filter((c) => c.stage === stage);
            return (
              <div key={stage} className={`p-3 rounded-2xl border ${STAGE_COLORS[stage]} space-y-3 min-h-[420px] flex flex-col`}>
                <div className="border-b border-white/5 pb-2 flex justify-between items-center">
                  <span className="text-[11px] font-bold text-white uppercase">{stageLabel[stage]}</span>
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
                      <div className="text-[9px] text-slate-600 border-t border-white/5 pt-1.5">{t('recruitment.appliedOn', { date: c.dateApplied })}</div>
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
