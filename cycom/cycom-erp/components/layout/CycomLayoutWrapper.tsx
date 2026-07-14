'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import CycomSidebar from './CycomSidebar';
import CycomTopbar from './CycomTopbar';

export default function CycomLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  
  // Conditionally hide sidebar/topbar for full-screen routes (landing, login, public signing portal)
  const isFullScreen = pathname === '/' || pathname === '/login' || pathname?.startsWith('/sign/public/');

  if (isFullScreen) {
    return <main className="min-h-screen w-full">{children}</main>;
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
    </div>
  );
}
