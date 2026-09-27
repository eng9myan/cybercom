'use client';

import React, { useEffect, useState } from 'react';
import { Tag, Save, Loader2 } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface FieldValue {
  field_key: string;
  label: string;
  field_type: 'text' | 'number' | 'date' | 'boolean' | 'select';
  options: string[];
  required: boolean;
  value: any;
}

interface CustomFieldsPanelProps {
  /** One of products.cycom.customfields.registry.CUSTOMFIELD_MODELS' keys. */
  modelKey: string;
  recordId: string;
}

/**
 * Renders whatever custom fields a tenant has defined for `modelKey` against
 * one real record, and saves edits back onto that record's own `attributes`
 * JSON via the customfields API. Renders nothing when no fields are defined
 * for this model yet -- most records on most tenants won't have any.
 */
export default function CustomFieldsPanel({ modelKey, recordId }: CustomFieldsPanelProps) {
  const t = useT();
  const [fields, setFields] = useState<FieldValue[] | null>(null);
  const [draft, setDraft] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!recordId) return;
    fetch(`/api/cycom/rest/customfields/values/?model_key=${modelKey}&record_id=${recordId}`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : []))
      .then((data: FieldValue[]) => {
        setFields(data);
        const initial: Record<string, any> = {};
        data.forEach((f) => { initial[f.field_key] = f.value; });
        setDraft(initial);
      })
      .catch(() => setFields([]));
  }, [modelKey, recordId]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const resp = await fetch('/api/cycom/rest/customfields/values/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_key: modelKey, record_id: recordId, values: draft }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.errors ? Object.values(body.errors).join(' ') : (body.detail || t('customFields.saveFailed')));
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!fields || fields.length === 0) return null;

  return (
    <div className="glass-card p-6 space-y-4">
      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
        <Tag className="w-4 h-4 text-amber-400" /> {t('customFields.panelHeading')}
      </h3>
      <div className="space-y-3">
        {fields.map((f) => (
          <div key={f.field_key}>
            <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
              {f.label}{f.required && <span className="text-rose-400"> *</span>}
            </label>
            {f.field_type === 'select' ? (
              <select
                value={draft[f.field_key] ?? ''}
                onChange={(e) => setDraft((d) => ({ ...d, [f.field_key]: e.target.value }))}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none mt-0.5"
              >
                <option value="">—</option>
                {f.options.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
              </select>
            ) : f.field_type === 'boolean' ? (
              <div className="mt-1">
                <button
                  type="button"
                  onClick={() => setDraft((d) => ({ ...d, [f.field_key]: !d[f.field_key] }))}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition ${
                    draft[f.field_key] ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-slate-950 border-slate-850 text-slate-400'
                  }`}
                >
                  {draft[f.field_key] ? t('customFields.yes') : t('customFields.no')}
                </button>
              </div>
            ) : (
              <input
                type={f.field_type === 'number' ? 'number' : f.field_type === 'date' ? 'date' : 'text'}
                value={draft[f.field_key] ?? ''}
                onChange={(e) => setDraft((d) => ({ ...d, [f.field_key]: e.target.value }))}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none mt-0.5"
              />
            )}
          </div>
        ))}
      </div>
      {error && <p className="text-[11px] text-rose-400">{error}</p>}
      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full flex items-center justify-center gap-2 py-2 bg-amber-600/90 hover:bg-amber-500 disabled:opacity-50 rounded-lg text-white text-xs font-bold transition"
      >
        {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
        {saved ? t('customFields.saved') : t('customFields.saveBtn')}
      </button>
    </div>
  );
}
