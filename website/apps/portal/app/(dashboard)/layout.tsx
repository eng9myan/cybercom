"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ShieldCheck,
  Download,
  Server,
  LifeBuoy,
  BookOpen,
  User,
  Bell,
  LogOut,
  ChevronLeft,
  Menu,
  X,
  Settings,
  ChevronDown,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  badge?: number;
}

// ── Navigation config ─────────────────────────────────────────────────────────

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/licenses", label: "Licenses", icon: ShieldCheck },
  { href: "/downloads", label: "Downloads", icon: Download },
  { href: "/deployments", label: "Deployments", icon: Server },
  { href: "/tickets", label: "Support Tickets", icon: LifeBuoy, badge: 2 },
  { href: "/training", label: "Training", icon: BookOpen },
  { href: "/profile", label: "Profile", icon: User },
];

const BOTTOM_NAV_ITEMS = NAV_ITEMS.slice(0, 5);

// ── Mock user (replace with real auth session) ────────────────────────────────

const MOCK_USER = {
  name: "Mohammed Al-Nsour",
  email: "m.alnsour@cy-com.com",
  company: "CyberCom Client",
  avatarInitials: "MA",
};

// ── Nav Item component ────────────────────────────────────────────────────────

function SidebarNavItem({
  item,
  isActive,
  collapsed,
  onClick,
}: {
  item: NavItem;
  isActive: boolean;
  collapsed: boolean;
  onClick?: () => void;
}) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onClick}
      aria-current={isActive ? "page" : undefined}
      className={[
        "relative flex items-center gap-3 rounded-xl transition-all duration-200 group",
        collapsed ? "px-3 py-3 justify-center" : "px-4 py-3",
        isActive
          ? "bg-[rgba(237,108,0,0.1)] text-[#f59332]"
          : "text-[#94a3b8] hover:text-white hover:bg-[rgba(255,255,255,0.05)]",
      ].join(" ")}
      style={isActive ? { boxShadow: "inset -2px 0 0 #ed6c00" } : undefined}
      title={collapsed ? item.label : undefined}
    >
      <span className="relative shrink-0">
        <Icon
          className="w-5 h-5"
          aria-hidden="true"
          style={{ strokeWidth: isActive ? 2 : 1.75 }}
        />
        {item.badge && item.badge > 0 && (
          <span
            className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full flex items-center justify-center text-white"
            style={{ background: "#ed6c00", fontSize: "0.625rem", fontWeight: 700 }}
            aria-label={`${item.badge} unread`}
          >
            {item.badge}
          </span>
        )}
      </span>

      {!collapsed && (
        <span className="font-body text-sm font-medium leading-none truncate">
          {item.label}
        </span>
      )}

      {/* Tooltip for collapsed state */}
      {collapsed && (
        <span
          className="absolute left-full ml-3 px-3 py-2 rounded-lg text-xs font-medium text-white opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 whitespace-nowrap z-50"
          style={{
            background: "rgba(15,15,26,0.95)",
            border: "1px solid rgba(255,255,255,0.1)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
          }}
          role="tooltip"
        >
          {item.label}
          {item.badge ? ` (${item.badge})` : ""}
        </span>
      )}
    </Link>
  );
}

// ── User menu dropdown ────────────────────────────────────────────────────────

