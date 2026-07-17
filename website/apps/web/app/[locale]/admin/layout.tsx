"use client";

import Link from "next/link";
import { usePathname, useParams, useRouter } from "next/navigation";
import {
  LayoutDashboard, Users, ShoppingBag, Package,
  TrendingUp, Settings, Bell, LogOut, ChevronRight,
  Shield, Menu, X, BarChart3, Loader2,
} from "lucide-react";
import { useState, useEffect } from "react";
import { tokenStore } from "@/lib/auth/tokens";
import { isPlatformAdmin, logout, decodeAccessTokenClaims } from "@/lib/auth/cyidentity";

const NAV = [
  { href: "/en/admin", label: "Revenue", icon: TrendingUp, exact: true },
  { href: "/en/admin/customers", label: "Customers", icon: Users },
  { href: "/en/admin/subscriptions", label: "Subscriptions", icon: ShoppingBag },
  { href: "/en/admin/products", label: "Products", icon: Package },
];

const PUBLIC_ADMIN_PATHS = ["/admin/login", "/admin/auth/callback"];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const params = useParams();
  const router = useRouter();
  const locale = (params.locale as string) ?? "en";
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  const isPublicPath = PUBLIC_ADMIN_PATHS.some((p) => pathname.includes(p));

  useEffect(() => {
    if (isPublicPath) {
      setAuthChecked(true);
      return;
    }
    if (!tokenStore.isAuthenticated() || !isPlatformAdmin()) {
      router.replace(`/${locale}/admin/login`);
      return;
    }
    setAuthChecked(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  function isActive(item: (typeof NAV)[0]) {
    return item.exact ? pathname === item.href : pathname.startsWith(item.href);
  }

  const claims = authChecked && !isPublicPath ? decodeAccessTokenClaims() : null;
  const adminLabel = claims?.email || claims?.preferred_username || "Admin";

  if (isPublicPath) {
    return <>{children}</>;
  }

  if (!authChecked) {
    return (
      <div className="min-h-dvh flex items-center justify-center bg-cy-darker">
        <Loader2 className="w-6 h-6 text-cy-orange animate-spin" />
      </div>
    );
  }

  const Sidebar = (
    <aside className="w-64 flex-shrink-0 bg-cy-dark/90 border-r border-cy-glass-border flex flex-col h-full">
      <div className="px-5 py-5 border-b border-cy-glass-border">
        <Link href="/en/admin" className="flex items-center gap-2 text-white font-heading font-bold text-lg">
          <Shield className="w-5 h-5 text-red-400" />
          CyberCom
          <span className="text-xs font-normal text-red-400 ml-1 px-1.5 py-0.5 rounded bg-red-500/10 border border-red-500/20">Admin</span>
        </Link>
      </div>

      <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = isActive(item);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${active ? "bg-red-500/15 text-red-400 border border-red-500/20" : "text-cy-gray-300 hover:bg-cy-glass-border/50 hover:text-white"}`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
              {active && <ChevronRight className="w-3.5 h-3.5 ml-auto" />}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 py-3 border-t border-cy-glass-border space-y-1">
        <div className="px-3 py-2 text-xs text-cy-gray-500 truncate">Logged in as: {adminLabel}</div>
        <Link href={`/${locale}/portal`} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-cy-gray-300 hover:bg-cy-glass-border/50 hover:text-white transition-all">
          <LayoutDashboard className="w-4 h-4" />
          Customer Portal
        </Link>
        <Link href={`/${locale}`} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-cy-gray-300 hover:bg-cy-glass-border/50 hover:text-white transition-all">
          <BarChart3 className="w-4 h-4" />
          Website
        </Link>
        <button onClick={() => logout(locale)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-cy-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all w-full">
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  );

  return (
    <div className="min-h-dvh flex flex-col pt-16 bg-cy-darker">
      <div className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-red-500/20 bg-cy-dark/90 sticky top-16 z-30">
        <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-cy-glass-border/50 text-cy-gray-300">
          <Menu className="w-5 h-5" />
        </button>
        <span className="text-sm font-medium text-red-400">Admin Panel</span>
        <div className="w-9" />
      </div>

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
        <div className="hidden lg:flex">{Sidebar}</div>
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
