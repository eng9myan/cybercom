"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard, Users, ShieldAlert, Settings, User, LogOut, Bell, ChevronLeft, ChevronRight,
  Target, FileText, ShoppingBag, BarChart3, MessageSquare, Layers, Search, Sparkles, Command,
  Package, Warehouse, ArrowLeftRight, Tag, Monitor, Clock, Truck, Building2,
} from "lucide-react";
import Logo from "@/components/brand/Logo";
import { api } from "@/lib/api";

const NAV_GROUPS = [
  {
    label: "Overview",
    items: [
      { name: "Dashboard", path: "/app", icon: LayoutDashboard },
      { name: "Sales Analytics", path: "/app/sales-dashboard", icon: BarChart3 },
    ],
  },
  {
    label: "Pipeline",
    items: [
      { name: "CRM Kanban", path: "/app/crm", icon: Layers },
      { name: "Leads", path: "/app/leads", icon: Target },
      { name: "Quotations", path: "/app/quotations", icon: FileText },
      { name: "Sales Orders", path: "/app/orders", icon: ShoppingBag },
    ],
  },
  {
    label: "Point of Sale",
    items: [
      { name: "POS Terminal", path: "/app/pos", icon: Monitor },
      { name: "Sessions", path: "/app/pos/sessions", icon: Clock },
    ],
  },
  {
    label: "Catalog",
    items: [
      { name: "Products", path: "/app/catalog", icon: Package },
      { name: "Categories", path: "/app/catalog/categories", icon: Tag },
    ],
  },
  {
    label: "Inventory",
    items: [
      { name: "Stock Levels", path: "/app/inventory", icon: Warehouse },
      { name: "Stock Movements", path: "/app/inventory/movements", icon: ArrowLeftRight },
      { name: "Inter-Branch Transfers", path: "/app/inventory/transfers", icon: Truck },
    ],
  },
  {
    label: "Purchasing",
    items: [
      { name: "Purchase Orders", path: "/app/purchasing", icon: Truck },
      { name: "Vendors", path: "/app/purchasing/vendors", icon: Building2 },
    ],
  },
  {
    label: "Customer",
    items: [
      { name: "Customer Portal", path: "/app/customer-portal", icon: MessageSquare },
    ],
  },
  {
    label: "Administration",
    items: [
      { name: "Users", path: "/app/users", icon: Users },
      { name: "Roles & RBAC", path: "/app/roles", icon: ShieldAlert },
      { name: "System Settings", path: "/app/settings", icon: Settings },
      { name: "Device Registry", path: "/app/settings/devices", icon: Monitor },
      { name: "My Profile", path: "/app/profile", icon: User },
    ],
  },
];

const FLAT_NAV = NAV_GROUPS.flatMap((g) => g.items);

