'use client';

// No-code automation rules: when <event> on <source>, if <conditions>, do <actions>.
// Everything the builder offers comes from the backend catalog
// (/api/v1/automation/catalog/) -- the same whitelist the engine enforces,
// so the UI can never offer a field the server would reject.

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft, Plus, Trash2, Zap, Play, X, History, CheckCircle2, AlertTriangle, MinusCircle,
} from 'lucide-react';
import { useT } from '@/lib/i18n';

interface FieldDef { key: string; label: string; type: string }
interface SourceDef { key: string; label: string; fields: FieldDef[]; writable_fields: FieldDef[] }
interface OperatorDef { key: string; label: string; numeric_only: boolean }
interface KeyLabel { key: string; label: string }
interface Catalog {
  sources: SourceDef[];
  operators: OperatorDef[];
  action_types: KeyLabel[];
  trigger_events: KeyLabel[];
}

interface Condition { field: string; operator: string; value: string }
interface RuleAction { type: string; [k: string]: unknown }
interface Run {
  id: string; status: string; detail: string; event: string; record_id: string; created_at: string;
}
interface Rule {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  trigger_source: string;
  trigger_event: string;
  conditions: Condition[];
  actions: RuleAction[];
  run_count: number;
  last_run_at: string | null;
  runs_recent: Run[];
}

const EMPTY_RULE = {
  name: '', description: '', is_active: true,
  trigger_source: '', trigger_event: 'created_or_updated',
  conditions: [] as Condition[], actions: [] as RuleAction[],
};

