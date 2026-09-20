'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, Calendar, FlaskConical, Stethoscope } from 'lucide-react';
import { useT } from '@/lib/i18n';

const LINKS = [
  { href: '/', icon: LayoutDashboard, key: 'nav.overview' },
  { href: '/patients', icon: Users, key: 'nav.patients' },
  { href: '/schedule', icon: Calendar, key: 'nav.schedule' },
  { href: '/orders', icon: FlaskConical, key: 'nav.orders' },
] as const;

export default function ProviderSidebar() {
  const pathname = usePathname();
  const t = useT();

  return (
    <aside className="w-[220px] shrink-0 border-e border-white/5 bg-[#0a0f1e] flex flex-col">
      <div className="h-16 flex items-center gap-2 px-5 border-b border-white/5">
        <Stethoscope className="w-5 h-5 text-[var(--cy-teal)]" />
        <span className="font-black tracking-tight text-sm">CyMed Provider</span>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {LINKS.map(({ href, icon: Icon, key }) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href} className={`nav-item ${active ? 'active' : ''}`}>
              <Icon className="w-4 h-4" />
              {t(key)}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
