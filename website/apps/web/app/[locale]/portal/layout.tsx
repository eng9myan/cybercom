"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, CreditCard, LifeBuoy, Settings,
  ShoppingBag, Bell, LogOut, ChevronRight, Menu, X,
  Building2,
} from "lucide-react";
import { useState } from "react";

const NAV = [
  { href: "/en/portal", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/en/portal/subscriptions", label: "Subscriptions", icon: ShoppingBag },
  { href: "/en/portal/billing", label: "Billing", icon: CreditCard },
  { href: "/en/portal/support", label: "Support", icon: LifeBuoy },
  { href: "/en/portal/settings", label: "Settings", icon: Settings },
];

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function isActive(item: (typeof NAV)[0]) {
    return item.exact ? pathname === item.href || pathname === item.href.replace("/en/", "/ar/")
      : pathname.startsWith(item.href) || pathname.startsWith(item.href.replace("/en/", "/ar/"));
  }

  const Sidebar = (
    <aside className="w-64 flex-shrink-0 bg-cy-dark/80 border-r border-cy-glass-border flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-cy-glass-border">
        <Link href="/en" className="flex items-center gap-2 text-white font-heading font-bold text-lg">
          <Building2 className="w-5 h-5 text-cy-orange" />
          CyberCom
          <span className="text-xs font-normal text-cy-gray-400 ml-1">Portal</span>
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = isActive(item);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${active ? "bg-cy-orange/15 text-cy-orange border border-cy-orange/20" : "text-cy-gray-300 hover:bg-cy-glass-border/50 hover:text-white"}`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
              {active && <ChevronRight className="w-3.5 h-3.5 ml-auto" />}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-4 border-t border-cy-glass-border space-y-1">
        <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-cy-gray-300 hover:bg-cy-glass-border/50 hover:text-white transition-all w-full">
          <Bell className="w-4 h-4" />
          Notifications
        </button>
        <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-cy-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all w-full">
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  );

  return (
    <div className="min-h-dvh flex flex-col pt-16 bg-cy-darker">
      {/* Mobile topbar */}
      <div className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-cy-glass-border bg-cy-dark/80 sticky top-16 z-30">
        <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-cy-glass-border/50 text-cy-gray-300">
          <Menu className="w-5 h-5" />
        </button>
        <span className="text-sm font-medium text-white">Customer Portal</span>
        <div className="w-9" />
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <div className="relative flex">
            {Sidebar}
            <button onClick={() => setSidebarOpen(false)} className="absolute top-4 right-4 p-1.5 rounded-lg bg-cy-glass-border text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar */}
        <div className="hidden lg:flex">{Sidebar}</div>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
