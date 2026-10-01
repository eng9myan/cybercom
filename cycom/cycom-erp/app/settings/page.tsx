'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Percent, Workflow, Key, Cloud, Tag, FileCheck2 } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface SystemStatus {
  company: { name: string; tax_id: string; country_code: string; currency: string; timezone: string };
  integrations: { key: string; detail: string; status: string }[];
}

const STATUS_TONE: Record<string, string> = {
  connected: 'text-emerald-400', configured: 'text-emerald-400', manual: 'text-amber-400',
  not_configured: 'text-slate-500', not_applicable: 'text-slate-600',
};

export default function SettingsAdminPage() {
  const t = useT();
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    fetch('/api/cycom/rest/common/system-status/', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then(setStatus)
      .catch(() => {});
  }, []);
  return (
    <div className="space-y-6 text-xs md:text-sm">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('settingsMain.title')}</h1>
          <p className="page-subtitle">{t('settingsMain.subtitle')}</p>
        </div>
      </div>

      {/* Global Enterprise Pillars Command Grid */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('settingsMain.pillarsHeading')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/settings/custom-fields"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-amber-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <Tag className="w-6 h-6 text-amber-400 mb-2" />
              <h4 className="font-semibold text-slate-200">{t('settingsMain.customFieldsTitle')}</h4>
              <p className="text-[10px] text-slate-500 mt-1">{t('settingsMain.customFieldsDesc')}</p>
            </div>
            <span className="text-[10px] text-amber-400 font-bold mt-4 inline-block">{t('settingsMain.configure')}</span>
          </Link>

          <Link
            href="/settings/einvoicing"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-cyan-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <FileCheck2 className="w-6 h-6 text-cyan-400 mb-2" />
              <h4 className="font-semibold text-slate-200">{t('settingsMain.einvoicingTitle')}</h4>
              <p className="text-[10px] text-slate-500 mt-1">{t('settingsMain.einvoicingDesc')}</p>
            </div>
            <span className="text-[10px] text-cyan-400 font-bold mt-4 inline-block">{t('settingsMain.configure')}</span>
          </Link>

          <Link
            href="/settings/tax"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-blue-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <Percent className="w-6 h-6 text-blue-400 mb-2" />
              <h4 className="font-semibold text-slate-200">{t('settingsMain.taxTitle')}</h4>
              <p className="text-[10px] text-slate-500 mt-1">{t('settingsMain.taxDesc')}</p>
            </div>
            <span className="text-[10px] text-blue-400 font-bold mt-4 inline-block">{t('settingsMain.configure')}</span>
          </Link>

          <Link
            href="/settings/workflows"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-indigo-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <Workflow className="w-6 h-6 text-indigo-400 mb-2" />
              <h4 className="font-semibold text-slate-200">{t('settingsMain.workflowsTitle')}</h4>
              <p className="text-[10px] text-slate-500 mt-1">{t('settingsMain.workflowsDesc')}</p>
            </div>
            <span className="text-[10px] text-indigo-400 font-bold mt-4 inline-block">{t('settingsMain.configure')}</span>
          </Link>

          <Link
            href="/settings/security"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-emerald-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <Key className="w-6 h-6 text-emerald-400 mb-2" />
              <h4 className="font-semibold text-slate-200">{t('settingsMain.securityTitle')}</h4>
              <p className="text-[10px] text-slate-500 mt-1">{t('settingsMain.securityDesc')}</p>
            </div>
            <span className="text-[10px] text-emerald-400 font-bold mt-4 inline-block">{t('settingsMain.configure')}</span>
          </Link>

          <Link
            href="/settings/modules"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-purple-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <Cloud className="w-6 h-6 text-purple-400 mb-2" />
              <h4 className="font-semibold text-slate-200">{t('settingsMain.modulesTitle')}</h4>
              <p className="text-[10px] text-slate-500 mt-1">{t('settingsMain.modulesDesc')}</p>
            </div>
            <span className="text-[10px] text-purple-400 font-bold mt-4 inline-block">{t('settingsMain.configure')}</span>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Company profile -- real tenant data */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('settingsMain.companyProfile')}</h2>
          {!status ? (
            <p className="text-xs text-slate-500">{t('settingsMain.loading')}</p>
          ) : (
            <div className="space-y-3 text-sm">
              {([
                ['orgName', status.company.name],
                ['taxId', status.company.tax_id],
                ['country', status.company.country_code],
                ['localCurrency', status.company.currency],
                ['timezone', status.company.timezone],
              ] as const).map(([key, value]) => (
                <div key={key}>
                  <span className="text-xs text-slate-500 block">{t(`settingsMain.${key}`)}</span>
                  <span className="text-slate-200 font-semibold">{value || t('settingsMain.notSet')}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Integrations -- each one's actual configuration state */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('settingsMain.integrationsHeading')}</h2>
          {!status ? (
            <p className="text-xs text-slate-500">{t('settingsMain.loading')}</p>
          ) : (
            <div className="space-y-3 text-xs">
              {status.integrations.map((i) => (
                <div key={i.key} className="flex justify-between items-center gap-3 pb-2 border-b border-white/5 last:border-0">
                  <span className="text-slate-400">
                    {t(`settingsMain.integration.${i.key}`)}
                    {i.detail && <span className="text-slate-600"> · {i.detail}</span>}
                  </span>
                  <span className={`font-semibold ${STATUS_TONE[i.status] || 'text-slate-500'}`}>{t(`settingsMain.integrationStatus.${i.status}`)}</span>
                </div>
              ))}
              <p className="text-[10px] text-slate-600">{t('settingsMain.integrationsNote')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
