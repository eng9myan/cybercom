"use client";
import { useState } from "react";
import type { ModuleCategory } from "./ModuleExplorer";

export interface PermissionRole {
  role: string;
  level: "full" | "operations" | "clinical" | "finance" | "hr" | "inventory" | "limited" | "readonly";
  categories: ModuleCategory[];
  description: string;
}

const LEVEL_STYLE: Record<PermissionRole["level"], { badge: string; label: string }> = {
  full:       { badge: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", label: "Full Access" },
  operations: { badge: "text-blue-400 bg-blue-500/10 border-blue-500/20",          label: "Operations" },
  clinical:   { badge: "text-teal-400 bg-teal-500/10 border-teal-500/20",          label: "Clinical" },
  finance:    { badge: "text-sky-400 bg-sky-500/10 border-sky-500/20",             label: "Finance" },
  hr:         { badge: "text-pink-400 bg-pink-500/10 border-pink-500/20",          label: "HR" },
  inventory:  { badge: "text-orange-400 bg-orange-500/10 border-orange-500/20",    label: "Inventory" },
  limited:    { badge: "text-amber-400 bg-amber-500/10 border-amber-500/20",       label: "Limited" },
  readonly:   { badge: "text-slate-400 bg-slate-500/10 border-slate-500/20",       label: "Read Only" },
};

const CAT_LABEL: Record<ModuleCategory, string> = {
  clinical:   "Clinical",
  erp:        "ERP",
  ai:         "AI",
  operations: "Operations",
  finance:    "Finance",
  hr:         "HR",
  inventory:  "Inventory",
  reports:    "Reports",
  admin:      "Admin",
};

export function PermissionsMatrix({ roles }: { roles: PermissionRole[] }) {
  const [activeRole, setActiveRole] = useState<string | null>(null);

  const allCats = Array.from(
    new Set(roles.flatMap(r => r.categories))
  ) as ModuleCategory[];

  const selected = activeRole ? roles.find(r => r.role === activeRole) : null;

  return (
    <div>
      {/* Info banner */}
      <div className="glass-card p-4 rounded-xl border border-blue-500/15 mb-8 flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
          <span className="text-blue-400 text-sm font-bold">P</span>
        </div>
        <div>
          <p className="text-sm font-medium text-white mb-0.5">Role-Based Access Control</p>
          <p className="text-xs text-cy-gray-400 leading-relaxed">
            Each user is assigned a role by the System Admin. The role determines which modules and actions are visible.
            Admins can customize permissions per user — add or restrict access beyond the role default.
            Module visibility is enforced in real time — unauthorized routes redirect to the user&apos;s home screen.
          </p>
        </div>
      </div>

      {/* Role cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
        {roles.map(role => {
          const style = LEVEL_STYLE[role.level];
          const isSelected = activeRole === role.role;
          return (
            <button
              key={role.role}
              onClick={() => setActiveRole(isSelected ? null : role.role)}
              className={`glass-card p-5 rounded-xl text-left transition-all duration-200 w-full ${
                isSelected ? "border-cy-orange/30 bg-cy-glass-bg-hover" : "hover:border-cy-glass-bg-hover"
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-sm font-heading font-semibold text-white">{role.role}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium flex-shrink-0 ${style.badge}`}>
                  {style.label}
                </span>
              </div>
              <p className="text-xs text-cy-gray-400 mb-3 leading-relaxed">{role.description}</p>
              <div className="flex flex-wrap gap-1">
                {role.categories.map(cat => (
                  <span key={cat} className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04] text-cy-gray-400 border border-cy-glass-border">
                    {CAT_LABEL[cat]}
                  </span>
                ))}
              </div>
              <p className={`text-[10px] mt-2 ${isSelected ? "text-cy-orange" : "text-cy-gray-500"}`}>
                {isSelected ? "▲ Hide module access" : "▼ See module access"}
              </p>
            </button>
          );
        })}
      </div>

      {/* Selected role detail */}
      {selected && (
        <div className="glass-card p-6 rounded-2xl border border-cy-orange/20">
          <div className="flex items-center gap-3 mb-4">
            <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${LEVEL_STYLE[selected.level].badge}`}>
              {LEVEL_STYLE[selected.level].label}
            </span>
            <h3 className="font-heading font-semibold text-white">{selected.role}</h3>
          </div>
          <p className="text-sm text-cy-gray-400 mb-6">{selected.description}</p>

          {/* Permission matrix table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr>
                  <th className="text-left py-2 pr-4 text-cy-gray-500 font-medium">Module Category</th>
                  <th className="text-center px-3 py-2 text-cy-gray-500 font-medium">View</th>
                  <th className="text-center px-3 py-2 text-cy-gray-500 font-medium">Create</th>
                  <th className="text-center px-3 py-2 text-cy-gray-500 font-medium">Edit</th>
                  <th className="text-center px-3 py-2 text-cy-gray-500 font-medium">Delete</th>
                </tr>
              </thead>
              <tbody>
                {allCats.map(cat => {
                  const hasAccess = selected.categories.includes(cat);
                  const isFullAdmin = selected.level === "full";
                  const canWrite = hasAccess && selected.level !== "readonly";
                  const canDelete = isFullAdmin || (hasAccess && selected.level === "operations");
                  return (
                    <tr key={cat} className={`border-t border-cy-glass-border ${hasAccess ? "" : "opacity-40"}`}>
                      <td className="py-2 pr-4 font-medium text-white">{CAT_LABEL[cat]}</td>
                      <td className="text-center px-3 py-2">
                        {hasAccess ? <span className="text-emerald-400">✓</span> : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="text-center px-3 py-2">
                        {canWrite ? <span className="text-emerald-400">✓</span> : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="text-center px-3 py-2">
                        {canWrite ? <span className="text-emerald-400">✓</span> : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="text-center px-3 py-2">
                        {canDelete ? <span className="text-emerald-400">✓</span> : <span className="text-amber-400">—</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <p className="text-[10px] text-cy-gray-500 mt-4">
            Permissions above show defaults for this role. System Admins can override per-user permissions from Settings → Users & Access.
          </p>
        </div>
      )}
    </div>
  );
}
