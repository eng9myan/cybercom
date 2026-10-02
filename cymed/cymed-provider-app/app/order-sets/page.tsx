'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ListChecks, Search, Send, X } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type OrderSetItem = {
  id: string;
  order_type: string;
  code: string;
  display: string;
  quantity: number;
  priority: string;
  instructions: string;
  default_selected: boolean;
  sort_order: number;
};

type OrderSet = {
  id: string;
  code: string;
  name: string;
  description: string;
  specialty: string;
  is_active: boolean;
  items: OrderSetItem[];
};

type Page<T> = { results: T[]; next: string | null };

type CreatedOrder = {
  id: string;
  order_type: string;
  status: string;
};

async function fetchAll<T>(url: string): Promise<T[]> {
  const all: T[] = [];
  let next: string | null = url;
  while (next) {
    const res = await fetch(next, { credentials: 'include' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const json = (await res.json()) as Page<T>;
    all.push(...json.results);
    next = json.next;
  }
  return all;
}

export default function OrderSetsPage() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();

  const [sets, setSets] = useState<OrderSet[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');

  const [selected, setSelected] = useState<OrderSet | null>(null);
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());
  const [patientId, setPatientId] = useState('');
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applyResult, setApplyResult] = useState<CreatedOrder[] | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchAll<OrderSet>('/api/cymed/rest/order-sets/?is_active=true')
      .then((rows) => setSets(rows))
      .catch((e) => setError(e instanceof Error ? e.message : t('orderSets.loadFailed')))
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => {
    if (!authLoading && user) load();
  }, [authLoading, user, load]);

  const filtered = useMemo(() => {
    if (!sets) return [];
    const q = query.trim().toLowerCase();
    if (!q) return sets;
    return sets.filter(
      (s) => s.name.toLowerCase().includes(q) || s.specialty.toLowerCase().includes(q) || s.code.toLowerCase().includes(q),
    );
  }, [sets, query]);

  const openSet = (s: OrderSet) => {
    setSelected(s);
    setCheckedItems(new Set(s.items.filter((i) => i.default_selected).map((i) => i.id)));
    setPatientId('');
    setApplyError(null);
    setApplyResult(null);
  };

  const toggleItem = (id: string) => {
    setCheckedItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const apply = async () => {
    if (!selected || !patientId.trim()) {
      setApplyError(t('orderSets.patientRequired'));
      return;
    }
    setApplying(true);
    setApplyError(null);
    try {
      const res = await fetch(`/api/cymed/rest/order-sets/${selected.id}/apply/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ patient: patientId.trim(), item_ids: Array.from(checkedItems) }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      }
      setApplyResult(body as CreatedOrder[]);
    } catch (e) {
      setApplyError(e instanceof Error ? e.message : t('orderSets.applyFailed'));
    } finally {
      setApplying(false);
    }
  };

  if (authLoading) {
    return <LoadingCard label={t('common.loading')} />;
  }

  if (!user) {
    return (
      <div className="glass-card p-10 text-center max-w-md mx-auto mt-16">
        <h2 className="text-lg font-bold mb-2">{t('auth.signInTitle')}</h2>
        <p className="text-sm text-slate-400 mb-5">{t('auth.signInDetail')}</p>
        <a href="/login" className="btn-primary inline-block">{t('auth.signIn')}</a>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('orderSets.title')}</h1>
          <p className="page-subtitle">{t('orderSets.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2 bg-white/3 border border-white/8 rounded-xl px-3 py-1.5 w-[280px]">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('orderSets.searchPlaceholder')}
            className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full"
          />
        </div>
      </div>

      {loading ? (
        <LoadingCard label={t('common.loading')} />
      ) : error ? (
        <ErrorCard error={error} />
      ) : filtered.length === 0 ? (
        <EmptyCard label={t('orderSets.empty')} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((s) => (
            <button
              key={s.id}
              onClick={() => openSet(s)}
              className="glass-card p-4 text-start hover:border-[var(--cy-teal)]/30 transition-colors"
            >
              <div className="flex items-center gap-2 mb-1">
                <ListChecks className="w-4 h-4 text-[var(--cy-teal)]" />
                <span className="font-bold text-white text-sm">{s.name}</span>
              </div>
              {s.specialty && <span className="badge badge-blue mb-2">{s.specialty}</span>}
              <p className="text-xs text-slate-500 line-clamp-2">{s.description}</p>
              <p className="text-[10px] text-slate-600 mt-2">{t('orderSets.itemCount', { n: s.items.length })}</p>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-lg space-y-3 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white">{selected.name}</h3>
                {selected.specialty && <span className="badge badge-blue">{selected.specialty}</span>}
              </div>
              <button onClick={() => setSelected(null)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-slate-400">{selected.description}</p>

            <div className="space-y-1.5">
              {selected.items
                .slice()
                .sort((a, b) => a.sort_order - b.sort_order)
                .map((item) => (
                  <label
                    key={item.id}
                    className="flex items-start gap-2 p-2 rounded-lg hover:bg-white/5 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={checkedItems.has(item.id)}
                      onChange={() => toggleItem(item.id)}
                      className="mt-0.5"
                    />
                    <span className="flex-1">
                      <span className="text-sm text-white">{item.display}</span>
                      <span className="block text-[10px] text-slate-500">
                        {item.order_type} · {item.code} · {t('orderSets.qty')} {item.quantity}
                        {item.instructions && ` · ${item.instructions}`}
                      </span>
                    </span>
                    <span className="badge badge-yellow text-[9px]">{item.priority}</span>
                  </label>
                ))}
            </div>

            <div className="pt-2 border-t border-white/5 space-y-2">
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder={t('orderSets.patientIdPlaceholder')}
                className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500"
              />
              {applyError && <p className="text-xs text-rose-400">{applyError}</p>}
              {applyResult && (
                <div className="text-xs text-emerald-400">
                  {t('orderSets.applySuccess', { n: applyResult.length })}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <button onClick={() => setSelected(null)} className="btn-secondary text-xs px-3 py-1.5">
                  {t('common.cancel')}
                </button>
                <button
                  onClick={apply}
                  disabled={applying || checkedItems.size === 0}
                  className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1"
                >
                  <Send className="w-3.5 h-3.5" />
                  {t('orderSets.apply')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