function UserMenu({ collapsed }: { collapsed: boolean }) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="User menu"
        className={[
          "flex items-center gap-3 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.06)] group w-full",
          collapsed ? "p-2 justify-center" : "p-3",
        ].join(" ")}
        style={{ minHeight: "44px" }}
      >
        {/* Avatar */}
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center font-heading font-semibold text-xs shrink-0"
          style={{ background: "rgba(237,108,0,0.2)", color: "#ed6c00", border: "1px solid rgba(237,108,0,0.3)" }}
          aria-hidden="true"
        >
          {MOCK_USER.avatarInitials}
        </div>

        {!collapsed && (
          <>
            <div className="min-w-0 flex-1 text-left">
              <p className="text-sm font-medium text-white truncate leading-none">
                {MOCK_USER.name}
              </p>
              <p className="text-xs truncate mt-0.5" style={{ color: "#64748b" }}>
                {MOCK_USER.company}
              </p>
            </div>
            <ChevronDown
              className={`w-4 h-4 shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
              style={{ color: "#64748b" }}
              aria-hidden="true"
            />
          </>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div
          role="menu"
          aria-label="User options"
          className="absolute bottom-full mb-2 left-0 w-56 rounded-xl overflow-hidden z-50"
          style={{
            background: "rgba(15,15,26,0.97)",
            border: "1px solid rgba(255,255,255,0.1)",
            boxShadow: "0 -8px 40px rgba(0,0,0,0.6)",
            backdropFilter: "blur(20px)",
          }}
        >
          {/* Email header */}
          <div className="px-4 py-3 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
            <p className="text-xs font-medium text-white">{MOCK_USER.name}</p>
            <p className="text-xs mt-0.5" style={{ color: "#64748b" }}>{MOCK_USER.email}</p>
          </div>

          <div className="p-1.5">
            {[
              { href: "/profile", icon: User, label: "My Profile" },
              { href: "/profile/settings", icon: Settings, label: "Account Settings" },
            ].map(({ href, icon: Icon, label }) => (
              <Link
                key={href}
                href={href}
                role="menuitem"
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors hover:bg-[rgba(255,255,255,0.06)]"
                style={{ color: "#94a3b8" }}
              >
                <Icon className="w-4 h-4" aria-hidden="true" />
                <span>{label}</span>
              </Link>
            ))}
          </div>

          <div className="p-1.5 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
            <Link
              href="/login"
              role="menuitem"
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors hover:bg-[rgba(239,68,68,0.08)] group w-full"
              style={{ color: "#f87171" }}
            >
              <LogOut className="w-4 h-4" aria-hidden="true" />
              <span>Sign out</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main layout ───────────────────────────────────────────────────────────────

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  const closeMobileMenu = useCallback(() => setMobileMenuOpen(false), []);

  // Close notifications on outside click
  useEffect(() => {
    if (!notifOpen) return;
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [notifOpen]);

  // Close mobile menu on resize to desktop
  useEffect(() => {
    const handler = () => {
      if (window.innerWidth >= 1024) setMobileMenuOpen(false);
    };
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  const isActive = useCallback(
    (href: string) => {
      if (href === "/") return pathname === "/";
      return pathname.startsWith(href);
    },
    [pathname]
  );

  return (
    <div
      className="min-h-dvh flex"
      style={{ background: "#0a0a0f" }}
    >
      {/* ── Sidebar (desktop) ── */}
      <aside
        id="sidebar"
        aria-label="Main navigation"
        className={[
          "hidden lg:flex flex-col fixed top-0 left-0 h-full glass-sidebar z-40 transition-all duration-300",
          sidebarCollapsed ? "w-16" : "w-64",
        ].join(" ")}
      >
        {/* Logo */}
        <div
          className="flex items-center gap-3 px-4 h-16 shrink-0"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
        >
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: "rgba(237,108,0,0.15)", border: "1px solid rgba(237,108,0,0.3)" }}
            aria-hidden="true"
          >
            <ShieldCheck className="w-4 h-4" style={{ color: "#ed6c00" }} />
          </div>
          {!sidebarCollapsed && (
            <div className="min-w-0">
              <p className="font-heading font-semibold text-white text-sm leading-none truncate">
                CyberCom
              </p>
              <p className="text-xs mt-0.5" style={{ color: "#64748b" }}>
                Customer Portal
              </p>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav
          className="flex-1 overflow-y-auto overflow-x-hidden px-2 py-4 space-y-1"
          aria-label="Sidebar navigation"
        >
          {NAV_ITEMS.map((item) => (
            <SidebarNavItem
              key={item.href}
              item={item}
              isActive={isActive(item.href)}
              collapsed={sidebarCollapsed}
            />
          ))}
        </nav>

        {/* Bottom: user + collapse toggle */}
        <div
          className="shrink-0 px-2 py-3 space-y-1"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          <UserMenu collapsed={sidebarCollapsed} />

          {/* Collapse toggle */}
          <button
            onClick={() => setSidebarCollapsed((v) => !v)}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            className={[
              "flex items-center gap-3 rounded-xl px-3 py-2.5 w-full transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)]",
              sidebarCollapsed ? "justify-center" : "",
            ].join(" ")}
            style={{ color: "#475569", minHeight: "44px" }}
          >
            <ChevronLeft
              className={`w-4 h-4 transition-transform duration-300 ${sidebarCollapsed ? "rotate-180" : ""}`}
              aria-hidden="true"
            />
            {!sidebarCollapsed && (
              <span className="text-xs font-medium">Collapse</span>
            )}
          </button>
        </div>
      </aside>

      {/* ── Mobile drawer overlay ── */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          aria-hidden="true"
          onClick={closeMobileMenu}
          style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }}
        />
      )}

      {/* ── Mobile drawer ── */}
      <aside
        id="mobile-menu"
        aria-label="Mobile navigation"
        aria-hidden={!mobileMenuOpen}
        className={[
          "fixed top-0 left-0 h-full w-72 glass-sidebar z-50 flex flex-col lg:hidden transition-transform duration-300",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full",
        ].join(" ")}
      >
        {/* Mobile logo + close */}
        <div
          className="flex items-center justify-between px-4 h-16 shrink-0"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: "rgba(237,108,0,0.15)", border: "1px solid rgba(237,108,0,0.3)" }}
              aria-hidden="true"
            >
              <ShieldCheck className="w-3.5 h-3.5" style={{ color: "#ed6c00" }} />
            </div>
            <span className="font-heading font-semibold text-white text-sm">
              CyberCom Portal
            </span>
          </div>
          <button
            onClick={closeMobileMenu}
            aria-label="Close navigation menu"
            className="btn-ghost !p-2 !min-h-0"
            style={{ color: "#94a3b8" }}
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Mobile nav */}
        <nav
          className="flex-1 overflow-y-auto px-2 py-4 space-y-1"
          aria-label="Mobile navigation"
        >
          {NAV_ITEMS.map((item) => (
            <SidebarNavItem
              key={item.href}
              item={item}
              isActive={isActive(item.href)}
              collapsed={false}
              onClick={closeMobileMenu}
            />
          ))}
        </nav>

        {/* Mobile user */}
        <div
          className="px-2 py-3 shrink-0"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          <UserMenu collapsed={false} />
        </div>
      </aside>

      {/* ── Main area ── */}
      <div
        className={[
          "flex-1 flex flex-col min-h-dvh transition-all duration-300",
          "lg:ml-64",
          sidebarCollapsed ? "lg:ml-16" : "lg:ml-64",
        ].join(" ")}
      >
        {/* ── Topbar ── */}
        <header
          className="sticky top-0 z-30 h-16 glass-topbar flex items-center px-4 sm:px-6 gap-4"
          role="banner"
        >
          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Open navigation menu"
            aria-controls="mobile-menu"
            aria-expanded={mobileMenuOpen}
            className="lg:hidden btn-ghost !p-2 !min-h-0 -ml-1"
            style={{ color: "#94a3b8" }}
          >
            <Menu className="w-5 h-5" aria-hidden="true" />
          </button>

          {/* Page title — filled by children via context ideally; show portal name here */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate font-heading" aria-live="polite">
              {NAV_ITEMS.find((n) => isActive(n.href))?.label ?? "Portal"}
            </p>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            {/* Notifications */}
            <div className="relative" ref={notifRef}>
              <button
                onClick={() => setNotifOpen((v) => !v)}
                aria-label="Notifications (2 unread)"
                aria-haspopup="true"
                aria-expanded={notifOpen}
                className="relative btn-ghost !p-2.5 !min-h-0"
                style={{ color: "#94a3b8" }}
              >
                <Bell className="w-5 h-5" aria-hidden="true" />
                <span
                  className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
                  style={{ background: "#ed6c00" }}
                  aria-hidden="true"
                />
              </button>

              {notifOpen && (
                <div
                  role="dialog"
                  aria-label="Notifications"
                  className="absolute right-0 top-full mt-2 w-80 rounded-2xl overflow-hidden z-50"
                  style={{
                    background: "rgba(15,15,26,0.97)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    boxShadow: "0 16px 48px rgba(0,0,0,0.6)",
                    backdropFilter: "blur(20px)",
                  }}
                >
                  <div
                    className="flex items-center justify-between px-4 py-3"
                    style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
                  >
                    <h2 className="font-heading text-sm font-semibold text-white">
                      Notifications
                    </h2>
                    <button
                      className="text-xs transition-colors hover:text-white"
                      style={{ color: "#64748b" }}
                    >
                      Mark all read
                    </button>
                  </div>

                  <ul className="max-h-72 overflow-y-auto" role="list">
                    {[
                      {
                        title: "License expiring soon",
                        body: "CyMed Pro — expires in 14 days",
                        time: "2h ago",
                        unread: true,
                      },
                      {
                        title: "Ticket #4821 updated",
                        body: "Your support ticket has a new response",
                        time: "5h ago",
                        unread: true,
                      },
                      {
                        title: "Download available",
                        body: "CyMed v3.2.1 update is ready",
                        time: "1d ago",
                        unread: false,
                      },
                    ].map((n, i) => (
                      <li
                        key={i}
                        className="flex gap-3 px-4 py-3 transition-colors hover:bg-[rgba(255,255,255,0.04)]"
                        style={{ borderBottom: i < 2 ? "1px solid rgba(255,255,255,0.04)" : "none" }}
                      >
                        <div
                          className="w-2 h-2 rounded-full shrink-0 mt-1.5"
                          style={{ background: n.unread ? "#ed6c00" : "transparent", border: n.unread ? "none" : "1px solid rgba(255,255,255,0.15)" }}
                          aria-hidden="true"
                        />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-white truncate">{n.title}</p>
                          <p className="text-xs mt-0.5 truncate" style={{ color: "#64748b" }}>
                            {n.body}
                          </p>
                          <p className="text-xs mt-1" style={{ color: "#475569" }}>
                            {n.time}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>

                  <div className="px-4 py-2.5" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                    <button className="text-xs w-full text-center transition-colors hover:text-white" style={{ color: "#64748b" }}>
                      View all notifications
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Desktop user avatar (quick logout) */}
            <Link
              href="/profile"
              aria-label="Go to profile"
              className="hidden sm:flex w-9 h-9 rounded-xl items-center justify-center font-heading font-semibold text-xs transition-all hover:ring-2 hover:ring-[rgba(237,108,0,0.4)]"
              style={{
                background: "rgba(237,108,0,0.15)",
                color: "#ed6c00",
                border: "1px solid rgba(237,108,0,0.25)",
              }}
            >
              {MOCK_USER.avatarInitials}
            </Link>
          </div>
        </header>

        {/* ── Page content ── */}
        <main
          id="main-content"
          className="flex-1 px-4 sm:px-6 lg:px-8 py-6 pb-24 lg:pb-8"
          tabIndex={-1}
        >
          {children}
        </main>
      </div>

      {/* ── Mobile bottom nav ── */}
      <nav
        className="lg:hidden fixed bottom-0 left-0 right-0 z-30 flex items-center justify-around px-2 pb-safe"
        aria-label="Mobile bottom navigation"
        style={{
          background: "rgba(10,10,15,0.95)",
          borderTop: "1px solid rgba(255,255,255,0.06)",
          backdropFilter: "blur(20px)",
          height: "64px",
          paddingBottom: "env(safe-area-inset-bottom)",
        }}
      >
        {BOTTOM_NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              aria-label={item.badge ? `${item.label} (${item.badge} unread)` : item.label}
              className="relative flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all duration-200 min-w-[52px]"
              style={{ color: active ? "#f59332" : "#64748b" }}
            >
              <span className="relative">
                <Icon
                  className="w-5 h-5"
                  aria-hidden="true"
                  style={{ strokeWidth: active ? 2 : 1.75 }}
                />
                {item.badge && item.badge > 0 && (
                  <span
                    className="absolute -top-1 -right-1.5 w-3.5 h-3.5 rounded-full flex items-center justify-center text-white"
                    style={{ background: "#ed6c00", fontSize: "0.5rem", fontWeight: 700 }}
                    aria-hidden="true"
                  >
                    {item.badge}
                  </span>
                )}
              </span>
              <span className="text-2xs font-medium" style={{ fontSize: "0.625rem" }}>
                {item.label.split(" ")[0]}
              </span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
