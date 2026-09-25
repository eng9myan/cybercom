'use client';

// Custom Reports (BI). Renders/builds saved pivots via the generic
// authenticated REST proxy:
//   GET  /api/cycom/rest/reporting/sources/                 (source/dimension/measure whitelist)
//   GET  /api/cycom/rest/reporting/saved-reports/            (list)
//   POST /api/cycom/rest/reporting/saved-reports/            (create)
//   GET  /api/cycom/rest/reporting/saved-reports/<id>/run/   (execute)

import React, { useEffect, useState } from 'react';
import { BarChart3, Play, Plus } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';
import { useT } from '@/lib/i18n';

interface SourceMeta {
  key: string;
  label: string;
  dimensions: { key: string; label: string }[];
  measures: { key: string; label: string }[];
}

// The backend's source/dimension/measure `label` strings (products/cycom/
// reporting/registry.py) are plain English — they're identifiers for a
// finite, backend-owned whitelist, not user content, so translating them
// belongs here rather than in Django's own i18n. Keyed by "sourceKey" or
// "sourceKey.itemKey" so the same server key (e.g. "count") can carry a
// different label per source ("Order Count" vs "Invoice Count"). Any
// future backend source without an entry here just falls back to the
// server's English label instead of breaking.
const META_LABEL_KEYS: Record<string, string> = {
  sales_orders: 'sourceSalesOrders',
  invoices: 'sourceInvoices',
  'sales_orders.status': 'dimStatus',
  'sales_orders.customer': 'dimCustomer',
  'sales_orders.salesperson': 'dimSalesperson',
  'sales_orders.count': 'measureOrderCount',
  'sales_orders.amount_total': 'measureAmountTotal',
  'invoices.status': 'dimStatus',
  'invoices.invoice_type': 'dimInvoiceType',
  'invoices.count': 'measureInvoiceCount',
  'invoices.amount_total': 'measureAmountTotal',
  'invoices.amount_paid': 'measureAmountPaid',
};

interface SavedReport {
  id: string;
  name: string;
  source: string;
  dimension: string;
  measure: string;
  aggregation: string;
  chart_type: 'table' | 'bar' | 'pie';
}

interface ReportRow {
  label: string;
  value: number;
}

const PIE_COLORS = ['#00F0FF', '#7C3AED', '#F59E0B', '#10B981', '#EF4444', '#3B82F6'];

