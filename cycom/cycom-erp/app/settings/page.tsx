'use client';

import React from 'react';
import Link from 'next/link';
import { Settings, Shield, Cpu, Sliders, Percent, Workflow, Key, Cloud } from 'lucide-react';

export default function SettingsAdminPage() {
  return (
    <div className="space-y-6 text-xs md:text-sm">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">System Settings & Administration</h1>
          <p className="page-subtitle">Configure global parameters, developer whitelists, database triggers, and Cycom connector bridges.</p>
        </div>
      </div>

      {/* Global Enterprise Pillars Command Grid */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Global Enterprise Pillars (POC Controls)</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link 
            href="/settings/tax"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-blue-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <Percent className="w-6 h-6 text-blue-400 mb-2" />
              <h4 className="font-semibold text-slate-200">Tax & JoFotara</h4>
              <p className="text-[10px] text-slate-500 mt-1">Configure VAT/WHT rates and inspect Jordan JoFotara XML envelopes.</p>
            </div>
            <span className="text-[10px] text-blue-400 font-bold mt-4 inline-block">Configure →</span>
          </Link>

          <Link 
            href="/settings/workflows"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-indigo-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <Workflow className="w-6 h-6 text-indigo-400 mb-2" />
              <h4 className="font-semibold text-slate-200">Workflow Rules</h4>
              <p className="text-[10px] text-slate-500 mt-1">Design low-code rule triggers and route validation conditions.</p>
            </div>
            <span className="text-[10px] text-indigo-400 font-bold mt-4 inline-block">Configure →</span>
          </Link>

          <Link 
            href="/settings/security"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-emerald-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <Key className="w-6 h-6 text-emerald-400 mb-2" />
              <h4 className="font-semibold text-slate-200">SSO & Ledger Integrity</h4>
              <p className="text-[10px] text-slate-500 mt-1">Enable Identity Provider SSO and verify cryptographic audit hashes.</p>
            </div>
            <span className="text-[10px] text-emerald-400 font-bold mt-4 inline-block">Configure →</span>
          </Link>

          <Link 
            href="/settings/modules"
            className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-purple-500/30 hover:bg-slate-900/20 transition-all flex flex-col justify-between"
          >
            <div>
              <Cloud className="w-6 h-6 text-purple-400 mb-2" />
              <h4 className="font-semibold text-slate-200">Cycom.sh Extension Hub</h4>
              <p className="text-[10px] text-slate-500 mt-1">Hot-load custom packages and track Git-integrated sandbox status.</p>
            </div>
            <span className="text-[10px] text-purple-400 font-bold mt-4 inline-block">Configure →</span>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - General Parameters */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Company Profile</h2>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-xs text-slate-500 block">Organization Name</span>
              <span className="text-slate-200 font-semibold">Cycom Co.</span>
            </div>
            <div>
              <span className="text-xs text-slate-500 block">ERP Identity Brand</span>
              <span className="text-slate-200 font-semibold">CYCOM ERP</span>
            </div>
            <div>
              <span className="text-xs text-slate-500 block">Local Currency Settings</span>
              <span className="text-slate-200 font-semibold">Jordanian Dinar (JOD)</span>
            </div>
          </div>
        </div>

        {/* Right Column - Dev bridges */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Cycom Core Bridges</h2>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="text-slate-400">Active Biometric API Bridge</span>
              <span className="text-[#10B981] font-semibold">Healthy</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="text-slate-400">Sales Pricing Margin Verifier</span>
              <span className="text-[#10B981] font-semibold">Active</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Accounting Move Draft Lock</span>
              <span className="text-[#10B981] font-semibold">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
