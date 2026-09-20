'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import ProviderSidebar from './ProviderSidebar';
import ProviderTopbar from './ProviderTopbar';

export default function ProviderLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isFullScreen = pathname === '/login';

  if (isFullScreen) {
    return <main className="min-h-screen w-full">{children}</main>;
  }

  return (
    <div className="flex min-h-screen w-full bg-[#0a0f1e]">
      <ProviderSidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <ProviderTopbar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
