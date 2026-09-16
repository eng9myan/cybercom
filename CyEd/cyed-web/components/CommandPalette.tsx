"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ALL_NAV } from "@/lib/nav";
import { CornerDownLeft } from "lucide-react";

export default function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return ALL_NAV;
    return ALL_NAV.filter(
      (n) => n.label.toLowerCase().includes(q) || (n.keywords ?? "").includes(q) || n.href.includes(q)
    );
  }, [query]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      setTimeout(() => inputRef.current?.focus(), 20);
    }
  }, [open]);

  useEffect(() => {
    setActive(0);
  }, [query]);

  if (!open) return null;

  const go = (href: string) => {
    onClose();
    router.push(href);
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(results.length - 1, a + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(0, a - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results[active]) go(results[active].href);
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <div className="cmdk-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Command palette">
      <div className="cmdk" onClick={(e) => e.stopPropagation()} onKeyDown={onKey}>
        <input
          ref={inputRef}
          className="cmdk-input"
          placeholder="Jump to… (type a page, e.g. attendance, fees, tutor)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search pages"
        />
        <div style={{ maxHeight: "48vh", overflowY: "auto", padding: "0.35rem 0" }}>
          {results.length === 0 && (
            <div className="cmdk-item" aria-disabled>
              No matches
            </div>
          )}
          {results.map((n, i) => {
            const Icon = n.icon;
            return (
              <div
                key={n.href}
                className={`cmdk-item ${i === active ? "active" : ""}`}
                onMouseEnter={() => setActive(i)}
                onClick={() => go(n.href)}
                role="button"
                tabIndex={-1}
              >
                <Icon size={16} aria-hidden="true" />
                <span style={{ flex: 1 }}>{n.label}</span>
                <span style={{ fontSize: 11, color: "var(--faint)" }}>{n.href}</span>
                {i === active && <CornerDownLeft size={13} aria-hidden="true" />}
              </div>
            );
          })}
        </div>
        <div
          style={{
            display: "flex",
            gap: 12,
            padding: "0.55rem 1.1rem",
            borderTop: "1px solid var(--border)",
            fontSize: 11,
            color: "var(--faint)",
          }}
        >
          <span>
            <span className="kbd">↑↓</span> navigate
          </span>
          <span>
            <span className="kbd">↵</span> open
          </span>
          <span>
            <span className="kbd">esc</span> close
          </span>
        </div>
      </div>
    </div>
  );
}
