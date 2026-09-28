'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft, Sparkles, Upload, FileText, CheckCircle2, AlertTriangle,
  Loader2, RefreshCw, Plus, Trash2, X, FilePlus2, ExternalLink,
} from 'lucide-react';
import { useT } from '@/lib/i18n';
import { formatApiErrors } from '@/lib/apiErrors';

type DocType = 'invoice' | 'purchase_order' | 'bank_statement';
type Status = 'pending' | 'parsed' | 'failed' | 'reviewed' | 'applied';

interface ParsedDoc {
  id: string;
  document_type: DocType;
  file: string;
  original_filename: string;
  status: Status;
  extracted_data: Record<string, any>;
  error_message: string;
  reviewed_data: Record<string, any> | null;
  applied_record_type: '' | 'invoice' | 'purchase_order';
  applied_record_id: string | null;
  created_at: string;
}

interface Option { id: string; label: string; name?: string; partner_type?: string; account_type?: string }
interface ApplyOptions { partners: Option[]; accounts: Option[]; warehouses: Option[]; products: Option[] }

const DOC_TYPES: DocType[] = ['invoice', 'purchase_order', 'bank_statement'];

function recordHref(doc: ParsedDoc) {
  if (!doc.applied_record_id) return null;
  if (doc.applied_record_type === 'invoice') return `/accounting/invoices/${doc.applied_record_id}`;
  if (doc.applied_record_type === 'purchase_order') return `/purchase/orders/${doc.applied_record_id}`;
  return null;
}

const norm = (s: unknown) => String(s ?? '').trim().toLowerCase();

/** Best-effort preselect: an exact (case-insensitive) name match only.
 * Anything fuzzier risks silently attaching the wrong partner/product. */
function matchByName(options: Option[], name: unknown, key: (o: Option) => string = (o) => o.label) {
  const n = norm(name);
  if (!n) return '';
  return options.find((o) => norm(key(o)) === n)?.id || '';
}

function num(v: unknown): number | null {
  if (v === null || v === undefined || String(v).trim() === '') return null;
  const n = Number(String(v).replace(/,/g, ''));
  return Number.isFinite(n) ? n : null;
}