export default function CustomReportsPage() {
  const t = useT();
  const metaLabel = (path: string, fallback: string) =>
    META_LABEL_KEYS[path] ? t(`customReports.${META_LABEL_KEYS[path]}`) : fallback;
  const [sources, setSources] = useState<SourceMeta[]>([]);
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(true);

  const [name, setName] = useState('');
  const [source, setSource] = useState('');
  const [dimension, setDimension] = useState('');
  const [measure, setMeasure] = useState('');
  const [aggregation, setAggregation] = useState('sum');
  const [chartType, setChartType] = useState<'table' | 'bar' | 'pie'>('table');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [activeReport, setActiveReport] = useState<SavedReport | null>(null);
  const [rows, setRows] = useState<ReportRow[]>([]);
  const [running, setRunning] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [sourcesRes, reportsRes] = await Promise.all([
        fetch('/api/cycom/rest/reporting/sources/', { credentials: 'include' }),
        fetch('/api/cycom/rest/reporting/saved-reports/', { credentials: 'include' }),
      ]);
      const sourcesData = await sourcesRes.json();
      const reportsData = await reportsRes.json();
      setSources(sourcesData);
      setReports(Array.isArray(reportsData) ? reportsData : reportsData.results || []);
      if (sourcesData.length > 0 && !source) setSource(sourcesData[0].key);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedSource = sources.find((s) => s.key === source);

  useEffect(() => {
    if (!selectedSource) return;
    if (!selectedSource.dimensions.some((d) => d.key === dimension)) {
      setDimension(selectedSource.dimensions[0]?.key || '');
    }
    if (!selectedSource.measures.some((m) => m.key === measure)) {
      setMeasure(selectedSource.measures[0]?.key || '');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, sources]);

  const createReport = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const res = await fetch('/api/cycom/rest/reporting/saved-reports/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name, source, dimension, measure, aggregation, chart_type: chartType }),
      });
      if (!res.ok) throw new Error(t('customReports.createFailed'));
      setName('');
      await load();
    } catch (e2) {
      setCreateError(e2 instanceof Error ? e2.message : t('customReports.createFailed'));
    } finally {
      setCreating(false);
    }
  };

  const runReport = async (report: SavedReport) => {
    setActiveReport(report);
    setRunning(true);
    try {
      const res = await fetch(`/api/cycom/rest/reporting/saved-reports/${report.id}/run/`, { credentials: 'include' });
      const data = await res.json();
      setRows(Array.isArray(data) ? data : []);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex items-center gap-2.5">
        <BarChart3 className="w-5 h-5 text-cyan-400" />
        <h1 className="text-lg font-black text-white">{t('customReports.title')}</h1>
      </header>

      <form onSubmit={createReport} className="glass-card p-5 space-y-3">
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <Plus className="w-4 h-4" /> {t('customReports.newReport')}
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={t('customReports.namePlaceholder')}
            required
            className="col-span-2 md:col-span-3 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
          />
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
          >
            {sources.map((s) => (
              <option key={s.key} value={s.key}>{metaLabel(s.key, s.label)}</option>
            ))}
          </select>
          <select
            value={dimension}
            onChange={(e) => setDimension(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
          >
            {selectedSource?.dimensions.map((d) => (
              <option key={d.key} value={d.key}>{metaLabel(`${source}.${d.key}`, d.label)}</option>
            ))}
          </select>
          <select
            value={measure}
            onChange={(e) => setMeasure(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
          >
            {selectedSource?.measures.map((m) => (
              <option key={m.key} value={m.key}>{metaLabel(`${source}.${m.key}`, m.label)}</option>
            ))}
          </select>
          <select
            value={aggregation}
            onChange={(e) => setAggregation(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
          >
            <option value="sum">{t('customReports.aggSum')}</option>
            <option value="avg">{t('customReports.aggAvg')}</option>
            <option value="count">{t('customReports.aggCount')}</option>
          </select>
          <select
            value={chartType}
            onChange={(e) => setChartType(e.target.value as 'table' | 'bar' | 'pie')}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
          >
            <option value="table">{t('customReports.chartTable')}</option>
            <option value="bar">{t('customReports.chartBar')}</option>
            <option value="pie">{t('customReports.chartPie')}</option>
          </select>
        </div>
        {createError && <p className="text-red-400 text-xs">{createError}</p>}
        <button type="submit" disabled={creating} className="btn-primary py-1.5 px-4 text-xs disabled:opacity-50">
          {creating ? t('customReports.creating') : t('customReports.create')}
        </button>
      </form>

      {loading && <p className="text-slate-500 text-sm">{t('customReports.loading')}</p>}

      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <h2 className="text-xs font-black text-slate-400 uppercase tracking-wide">{t('customReports.savedReports')}</h2>
            {reports.length === 0 && <p className="text-slate-500 text-xs italic">{t('customReports.empty')}</p>}
            {reports.map((r) => (
              <button
                key={r.id}
                onClick={() => runReport(r)}
                className={`w-full text-start glass-card p-3 flex items-center justify-between gap-2 hover:border-white/20 transition-colors ${
                  activeReport?.id === r.id ? 'border-cyan-500/40' : ''
                }`}
              >
                <span className="text-sm text-white truncate">{r.name}</span>
                <Play className="w-3.5 h-3.5 text-slate-500 shrink-0" />
              </button>
            ))}
          </div>

          <div className="md:col-span-2 glass-card p-5 min-h-[320px]">
            {!activeReport && <p className="text-slate-500 text-sm italic">{t('customReports.selectPrompt')}</p>}
            {activeReport && running && <p className="text-slate-500 text-sm">{t('customReports.running')}</p>}
            {activeReport && !running && rows.length === 0 && (
              <p className="text-slate-500 text-sm italic">{t('customReports.noData')}</p>
            )}
            {activeReport && !running && rows.length > 0 && activeReport.chart_type === 'table' && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-start text-slate-500 text-xs uppercase border-b border-white/5">
                    <th className="pb-2 font-bold">{t('customReports.colLabel')}</th>
                    <th className="pb-2 font-bold text-end">{t('customReports.colValue')}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.label} className="border-b border-white/5">
                      <td className="py-2 text-white">{row.label}</td>
                      <td className="py-2 text-end text-slate-300">{row.value.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {activeReport && !running && rows.length > 0 && activeReport.chart_type === 'bar' && (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={rows}>
                  <XAxis dataKey="label" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ background: '#0f0f1a', border: '1px solid rgba(255,255,255,0.1)' }} />
                  <Bar dataKey="value" fill="#00F0FF" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
            {activeReport && !running && rows.length > 0 && activeReport.chart_type === 'pie' && (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={rows} dataKey="value" nameKey="label" outerRadius={100} label>
                    {rows.map((row, i) => (
                      <Cell key={row.label} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0f0f1a', border: '1px solid rgba(255,255,255,0.1)' }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
