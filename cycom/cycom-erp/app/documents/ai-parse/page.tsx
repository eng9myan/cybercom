'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft, Sparkles, Upload, FileText, CheckCircle2, AlertTriangle,
  Loader2, RefreshCw, Plus, Trash2, X,
} from 'lucide-react';
import { useT } from '@/lib/i18n';

type DocType = 'invoice' | 'purchase_order' | 'bank_statement';
type Status = 'pending' | 'parsed' | 'failed' | 'reviewed';

interface ParsedDoc {
  id: string;
  document_type: DocType;
  file: string;
  original_filename: string;
  status: Status;
  extracted_data: Record<string, any>;
  error_message: string;
  reviewed_data: Record<string, any> | null;
  created_at: string;
}

const DOC_TYPES: DocType[] = ['invoice', 'purchase_order', 'bank_statement'];

function statusTone(status: Status) {
  if (status === 'parsed') return 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400';
  if (status === 'reviewed') return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
  if (status === 'failed') return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
  return 'bg-slate-800 border-slate-700 text-slate-400';
}

/** Renders + edits one extracted-data object generically: scalars become
 * inputs, arrays-of-objects (line_items/transactions) become a small
 * editable table -- the same component works for all 3 document types
 * without hardcoding their schemas twice (once server-side, once here). */
