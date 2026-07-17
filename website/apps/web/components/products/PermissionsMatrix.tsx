"use client";
import { useState } from "react";
import { useTranslations } from "next-intl";
import type { ModuleCategory } from "./ModuleExplorer";

export interface PermissionRole {
  role: string;
  level: "full" | "operations" | "clinical" | "finance" | "hr" | "inventory" | "limited" | "readonly";
  categories: ModuleCategory[];
  description: string;
}

const LEVEL_STYLE: Record<PermissionRole["level"], { badge: string }> = {
  full:       { badge: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  operations: { badge: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
  clinical:   { badge: "text-teal-400 bg-teal-500/10 border-teal-500/20" },
  finance:    { badge: "text-sky-400 bg-sky-500/10 border-sky-500/20" },
  hr:         { badge: "text-pink-400 bg-pink-500/10 border-pink-500/20" },
  inventory:  { badge: "text-orange-400 bg-orange-500/10 border-orange-500/20" },
  limited:    { badge: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
  readonly:   { badge: "text-slate-400 bg-slate-500/10 border-slate-500/20" },
};

export function PermissionsMatrix({ roles }: { roles: PermissionRole[] }) {
  const t = useTranslations("productDetailPage.permissionsMatrix");
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
          <p className="text-sm font-medium text-white mb-0.5">{t("bannerTitle")}</p>
          <p className="text-xs text-cy-gray-400 leading-relaxed">
            {t("bannerDesc")}
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
                  {t(`levels.${role.level}`)}
                </span>
              </div>
              <p className="text-xs text-cy-gray-400 mb-3 leading-relaxed">{role.description}</p>
              <div className="flex flex-wrap gap-1">
                {role.categories.map(cat => (
                  <span key={cat} className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04] text-cy-gray-400 border border-cy-glass-border">
                    {t(`categories.${cat}`)}
                  </span>
                ))}
              </div>
              <p className={`text-[10px] mt-2 ${isSelected ? "text-cy-orange" : "text-cy-gray-500"}`}>
                {isSelected ? t("hideAccess") : t("seeAccess")}
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
              {t(`levels.${selected.level}`)}
            </span>
            <h3 className="font-heading font-semibold text-white">{selected.role}</h3>
          </div>
          <p className="text-sm text-cy-gray-400 mb-6">{selected.description}</p>

          {/* Permission matrix table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr>
                  <th className="text-left py-2 pr-4 text-cy-gray-500 font-medium">{t("moduleCategory")}</th>
                  <th className="text-center px-3 py-2 text-cy-gray-500 font-medium">{t("view")}</th>
                  <th className="text-center px-3 py-2 text-cy-gray-500 font-medium">{t("create")}</th>
                  <th className="text-center px-3 py-2 text-cy-gray-500 font-medium">{t("edit")}</th>
                  <th className="text-center px-3 py-2 text-cy-gray-500 font-medium">{t("delete")}</th>
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
                      <td className="py-2 pr-4 font-medium text-white">{t(`categories.${cat}`)}</td>
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
            {t("footnote")}
          </p>
        </div>
      )}
    </div>
  );
}
