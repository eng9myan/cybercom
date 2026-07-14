'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ArrowLeft, Cpu, Cloud, Code, Play, RefreshCw, CheckCircle2, 
  GitBranch, Terminal, ShieldAlert
} from 'lucide-react';
import { call } from '@/lib/cycom';

export default function ModuleManager() {
  const router = useRouter();
  
  // App Store Lists
  const [activeApps, setActiveApps] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [moduleName, setModuleName] = useState('cycom_packing_list');
  const [repo, setRepo] = useState('github.com/cybercom/cycom_packing_list');
  const [branch, setBranch] = useState('main');
  const [installing, setInstalling] = useState(false);
  const [installSuccess, setInstallSuccess] = useState<any>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:8888/api/kernel/status');
      if (res.ok) {
        const data = await res.json();
        setActiveApps(data.loaded_apps || []);
      }
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleInstallModule = async (e: React.FormEvent) => {
    e.preventDefault();
    setInstalling(true);
    setInstallSuccess(null);
    try {
      const res = await fetch('http://localhost:8888/api/modules/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          module_name: moduleName,
          github_repo: repo,
          branch: branch
        })
      });
      if (res.ok) {
        const data = await res.json();
        setInstallSuccess(data);
        fetchStatus();
      }
    } catch {
      alert('Installation failed.');
    } finally {
      setInstalling(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      {/* Header */}
      <div className="max-w-5xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/settings')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent flex items-center gap-2">
              <Cloud className="w-6 h-6 text-blue-400" /> Cycom.sh Extension command center
            </h1>
            <p className="text-xs text-slate-400 mt-1">Hot-load custom applications, pull branch updates from Git repositories, and provision staging sandboxes.</p>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dynamic App Install form */}
        <div className="lg:col-span-1 glass-card p-6 space-y-4 h-fit">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-2">
            <Code className="w-4 h-4 text-blue-400" /> Hot-Load Module
          </h3>
          <form onSubmit={handleInstallModule} className="space-y-4">
            <div className="space-y-1">
              <label className="text-slate-400">Module Technical Name</label>
              <input 
                type="text" required value={moduleName} onChange={e => setModuleName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
              />
            </div>
            
            <div className="space-y-1">
              <label className="text-slate-400 flex items-center gap-1.5"><Code className="w-3.5 h-3.5" /> Git Repository URI</label>
              <input 
                type="text" required value={repo} onChange={e => setRepo(e.target.value)}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 flex items-center gap-1.5"><GitBranch className="w-3.5 h-3.5" /> Deployment Branch</label>
              <input 
                type="text" required value={branch} onChange={e => setBranch(e.target.value)}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none font-mono"
              />
            </div>

            <button 
              type="submit" disabled={installing}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-semibold shadow-lg shadow-blue-600/15 transition flex items-center justify-center gap-2"
            >
              {installing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Build & Hot-Load App
            </button>
          </form>
        </div>

        {/* Console / Active apps panel */}
        <div className="lg:col-span-2 space-y-6">
          {installSuccess && (
            <div className="p-4 bg-emerald-950/40 border border-emerald-500/20 rounded-xl text-emerald-400 space-y-2 flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <h5 className="font-bold capitalize">Module Deploy Succeeded!</h5>
                <p className="text-[10px] text-emerald-500/80 leading-relaxed mt-0.5">
                  App `{installSuccess.module}` successfully integrated. Dynamic model schemas loaded, table schemas sync complete, and routes hot-loaded.
                </p>
                <div className="pt-2">
                  <a 
                    href={installSuccess.sandbox_url} target="_blank" rel="noopener noreferrer"
                    className="inline-block px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold"
                  >
                    Open Sandbox View
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* Active app list */}
          <div className="glass-card p-6">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 pb-3 mb-4 flex justify-between items-center">
              Active Module Register
              <span className="text-[10px] bg-slate-850 px-2 py-0.5 rounded text-slate-400 font-normal">Dynamic reload</span>
            </h3>
            {loading ? (
              <div className="text-center py-6 text-slate-500">Querying status...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {activeApps.map((app) => (
                  <div key={app} className="p-3 bg-slate-950/40 border border-slate-850 rounded-xl flex items-center justify-between gap-4">
                    <div>
                      <h4 className="font-semibold text-slate-300 capitalize">{app.replace('_', ' ')}</h4>
                      <p className="text-[10px] text-slate-500 mt-0.5">Status: hot-loaded</p>
                    </div>
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
