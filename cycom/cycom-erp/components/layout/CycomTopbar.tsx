'use client';

import Link from 'next/link';
import { Settings, Search, Bell, Activity, Sparkles, Building2, Menu } from 'lucide-react';
import { useCompany } from '@/context/CompanyContext';
import LanguageToggle from '@/components/LanguageToggle';
import { useT } from '@/lib/i18n';

interface CycomTopbarProps {
  onMenuClick: () => void;
}

export default function CycomTopbar({ onMenuClick }: CycomTopbarProps) {
  const { activeCompany } = useCompany();
  const t = useT();

  return (
    <header className="h-[var(--topbar-height)] bg-[#0a0f1e]/80 border-b border-white/5 flex items-center px-3 sm:px-6 justify-between backdrop-blur-md sticky top-0 z-40 gap-2">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {/* Mobile drawer toggle — sidebar is off-canvas below lg. */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 -ms-2 rounded-xl hover:bg-white/5 transition-colors text-slate-300 hover:text-white flex-shrink-0"
          aria-label={t('sidebar.openMenu')}
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Search Input */}
        <div className="flex items-center gap-2 bg-white/3 border border-white/8 rounded-xl px-3 py-1.5 w-full max-w-[160px] sm:max-w-[220px] lg:max-w-[280px]">
          <Search className="w-4 h-4 text-slate-500 flex-shrink-0" />
          <input
            type="text"
            placeholder={t('common.search') + '…'}
            className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full min-w-0"
          />
        </div>
      </div>

      {/* Right Tools */}
      <div className="flex items-center gap-2 sm:gap-4 flex-shrink-0">
        <LanguageToggle />
        {/* Active Company Indicator */}
        <div
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full border"
          style={{
            backgroundColor: `${activeCompany.color}10`,
            borderColor: `${activeCompany.color}30`
          }}
        >
          <Building2 className="w-3.5 h-3.5" style={{ color: activeCompany.color }} />
          <span className="text-[11px] font-bold" style={{ color: activeCompany.color }}>
            {activeCompany.shortName}
          </span>
          {activeCompany.type === 'retail' && activeCompany.branches && (
            <span className="text-[9px] font-mono text-slate-500">
              ({activeCompany.branches.length} stores)
            </span>
          )}
        </div>

        {/* System Health / Sync indicator */}
        <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
          <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span className="text-[11px] font-bold text-emerald-400">ZK Biometric Sync Active</span>
        </div>

        {/* AI copilot button */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#A855F7]/10 border border-[#A855F7]/20 text-[#A855F7]">
          <Sparkles className="w-3.5 h-3.5 animate-bounce" />
          <span className="text-[11px] font-bold">AI Enabled</span>
        </div>

        <button className="p-2 rounded-xl hover:bg-white/5 transition-colors text-slate-400 hover:text-white relative flex-shrink-0">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 end-1.5 w-1.5 h-1.5 bg-[#EF4444] rounded-full" />
        </button>

        <div className="hidden sm:block w-px h-5 bg-white/10" />

        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#E67E22] to-[#5DADE2] flex items-center justify-center text-[10px] font-black text-white flex-shrink-0">
            AG
          </div>
          <div className="text-start hidden lg:block">
            <p className="text-xs font-bold text-slate-200">Admin User</p>
            <p className="text-[9px] text-slate-500 uppercase tracking-widest font-bold">{activeCompany.name}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
