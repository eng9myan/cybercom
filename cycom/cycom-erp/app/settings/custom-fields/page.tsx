'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Plus, Trash2, Tag, X } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface RegistryEntry { key: string; label: string }
interface Definition {
  id: string;
  model_key: string;
  field_key: string;
  label: string;
  field_type: 'text' | 'number' | 'date' | 'boolean' | 'select';
  options: string[];
  is_required: boolean;
  is_active: boolean;
}

const FIELD_TYPES: Definition['field_type'][] = ['text', 'number', 'date', 'boolean', 'select'];

export default function CustomFieldsSettingsPage() {
  const t = useT();
  const router = useRouter();

  const [models, setModels] = useState<RegistryEntry[]>([]);
  const [modelKey, setModelKey] = useState('');
  const [definitions, setDefinitions] = useState<Definition[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [draftLabel, setDraftLabel] = useState('');
  const [draftType, setDraftType] = useState<Definition['field_type']>('text');
  const [draftOptions, setDraftOptions] = useState('');
  const [draftRequired, setDraftRequired] = useState(false);

  useEffect(() => {
    fetch('/api/cycom/rest/customfields/registry/', { credentials: 'include' })
      .then((r) => r.json())
      .then((data: RegistryEntry[]) => {
        setModels(data);
        if (data.length > 0) setModelKey(data[0].key);
      });
  }, []);

  const loadDefinitions = (key: string) => {
    if (!key) return;
    setLoading(true);
    fetch(`/api/cycom/rest/customfields/definitions/?model_key=${key}`, { credentials: 'include' })
      .then((r) => r.json())
      .then((data: Definition[]) => setDefinitions(data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadDefinitions(modelKey); }, [modelKey]);

  const slugify = (s: string) =>
    s.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 50);

  const handleCreate = async () => {
    setError(null);
    const fieldKey = slugify(draftLabel);
    if (!draftLabel.trim() || !fieldKey) {
      setError(t('customFields.labelRequired'));
      return;
    }
    const options = draftType === 'select'
      ? draftOptions.split(',').map((o) => o.trim()).filter(Boolean)
      : [];
    if (draftType === 'select' && options.length === 0) {
      setError(t('customFields.optionsRequired'));
      return;
    }
    const resp = await fetch('/api/cycom/rest/customfields/definitions/', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_key: modelKey, field_key: fieldKey, label: draftLabel.trim(),
        field_type: draftType, options, is_required: draftRequired,
      }),
    });
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      setError(body.detail || t('customFields.saveFailed'));
      return;
    }
    setDraftLabel(''); setDraftType('text'); setDraftOptions(''); setDraftRequired(false);
    setCreating(false);
    loadDefinitions(modelKey);
  };

  const toggleActive = async (defn: Definition) => {
    await fetch(`/api/cycom/rest/customfields/definitions/${defn.id}/`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !defn.is_active }),
    });
    loadDefinitions(modelKey);
  };

  const deleteDefinition = async (defn: Definition) => {
    if (!confirm(t('customFields.confirmDelete', { label: defn.label }))) return;
    await fetch(`/api/cycom/rest/customfields/definitions/${defn.id}/`, {
      method: 'DELETE',
      credentials: 'include',
    });
    loadDefinitions(modelKey);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex items-center gap-4 mb-8">
        <button
          onClick={() => router.push('/settings')}
          className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
        >
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
            {t('customFields.title')}
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('customFields.subtitle')}</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto space-y-6">
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <label className="text-slate-400 font-semibold">{t('customFields.modelLabel')}</label>
              <select
                value={modelKey}
                onChange={(e) => setModelKey(e.target.value)}
                className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
              >
                {models.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
              </select>
            </div>
            <button
              onClick={() => setCreating(true)}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600/90 hover:bg-amber-500 rounded-lg text-white font-semibold transition"
            >
              <Plus className="w-4 h-4" /> {t('customFields.addField')}
            </button>
          </div>

          {creating && (
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-850 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-slate-300">{t('customFields.newFieldHeading')}</h4>
                <button onClick={() => setCreating(false)} className="p-1 hover:bg-slate-800 rounded-lg transition">
                  <X className="w-4 h-4 text-slate-500" />
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] text-slate-500 font-bold uppercase">{t('customFields.fieldLabel')}</label>
                  <input
                    value={draftLabel} onChange={(e) => setDraftLabel(e.target.value)}
                    placeholder={t('customFields.fieldLabelPh')}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-slate-500 font-bold uppercase">{t('customFields.fieldType')}</label>
                  <select
                    value={draftType} onChange={(e) => setDraftType(e.target.value as Definition['field_type'])}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                  >
                    {FIELD_TYPES.map((ft) => <option key={ft} value={ft}>{t(`customFields.type.${ft}`)}</option>)}
                  </select>
                </div>
                {draftType === 'select' && (
                  <div className="col-span-2 space-y-1">
                    <label className="text-[10px] text-slate-500 font-bold uppercase">{t('customFields.optionsCsv')}</label>
                    <input
                      value={draftOptions} onChange={(e) => setDraftOptions(e.target.value)}
                      placeholder={t('customFields.optionsCsvPh')}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                )}
                <label className="col-span-2 flex items-center gap-2 text-slate-400">
                  <input type="checkbox" checked={draftRequired} onChange={(e) => setDraftRequired(e.target.checked)} />
                  {t('customFields.markRequired')}
                </label>
              </div>
              {error && <p className="text-[11px] text-rose-400">{error}</p>}
              <button
                onClick={handleCreate}
                className="px-4 py-2 bg-amber-600/90 hover:bg-amber-500 rounded-lg text-white font-semibold transition"
              >
                {t('customFields.saveBtn')}
              </button>
            </div>
          )}

          <div className="divide-y divide-white/5">
            {loading ? (
              <div className="py-8 text-center text-slate-500">{t('customFields.loading')}</div>
            ) : definitions.length === 0 ? (
              <div className="py-8 text-center text-slate-500 flex flex-col items-center gap-2">
                <Tag className="w-6 h-6 text-slate-700" />
                {t('customFields.emptyState')}
              </div>
            ) : (
              definitions.map((defn) => (
                <div key={defn.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-200 truncate">
                      {defn.label}{defn.is_required && <span className="text-rose-400"> *</span>}
                    </p>
                    <p className="text-[10px] text-slate-500 font-mono">
                      {defn.field_key} · {t(`customFields.type.${defn.field_type}`)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => toggleActive(defn)}
                      className={`px-2.5 py-1 rounded-full text-[10px] font-bold border transition ${
                        defn.is_active
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                          : 'bg-slate-900 border-slate-800 text-slate-500'
                      }`}
                    >
                      {defn.is_active ? t('customFields.active') : t('customFields.inactive')}
                    </button>
                    <button
                      onClick={() => deleteDefinition(defn)}
                      className="p-1.5 rounded-lg hover:bg-rose-500/10 text-slate-500 hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
