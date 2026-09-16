"use client";

import React from "react";

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-end justify-between mb-6 anim-fade-up">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">{title}</h1>
        {subtitle && (
          <p style={{ color: "var(--muted)" }} className="text-sm mt-1">
            {subtitle}
          </p>
        )}
      </div>
      {action}
    </div>
  );
}

/** Skeleton-shimmer loading (not a spinner). */
export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div>
      <span className="sr-only">{label}</span>
      <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))" }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="card p-5">
            <div className="skeleton" style={{ height: 12, width: "50%" }} />
            <div className="skeleton" style={{ height: 30, width: "70%", marginTop: 14 }} />
            <div className="skeleton" style={{ height: 10, width: "40%", marginTop: 12 }} />
          </div>
        ))}
      </div>
    </div>
  );
}

export function SkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="card p-4 space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton" style={{ height: 16, width: `${90 - i * 6}%` }} />
      ))}
    </div>
  );
}

export function ErrorNote({ error }: { error: string }) {
  return (
    <div
      className="card p-4 text-sm anim-fade-up"
      style={{ borderColor: "color-mix(in srgb, var(--bad) 45%, transparent)", color: "var(--bad)" }}
      role="alert"
    >
      {error}
    </div>
  );
}

export function Empty({ label, cta }: { label: string; cta?: React.ReactNode }) {
  return (
    <div className="card p-8 text-center anim-fade-up">
      <div
        aria-hidden="true"
        style={{
          width: 56,
          height: 56,
          margin: "0 auto 12px",
          borderRadius: 16,
          background: "var(--grad-primary)",
          opacity: 0.85,
          filter: "blur(0.2px)",
          boxShadow: "var(--glow-violet)",
        }}
      />
      <div className="text-sm" style={{ color: "var(--muted)" }}>
        {label}
      </div>
      {cta && <div className="mt-4">{cta}</div>}
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="label">{label}</label>
      {children}
    </div>
  );
}
