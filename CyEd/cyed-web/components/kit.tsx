"use client";

import React from "react";

/** Glass section panel with a title row + optional action. */
export function Panel({
  title,
  action,
  children,
  className = "",
  pad = true,
}: {
  title?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  pad?: boolean;
}) {
  return (
    <section className={`card card-hover ${pad ? "p-5" : ""} ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between" style={{ marginBottom: pad ? 14 : 0, padding: pad ? 0 : "1rem 1.1rem 0" }}>
          {typeof title === "string" ? <div className="label">{title}</div> : title}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

const STATUS_MAP: Record<string, "ok" | "warn" | "bad" | "info"> = {
  paid: "ok", settled: "ok", active: "ok", enrolled: "ok", approved: "ok", published: "ok",
  present: "ok", completed: "ok", accepted: "ok", current: "ok", delivered: "ok",
  partial: "warn", pending: "warn", requested: "warn", draft: "warn", applicant: "warn",
  overdue: "bad", unpaid: "bad", absent: "bad", rejected: "bad", cancelled: "bad", withdrawn: "bad",
  pending_review: "warn", flagged: "bad", distress: "bad",
};

export function Badge({ value }: { value: string }) {
  const kind = STATUS_MAP[(value || "").toLowerCase()] ?? "info";
  const cls = kind === "ok" ? "status-ok" : kind === "warn" ? "status-warn" : kind === "bad" ? "status-bad" : "";
  const label = (value || "—").replace(/_/g, " ");
  if (kind === "info") return <span className="pill" style={{ textTransform: "capitalize" }}>{label}</span>;
  return <span className={`status ${cls}`} style={{ textTransform: "capitalize" }}>{label}</span>;
}

/** Segmented control / tabs. */
export function Segmented<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div
      role="tablist"
      style={{
        display: "inline-flex",
        gap: 4,
        padding: 4,
        borderRadius: 999,
        background: "var(--panel-2)",
        border: "1px solid var(--border)",
      }}
    >
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(o.value)}
            className="btn"
            style={{
              padding: "0.35rem 0.85rem",
              borderRadius: 999,
              background: active ? "var(--grad-cyan)" : "transparent",
              color: active ? "#04121a" : "var(--muted)",
              boxShadow: active ? "0 4px 14px -6px rgba(34,211,238,0.6)" : "none",
            }}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

/** Centered glass modal. */
export function Modal({
  open,
  onClose,
  title,
  children,
  width = 520,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  width?: number;
}) {
  if (!open) return null;
  return (
    <div className="cmdk-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label={title}>
      <div
        className="card"
        style={{ width: `min(${width}px, 92vw)`, padding: "1.4rem", animation: "fade-up 0.22s cubic-bezier(0.22,1,0.36,1) both" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">{title}</h2>
          <button className="icon-btn" style={{ width: 30, height: 30 }} onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

/** Colored icon chip used in headers/cards. */
export function IconBadge({ children, color = "var(--cyan)" }: { children: React.ReactNode; color?: string }) {
  return (
    <div
      style={{
        display: "grid",
        placeItems: "center",
        width: 38,
        height: 38,
        borderRadius: 12,
        color,
        background: `color-mix(in srgb, ${color} 15%, transparent)`,
        border: `1px solid color-mix(in srgb, ${color} 30%, transparent)`,
        flexShrink: 0,
      }}
    >
      {children}
    </div>
  );
}
