'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Building2, CornerDownRight, Plus, Pencil, Trash2, X, Loader2 } from 'lucide-react';
import { LoadingCard, EmptyCard } from '@/components/CycomEmptyStates';
import { useT } from '@/lib/i18n';
import { formatApiErrors } from '@/lib/apiErrors';

interface Dept {
  id: string;
  name: string;
  code: string;
  parent: string | null;
  manager: string | null;
  manager_name: string | null;
  member_count: number;
  total_employee: number;
}
interface Emp { id: string; first_name: string; last_name: string; employee_number: string }
interface Node extends Dept { children: Node[] }

const API = '/api/cycom/rest/hr/departments/';
const inputCls = 'w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none text-xs mt-0.5';

/** Walks a paginated DRF list to the end (the employee list pages at 25). */
async function fetchAll<T>(url: string): Promise<T[]> {
  const out: T[] = [];
  let page = 1;
  for (;;) {
    const r = await fetch(`${url}?page=${page}`, { credentials: 'include' });
    if (!r.ok) break;
    const data = await r.json();
    if (Array.isArray(data)) return data;
    out.push(...(data.results || []));
    if (!data.next) break;
    page += 1;
  }
  return out;
}

function buildTree(flat: Dept[]): Node[] {
  const nodes: Record<string, Node> = {};
  flat.forEach((d) => { nodes[d.id] = { ...d, children: [] }; });
  const roots: Node[] = [];
  Object.values(nodes).forEach((n) => {
    if (n.parent && nodes[n.parent]) nodes[n.parent].children.push(n);
    else roots.push(n);
  });
  const sort = (list: Node[]) => { list.sort((a, b) => a.name.localeCompare(b.name)); list.forEach((n) => sort(n.children)); };
  sort(roots);
  return roots;
}

function descendants(flat: Dept[], id: string): Set<string> {
  const out = new Set<string>();
  const walk = (pid: string) => flat.filter((d) => d.parent === pid).forEach((d) => { out.add(d.id); walk(d.id); });
  walk(id);
  return out;
}

const TONES = ['bg-cyan-950/20 border-cyan-500/20', 'bg-white/5 border-white/5', 'bg-white/[0.03] border-white/5'];
const BADGES = ['badge-cyan', 'badge-purple', 'badge-orange'];