function ReviewFields({ data, onChange }: { data: Record<string, any>; onChange: (d: Record<string, any>) => void }) {
  const t = useT();
  const scalarKeys = Object.keys(data).filter((k) => !Array.isArray(data[k]));
  const arrayKeys = Object.keys(data).filter((k) => Array.isArray(data[k]));

  const setScalar = (key: string, value: string) => onChange({ ...data, [key]: value });

  const setArrayCell = (key: string, idx: number, field: string, value: string) => {
    const rows = [...(data[key] || [])];
    rows[idx] = { ...rows[idx], [field]: value };
    onChange({ ...data, [key]: rows });
  };

  const addRow = (key: string, columns: string[]) => {
    const blank: Record<string, string> = {};
    columns.forEach((c) => { blank[c] = ''; });
    onChange({ ...data, [key]: [...(data[key] || []), blank] });
  };

  const removeRow = (key: string, idx: number) => {
    const rows = [...(data[key] || [])];
    rows.splice(idx, 1);
    onChange({ ...data, [key]: rows });
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        {scalarKeys.map((key) => (
          <div key={key}>
            <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{key.replace(/_/g, ' ')}</label>
            <input
              value={data[key] ?? ''}
              onChange={(e) => setScalar(key, e.target.value)}
              className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none mt-0.5 text-xs"
            />
          </div>
        ))}
      </div>

      {arrayKeys.map((key) => {
        const rows: Record<string, any>[] = data[key] || [];
        const columns = rows.length > 0 ? Object.keys(rows[0]) : ['description', 'amount'];
        return (
          <div key={key} className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{key.replace(/_/g, ' ')}</label>
              <button onClick={() => addRow(key, columns)} className="flex items-center gap-1 text-[10px] text-cyan-400 hover:text-cyan-300">
                <Plus className="w-3 h-3" /> {t('docaiParse.addRow')}
              </button>
            </div>
            <div className="border border-slate-850 rounded-xl overflow-x-auto">
              <table className="w-full min-w-[420px] text-[11px]">
                <thead>
                  <tr className="bg-slate-950 text-slate-500 uppercase border-b border-slate-850">
                    {columns.map((c) => <th key={c} className="p-2 text-start font-bold">{c.replace(/_/g, ' ')}</th>)}
                    <th className="p-2 w-8" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {rows.map((row, idx) => (
                    <tr key={idx}>
                      {columns.map((c) => (
                        <td key={c} className="p-1.5">
                          <input
                            value={row[c] ?? ''}
                            onChange={(e) => setArrayCell(key, idx, c, e.target.value)}
                            className="w-full bg-transparent border-none outline-none text-slate-200"
                          />
                        </td>
                      ))}
                      <td className="p-1.5">
                        <button onClick={() => removeRow(key, idx)} className="text-slate-600 hover:text-rose-400">
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {rows.length === 0 && (
                    <tr><td colSpan={columns.length + 1} className="p-3 text-center text-slate-600">{t('docaiParse.noRows')}</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function DocAIParsePage() {
  const t = useT();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [docs, setDocs] = useState<ParsedDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [docType, setDocType] = useState<DocType>('invoice');
  const [selected, setSelected] = useState<ParsedDoc | null>(null);
  const [draft, setDraft] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    fetch('/api/cycom/rest/docai/documents/', { credentials: 'include' })
      .then((r) => r.json())
      .then((data: ParsedDoc[]) => setDocs(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('document_type', docType);
    formData.append('file', file);
    try {
      await fetch('/api/cycom/rest/docai/documents/', {
        method: 'POST', credentials: 'include', body: formData,
      });
      load();
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const openDoc = (doc: ParsedDoc) => {
    setSelected(doc);
    setDraft(doc.reviewed_data || doc.extracted_data || {});
  };

  const handleSaveReview = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const resp = await fetch(`/api/cycom/rest/docai/documents/${selected.id}/review/`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviewed_data: draft }),
      });
      if (resp.ok) {
        setSelected(null);
        load();
      }
    } finally {
      setSaving(false);
    }
  };

  const handleReparse = async (doc: ParsedDoc) => {
    await fetch(`/api/cycom/rest/docai/documents/${doc.id}/reparse/`, {
      method: 'POST', credentials: 'include',
    });
    load();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-5xl mx-auto flex items-center gap-4 mb-8">
        <button onClick={() => router.push('/documents')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-[#A855F7] to-[#00F0FF] bg-clip-text text-transparent flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-[#A855F7]" /> {t('docaiParse.title')}
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('docaiParse.subtitle')}</p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto space-y-6">
        <div className="glass-card p-5 flex flex-wrap items-center gap-3">
          <select
            value={docType} onChange={(e) => setDocType(e.target.value as DocType)}
            className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
          >
            {DOC_TYPES.map((dt) => <option key={dt} value={dt}>{t(`docaiParse.type.${dt}`)}</option>)}
          </select>
          <input
            ref={fileInputRef} type="file" accept="application/pdf,image/png,image/jpeg,image/webp"
            onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
            className="hidden" id="docai-file-input"
          />
          <label
            htmlFor="docai-file-input"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-[#A855F7] to-[#00F0FF] text-white font-bold cursor-pointer hover:opacity-90 transition"
          >
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            {uploading ? t('docaiParse.uploading') : t('docaiParse.uploadBtn')}
          </label>
          <span className="text-[10px] text-slate-500">{t('docaiParse.uploadHint')}</span>
        </div>

        <div className="glass-card p-5 space-y-1">
          {loading ? (
            <div className="py-8 text-center text-slate-500">{t('docaiParse.loading')}</div>
          ) : docs.length === 0 ? (
            <div className="py-10 text-center text-slate-500 flex flex-col items-center gap-2">
              <FileText className="w-6 h-6 text-slate-700" />
              {t('docaiParse.emptyState')}
            </div>
          ) : (
            docs.map((doc) => (
              <button
                key={doc.id}
                onClick={() => (doc.status === 'failed' ? undefined : openDoc(doc))}
                className="w-full flex items-center justify-between gap-3 p-3 rounded-xl hover:bg-white/5 transition-colors text-start"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <FileText className="w-4 h-4 text-slate-500 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-200 truncate">{doc.original_filename}</p>
                    <p className="text-[10px] text-slate-500">{t(`docaiParse.type.${doc.document_type}`)} · {new Date(doc.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {doc.status === 'failed' && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleReparse(doc); }}
                      className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400"
                      title={t('docaiParse.retryParse')}
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${statusTone(doc.status)}`}>
                    {t(`docaiParse.status.${doc.status}`)}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/5 p-5">
              <div>
                <h3 className="font-bold text-white">{selected.original_filename}</h3>
                <p className="text-[10px] text-slate-500">{t(`docaiParse.type.${selected.document_type}`)}</p>
              </div>
              <button onClick={() => setSelected(null)} className="p-1.5 hover:bg-slate-800 rounded-lg transition">
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>
            <div className="p-5">
              {selected.status === 'failed' ? (
                <div className="flex items-start gap-3 p-4 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{selected.error_message}</span>
                </div>
              ) : (
                <ReviewFields data={draft} onChange={setDraft} />
              )}
            </div>
            {selected.status !== 'failed' && (
              <div className="flex justify-end gap-3 border-t border-white/5 p-5">
                <button onClick={() => setSelected(null)} className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition text-xs font-semibold">
                  {t('docaiParse.cancel')}
                </button>
                <button
                  onClick={handleSaveReview}
                  disabled={saving}
                  className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-white font-semibold shadow-lg shadow-emerald-600/15 transition text-xs"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  {t('docaiParse.markReviewed')}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
