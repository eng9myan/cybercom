'use client';

import React from 'react';
import Link from 'next/link';
import { Percent, Workflow, Key, Cloud } from 'lucide-react';
import { useT } from '@/lib/i18n';

export default function SettingsAdminPage() {
  const t = useT();
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
        {/* Left Column - General Parameters */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('settingsMain.companyProfile')}</h2>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-xs text-slate-500 block">{t('settingsMain.orgName')}</span>
              <span className="text-slate-200 font-semibold">Cycom Co.</span>
            </div>
            <div>
              <span className="text-xs text-slate-500 block">{t('settingsMain.erpBrand')}</span>
              <span className="text-slate-200 font-semibold">CYCOM ERP</span>
            </div>
            <div>
              <span className="text-xs text-slate-500 block">{t('settingsMain.localCurrency')}</span>
              <span className="text-slate-200 font-semibold">Jordanian Dinar (JOD)</span>
            </div>
          </div>
        </div>

        {/* Right Column - Dev bridges */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{t('settingsMain.bridgesHeading')}</h2>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="text-slate-400">{t('settingsMain.biometricBridge')}</span>
              <span className="text-[#10B981] font-semibold">{t('settingsMain.healthy')}</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="text-slate-400">{t('settingsMain.pricingVerifier')}</span>
              <span className="text-[#10B981] font-semibold">{t('settingsMain.active')}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">{t('settingsMain.draftLock')}</span>
              <span className="text-[#10B981] font-semibold">{t('settingsMain.active')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
