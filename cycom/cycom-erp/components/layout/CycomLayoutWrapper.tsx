'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import CycomSidebar from './CycomSidebar';
import CycomTopbar from './CycomTopbar';
import CyaiChatWidget from '../CyaiChatWidget';
import PublicChatWidget from '../PublicChatWidget';

const PUBLIC_SITE_PREFIXES = ['/store/', '/blog/', '/forum/', '/learn/', '/site/'];

export default function CycomLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Conditionally hide sidebar/topbar for full-screen routes (landing, login, public signing portal,
  // public storefront, public blog, public forum, public course catalog — visitors never see the internal admin shell)
  const publicSitePrefix = PUBLIC_SITE_PREFIXES.find((p) => pathname?.startsWith(p));
  const isFullScreen =
    pathname === '/' || pathname === '/login' || pathname?.startsWith('/sign/public/') || !!publicSitePrefix;

  if (isFullScreen) {
    // e.g. '/store/acme-co/cart' -> 'acme-co' — the tenant slug every public page is scoped under.
    const tenantSlug = publicSitePrefix ? pathname?.slice(publicSitePrefix.length).split('/')[0] : undefined;
    return (
      <main className="min-h-screen w-full">
        {children}
        {tenantSlug && <PublicChatWidget slug={tenantSlug} />}
      </main>
    );
  }

  return (
    <div className="flex min-h-screen w-full bg-[#0a0f1e]">
      <CycomSidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <CycomTopbar />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
      <CyaiChatWidget />
    </div>
  );
}