export default function AutomationPage() {
  const t = useT();
  const router = useRouter();

  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<{ kind: 'success' | 'error'; text: string } | null>(null);

  const [editing, setEditing] = useState<typeof EMPTY_RULE & { id?: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [historyFor, setHistoryFor] = useState<Rule | null>(null);

  const loadRules = useCallback(async () => {
    const res = await fetch('/api/cycom/rest/automation/rules/', { credentials: 'include' });
    const data = await res.json();
    setRules((data.results || data) as Rule[]);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [catRes] = await Promise.all([
          fetch('/api/cycom/rest/automation/catalog/', { credentials: 'include' }),
          loadRules(),
        ]);
        setCatalog(await catRes.json());
      } catch (err: any) {
        setStatus({ kind: 'error', text: t('automation.loadFailed', { msg: err.message }) });
      } finally {
        setLoading(false);
      }
    })();
  }, [loadRules, t]);

  const source = catalog?.sources.find((s) => s.key === editing?.trigger_source) || null;

  const save = async () => {
    if (!editing) return;
    setSaving(true);
    setStatus(null);
    try {
      const isEdit = Boolean(editing.id);
      const res = await fetch(
        isEdit ? `/api/cycom/rest/automation/rules/${editing.id}/` : '/api/cycom/rest/automation/rules/',
        {
          method: isEdit ? 'PATCH' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(editing),
        },
      );
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setStatus({ kind: 'success', text: t('automation.saved') });
        setEditing(null);
        await loadRules();
      } else {
        setStatus({ kind: 'error', text: t('automation.saveFailed', { msg: JSON.stringify(data) }) });
      }
    } catch (err: any) {
      setStatus({ kind: 'error', text: t('automation.saveFailed', { msg: err.message }) });
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (rule: Rule) => {
    await fetch(`/api/cycom/rest/automation/rules/${rule.id}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ is_active: !rule.is_active }),
    });
    await loadRules();
  };

  const remove = async (rule: Rule) => {
    await fetch(`/api/cycom/rest/automation/rules/${rule.id}/`, {
      method: 'DELETE', credentials: 'include',
    });
    await loadRules();
  };

  const patchEditing = (patch: Partial<typeof EMPTY_RULE>) =>
    setEditing((e) => (e ? { ...e, ...patch } : e));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-6xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent flex items-center gap-2">
              <Zap className="w-6 h-6 text-indigo-400" /> {t('automation.title')}
            </h1>
            <p className="text-xs text-slate-400 mt-1">{t('automation.subtitle')}</p>
          </div>
        </div>
        <button
          onClick={() => setEditing({ ...EMPTY_RULE, trigger_source: catalog?.sources[0]?.key || '' })}
          className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-semibold shadow-lg shadow-blue-600/15 transition"
        >
          <Plus className="w-4 h-4" /> {t('automation.newRule')}
        </button>
      </div>

      <div className="max-w-6xl mx-auto space-y-6">
        {status && (
          <div className={`flex items-center justify-between px-4 py-3 rounded-lg border text-xs font-medium ${
            status.kind === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/20 text-emerald-400'
              : 'bg-rose-950/40 border-rose-500/20 text-rose-400'
          }`}>
            <span className="truncate">{status.text}</span>
            <button onClick={() => setStatus(null)} className="p-1 hover:bg-white/5 rounded transition">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Builder */}
        {editing && catalog && (
          <div className="glass-card p-6 space-y-5 border border-blue-500/20">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                {editing.id ? t('automation.editRule') : t('automation.newRule')}
              </h3>
              <button onClick={() => setEditing(null)} className="p-1 hover:bg-slate-800 rounded transition">
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-slate-400">{t('automation.ruleName')}</label>
                <input
                  type="text" value={editing.name} onChange={(e) => patchEditing({ name: e.target.value })}
                  placeholder={t('automation.ruleNamePh')}
                  className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                />
              </div>
              <div className="space-y-1">
                <label className="text-slate-400">{t('automation.description')}</label>
                <input
                  type="text" value={editing.description} onChange={(e) => patchEditing({ description: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                />
              </div>
            </div>

            {/* WHEN */}
            <div className="space-y-2 border-t border-white/5 pt-4">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-blue-400">{t('automation.whenHeading')}</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <select
                  value={editing.trigger_source}
                  onChange={(e) => patchEditing({ trigger_source: e.target.value, conditions: [], actions: [] })}
                  className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                >
                  {catalog.sources.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
                </select>
                <select
                  value={editing.trigger_event}
                  onChange={(e) => patchEditing({ trigger_event: e.target.value })}
                  className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                >
                  {catalog.trigger_events.map((ev) => <option key={ev.key} value={ev.key}>{ev.label}</option>)}
                </select>
              </div>
            </div>

            {/* IF */}
            <div className="space-y-2 border-t border-white/5 pt-4">
              <div className="flex items-center justify-between">
                <h4 className="text-[10px] font-bold uppercase tracking-widest text-amber-400">{t('automation.ifHeading')}</h4>
                <span className="text-[10px] text-slate-500">{t('automation.allMustMatch')}</span>
              </div>
              {editing.conditions.length === 0 && (
                <p className="text-[10px] text-slate-500">{t('automation.noConditions')}</p>
              )}
              {editing.conditions.map((cond, idx) => {
                const fieldDef = source?.fields.find((f) => f.key === cond.field);
                return (
                  <div key={idx} className="grid grid-cols-[1fr_1fr_1fr_auto] gap-2 items-center">
                    <select
                      value={cond.field}
                      onChange={(e) => {
                        const next = [...editing.conditions];
                        next[idx] = { ...cond, field: e.target.value };
                        patchEditing({ conditions: next });
                      }}
                      className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    >
                      <option value="">{t('automation.pickField')}</option>
                      {source?.fields.map((f) => <option key={f.key} value={f.key}>{f.label}</option>)}
                    </select>
                    <select
                      value={cond.operator}
                      onChange={(e) => {
                        const next = [...editing.conditions];
                        next[idx] = { ...cond, operator: e.target.value };
                        patchEditing({ conditions: next });
                      }}
                      className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    >
                      {catalog.operators
                        .filter((op) => !op.numeric_only || fieldDef?.type === 'number')
                        .map((op) => <option key={op.key} value={op.key}>{op.label}</option>)}
                    </select>
                    <input
                      type={fieldDef?.type === 'number' ? 'number' : 'text'}
                      value={cond.value}
                      onChange={(e) => {
                        const next = [...editing.conditions];
                        next[idx] = { ...cond, value: e.target.value };
                        patchEditing({ conditions: next });
                      }}
                      placeholder={t('automation.value')}
                      className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                    <button
                      onClick={() => patchEditing({ conditions: editing.conditions.filter((_, i) => i !== idx) })}
                      className="p-2 hover:bg-slate-800 rounded-lg transition"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-slate-500" />
                    </button>
                  </div>
                );
              })}
              <button
                onClick={() => patchEditing({
                  conditions: [...editing.conditions, { field: source?.fields[0]?.key || '', operator: 'eq', value: '' }],
                })}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg transition text-xs"
              >
                <Plus className="w-3.5 h-3.5" /> {t('automation.addCondition')}
              </button>
            </div>

            {/* THEN */}
            <div className="space-y-2 border-t border-white/5 pt-4">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-emerald-400">{t('automation.thenHeading')}</h4>
              {editing.actions.length === 0 && (
                <p className="text-[10px] text-slate-500">{t('automation.noActions')}</p>
              )}
              {editing.actions.map((act, idx) => {
                const patchAction = (patch: Record<string, unknown>) => {
                  const next = [...editing.actions];
                  next[idx] = { ...act, ...patch };
                  patchEditing({ actions: next });
                };
                return (
                  <div key={idx} className="p-3 bg-slate-950/40 border border-slate-850 rounded-xl space-y-2">
                    <div className="flex items-center gap-2">
                      <select
                        value={act.type}
                        onChange={(e) => patchEditing({
                          actions: editing.actions.map((a, i) => (i === idx ? { type: e.target.value } : a)),
                        })}
                        className="flex-1 bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                      >
                        {catalog.action_types.map((a) => <option key={a.key} value={a.key}>{a.label}</option>)}
                      </select>
                      <button
                        onClick={() => patchEditing({ actions: editing.actions.filter((_, i) => i !== idx) })}
                        className="p-2 hover:bg-slate-800 rounded-lg transition"
                      >
                        <Trash2 className="w-3.5 h-3.5 text-slate-500" />
                      </button>
                    </div>

                    {act.type === 'set_field' && (
                      <div className="grid grid-cols-2 gap-2">
                        <select
                          value={(act.field as string) || ''}
                          onChange={(e) => patchAction({ field: e.target.value })}
                          className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                        >
                          <option value="">{t('automation.pickField')}</option>
                          {source?.writable_fields.map((f) => <option key={f.key} value={f.key}>{f.label}</option>)}
                        </select>
                        <input
                          type="text" value={(act.value as string) || ''}
                          onChange={(e) => patchAction({ value: e.target.value })}
                          placeholder={t('automation.value')}
                          className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                        />
                        {source?.writable_fields.length === 0 && (
                          <p className="col-span-2 text-[10px] text-amber-400">{t('automation.noWritableFields')}</p>
                        )}
                      </div>
                    )}

                    {(act.type === 'create_task' || act.type === 'create_todo') && (
                      <div className="grid grid-cols-2 gap-2">
                        <input
                          type="text"
                          value={(act.type === 'create_task' ? (act.name as string) : (act.title as string)) || ''}
                          onChange={(e) => patchAction(act.type === 'create_task' ? { name: e.target.value } : { title: e.target.value })}
                          placeholder={t('automation.taskTitlePh')}
                          className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                        />
                        <input
                          type="text" value={(act.assignee as string) || ''}
                          onChange={(e) => patchAction({ assignee: e.target.value })}
                          placeholder={t('automation.assignee')}
                          className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                        />
                      </div>
                    )}

                    {act.type === 'send_email' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <input
                          type="text" value={(act.to as string) || ''}
                          onChange={(e) => patchAction({ to: e.target.value })}
                          placeholder={t('automation.emailToPh')} dir="ltr"
                          className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                        />
                        <input
                          type="text" value={(act.subject as string) || ''}
                          onChange={(e) => patchAction({ subject: e.target.value })}
                          placeholder={t('automation.emailSubjectPh')}
                          className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                        />
                        <textarea
                          rows={2} value={(act.body as string) || ''}
                          onChange={(e) => patchAction({ body: e.target.value })}
                          placeholder={t('automation.emailBodyPh')}
                          className="md:col-span-2 bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                        />
                      </div>
                    )}
                    <p className="text-[10px] text-slate-600">{t('automation.placeholderHint')}</p>
                  </div>
                );
              })}
              <button
                onClick={() => patchEditing({ actions: [...editing.actions, { type: catalog.action_types[0].key }] })}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg transition text-xs"
              >
                <Plus className="w-3.5 h-3.5" /> {t('automation.addAction')}
              </button>
            </div>

            <div className="flex justify-end gap-3 border-t border-white/5 pt-4">
              <button onClick={() => setEditing(null)} className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition">
                {t('automation.cancel')}
              </button>
              <button
                onClick={save} disabled={saving || !editing.name}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-white font-semibold transition"
              >
                {t('automation.saveRule')}
              </button>
            </div>
          </div>
        )}

        {/* Rule list */}
        <div className="glass-card p-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 pb-3 mb-4">
            {t('automation.rulesHeading', { count: String(rules.length) })}
          </h3>
          {loading ? (
            <div className="text-center py-6 text-slate-500">{t('automation.loading')}</div>
          ) : rules.length === 0 ? (
            <div className="text-center py-10 text-slate-500">{t('automation.empty')}</div>
          ) : (
            <div className="space-y-3">
              {rules.map((rule) => {
                const src = catalog?.sources.find((s) => s.key === rule.trigger_source);
                return (
                  <div key={rule.id} className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl">
                    <div className="flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-slate-200 truncate">{rule.name}</h4>
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                            rule.is_active
                              ? 'bg-emerald-950/40 text-emerald-400 border-emerald-500/20'
                              : 'bg-slate-800 text-slate-500 border-slate-700/50'
                          }`}>
                            {rule.is_active ? t('automation.active') : t('automation.paused')}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-500 mt-1">
                          {src?.label || rule.trigger_source} · {rule.conditions.length} {t('automation.conditionsLabel')} · {rule.actions.length} {t('automation.actionsLabel')} · {t('automation.ranTimes', { n: String(rule.run_count) })}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={() => setHistoryFor(historyFor?.id === rule.id ? null : rule)}
                          className="p-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg transition"
                          title={t('automation.history')}
                        >
                          <History className="w-3.5 h-3.5 text-slate-400" />
                        </button>
                        <button
                          onClick={() => toggleActive(rule)}
                          className="p-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg transition"
                          title={rule.is_active ? t('automation.pause') : t('automation.activate')}
                        >
                          {rule.is_active
                            ? <MinusCircle className="w-3.5 h-3.5 text-amber-400" />
                            : <Play className="w-3.5 h-3.5 text-emerald-400" />}
                        </button>
                        <button
                          onClick={() => setEditing({
                            id: rule.id, name: rule.name, description: rule.description,
                            is_active: rule.is_active, trigger_source: rule.trigger_source,
                            trigger_event: rule.trigger_event, conditions: rule.conditions, actions: rule.actions,
                          })}
                          className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg transition text-xs"
                        >
                          {t('automation.edit')}
                        </button>
                        <button
                          onClick={() => remove(rule)}
                          className="p-2 bg-rose-950/20 border border-rose-500/20 hover:bg-rose-500/10 rounded-lg transition"
                        >
                          <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                        </button>
                      </div>
                    </div>

                    {historyFor?.id === rule.id && (
                      <div className="mt-4 border-t border-white/5 pt-3 space-y-2">
                        <h5 className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">
                          {t('automation.recentRuns')}
                        </h5>
                        {rule.runs_recent.length === 0 ? (
                          <p className="text-[10px] text-slate-600">{t('automation.noRuns')}</p>
                        ) : rule.runs_recent.map((run) => (
                          <div key={run.id} className="flex items-start gap-2 text-[10px]">
                            {run.status === 'matched' && <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0 mt-0.5" />}
                            {run.status === 'skipped' && <MinusCircle className="w-3 h-3 text-slate-500 flex-shrink-0 mt-0.5" />}
                            {run.status === 'failed' && <AlertTriangle className="w-3 h-3 text-rose-400 flex-shrink-0 mt-0.5" />}
                            <span className="text-slate-500">{new Date(run.created_at).toLocaleString()}</span>
                            <span className="text-slate-400 truncate">{run.detail || run.status}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
