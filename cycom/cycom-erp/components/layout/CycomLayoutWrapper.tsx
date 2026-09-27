'use client';

import React, { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import CycomSidebar from './CycomSidebar';
import CycomTopbar from './CycomTopbar';
import CyaiChatWidget from '../CyaiChatWidget';
import PublicChatWidget from '../PublicChatWidget';
import CommandPalette from '../CommandPalette';

const PUBLIC_SITE_PREFIXES = ['/store/', '/blog/', '/forum/', '/learn/', '/site/'];

export default function CycomLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Close the mobile drawer on every navigation instead of leaving it open
  // over the new page.
  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

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
      <CycomSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <CycomTopbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          {children}
        </main>
      </div>
      <CyaiChatWidget />
      {/* Ctrl/Cmd+K from anywhere in the admin shell. */}
      <CommandPalette />
    </div>
  );
}