export default function DepartmentHierarchy() {
  const t = useT();
  const [flat, setFlat] = useState<Dept[] | null>(null);
  const [employees, setEmployees] = useState<Emp[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Partial<Dept> | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string[] | null>(null);
  const [rowError, setRowError] = useState<{ id: string; msg: string } | null>(null);

  const load = useCallback(async () => {
    const r = await fetch(API, { credentials: 'include' });
    if (!r.ok) { setLoadError(String(r.status)); return; }
    setFlat(await r.json());
  }, []);

  useEffect(() => {
    load();
    fetchAll<Emp>('/api/cycom/rest/hr/employees/').then(setEmployees).catch(() => {});
  }, [load]);

  const tree = useMemo(() => (flat ? buildTree(flat) : []), [flat]);
  const totalEmps = (flat || []).reduce((a, d) => a + d.member_count, 0);

  const save = async () => {
    if (!editing) return;
    setSaving(true);
    setFormError(null);
    const body = { name: editing.name, code: editing.code || '', parent: editing.parent || null, manager: editing.manager || null };
    const resp = await fetch(editing.id ? `${API}${editing.id}/` : API, {
      method: editing.id ? 'PATCH' : 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    });
    const data = await resp.json().catch(() => null);
    setSaving(false);
    if (resp.ok) { setEditing(null); load(); } else setFormError(formatApiErrors(data).length ? formatApiErrors(data) : [String(resp.status)]);
  };

  const remove = async (d: Dept) => {
    setRowError(null);
    const resp = await fetch(`${API}${d.id}/`, { method: 'DELETE', credentials: 'include' });
    if (resp.ok) load();
    else {
      const data = await resp.json().catch(() => null);
      setRowError({ id: d.id, msg: formatApiErrors(data).join(' ') || String(resp.status) });
    }
  };

  const renderNode = (n: Node, depth: number): React.ReactNode => {
    const level = Math.min(depth, 2);
    return (
      <div key={n.id} className="space-y-3">
        <div className={`flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl border ${TONES[level]}`}>
          <div className="flex items-center gap-2.5 min-w-0">
            {depth === 0 ? <Building2 className="w-5 h-5 text-cyan-400 flex-shrink-0" /> : <CornerDownRight className="w-4 h-4 text-slate-500 flex-shrink-0" />}
            <div className="min-w-0">
              <h3 className={`font-bold truncate ${depth === 0 ? 'text-base text-white' : 'text-sm text-slate-200'}`}>
                {n.name}{n.code && <span className="ms-2 text-[10px] font-mono text-slate-500">{n.code}</span>}
              </h3>
              <p className="text-xs text-slate-400">{t('hrDepts.head', { name: n.manager_name || t('hrDepts.unassigned') })}</p>
              {rowError?.id === n.id && <p className="text-[11px] text-rose-400 mt-1">{rowError.msg}</p>}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-end">
              <span className="text-[10px] text-slate-500 block">{t('hrDepts.directChild')}</span>
              <span className="text-xs font-semibold text-slate-300">{n.member_count} / {n.total_employee - n.member_count}</span>
            </div>
            <span className={`badge ${BADGES[level]}`}>{t('hrDepts.totalBadge', { n: n.total_employee })}</span>
            <button onClick={() => setEditing({ parent: n.id })} title={t('hrDepts.addSub')} className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400"><Plus className="w-3.5 h-3.5" /></button>
            <button onClick={() => setEditing(n)} title={t('hrDepts.edit')} className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400"><Pencil className="w-3.5 h-3.5" /></button>
            <button onClick={() => remove(n)} title={t('hrDepts.delete')} className="p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-500 hover:text-rose-400"><Trash2 className="w-3.5 h-3.5" /></button>
          </div>
        </div>
        {n.children.length > 0 && (
          <div className="ps-6 space-y-3 border-s border-white/5">{n.children.map((c) => renderNode(c, depth + 1))}</div>
        )}
      </div>
    );
  };

  const blocked = editing?.id ? descendants(flat || [], editing.id) : new Set<string>();

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('hrDepts.title')}</h1>
          <p className="page-subtitle">{t('hrDepts.subtitle')}</p>
        </div>
        <button onClick={() => setEditing({})} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> {t('hrDepts.add')}
        </button>
      </div>

      {!flat && !loadError && <LoadingCard label={t('hrDepts.loading')} />}
      {loadError && <div className="glass-card p-6 text-rose-400 text-sm">{t('hrDepts.loadFailed', { msg: loadError })}</div>}
      {flat && tree.length === 0 && <EmptyCard label={t('hrDepts.empty')} />}

      {flat && tree.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="glass-card p-6 lg:col-span-2 space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('hrDepts.orgTree')}</h2>
            {tree.map((n) => renderNode(n, 0))}
          </div>
          <div className="space-y-6">
            <div className="glass-card p-6">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('hrDepts.rollupStats')}</h2>
              <div className="space-y-4 text-sm">
                {([['totalDepartments', flat.length], ['totalEmployees', totalEmps], ['rootDepartments', tree.length]] as const).map(([k, v]) => (
                  <div key={k} className="flex justify-between items-center pb-3 border-b border-white/5">
                    <span className="text-slate-400">{t(`hrDepts.${k}`)}</span>
                    <span className="text-white font-bold">{v}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="glass-card p-6 border-cyan-500/20">
              <h3 className="text-sm font-bold text-white mb-2">{t('hrDepts.countLogicHeading')}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{t('hrDepts.countLogicBody')}</p>
            </div>
          </div>
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/5 p-5">
              <h3 className="font-bold text-white">{editing.id ? t('hrDepts.edit') : t('hrDepts.add')}</h3>
              <button onClick={() => setEditing(null)} className="p-1.5 hover:bg-slate-800 rounded-lg"><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <div className="p-5 space-y-3 text-xs">
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('hrDepts.name')}</label>
                <input value={editing.name || ''} onChange={(e) => setEditing({ ...editing, name: e.target.value })} className={inputCls} />
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('hrDepts.code')}</label>
                <input value={editing.code || ''} onChange={(e) => setEditing({ ...editing, code: e.target.value })} className={inputCls} />
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('hrDepts.parent')}</label>
                <select value={editing.parent || ''} onChange={(e) => setEditing({ ...editing, parent: e.target.value || null })} className={inputCls}>
                  <option value="">{t('hrDepts.topLevel')}</option>
                  {(flat || []).filter((d) => d.id !== editing.id && !blocked.has(d.id)).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('hrDepts.manager')}</label>
                <select value={editing.manager || ''} onChange={(e) => setEditing({ ...editing, manager: e.target.value || null })} className={inputCls}>
                  <option value="">{t('hrDepts.unassigned')}</option>
                  {employees.map((e) => <option key={e.id} value={e.id}>{e.first_name} {e.last_name} ({e.employee_number})</option>)}
                </select>
              </div>
              {formError && <div className="p-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400">{formError.map((m, i) => <p key={i}>{m}</p>)}</div>}
            </div>
            <div className="flex justify-end gap-3 border-t border-white/5 p-5">
              <button onClick={() => setEditing(null)} className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg text-xs font-semibold">{t('hrDepts.cancel')}</button>
              <button onClick={save} disabled={saving || !editing.name?.trim()} className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-white font-semibold text-xs">
                {saving && <Loader2 className="w-4 h-4 animate-spin" />} {t('hrDepts.save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
