"use client";
import { useState, useMemo } from "react";

export type ModuleCategory =
  | "clinical"
  | "erp"
  | "ai"
  | "operations"
  | "finance"
  | "hr"
  | "inventory"
  | "reports"
  | "admin";

export interface ProductModule {
  name: string;
  category: ModuleCategory;
  desc: string;
  roles: string[];
  workflow?: string;
  permission?: string;
  demoRoute?: string;
}

const CAT_META: Record<ModuleCategory, { label: string; pill: string; dot: string }> = {
  clinical:   { label: "Clinical",    pill: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",  dot: "bg-emerald-400" },
  erp:        { label: "ERP",         pill: "text-blue-400 bg-blue-500/10 border-blue-500/20",           dot: "bg-blue-400" },
  ai:         { label: "AI",          pill: "text-purple-400 bg-purple-500/10 border-purple-500/20",     dot: "bg-purple-400" },
  operations: { label: "Operations",  pill: "text-amber-400 bg-amber-500/10 border-amber-500/20",        dot: "bg-amber-400" },
  finance:    { label: "Finance",     pill: "text-sky-400 bg-sky-500/10 border-sky-500/20",              dot: "bg-sky-400" },
  hr:         { label: "HR",          pill: "text-pink-400 bg-pink-500/10 border-pink-500/20",           dot: "bg-pink-400" },
  inventory:  { label: "Inventory",   pill: "text-orange-400 bg-orange-500/10 border-orange-500/20",     dot: "bg-orange-400" },
  reports:    { label: "Reports",     pill: "text-teal-400 bg-teal-500/10 border-teal-500/20",           dot: "bg-teal-400" },
  admin:      { label: "Admin",       pill: "text-slate-400 bg-slate-500/10 border-slate-500/20",        dot: "bg-slate-400" },
};

type TabKey = "all" | ModuleCategory;

const TAB_ORDER: TabKey[] = ["all", "clinical", "erp", "ai", "operations", "finance", "hr", "inventory", "reports", "admin"];

export function ModuleExplorer({ modules }: { modules: ProductModule[] }) {
  const [activeTab, setActiveTab] = useState<TabKey>("all");
  const [expanded, setExpanded] = useState<string | null>(null);

  const presentCats = useMemo(
    () => new Set(modules.map(m => m.category)),
    [modules]
  );

  const tabs = useMemo(
    () => TAB_ORDER.filter(t => t === "all" || presentCats.has(t as ModuleCategory)),
    [presentCats]
  );

  const filtered = activeTab === "all" ? modules : modules.filter(m => m.category === activeTab);

  const tabLabel = (t: TabKey) => t === "all" ? "All Modules" : CAT_META[t as ModuleCategory].label;
  const tabCount = (t: TabKey) => t === "all" ? modules.length : modules.filter(m => m.category === t).length;

  return (
    <div>
      {/* Tab bar — horizontal scroll on mobile */}
      <div className="flex gap-1.5 mb-8 overflow-x-auto pb-1 scrollbar-hide" role="tablist">
        {tabs.map(tab => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-shrink-0 px-3.5 py-2 rounded-lg text-xs font-medium border transition-all duration-150 flex items-center gap-1.5 ${
              activeTab === tab
                ? "bg-cy-orange/15 border-cy-orange/40 text-cy-orange"
                : "bg-cy-glass-bg border-cy-glass-border text-cy-gray-400 hover:text-white hover:border-cy-glass-bg-hover"
            }`}
          >
            {tab !== "all" && (
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${CAT_META[tab as ModuleCategory].dot}`} />
            )}
            {tabLabel(tab)}
            <span className="opacity-50 text-[10px]">{tabCount(tab)}</span>
          </button>
        ))}
      </div>

      {/* Module grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map(mod => {
          const s = CAT_META[mod.category];
          const isExpanded = expanded === mod.name;
          return (
            <button
              key={mod.name}
              onClick={() => setExpanded(isExpanded ? null : mod.name)}
              className={`glass-card p-5 rounded-xl text-left transition-all duration-200 w-full ${
                isExpanded ? "border-cy-orange/30 bg-cy-glass-bg-hover" : "hover:border-cy-glass-bg-hover"
              }`}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-sm font-heading font-semibold text-white leading-snug">{mod.name}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border flex-shrink-0 font-medium ${s.pill}`}>
                  {s.label}
                </span>
              </div>

              {/* Description */}
              <p className="text-xs text-cy-gray-400 leading-relaxed mb-3">{mod.desc}</p>

              {/* Roles */}
              {mod.roles.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {mod.roles.map(role => (
                    <span key={role} className="text-[10px] px-1.5 py-0.5 rounded-md bg-white/[0.04] text-cy-gray-400 border border-cy-glass-border">
                      {role}
                    </span>
                  ))}
                </div>
              )}

              {/* Expanded detail */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-cy-glass-border space-y-2">
                  {mod.workflow && (
                    <div>
                      <span className="text-[10px] text-cy-orange uppercase tracking-wider font-medium">Workflow</span>
                      <p className="text-xs text-cy-gray-300 mt-0.5">{mod.workflow}</p>
                    </div>
                  )}
                  {mod.permission && (
                    <div>
                      <span className="text-[10px] text-cy-orange uppercase tracking-wider font-medium">Required Permission</span>
                      <p className="text-xs text-cy-gray-300 mt-0.5 capitalize">{mod.permission}</p>
                    </div>
                  )}
                  {mod.demoRoute && (
                    <div>
                      <span className="text-[10px] text-cy-orange uppercase tracking-wider font-medium">Demo Path</span>
                      <p className="text-xs font-mono text-cy-gray-300 mt-0.5">{mod.demoRoute}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Expand hint */}
              <div className={`text-[10px] mt-2 transition-colors ${isExpanded ? "text-cy-orange" : "text-cy-gray-500"}`}>
                {isExpanded ? "▲ Collapse" : "▼ Workflow & permissions"}
              </div>
            </button>
          );
        })}
      </div>

      {/* Total count */}
      <p className="text-xs text-cy-gray-500 mt-4">
        Showing {filtered.length} of {modules.length} modules.{" "}
        <button onClick={() => setActiveTab("all")} className="text-cy-orange hover:text-cy-orange-light transition-colors">
          View all
        </button>
      </p>
    </div>
  );
}
