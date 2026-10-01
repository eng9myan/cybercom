'use client';

import Link from 'next/link';
import { Search, Building2, Menu } from 'lucide-react';
import { useCompany } from '@/context/CompanyContext';
import { useAuth } from '@/context/AuthContext';
import LanguageToggle from '@/components/LanguageToggle';
import { useT } from '@/lib/i18n';

interface CycomTopbarProps {
  onMenuClick: () => void;
}

export default function CycomTopbar({ onMenuClick }: CycomTopbarProps) {
  const { activeCompany } = useCompany();
  const { user } = useAuth();
  const t = useT();
  const displayName = user?.name || user?.username || '';
  const initials = displayName.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase() || '?';
  // The real search is the command palette (Ctrl/Cmd+K); this box opens it.
  const openPalette = () => window.dispatchEvent(new CustomEvent('cycom:open-palette'));

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
            readOnly
            onFocus={(e) => { e.currentTarget.blur(); openPalette(); }}
            onClick={openPalette}
            placeholder={t('common.search') + '…  Ctrl K'}
            className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full min-w-0 cursor-pointer"
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
          {activeCompany.branches && activeCompany.branches.length > 1 && (
            <span className="text-[9px] font-mono text-slate-500">
              ({t('topbar.locations', { n: activeCompany.branches.length })})
            </span>
          )}
        </div>

        <div className="hidden sm:block w-px h-5 bg-white/10" />

        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#E67E22] to-[#5DADE2] flex items-center justify-center text-[10px] font-black text-white flex-shrink-0">
            {initials}
          </div>
          <div className="text-start hidden lg:block">
            <p className="text-xs font-bold text-slate-200">{displayName}</p>
            <p className="text-[9px] text-slate-500 uppercase tracking-widest font-bold">{activeCompany.name}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
