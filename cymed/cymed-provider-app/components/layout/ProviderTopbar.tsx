'use client';

import { LogOut } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import LanguageToggle from '@/components/LanguageToggle';
import { useT } from '@/lib/i18n';

export default function ProviderTopbar() {
  const { user, logout } = useAuth();
  const t = useT();

  return (
    <header className="h-16 bg-[#0a0f1e]/80 border-b border-white/5 flex items-center px-6 justify-end gap-4 backdrop-blur-md sticky top-0 z-40">
      <LanguageToggle />
      {user && (
        <div className="flex items-center gap-3">
          <div className="text-end hidden sm:block">
            <p className="text-xs font-bold text-slate-200">{user.name}</p>
            <p className="text-[9px] text-slate-500 uppercase tracking-widest font-bold">
              {user.username}
            </p>
          </div>
          <button
            onClick={() => logout()}
            className="p-2 rounded-xl hover:bg-white/5 transition-colors text-slate-400 hover:text-white"
            title={t('common.logout')}
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      )}
    </header>
  );
}
