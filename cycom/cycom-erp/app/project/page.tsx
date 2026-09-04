'use client';

import React, { useEffect, useState } from 'react';
import { Plus, Trash2, ArrowRight, ArrowLeft, Clock } from 'lucide-react';
import { create, unlink, searchRead } from '@/lib/cycom';
import { fmtCode, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';
import { useT } from '@/lib/i18n';

type StageKey = 'backlog' | 'inProgress' | 'review' | 'done';

interface ProjectTask {
  rawId: number;
  id: string;
  title: string;
  project: string;
  assignee: string;
  estHours: number;
  loggedHours: number;
  stage: StageKey;
}

type CycomTask = {
  id: number;
  name?: string;
  project_id?: Many2One;
  user_ids?: number[];
  allocated_hours?: number;
  planned_hours?: number;
  effective_hours?: number;
  stage_id?: Many2One;
  state?: string;
};

const STAGES: StageKey[] = ['backlog', 'inProgress', 'review', 'done'];

const STAGE_COLORS: Record<StageKey, string> = {
  backlog: 'border-slate-500/20 bg-slate-500/2',
  inProgress: 'border-cyan-500/20 bg-cyan-500/2',
  review: 'border-purple-500/20 bg-purple-500/2',
  done: 'border-emerald-500/20 bg-emerald-500/2',
};

function stageFromCycom(name: string): StageKey {
  const s = (name || '').toLowerCase();
  if (s.includes('done') || s.includes('closed')) return 'done';
  if (s.includes('review') || s.includes('test')) return 'review';
  if (s.includes('progress') || s.includes('working') || s.includes('doing')) return 'inProgress';
  return 'backlog';
}

function mapTask(t: CycomTask, userMap: Record<number, string>): ProjectTask {
  const firstAssignee = t.user_ids && t.user_ids.length ? (userMap[t.user_ids[0]] || `User ${t.user_ids[0]}`) : 'Unassigned';
  return {
    rawId: t.id,
    id: fmtCode('TSK', t.id, 3),
    title: t.name || `Task ${t.id}`,
    project: m2oName(t.project_id, 'No project'),
    assignee: firstAssignee,
    estHours: Number(t.allocated_hours ?? t.planned_hours ?? 0),
    loggedHours: Number(t.effective_hours ?? 0),
    stage: t.stage_id ? stageFromCycom(m2oName(t.stage_id)) : 'backlog',
  };
}

export default function ProjectPage() {
  const t = useT();
  const [tasks, setTasks] = useState<ProjectTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [taskTitle, setTaskTitle] = useState('');
  const [projName, setProjName] = useState('General');
  const [assignee] = useState('Cycom User');
  const [estHours, setEstHours] = useState('8');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const raw = await searchRead<CycomTask>(
          'project.task',
          [],
          ['name', 'project_id', 'user_ids', 'allocated_hours', 'planned_hours', 'effective_hours', 'stage_id', 'state'],
          { limit: 200, order: 'id desc' },
        );
        const userIds = Array.from(new Set(raw.flatMap((tk) => tk.user_ids || [])));
        const users = userIds.length
          ? await searchRead<{ id: number; name: string }>('res.users', [['id', 'in', userIds]], ['name'], { limit: userIds.length })
          : [];
        const userMap: Record<number, string> = {};
        users.forEach((u) => { userMap[u.id] = u.name; });
        if (cancelled) return;
        setTasks(raw.map((r) => mapTask(r, userMap)));
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load project.task');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const stageLabel: Record<StageKey, string> = {
    backlog: t('projectBoard.stageBacklog'),
    inProgress: t('projectBoard.stageInProgress'),
    review: t('projectBoard.stageReview'),
    done: t('projectBoard.stageDone'),
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle) return;
    try {
      const id = await create('project.task', { name: taskTitle, allocated_hours: parseFloat(estHours) || 0 });
      setTasks([
        { rawId: id, id: fmtCode('TSK', id, 3), title: taskTitle, project: projName, assignee, estHours: parseFloat(estHours) || 0, loggedHours: 0, stage: 'backlog' },
        ...tasks,
      ]);
      setTaskTitle(''); setEstHours('8');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
    }
  };

  const promoteTask = (rawId: number) => {
    setTasks(tasks.map((tk) => {
      if (tk.rawId !== rawId) return tk;
      const idx = STAGES.indexOf(tk.stage);
      return { ...tk, stage: STAGES[Math.min(idx + 1, STAGES.length - 1)] };
    }));
  };

  const demoteTask = (rawId: number) => {
    setTasks(tasks.map((tk) => {
      if (tk.rawId !== rawId) return tk;
      const idx = STAGES.indexOf(tk.stage);
      return { ...tk, stage: STAGES[Math.max(idx - 1, 0)] };
    }));
  };

  const deleteTask = async (rawId: number) => {
    setTasks(tasks.filter((tk) => tk.rawId !== rawId));
    try { await unlink('project.task', [rawId]); } catch { /* swallow */ }
  };

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('projectBoard.title')}</h1>
          <p className="page-subtitle">{t('projectBoard.subtitle')}</p>
        </div>
      </div>

      {loading && <LoadingCard label={t('projectBoard.loading')} />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && tasks.length === 0 && <EmptyCard label={t('projectBoard.empty')} />}

      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="glass-card p-5 space-y-4 h-fit">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('projectBoard.newTask')}</h2>
              <Plus className="w-4 h-4 text-[#A855F7]" />
            </div>
            <form onSubmit={handleCreateTask} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('projectBoard.fieldTitle')}</label>
                <input type="text" required placeholder={t('projectBoard.titlePlaceholder')} value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} className="input-field" />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('projectBoard.project')}</label>
                <input type="text" value={projName} onChange={(e) => setProjName(e.target.value)} className="input-field" />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('projectBoard.allocatedHours')}</label>
                <input type="number" min="0" value={estHours} onChange={(e) => setEstHours(e.target.value)} className="input-field font-mono" />
              </div>
              <button type="submit" className="btn-primary w-full py-2">{t('projectBoard.createTask')}</button>
            </form>
          </div>

          <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-4 gap-3.5 items-start">
            {STAGES.map((stage) => {
              const stageTasks = tasks.filter((tk) => tk.stage === stage);
              return (
                <div key={stage} className={`p-3 rounded-2xl border ${STAGE_COLORS[stage]} space-y-3 min-h-[420px] flex flex-col`}>
                  <div className="border-b border-white/5 pb-2 flex justify-between items-center">
                    <span className="text-[11px] font-bold text-white uppercase">{stageLabel[stage]}</span>
                    <span className="text-[9px] bg-white/5 px-2 py-0.5 rounded font-mono font-bold text-slate-400">{stageTasks.length}</span>
                  </div>
                  <div className="space-y-2 flex-1 overflow-y-auto pr-1">
                    {stageTasks.map((tk) => (
                      <div key={tk.rawId} className="p-3 rounded-xl bg-[#0B0F19]/90 border border-white/5 hover:border-white/12 shadow-sm space-y-2 group transition-all">
                        <div className="flex justify-between items-start gap-2">
                          <span className="text-[11px] font-bold text-white group-hover:text-[#E67E22] transition-colors break-words">{tk.title}</span>
                          <button onClick={() => deleteTask(tk.rawId)} className="p-0.5 rounded hover:bg-red-500/10 text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono flex items-center gap-1.5">
                          <Clock className="w-3 h-3" /> {t('projectBoard.hoursProgress', { logged: tk.loggedHours, est: tk.estHours })}
                        </div>
                        <div className="text-[9px] text-slate-500 truncate">{tk.project} · {tk.assignee}</div>
                        <div className="flex justify-between border-t border-white/5 pt-2 mt-2">
                          {STAGES.indexOf(stage) > 0 ? (
                            <button onClick={() => demoteTask(tk.rawId)} className="p-1 rounded bg-white/3 hover:bg-white/8 text-slate-400"><ArrowLeft className="w-2.5 h-2.5" /></button>
                          ) : <div />}
                          {STAGES.indexOf(stage) < STAGES.length - 1 ? (
                            <button onClick={() => promoteTask(tk.rawId)} className="p-1 rounded bg-white/3 hover:bg-white/8 text-slate-400"><ArrowRight className="w-2.5 h-2.5" /></button>
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
      )}
    </div>
  );
}
