"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { PanelLeftClose, PanelLeftOpen, SlidersHorizontal } from "lucide-react";
import { ROLE_ACCENT } from "@/lib/nav";
import { usePrefs, useVisibleNav } from "@/lib/prefs";
import WorkspaceSettings from "@/components/WorkspaceSettings";

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [customising, setCustomising] = useState(false);
  const { prefs } = usePrefs();
  const groups = useVisibleNav(prefs);

  return (
    <>
      <nav aria-label="Primary" className={`cyed-sidebar ${collapsed ? "collapsed" : ""}`}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.4rem 0.5rem 0.6rem" }}>
          {!collapsed && (
            <div className="anim-fade-in">
              <div style={{ fontSize: "1.15rem", fontWeight: 900, letterSpacing: "-0.02em" }}>
                Cy<span className="grad-text">Ed</span>
              </div>
              <div className="label" style={{ marginTop: 1 }}>
                School OS
              </div>
            </div>
          )}
          <button
            className="icon-btn"
            style={{ width: 32, height: 32 }}
            onClick={() => setCollapsed((c) => !c)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
          >
            {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          </button>
        </div>

        {groups.map((grp) => {
          const accent = ROLE_ACCENT[grp.role];
          return (
            <div key={grp.group} style={{ ["--role" as string]: accent.role, ["--role-2" as string]: accent.role2 }}>
              {!collapsed && <div className="nav-group-label">{grp.group}</div>}
              {grp.items.map(({ href, label, icon: Icon }) => {
                const active = pathname === href;
                return (
                  <Link
                    key={href}
                    href={href}
                    aria-current={active ? "page" : undefined}
                    className={`nav-item ${active ? "active" : ""}`}
                    title={collapsed ? label : undefined}
                  >
                    <span className="nav-ico">
                      <Icon size={17} aria-hidden="true" />
                    </span>
                    <span className="nav-label">{label}</span>
                  </Link>
                );
              })}
            </div>
          );
        })}

        <div style={{ marginTop: "auto", paddingTop: 8 }}>
          <button
            className="nav-item"
            onClick={() => setCustomising(true)}
            style={{ width: "100%", cursor: "pointer", background: "transparent" }}
            title="Customise which modules you see"
          >
            <span className="nav-ico">
              <SlidersHorizontal size={17} aria-hidden="true" />
            </span>
            <span className="nav-label">Customise</span>
          </button>
          {!collapsed && (
            <div className="nav-group-label" style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span className="live-dot" /> AU · ACARA-aligned
            </div>
          )}
        </div>
      </nav>

      <WorkspaceSettings open={customising} onClose={() => setCustomising(false)} />
    </>
  );
}
