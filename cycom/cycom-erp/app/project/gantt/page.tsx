'use client';

// Gantt + critical path. The schedule (early/late start, slack, which tasks
// are critical) is computed server-side by products.cycom.project.scheduling
// so the chart and any other consumer can't disagree about the maths.

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft, GanttChartSquare, AlertTriangle, Flag, Clock, CalendarDays,
} from 'lucide-react';
import { useT } from '@/lib/i18n';

interface ScheduledTask {
  id: string;
  name: string;
  stage: string;
  assignee: string;
  duration_days: number;
  early_start: string;
  early_finish: string;
  late_start: string;
  late_finish: string;
  slack_days: number;
  is_critical: boolean;
  depends_on: string[];
  due_date: string | null;
  overruns_due_date: boolean;
}

interface Schedule {
  tasks: ScheduledTask[];
  project_start: string | null;
  project_finish: string | null;
  duration_days: number;
  critical_count: number;
}

interface ProjectRow { id: string; name: string }

const DAY_MS = 86400000;
const MIN_COL = 28; // px per day

function dayDiff(a: string, b: string) {
  return Math.round((Date.parse(a) - Date.parse(b)) / DAY_MS);
}

export default function GanttPage() {
  const t = useT();
  const router = useRouter();

  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [projectId, setProjectId] = useState('');
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/cycom/rest/project/projects/', { credentials: 'include' })
      .then((r) => r.json())
      .then((d) => {
        const rows = (d.results || d) as ProjectRow[];
        setProjects(rows);
        if (rows.length) setProjectId(rows[0].id);
      })
      .catch((err) => setError(t('gantt.loadFailed', { msg: err.message })));
  }, [t]);

  const load = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/cycom/rest/project/projects/${projectId}/schedule/`, {
        credentials: 'include',
      });
      const data = await res.json();
      if (res.status === 409) {
        setSchedule(null);
        setError(data.detail);
      } else if (res.ok) {
        setSchedule(data);
      } else {
        setError(t('gantt.loadFailed', { msg: data.detail || res.statusText }));
      }
    } catch (err: any) {
      setError(t('gantt.loadFailed', { msg: err.message }));
    } finally {
      setLoading(false);
    }
  }, [projectId, t]);

  useEffect(() => { load(); }, [load]);

  const days = useMemo(() => {
    if (!schedule?.project_start || !schedule.project_finish) return [];
    const out: string[] = [];
    const start = Date.parse(schedule.project_start);
    const total = dayDiff(schedule.project_finish, schedule.project_start) + 1;
    for (let i = 0; i < total; i++) out.push(new Date(start + i * DAY_MS).toISOString().slice(0, 10));
    return out;
  }, [schedule]);

  const todayIdx = useMemo(() => {
    if (!schedule?.project_start) return -1;
    const today = new Date().toISOString().slice(0, 10);
    const idx = dayDiff(today, schedule.project_start);
    return idx >= 0 && idx < days.length ? idx : -1;
  }, [schedule, days.length]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-[1400px] mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/project')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent flex items-center gap-2">
              <GanttChartSquare className="w-6 h-6 text-cyan-400" /> {t('gantt.title')}
            </h1>
            <p className="text-xs text-slate-400 mt-1">{t('gantt.subtitle')}</p>
          </div>
        </div>
        <select
          value={projectId} onChange={(e) => setProjectId(e.target.value)}
          className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none min-w-[220px]"
        >
          {projects.length === 0 && <option value="">{t('gantt.noProjects')}</option>}
          {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      <div className="max-w-[1400px] mx-auto space-y-6">
        {error && (
          <div className="flex items-start gap-3 px-4 py-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {schedule && schedule.tasks.length > 0 && (
          <>
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { icon: CalendarDays, label: t('gantt.projectStart'), value: schedule.project_start, tone: 'text-slate-200' },
                { icon: Flag, label: t('gantt.projectFinish'), value: schedule.project_finish, tone: 'text-slate-200' },
                { icon: Clock, label: t('gantt.durationDays'), value: String(schedule.duration_days), tone: 'text-cyan-400' },
                { icon: AlertTriangle, label: t('gantt.criticalTasks'), value: String(schedule.critical_count), tone: 'text-rose-400' },
              ].map((card) => (
                <div key={card.label} className="glass-card p-4">
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                    <card.icon className="w-3.5 h-3.5" /> {card.label}
                  </div>
                  <div className={`mt-1 text-lg font-bold font-mono ${card.tone}`}>{card.value}</div>
                </div>
              ))}
            </div>

            {/* Chart. Forced LTR: a date axis reads left-to-right in both
                locales, same convention the app already uses for IBANs. */}
            <div className="glass-card p-0 overflow-hidden">
              <div className="overflow-x-auto" dir="ltr">
                <div style={{ minWidth: 320 + days.length * MIN_COL }}>
                  {/* header */}
                  <div className="flex border-b border-white/5 sticky top-0 bg-slate-950/80 backdrop-blur z-10">
                    <div className="w-[320px] flex-shrink-0 px-4 py-2 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                      {t('gantt.task')}
                    </div>
                    <div className="flex">
                      {days.map((d, i) => {
                        const dt = new Date(d);
                        const weekend = dt.getDay() === 5 || dt.getDay() === 6;
                        return (
                          <div
                            key={d}
                            style={{ width: MIN_COL }}
                            className={`flex-shrink-0 text-center py-2 border-l border-white/5 ${
                              weekend ? 'bg-slate-900/40' : ''
                            } ${i === todayIdx ? 'bg-cyan-500/10' : ''}`}
                          >
                            <div className="text-[9px] text-slate-600">{dt.getDate()}</div>
                            {(i === 0 || dt.getDate() === 1) && (
                              <div className="text-[8px] text-slate-500 uppercase">
                                {dt.toLocaleString(undefined, { month: 'short' })}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* rows */}
                  {schedule.tasks.map((task) => {
                    const offset = dayDiff(task.early_start, schedule.project_start!);
                    const slackOffset = dayDiff(task.early_finish, schedule.project_start!) + 1;
                    return (
                      <div key={task.id} className="flex border-b border-white/5 hover:bg-white/[0.02] group">
                        <div className="w-[320px] flex-shrink-0 px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            {task.is_critical && <span className="w-1.5 h-1.5 rounded-full bg-rose-500 flex-shrink-0" />}
                            <span className="truncate text-slate-200">{task.name}</span>
                            {task.overruns_due_date && (
                              <span title={t('gantt.pastDue')}>
                                <AlertTriangle className="w-3 h-3 text-amber-400 flex-shrink-0" />
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-slate-600 mt-0.5 truncate">
                            {task.assignee || t('gantt.unassigned')} · {task.duration_days}d
                            {task.slack_days > 0 && ` · ${t('gantt.slackDays', { n: String(task.slack_days) })}`}
                          </div>
                        </div>
                        <div className="flex relative">
                          {days.map((d, i) => {
                            const dt = new Date(d);
                            const weekend = dt.getDay() === 5 || dt.getDay() === 6;
                            return (
                              <div
                                key={d}
                                style={{ width: MIN_COL }}
                                className={`flex-shrink-0 border-l border-white/5 ${weekend ? 'bg-slate-900/40' : ''} ${
                                  i === todayIdx ? 'bg-cyan-500/10' : ''
                                }`}
                              />
                            );
                          })}
                          {/* slack tail */}
                          {task.slack_days > 0 && (
                            <div
                              className="absolute top-1/2 -translate-y-1/2 h-1.5 rounded-full bg-slate-700/40 border border-dashed border-slate-600/50"
                              style={{ left: slackOffset * MIN_COL + 2, width: task.slack_days * MIN_COL - 4 }}
                              title={t('gantt.slackDays', { n: String(task.slack_days) })}
                            />
                          )}
                          {/* the bar */}
                          <div
                            className={`absolute top-1/2 -translate-y-1/2 h-5 rounded-md flex items-center px-2 text-[10px] font-semibold transition-all group-hover:brightness-110 ${
                              task.is_critical
                                ? 'bg-gradient-to-r from-rose-600 to-rose-500 text-white shadow-lg shadow-rose-900/30'
                                : 'bg-gradient-to-r from-cyan-600 to-blue-500 text-white'
                            }`}
                            style={{ left: offset * MIN_COL + 2, width: task.duration_days * MIN_COL - 4 }}
                            title={`${task.early_start} → ${task.early_finish}`}
                          >
                            <span className="truncate">{task.duration_days}d</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="flex flex-wrap items-center gap-6 text-[10px] text-slate-500">
              <span className="flex items-center gap-2">
                <span className="w-6 h-2.5 rounded bg-gradient-to-r from-rose-600 to-rose-500" /> {t('gantt.legendCritical')}
              </span>
              <span className="flex items-center gap-2">
                <span className="w-6 h-2.5 rounded bg-gradient-to-r from-cyan-600 to-blue-500" /> {t('gantt.legendNormal')}
              </span>
              <span className="flex items-center gap-2">
                <span className="w-6 h-1.5 rounded bg-slate-700/40 border border-dashed border-slate-600/50" /> {t('gantt.legendSlack')}
              </span>
              <span className="flex items-center gap-2">
                <AlertTriangle className="w-3 h-3 text-amber-400" /> {t('gantt.legendPastDue')}
              </span>
            </div>
          </>
        )}

        {!loading && !error && schedule && schedule.tasks.length === 0 && (
          <div className="glass-card p-12 text-center text-slate-500">{t('gantt.emptyProject')}</div>
        )}
        {loading && <div className="glass-card p-12 text-center text-slate-500">{t('gantt.loading')}</div>}
      </div>
    </div>
  );
}