function Picker({ label, value, onChange, options, allowNone, noneLabel, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; options: Option[];
  allowNone?: boolean; noneLabel?: string; placeholder: string;
}) {
  return (
    <div>
      <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none mt-0.5 text-xs"
      >
        <option value="">{allowNone ? noneLabel : placeholder}</option>
        {options.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
      </select>
    </div>
  );
}

/** Turns a reviewed invoice/PO into a real draft record. The reviewer picks
 * the FKs the AI can't read off a page (partner, accounts, warehouse, and a
 * product per PO line); the backend re-validates every one of them against
 * the tenant and runs the real Invoice/PO serializers. */
function ApplyPanel({ doc, draft, onApplied }: {
  doc: ParsedDoc; draft: Record<string, any>; onApplied: (d: ParsedDoc) => void;
}) {
  const t = useT();
  const [options, setOptions] = useState<ApplyOptions | null>(null);
  const [params, setParams] = useState<Record<string, any>>({});
  const [applying, setApplying] = useState(false);
  const [errors, setErrors] = useState<string[] | null>(null);

  const reviewed = doc.reviewed_data || {};
  const lineItems: Record<string, any>[] = Array.isArray(reviewed.line_items) ? reviewed.line_items : [];
  const dirty = JSON.stringify(draft) !== JSON.stringify(reviewed);

  useEffect(() => {
    fetch('/api/cycom/rest/docai/documents/apply-options/', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((opts: ApplyOptions | null) => {
        if (!opts) return;
        setOptions(opts);
        const partnerId = matchByName(opts.partners, reviewed.vendor_name);
        if (doc.document_type === 'invoice') {
          const sub = num(reviewed.subtotal);
          const tax = num(reviewed.tax_amount);
          const pct = sub && tax && sub > 0 ? Math.round((tax / sub) * 10000) / 100 : 0;
          setParams({ invoice_type: 'vendor', partner: partnerId, tax_percent: String(pct) });
        } else {
          setParams({
            vendor: partnerId,
            line_products: lineItems.map((li) =>
              matchByName(opts.products, li.description, (o) => o.name || o.label)),
          });
        }
      });
    // Options only need loading once per opened document.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc.id]);

  const set = (key: string, value: any) => setParams((p) => ({ ...p, [key]: value }));
  const setLineProduct = (idx: number, value: string) =>
    setParams((p) => {
      const next = [...(p.line_products || [])];
      next[idx] = value;
      return { ...p, line_products: next };
    });

  const handleApply = async () => {
    setApplying(true);
    setErrors(null);
    try {
      const resp = await fetch(`/api/cycom/rest/docai/documents/${doc.id}/apply/`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      const body = await resp.json().catch(() => null);
      if (resp.ok && body) onApplied(body);
      else setErrors(formatApiErrors(body).length ? formatApiErrors(body) : [String(resp.status)]);
    } finally {
      setApplying(false);
    }
  };

  if (!options) {
    return <div className="py-4 text-center text-slate-500">{t('docaiParse.loadingOptions')}</div>;
  }

  const pick = t('docaiParse.selectPlaceholder');
  const isInvoice = doc.document_type === 'invoice';
  const partnerOptions = options.partners.filter((p) => {
    const want = isInvoice && params.invoice_type === 'customer' ? 'customer' : 'vendor';
    return p.partner_type === want || p.partner_type === 'both';
  });
  const taxPct = num(params.tax_percent) || 0;
  const ready = isInvoice
    ? Boolean(params.partner && params.control_account && params.line_account && (taxPct === 0 || params.tax_account))
    : Boolean(params.vendor && params.warehouse && params.offset_account
        && (params.line_products || []).length === lineItems.length
        && (params.line_products || []).every(Boolean));

  return (
    <div className="space-y-4">
      <p className="text-[11px] text-slate-400">
        {isInvoice ? t('docaiParse.applyHintInvoice') : t('docaiParse.applyHintPo')}
      </p>

      {isInvoice ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('docaiParse.invoiceType')}</label>
            <select
              value={params.invoice_type || 'vendor'}
              onChange={(e) => setParams((p) => ({ ...p, invoice_type: e.target.value, partner: '' }))}
              className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none mt-0.5 text-xs"
            >
              <option value="vendor">{t('docaiParse.invoiceTypeVendor')}</option>
              <option value="customer">{t('docaiParse.invoiceTypeCustomer')}</option>
            </select>
          </div>
          <Picker label={t('docaiParse.partner')} value={params.partner || ''} onChange={(v) => set('partner', v)} options={partnerOptions} placeholder={pick} />
          <Picker label={t('docaiParse.controlAccount')} value={params.control_account || ''} onChange={(v) => set('control_account', v)} options={options.accounts} placeholder={pick} />
          <Picker label={t('docaiParse.lineAccount')} value={params.line_account || ''} onChange={(v) => set('line_account', v)} options={options.accounts} placeholder={pick} />
          <div>
            <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('docaiParse.taxPercent')}</label>
            <input
              type="number" min={0} max={100} step="0.01"
              value={params.tax_percent ?? ''}
              onChange={(e) => set('tax_percent', e.target.value)}
              className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none mt-0.5 text-xs"
            />
          </div>
          <Picker
            label={t('docaiParse.taxAccount')} value={params.tax_account || ''} onChange={(v) => set('tax_account', v)}
            options={options.accounts} placeholder={pick} allowNone={taxPct === 0} noneLabel={t('docaiParse.none')}
          />
        </div>
      ) : (
        <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Picker label={t('docaiParse.vendor')} value={params.vendor || ''} onChange={(v) => set('vendor', v)} options={partnerOptions} placeholder={pick} />
            <Picker label={t('docaiParse.warehouse')} value={params.warehouse || ''} onChange={(v) => set('warehouse', v)} options={options.warehouses} placeholder={pick} />
            <Picker label={t('docaiParse.offsetAccount')} value={params.offset_account || ''} onChange={(v) => set('offset_account', v)} options={options.accounts} placeholder={pick} />
          </div>
          <div className="space-y-2">
            {lineItems.map((li, idx) => (
              <div key={idx} className="grid grid-cols-1 sm:grid-cols-2 gap-2 items-end">
                <div className="text-[11px] text-slate-300 truncate">
                  <span className="text-slate-500">{t('docaiParse.lineN', { n: idx + 1 })}:</span> {li.description || '—'}
                  <span className="text-slate-500 font-mono"> · {li.quantity ?? 1} × {li.unit_price ?? li.amount ?? '—'}</span>
                </div>
                <Picker
                  label={t('docaiParse.lineProduct')} value={(params.line_products || [])[idx] || ''}
                  onChange={(v) => setLineProduct(idx, v)} options={options.products} placeholder={pick}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {dirty && (
        <div className="flex items-start gap-2 p-3 rounded-lg border bg-amber-950/40 border-amber-500/20 text-amber-400 text-[11px]">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" /> {t('docaiParse.applyUnsaved')}
        </div>
      )}
      {errors && (
        <div className="flex items-start gap-2 p-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400 text-[11px]">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">{t('docaiParse.applyFailed')}</p>
            {errors.map((line, i) => <p key={i}>{line}</p>)}
          </div>
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={handleApply}
          disabled={applying || dirty || !ready}
          className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-[#A855F7] to-[#00F0FF] disabled:opacity-40 rounded-lg text-white font-semibold transition text-xs"
        >
          {applying ? <Loader2 className="w-4 h-4 animate-spin" /> : <FilePlus2 className="w-4 h-4" />}
          {applying ? t('docaiParse.applying') : t('docaiParse.applyBtn')}
        </button>
      </div>
    </div>
  );
}

function statusTone(status: Status) {
  if (status === 'parsed') return 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400';
  if (status === 'reviewed') return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
  if (status === 'applied') return 'bg-violet-500/10 border-violet-500/30 text-violet-400';
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
        // Stay open: the next step (creating the real record) happens here.
        const updated: ParsedDoc = await resp.json();
        setSelected(updated);
        setDraft(updated.reviewed_data || {});
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
              ) : selected.status === 'applied' ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-lg border bg-violet-950/30 border-violet-500/20 text-violet-300">
                    <span className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4" /> {t('docaiParse.appliedNote')}</span>
                    {recordHref(selected) && (
                      <Link href={recordHref(selected)!} className="flex items-center gap-1.5 text-xs font-semibold text-violet-200 hover:text-white">
                        {t('docaiParse.viewRecord')} <ExternalLink className="w-3.5 h-3.5" />
                      </Link>
                    )}
                  </div>
                  <pre className="text-[10px] text-slate-400 bg-slate-950 border border-slate-850 rounded-lg p-3 overflow-x-auto" dir="ltr">
                    {JSON.stringify(selected.reviewed_data, null, 2)}
                  </pre>
                </div>
              ) : (
                <ReviewFields data={draft} onChange={setDraft} />
              )}
            </div>
            {selected.status !== 'failed' && selected.status !== 'applied' && (
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
            {(selected.status === 'parsed' || selected.status === 'reviewed') && (
              <div className="border-t border-white/5 p-5 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <FilePlus2 className="w-4 h-4 text-[#A855F7]" /> {t('docaiParse.applyHeading')}
                </h4>
                {selected.document_type === 'bank_statement' ? (
                  <p className="text-[11px] text-slate-500">{t('docaiParse.bankStatementNoApply')}</p>
                ) : selected.status !== 'reviewed' ? (
                  <p className="text-[11px] text-slate-500">{t('docaiParse.applyReviewFirst')}</p>
                ) : (
                  <ApplyPanel
                    // Re-init pickers (esp. one product per line) whenever a
                    // re-saved review changes the line items.
                    key={`${selected.id}:${JSON.stringify(selected.reviewed_data)}`}
                    doc={selected}
                    draft={draft}
                    onApplied={(updated) => { setSelected(updated); load(); }}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