export default function AppLayout({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [tenantName, setTenantName] = useState("");
  const [username, setUsername] = useState("");
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);

  useEffect(() => {
    const token = typeof window !== "undefined" && localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }
    setTenantName(localStorage.getItem("tenant_name") || "Acme Tenant");
    setUsername(localStorage.getItem("username") || "Operator");
    fetchNotifications();
    checkOnboarding();
  }, []);

  const checkOnboarding = async () => {
    try {
      const res = await api.get("/api/v1/tenants/settings/");
      const list = Array.isArray(res) ? res : res.results || [];
      if (list[0] && !list[0].onboarding_completed) {
        router.push("/onboarding");
      }
    } catch (_) {}
  };

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const tenantId = localStorage.getItem("tenant_id");
      const base = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${base}/api/v1/notifications/`, {
        headers: { Authorization: `Bearer ${token}`, "X-Tenant-ID": tenantId },
      });
      if (res.ok) setNotifications(await res.json());
    } catch (_) {}
  };

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const base = process.env.NEXT_PUBLIC_API_URL || "";
      await fetch(`${base}/api/v1/identity/logout/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (_) {}
    localStorage.clear();
    router.push("/login");
  };

  const currentPage = FLAT_NAV.find((n) => n.path === pathname);
  const unread = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="min-h-dvh flex bg-[var(--color-surface)] text-[var(--color-ink)]">
      {/* Sidebar */}
      <aside
        className={`hidden md:flex flex-col bg-[var(--color-surface)] border-r border-[rgba(255,255,255,0.07)] transition-[width] duration-300 ${
          collapsed ? "w-[76px]" : "w-[260px]"
        }`}
      >
        <div className="h-16 px-4 flex items-center justify-between border-b border-[rgba(255,255,255,0.07)]">
          {collapsed ? <Logo mark href={null} /> : <Logo href={null} />}
        </div>

        {!collapsed && (
          <div className="px-4 py-4 border-b border-[rgba(255,255,255,0.07)]">
            <button className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-[var(--color-surface-2)] hover:bg-[var(--color-line)] transition text-left">
              <span className="flex items-center gap-2 min-w-0">
                <span className="w-6 h-6 rounded-md bg-gradient-to-br from-[#ED6C00] to-[#FF8A2A] text-white text-[10px] font-bold flex items-center justify-center shrink-0">
                  {(tenantName || "T").slice(0, 2).toUpperCase()}
                </span>
                <span className="text-sm font-semibold truncate">{tenantName}</span>
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-[var(--color-ink-muted)]" />
            </button>
          </div>
        )}

        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
          {NAV_GROUPS.map((group) => (
            <div key={group.label}>
              {!collapsed && (
                <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[var(--color-ink-muted)]">
                  {group.label}
                </div>
              )}
              <ul className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = pathname === item.path;
                  return (
                    <li key={item.path}>
                      <Link
                        href={item.path}
                        title={collapsed ? item.name : undefined}
                        className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors relative ${
                          active
                            ? "bg-[rgba(237,108,0,0.10)] text-[var(--color-ink)]"
                            : "text-[var(--color-ink-soft)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)]"
                        }`}
                      >
                        {active && (
                          <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-r bg-[#ED6C00]" aria-hidden />
                        )}
                        <Icon className={`w-[18px] h-[18px] shrink-0 ${active ? "text-[#ED6C00]" : ""}`} />
                        {!collapsed && <span className="truncate">{item.name}</span>}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="border-t border-[rgba(255,255,255,0.07)] p-3 space-y-2">
          {!collapsed && (
            <div className="flex items-center gap-3 px-2 py-2 rounded-lg">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#59C3E1] to-[#0E7C9B] text-white text-xs font-bold flex items-center justify-center shrink-0">
                {(username || "U").slice(0, 2).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-semibold truncate">{username}</div>
                <div className="text-xs text-[var(--color-ink-muted)] truncate">Admin</div>
              </div>
              <button
                onClick={handleLogout}
                aria-label="Sign out"
                className="w-9 h-9 rounded-lg hover:bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] hover:text-[#DC2626] flex items-center justify-center transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="w-full h-9 rounded-lg border border-[var(--color-line)] hover:bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] flex items-center justify-center transition"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-16 bg-[rgba(15,15,26,0.85)] backdrop-blur-xl border-b border-[rgba(255,255,255,0.07)] sticky top-0 z-30">
          <div className="h-full px-4 md:px-8 flex items-center gap-4">
            <div className="min-w-0">
              <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--color-ink-muted)]">
                {tenantName}
              </div>
              <h1 className="text-base md:text-lg font-heading font-bold leading-tight truncate">
                {currentPage?.name || "Console"}
              </h1>
            </div>

            <div className="flex-1 max-w-xl mx-auto hidden md:block">
              <button
                onClick={() => setAiOpen(true)}
                className="w-full h-10 px-3 rounded-xl border border-[var(--color-line)] bg-[var(--color-surface)] hover:border-[var(--color-ink)] flex items-center gap-2 text-sm text-[var(--color-ink-muted)] transition"
              >
                <Search className="w-4 h-4" />
                <span className="flex-1 text-left">Ask AI or search anything…</span>
                <span className="hidden md:inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-[rgba(255,255,255,0.12)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]">
                  <Command className="w-3 h-3" /> K
                </span>
              </button>
            </div>

            <div className="flex items-center gap-2 ml-auto">
              <button
                onClick={() => setAiOpen(true)}
                className="cy-btn cy-btn-primary !py-2 !px-3 text-sm"
              >
                <Sparkles className="w-4 h-4" /> <span className="hidden sm:inline">AI Copilot</span>
              </button>

              <div className="relative">
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  aria-label="Notifications"
                  className="relative w-10 h-10 rounded-xl border border-[var(--color-line)] bg-white hover:bg-[var(--color-surface-2)] flex items-center justify-center transition"
                >
                  <Bell className="w-[18px] h-[18px] text-[var(--color-ink-soft)]" />
                  {unread > 0 && (
                    <span className="absolute top-1.5 right-1.5 min-w-[16px] h-4 px-1 rounded-full bg-[#ED6C00] text-white text-[10px] font-bold flex items-center justify-center">
                      {unread > 9 ? "9+" : unread}
                    </span>
                  )}
                </button>
                {showNotifications && (
                  <div className="absolute top-full right-0 mt-2 w-80 cy-glass p-3 z-50">
                    <div className="px-1 pb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[var(--color-ink-muted)]">
                      Notifications
                    </div>
                    <div className="max-h-72 overflow-y-auto space-y-2">
                      {notifications.length === 0 && (
                        <div className="text-sm text-[var(--color-ink-muted)] text-center py-6">
                          You're all caught up.
                        </div>
                      )}
                      {notifications.map((n) => (
                        <div
                          key={n.id}
                          className={`p-3 rounded-lg border text-sm ${
                            n.is_read
                              ? "bg-[var(--color-surface-2)] border-[rgba(255,255,255,0.07)]"
                              : "bg-[rgba(237,108,0,0.06)] border-[rgba(237,108,0,0.25)]"
                          }`}
                        >
                          <div className="font-semibold">{n.title}</div>
                          <div className="text-xs text-[var(--color-ink-soft)] mt-0.5">{n.message}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 md:p-8 overflow-y-auto">{children}</main>
      </div>

      {/* AI Command Palette */}
      {aiOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="AI Copilot"
          className="fixed inset-0 z-[100] flex items-start justify-center pt-[12vh] px-4 bg-black/40 backdrop-blur-sm"
          onClick={() => setAiOpen(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-2xl rounded-2xl bg-[var(--color-surface)] shadow-2xl border border-[rgba(255,255,255,0.10)] overflow-hidden"
          >
            <div className="flex items-center gap-3 px-4 h-14 border-b border-[var(--color-line)]">
              <Sparkles className="w-5 h-5 text-[#ED6C00]" />
              <input
                autoFocus
                placeholder="Draft a quote, forecast Q3, find dormant leads…"
                className="flex-1 bg-transparent text-base placeholder:text-[var(--color-ink-muted)] focus:outline-none"
              />
              <button
                onClick={() => setAiOpen(false)}
                className="text-xs text-[var(--color-ink-muted)] px-2 py-1 rounded border border-[var(--color-line)]"
              >
                Esc
              </button>
            </div>
            <div className="p-3 max-h-[50vh] overflow-y-auto">
              <div className="px-2 pb-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[var(--color-ink-muted)]">
                Suggested
              </div>
              {[
                { t: "Summarize this week's pipeline movement", i: BarChart3 },
                { t: "Draft a follow-up sequence for stalled deals", i: MessageSquare },
                { t: "Generate Q3 revenue forecast", i: Sparkles },
                { t: "Find leads inactive 30+ days", i: Target },
              ].map((s, i) => (
                <button
                  key={i}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-[var(--color-surface-2)] text-left transition"
                >
                  <s.i className="w-4 h-4 text-[var(--color-ink-muted)]" />
                  <span className="text-sm flex-1">{s.t}</span>
                  <ChevronRight className="w-4 h-4 text-[var(--color-ink-muted)]" />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
