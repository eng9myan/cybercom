'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { PenTool, FileText, Send, CheckCircle } from 'lucide-react';

const SIGN_TABS = [
  { label: 'Dashboard', href: '/sign', icon: PenTool, exact: true },
  { label: 'Templates', href: '/sign/templates', icon: FileText, exact: false },
  { label: 'Signature Requests', href: '/sign/requests', icon: Send, exact: false },
];

export default function SignLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const isActive = (tab: typeof SIGN_TABS[0]) => {
    if (tab.exact) return pathname === tab.href;
    return pathname === tab.href || pathname.startsWith(tab.href + '/');
  };

  return (
    <div className="space-y-0">
      {/* Sub-Navigation Bar */}
      <div className="flex items-center gap-1 px-1 py-1.5 mb-6 bg-white/[0.02] border border-white/5 rounded-2xl backdrop-blur-sm overflow-x-auto">
        {SIGN_TABS.map((tab) => {
          const Icon = tab.icon;
          const active = isActive(tab);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap
                ${active
                  ? 'bg-gradient-to-br from-rose-500/15 to-purple-500/10 border border-rose-500/25 text-white shadow-md shadow-rose-500/5'
                  : 'border border-transparent text-slate-400 hover:bg-white/5 hover:text-slate-200'
                }
              `}
            >
              <Icon className={`w-3.5 h-3.5 ${active ? 'text-rose-400' : 'text-slate-500'}`} />
              {tab.label}
            </Link>
          );
        })}
      </div>

      {/* Page Content */}
      {children}
    </div>
  );
}
