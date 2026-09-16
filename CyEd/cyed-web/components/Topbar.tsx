"use client";

import { useEffect, useState } from "react";
import { Search, Bell, Sun, Moon, Command } from "lucide-react";
import { useTheme } from "@/lib/hooks";
import CommandPalette from "@/components/CommandPalette";

export default function Topbar() {
  const [theme, toggle] = useTheme();
  const [cmdkOpen, setCmdkOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdkOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <header className="topbar">
      <button className="searchbar" onClick={() => setCmdkOpen(true)} aria-label="Open command palette">
        <Search size={15} />
        <span style={{ flex: 1, textAlign: "left", fontSize: "0.82rem" }}>Search or jump to…</span>
        <span className="kbd" style={{ display: "inline-flex", alignItems: "center", gap: 3 }}>
          <Command size={10} />K
        </span>
      </button>

      <div style={{ flex: 1 }} />

      <div className="topbar-live" style={{ display: "flex", alignItems: "center", gap: 6, marginRight: 4 }}>
        <span className="live-dot" aria-hidden="true" />
        <span style={{ fontSize: 11, color: "var(--muted)" }}>Live</span>
      </div>

      <button className="icon-btn" aria-label="Notifications">
        <Bell size={16} />
        <span
          aria-hidden="true"
          style={{
            position: "absolute",
            top: 8,
            right: 9,
            width: 7,
            height: 7,
            borderRadius: 999,
            background: "var(--violet)",
            boxShadow: "0 0 8px var(--violet)",
          }}
        />
      </button>

      <button className="icon-btn" onClick={toggle} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
        {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
      </button>

      <button
        className="icon-btn"
        aria-label="Profile"
        style={{ background: "var(--grad-primary)", color: "#fff", fontWeight: 800, fontSize: 13, border: "none" }}
      >
        A
      </button>

      <CommandPalette open={cmdkOpen} onClose={() => setCmdkOpen(false)} />
    </header>
  );
}
