'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart2, Users, Building2, Award, FileText, Shield
} from 'lucide-react';

const HR_TABS = [
  { label: 'Dashboard', href: '/hr', icon: BarChart2, exact: true },
  { label: 'Employees', href: '/hr/employees', icon: Users, exact: false },
  { label: 'Departments', href: '/hr/departments', icon: Building2, exact: false },
  { label: 'Insurance', href: '/hr/insurance', icon: Award, exact: false },
  { label: 'Documents', href: '/hr/documents', icon: FileText, exact: false },
  { label: 'Requests', href: '/hr/requests', icon: Shield, exact: false },
];

export default function HRLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const isActive = (tab: typeof HR_TABS[0]) => {
    if (tab.exact) return pathname === tab.href;
    return pathname === tab.href || pathname.startsWith(tab.href + '/');
  };

  return (
    <div className="space-y-0">
      {/* Sub-Navigation Bar */}
      <div className="flex items-center gap-1 px-1 py-1.5 mb-6 bg-white/[0.02] border border-white/5 rounded-2xl backdrop-blur-sm overflow-x-auto">
        {HR_TABS.map((tab) => {
          const Icon = tab.icon;
          const active = isActive(tab);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap
                ${active
                  ? 'bg-gradient-to-br from-orange-500/15 to-blue-500/10 border border-orange-500/25 text-white shadow-md shadow-orange-500/5'
                  : 'border border-transparent text-slate-400 hover:bg-white/5 hover:text-slate-200'
                }
              `}
            >
              <Icon className={`w-3.5 h-3.5 ${active ? 'text-[#E67E22]' : 'text-slate-500'}`} />
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
