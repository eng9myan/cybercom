'use client';

import React, { useEffect, useState } from 'react';
import { ShieldCheck, Loader2, Save, Check } from 'lucide-react';
import { useT } from '@/lib/i18n';

type Tier = { id?: number; sequence: number; threshold_min: string; threshold_max: string | null; approver_role: string };
type Policy = { id: number; document_type: string; name: string; currency: string; is_active: boolean; tiers: Tier[] };

function recomputeMins(tiers: Tier[]): Tier[] {
  let prevMax = '0';
  const out = tiers.map((tr, i) => {
    const min = i === 0 ? '0' : prevMax;
    prevMax = tr.threshold_max ?? '0';
    return { ...tr, sequence: i + 1, threshold_min: min };
  });
  if (out.length) out[out.length - 1] = { ...out[out.length - 1], threshold_max: null }; // only the last band may be open-ended
  return out;
}

export default function ApprovalPoliciesPage() {
  const t = useT();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [savedId, setSavedId] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/cycom/provisioning/approval-policies/');
      if (!res.ok) throw new Error(`${t('approvalPolicies.loadError')} (${res.status})`);
      const data = await res.json();
      const rows: Policy[] = (data.results ?? data) as Policy[];
      setPolicies(rows.map((p) => ({ ...p, tiers: [...p.tiers].sort((a, b) => a.sequence - b.sequence) })));
    } catch (e: any) {
      setError(e.message || t('approvalPolicies.loadError'));
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const patch = (id: number, updater: (p: Policy) => Policy) =>
    setPolicies((rows) => rows.map((p) => (p.id === id ? updater(p) : p)));

  const toggleActive = (id: number) => patch(id, (p) => ({ ...p, is_active: !p.is_active }));

  const updateTier = (id: number, index: number, field: 'threshold_max' | 'approver_role', value: string) =>
    patch(id, (p) => ({ ...p, tiers: recomputeMins(p.tiers.map((tr, i) => (i === index ? { ...tr, [field]: value } : tr))) }));

  const addTier = (id: number) =>
    patch(id, (p) => {
      const tiers = [...p.tiers];
      const last = tiers[tiers.length - 1];
      const newLast: Tier = { sequence: tiers.length + 1, threshold_min: '0', threshold_max: null, approver_role: last?.approver_role || '' };
      if (last) tiers[tiers.length - 1] = { ...last, threshold_max: String(Number(last.threshold_min || 0) + 100) };
      return { ...p, tiers: recomputeMins([...tiers, newLast]) };
    });

  const removeTier = (id: number, index: number) =>
    patch(id, (p) => ({ ...p, tiers: recomputeMins(p.tiers.filter((_, i) => i !== index)) }));

  const save = async (policy: Policy) => {
    setSavingId(policy.id);
    setSavedId(null);
    setError(null);
    try {
      const res = await fetch(`/api/cycom/provisioning/approval-policies/${policy.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          is_active: policy.is_active,
          tiers: policy.tiers.map((tr) => ({
            sequence: tr.sequence, threshold_min: tr.threshold_min,
            threshold_max: tr.threshold_max, approver_role: tr.approver_role,
          })),
        }),
      });
      if (!res.ok) throw new Error((await res.json())?.detail || `${t('approvalPolicies.saveError')} (${res.status})`);
      const updated = await res.json();
      patch(policy.id, () => ({ ...updated, tiers: [...updated.tiers].sort((a: Tier, b: Tier) => a.sequence - b.sequence) }));
      setSavedId(policy.id);
      setTimeout(() => setSavedId((id) => (id === policy.id ? null : id)), 2000);
    } catch (e: any) {
      setError(e.message || t('approvalPolicies.saveError'));
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
      <header>
        <h1 className="page-title flex items-center gap-2"><ShieldCheck className="w-5 h-5 text-[var(--cy-orange)]" /> {t('approvalPolicies.title')}</h1>
        <p className="page-subtitle">{t('approvalPolicies.subtitle')}</p>
      </header>

      {loading && (
        <div className="flex items-center justify-center py-16 text-slate-400 gap-2 text-sm">
          <Loader2 className="w-5 h-5 animate-spin" /> {t('common.loading')}
        </div>
      )}

      {error && (
        <div className="glass-card p-4 border border-rose-500/30 bg-rose-500/5 text-sm text-rose-300">{error}</div>
      )}

      {!loading && policies.length === 0 && !error && (
        <div className="glass-card py-16 text-center text-slate-500 text-sm border border-dashed border-white/10">
          {t('approvalPolicies.empty')}
        </div>
      )}

      <div className="space-y-4">
        {policies.map((p) => (
          <div key={p.id} className={`glass-card p-5 border transition-colors ${p.is_active ? 'border-white/10' : 'border-white/5 opacity-70'}`}>
            <div className="flex items-center justify-between gap-3 mb-3">
              <div>
                <div className="text-sm font-semibold text-white">{p.name}</div>
                <div className="text-[10px] font-mono uppercase text-slate-500">{p.document_type} · {p.currency}</div>
              </div>
              <button type="button" onClick={() => toggleActive(p.id)}
                className={`w-9 h-5 rounded-full relative transition-colors shrink-0 ${p.is_active ? 'bg-emerald-500/60' : 'bg-white/10'}`}>
                <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ${p.is_active ? 'start-4' : 'start-0.5'}`} />
              </button>
            </div>

            {p.is_active ? (
              <div className="space-y-1.5">
                {p.tiers.map((tier, i) => (
                  <div key={tier.id ?? i} className="flex items-center gap-2">
                    <span className="text-[11px] text-slate-500 w-16 shrink-0">{t('readyErp.approvalTierFrom', { min: tier.threshold_min })}</span>
                    <input type="number" className="input-field py-1.5 text-xs max-w-[110px] shrink-0" placeholder={t('readyErp.approvalNoLimit')}
                      value={tier.threshold_max ?? ''} disabled={i === p.tiers.length - 1}
                      onChange={(e) => updateTier(p.id, i, 'threshold_max', e.target.value)} />
                    <input type="text" className="input-field py-1.5 text-xs flex-1 min-w-0" value={tier.approver_role}
                      placeholder={t('readyErp.approvalRolePh')}
                      onChange={(e) => updateTier(p.id, i, 'approver_role', e.target.value)} />
                    {p.tiers.length > 1 && (
                      <button type="button" onClick={() => removeTier(p.id, i)} className="text-slate-500 hover:text-rose-400 px-1 text-sm leading-none">×</button>
                    )}
                  </div>
                ))}
                <button type="button" onClick={() => addTier(p.id)} className="text-[11px] text-[var(--cy-orange)] hover:underline">
                  + {t('readyErp.approvalAddTier')}
                </button>
              </div>
            ) : (
              <p className="text-[11px] text-slate-500">{t('readyErp.approvalDisabledNote')}</p>
            )}

            <div className="flex justify-end mt-3">
              <button type="button" onClick={() => save(p)} disabled={savingId === p.id}
                className="btn-primary inline-flex items-center gap-1.5 text-xs py-1.5 px-3 disabled:opacity-60">
                {savingId === p.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : savedId === p.id ? <Check className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
                {t('common.save')}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
