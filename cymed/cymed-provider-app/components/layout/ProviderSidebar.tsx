'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, Calendar, FlaskConical, Video, Stethoscope, MessageSquare, ListChecks, BedDouble, Pill } from 'lucide-react';
import { useT } from '@/lib/i18n';

const LINKS = [
  { href: '/', icon: LayoutDashboard, key: 'nav.overview' },
  { href: '/patients', icon: Users, key: 'nav.patients' },
  { href: '/admissions', icon: BedDouble, key: 'nav.admissions' },
  { href: '/schedule', icon: Calendar, key: 'nav.schedule' },
  { href: '/orders', icon: FlaskConical, key: 'nav.orders' },
  { href: '/order-sets', icon: ListChecks, key: 'nav.orderSets' },
  { href: '/dispensing', icon: Pill, key: 'nav.dispensing' },
  { href: '/messages', icon: MessageSquare, key: 'nav.messages' },
  { href: '/telemedicine', icon: Video, key: 'nav.telemedicine' },
] as const;

// Only these two map cleanly onto a single gated product (hospital ADT/eMAR,
// pharmacy dispensing) — everything else (patients/schedule/orders/
// order-sets/messages/telemedicine) runs on shared core clinical
// infrastructure that ProductEntitlementMiddleware deliberately never gates,
// so hiding them per-product would be guessing, not a real API boundary.
const PRODUCT_GATED_LINKS: Record<string, string> = {
  '/admissions': 'cymed_hospital',
  '/dispensing': 'cymed_pharmacy',
};

export default function ProviderSidebar() {
  const pathname = usePathname();
  const t = useT();
  // null = still loading or the fetch failed — fail open (show everything)
  // rather than block the page on an entitlements call, same as the
  // best-effort/degrade pattern already used for the lab/imaging result
  // viewer on /orders.
  const [entitled, setEntitled] = useState<string[] | null>(null);

  useEffect(() => {
    fetch('/api/cymed/rest/commercial/editions/my-entitlements/')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setEntitled(data?.products ?? null))
      .catch(() => setEntitled(null));
  }, []);

  const links = LINKS.filter(({ href }) => {
    const requiredProduct = PRODUCT_GATED_LINKS[href];
    if (!requiredProduct) return true;
    if (entitled === null) return true;
    return entitled.includes(requiredProduct);
  });

  return (
    <aside className="w-[220px] shrink-0 border-e border-white/5 bg-[#0a0f1e] flex flex-col">
      <div className="h-16 flex items-center gap-2 px-5 border-b border-white/5">
        <Stethoscope className="w-5 h-5 text-[var(--cy-teal)]" />
        <span className="font-black tracking-tight text-sm">CyMed Provider</span>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {links.map(({ href, icon: Icon, key }) => {
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
