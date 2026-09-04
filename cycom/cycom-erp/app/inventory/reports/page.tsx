'use client';

import React from 'react';
import { FileDown } from 'lucide-react';
import { useT } from '@/lib/i18n';

const WHITELISTS = [
  { id: 'WHL-101', branch: 'Zarqa Retail Shop', category: 'Confectionery Premium', productsAllowed: 'All premium items', audited: true },
  { id: 'WHL-102', branch: 'Irbid Warehouse', category: 'Imported Spices', productsAllowed: 'Selected Whitelist SKU set', audited: false },
];

export default function InventoryReports() {
  const t = useT();
  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('invReports.title')}</h1>
          <p className="page-subtitle">{t('invReports.subtitle')}</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <FileDown className="w-4 h-4" /> {t('invReports.exportCsv')}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6 space-y-4">
          <div className="flex justify-between items-center pb-3 border-b border-white/5">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('invReports.whitelistHeading')}</h2>
            <span className="badge badge-purple">{t('invReports.securityChecks')}</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">{t('invReports.whitelistBody')}</p>
          <div className="space-y-3">
            {WHITELISTS.map((wl) => (
              <div key={wl.id} className="p-3.5 rounded-lg bg-white/5 border border-white/5 flex justify-between items-center text-xs">
                <div>
                  <h4 className="font-bold text-slate-200">{wl.branch}</h4>
                  <span className="text-[10px] text-slate-500">{t('invReports.tier')}: {wl.category} • {wl.productsAllowed}</span>
                </div>
                <span className={`badge ${wl.audited ? 'badge-green' : 'badge-yellow'}`}>
                  {wl.audited ? t('invReports.audited') : t('invReports.auditPending')}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center pb-3 border-b border-white/5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('invReports.discrepancyHeading')}</h2>
              <span className="badge badge-cyan">{t('invReports.rulesConfig')}</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mt-3">{t('invReports.discrepancyBody')}</p>
          </div>
          <div className="p-4 rounded-xl bg-black/45 border border-white/5 text-xs text-slate-300">
            <div className="flex justify-between items-center">
              <span>{t('invReports.autoThreshold')}</span>
              <span className="font-mono text-cyan-400 font-bold">1% / &gt; JOD 50.00</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
