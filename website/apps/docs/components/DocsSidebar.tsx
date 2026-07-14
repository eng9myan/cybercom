"use client";

import React, { useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronDown,
  ChevronRight,
  Activity,
  Building2,
  Landmark,
  Bot,
  ShieldCheck,
  GitMerge,
  BookOpen,
  Code2,
  Rocket,
  FileText,
  HelpCircle,
  Tag,
  X,
} from "lucide-react";
import { NAV_SECTIONS } from "@/lib/types";
import { SearchBar } from "./SearchBar";
import { cn } from "@/lib/utils";

const SECTION_ICONS: Record<string, React.ReactNode> = {
  "getting-started": <Rocket className="w-4 h-4" />,
  "api-reference": <Code2 className="w-4 h-4" />,
  cymed: <Activity className="w-4 h-4" />,
  cycom: <Building2 className="w-4 h-4" />,
  cygov: <Landmark className="w-4 h-4" />,
  cyai: <Bot className="w-4 h-4" />,
  cyidentity: <ShieldCheck className="w-4 h-4" />,
  cyintegrationhub: <GitMerge className="w-4 h-4" />,
  "release-notes": <Tag className="w-4 h-4" />,
};

const SECTION_COLORS: Record<string, string> = {
  "getting-started": "#ed6c00",
  "api-reference": "#a78bfa",
  cymed: "#10b981",
  cycom: "#3b82f6",
  cygov: "#8b5cf6",
  cyai: "#ed6c00",
  cyidentity: "#59c3e1",
  cyintegrationhub: "#f59e0b",
  "release-notes": "#94a3b8",
};

interface DocsSidebarProps {
  /** Controlled from layout for mobile drawer */
  open?: boolean;
  onClose?: () => void;
}

export function DocsSidebar({ open, onClose }: DocsSidebarProps) {
  const pathname = usePathname();

  // Which groups are expanded — default expand the active section
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    for (const s of NAV_SECTIONS) {
      // Expand if any child matches current path
      const hasActive = s.items.some((item) => pathname.startsWith(`/${item.slug}`));
      initial[s.slug] = hasActive || s.slug === "getting-started";
    }
    return initial;
  });

  const toggle = useCallback((slug: string) => {
    setExpanded((prev) => ({ ...prev, [slug]: !prev[slug] }));
  }, []);

  const isItemActive = (itemSlug: string) => pathname === `/${itemSlug}` || pathname.startsWith(`/${itemSlug}/`);
  const isSectionActive = (section: (typeof NAV_SECTIONS)[0]) =>
    section.items.some((item) => isItemActive(item.slug));

  return (
    <>
      {/* Mobile overlay */}
      {open !== undefined && (
        <div
          className={cn(
            "fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden transition-opacity duration-200",
            open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
          )}
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel */}
      <aside
        id="docs-sidebar"
        aria-label="Documentation navigation"
        className={cn(
          "fixed top-0 left-0 h-full z-50 flex flex-col",
          "w-[var(--sidebar-width)] bg-[#0a0a0f] border-r border-white/[0.07]",
          // Desktop: always visible, no transform
          "lg:translate-x-0 lg:top-[var(--header-height)] lg:h-[calc(100dvh-var(--header-height))]",
          // Mobile: slide in/out
          open !== undefined
            ? cn("transition-transform duration-300 ease-out", open ? "translate-x-0" : "-translate-x-full")
            : "translate-x-0 hidden lg:flex"
        )}
      >
        {/* Mobile close + header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.07] lg:hidden">
          <span className="text-sm font-semibold text-white">Documentation</span>
          <button
            onClick={onClose}
            aria-label="Close navigation"
            className="btn-ghost !p-1.5 !rounded-md"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Sidebar search */}
        <div className="px-3 py-3 border-b border-white/[0.07]">
          <SearchBar variant="compact" placeholder="Quick search…" />
        </div>

        {/* Nav list */}
        <nav
          aria-label="Docs sections"
          className="flex-1 overflow-y-auto py-3 px-2"
        >
          {NAV_SECTIONS.map((section) => {
            const isExpanded = expanded[section.slug] ?? false;
            const isActive = isSectionActive(section);
            const color = SECTION_COLORS[section.slug] ?? "#94a3b8";
            const icon = SECTION_ICONS[section.slug];

            return (
              <div key={section.slug} className="mb-0.5">
                {/* Section header button */}
                <button
                  type="button"
                  onClick={() => toggle(section.slug)}
                  aria-expanded={isExpanded}
                  aria-controls={`sidebar-section-${section.slug}`}
                  className={cn(
                    "w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-all duration-150 group",
                    isActive
                      ? "text-white bg-white/[0.05]"
                      : "text-cy-gray-400 hover:text-white hover:bg-white/[0.04]"
                  )}
                >
                  {/* Icon */}
                  <span
                    className={cn(
                      "flex-shrink-0 transition-colors",
                      isActive ? "" : "group-hover:text-white"
                    )}
                    style={{ color: isActive ? color : undefined }}
                  >
                    {icon ?? <BookOpen className="w-4 h-4" />}
                  </span>

                  <span className="flex-1 text-xs font-semibold tracking-wide uppercase">
                    {section.title}
                  </span>

                  {/* Chevron */}
                  <span className="flex-shrink-0 transition-transform duration-200" style={{ transform: isExpanded ? "rotate(0deg)" : "rotate(-90deg)" }}>
                    <ChevronDown className="w-3.5 h-3.5 text-cy-gray-600" />
                  </span>
                </button>

                {/* Items */}
                <div
                  id={`sidebar-section-${section.slug}`}
                  className={cn(
                    "overflow-hidden transition-all duration-200",
                    isExpanded ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"
                  )}
                >
                  <ul className="mt-0.5 ml-3 pl-3.5 border-l border-white/[0.06] space-y-0.5 pb-2">
                    {section.items.map((item) => {
                      const active = isItemActive(item.slug);
                      return (
                        <li key={item.slug}>
                          <Link
                            href={`/${item.slug}`}
                            onClick={onClose}
                            className={cn(
                              "relative sidebar-item",
                              active && "active"
                            )}
                            aria-current={active ? "page" : undefined}
                          >
                            {item.title}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              </div>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-white/[0.07] space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-cy-gray-600">docs.cy-com.com</span>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://api.cy-com.com/api/v1/public/documentation/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-cy-gray-600 hover:text-cy-orange transition-colors flex items-center gap-1"
              aria-label="API reference (opens in new tab)"
            >
              <Code2 className="w-3 h-3" />
              API
            </a>
            <a
              href="https://www.cy-com.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-cy-gray-600 hover:text-cy-orange transition-colors flex items-center gap-1"
              aria-label="Main website (opens in new tab)"
            >
              <Rocket className="w-3 h-3" />
              Website
            </a>
            <a
              href="/release-notes"
              className="text-xs text-cy-gray-600 hover:text-cy-orange transition-colors flex items-center gap-1"
            >
              <Tag className="w-3 h-3" />
              Changelog
            </a>
          </div>
        </div>
      </aside>
    </>
  );
}
