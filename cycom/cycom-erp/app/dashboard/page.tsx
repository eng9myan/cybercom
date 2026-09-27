'use client';

// Real dashboard data from /api/v1/common/dashboard-summary/ -- this used
// to be a page of hardcoded numbers (a fabricated named employee in a
// sample alert, "18 online" biometric devices with no backend anywhere,
// "Warehouse Locks: Guards healthy" for a concept that doesn't exist).
// Every number here is a live aggregate; an empty tenant sees zeros, not
// sample data standing in for them.

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  RefreshCw, CheckCircle2, AlertTriangle,
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { useT } from '@/lib/i18n';

interface RevenuePoint { month: string; revenue: number }
interface Alert { source: string; type: string; desc: string; urgency: 'high' | 'medium' | 'low'; href: string }
interface PulseItem { label: string; value: string; tone: 'ok' | 'warn' }
interface Summary { revenue_trend: RevenuePoint[]; alerts: Alert[]; pulse: PulseItem[] }

export default function CommandCenter() {
  const t = useT();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetch('/api/cycom/rest/common/dashboard-summary/', { credentials: 'include' })
      .then((r) => r.json())
      .then((data) => setSummary(data))
      .catch((err) => setError(t('dashboard.loadFailed', { msg: err.message })))
      .finally(() => setLoading(false));
  };

  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps

  const totalRevenue = summary?.revenue_trend.reduce((sum, m) => sum + m.revenue, 0) ?? 0;
  const currency = 'JOD'; // display-only label; the underlying figures are already tenant-currency totals

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('dashboard.title')}</h1>
          <p className="page-subtitle">{t('dashboard.subtitle')}</p>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2">
          <RefreshCw className={`w-4 h-4 text-cyan-400 ${loading ? 'animate-spin' : ''}`} /> {t('dashboard.refreshTelemetry')}
        </button>
      </div>

      {error && (
        <div className="glass-card p-4 border border-rose-500/20 bg-rose-950/20 text-rose-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" /> {error}
        </div>
      )}

      {/* Main Revenue Chart */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('dashboard.revenueTrend')}</h2>
            <p className="text-2xl font-black text-white mt-1">
              {currency} {totalRevenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              <span className="text-xs text-slate-500 font-semibold ms-2">{t('dashboard.last6Months')}</span>
            </p>
          </div>
          <span className="badge badge-cyan font-mono text-[10px]">{t('dashboard.realData')}</span>
        </div>
        <div className="h-[280px] w-full text-slate-300 text-xs">
          {summary && summary.revenue_trend.every((m) => m.revenue === 0) ? (
            <div className="h-full flex items-center justify-center text-slate-600">
              {t('dashboard.noRevenueYet')}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={summary?.revenue_trend ?? []}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00F0FF" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#00F0FF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" stroke="#475569" />
                <YAxis stroke="#475569" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.07)' }}
                  labelStyle={{ color: '#94A3B8' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#00F0FF" fillOpacity={1} fill="url(#colorRevenue)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 columns - real alerts */}
        <div className="glass-card p-6 lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('dashboard.telemetryAlerts')}</h2>
            <span className="text-xs text-slate-500 font-mono">
              {t('dashboard.unresolvedEvents', { n: String(summary?.alerts.length ?? 0) })}
            </span>
          </div>

          {loading ? (
            <div className="py-10 text-center text-slate-500 text-xs">{t('dashboard.loading')}</div>
          ) : summary && summary.alerts.length === 0 ? (
            <div className="py-10 text-center text-slate-500 text-xs flex flex-col items-center gap-2">
              <CheckCircle2 className="w-6 h-6 text-emerald-500" />
              {t('dashboard.allClear')}
            </div>
          ) : (
            <div className="space-y-3">
              {summary?.alerts.map((alert, index) => (
                <Link
                  key={index}
                  href={alert.href}
                  className="flex justify-between items-start p-4 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="badge badge-purple">{alert.source}</span>
                      <span className="text-xs text-slate-300 font-bold">{alert.type}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{alert.desc}</p>
                  </div>
                  <span className={`badge ${alert.urgency === 'high' ? 'badge-red' : alert.urgency === 'medium' ? 'badge-yellow' : 'badge-cyan'}`}>
                    {t(`priority.${alert.urgency}`)}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Right column - real module counts */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('dashboard.modulesPulse')}</h3>
          <div className="space-y-3 text-xs">
            {summary?.pulse.map((item, i) => (
              <div
                key={item.label}
                className={`flex justify-between items-center pb-2 ${i < (summary.pulse.length - 1) ? 'border-b border-white/5' : ''}`}
              >
                <span className="text-slate-400 flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${item.tone === 'warn' ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                  {item.label}
                </span>
                <span className={`font-mono font-bold ${item.tone === 'warn' ? 'text-amber-400' : 'text-white'}`}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
