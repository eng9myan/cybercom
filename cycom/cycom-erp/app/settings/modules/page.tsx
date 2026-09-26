'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Boxes } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface AppEntry {
  key: string;
  name: string;
}

export default function InstalledModules() {
  const t = useT();
  const router = useRouter();

  const [apps, setApps] = useState<AppEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/cycom/rest/common/installed-apps/', { credentials: 'include' })
      .then((r) => r.json())
      .then((data) => setApps(data.apps || []))
      .catch((err) => setError(t('settingsModules.loadFailed', { msg: err.message })))
      .finally(() => setLoading(false));
  }, [t]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      {/* Header */}
      <div className="max-w-5xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/settings')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent flex items-center gap-2">
              <Boxes className="w-6 h-6 text-blue-400" /> {t('settingsModules.title')}
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">{t('settingsModules.subtitle')}</p>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto glass-card p-6">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 pb-3 mb-4">
          {t('settingsModules.registerHeading', { count: String(apps.length) })}
        </h3>

        {loading ? (
          <div className="text-center py-6 text-slate-500">{t('settingsModules.loading')}</div>
        ) : error ? (
          <div className="text-center py-6 text-rose-400">{error}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {apps.map((app) => (
              <div key={app.key} className="p-3 bg-slate-950/40 border border-slate-850 rounded-xl flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <h4 className="font-semibold text-slate-300 truncate">{app.name}</h4>
                  <p className="text-[10px] text-slate-500 mt-0.5 font-mono truncate" dir="ltr">{app.key}</p>
                </div>
                <span className="flex items-center gap-1.5 flex-shrink-0 text-[10px] text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  {t('settingsModules.statusActive')}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
