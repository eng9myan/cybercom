"use client";

import { useEffect, useState } from "react";
import { useReducedMotion } from "@/lib/hooks";

/** Radial progress ring (0–100). Fills smoothly on mount. */
export function RadialRing({
  value,
  size = 120,
  stroke = 10,
  label,
  sublabel,
  gradient = "cyan",
}: {
  value: number;
  size?: number;
  stroke?: number;
  label?: string;
  sublabel?: string;
  gradient?: "cyan" | "violet";
}) {
  const reduced = useReducedMotion();
  // The arc sweeps in from empty; the number never does. `shown` drives only
  // the stroke, because requestAnimationFrame is throttled to nothing in a
  // background or unpainted tab — and a ring that reads "0%" next to "23 of 25
  // sessions attended" is worse than one that does not animate at all.
  const [shown, setShown] = useState(reduced ? value : 0);
  useEffect(() => {
    if (reduced) return setShown(value);
    const frame = requestAnimationFrame(() => setShown(value));
    const settle = setTimeout(() => setShown(value), 150);
    return () => {
      cancelAnimationFrame(frame);
      clearTimeout(settle);
    };
  }, [value, reduced]);

  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const off = c * (1 - Math.max(0, Math.min(100, shown)) / 100);
  const gid = `ring-${gradient}`;
  const stops =
    gradient === "violet"
      ? ["#8b5cf6", "#d946ef"]
      : ["#3b82f6", "#22d3ee"];

  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} role="img" aria-label={label ? `${label}: ${Math.round(value)}%` : undefined}>
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={stops[0]} />
            <stop offset="100%" stopColor={stops[1]} />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={`url(#${gid})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={off}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: reduced ? "none" : "stroke-dashoffset 1.1s cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "grid",
          placeItems: "center",
          textAlign: "center",
        }}
      >
        <div>
          <div style={{ fontSize: size * 0.22, fontWeight: 800 }}>{Math.round(value)}%</div>
          {sublabel && <div style={{ fontSize: 10, color: "var(--muted)" }}>{sublabel}</div>}
        </div>
      </div>
    </div>
  );
}

/** Inline sparkline from a series of numbers. */
export function Sparkline({
  data,
  width = 120,
  height = 34,
  color = "var(--cyan)",
}: {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
}) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const step = width / (data.length - 1);
  const pts = data.map((d, i) => [i * step, height - ((d - min) / span) * (height - 4) - 2]);
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;
  return (
    <svg width={width} height={height} aria-hidden="true">
      <defs>
        <linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#spark-fill)" />
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="spark-draw"
      />
      <style>{`.spark-draw{stroke-dasharray:${width * 2};stroke-dashoffset:${width * 2};animation:spark 1s ease forwards}@keyframes spark{to{stroke-dashoffset:0}}@media(prefers-reduced-motion:reduce){.spark-draw{animation:none;stroke-dashoffset:0}}`}</style>
    </svg>
  );
}

/** Small vertical bar chart that grows in. */
export function MiniBars({ data, height = 60, labels }: { data: number[]; height?: number; labels?: string[] }) {
  const max = Math.max(...data, 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height }}>
      {data.map((d, i) => (
        <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
          <div
            title={labels?.[i]}
            style={{
              width: "100%",
              height: `${(d / max) * (height - 16)}px`,
              background: "var(--grad-cyan)",
              borderRadius: 5,
              transformOrigin: "bottom",
              animation: `barGrow 0.7s cubic-bezier(0.22,1,0.36,1) ${i * 0.05}s both`,
              boxShadow: "0 0 12px -4px rgba(34,211,238,0.6)",
            }}
          />
          {labels?.[i] && <span style={{ fontSize: 9, color: "var(--faint)" }}>{labels[i]}</span>}
        </div>
      ))}
      <style>{`@keyframes barGrow{from{transform:scaleY(0);opacity:0}to{transform:scaleY(1);opacity:1}}@media(prefers-reduced-motion:reduce){[style*=barGrow]{animation:none!important;transform:none!important}}`}</style>
    </div>
  );
}

/** Attendance-style heatmap grid (weeks × days), intensity 0–1. */
export function Heatmap({
  weeks = 12,
  days = 5,
  seedLabel = "attendance",
}: {
  weeks?: number;
  days?: number;
  seedLabel?: string;
}) {
  // Deterministic pseudo-random so SSR/CSR match (no hydration mismatch).
  const cell = (w: number, d: number) => {
    const x = Math.sin((w + 1) * 12.9898 + (d + 1) * 78.233) * 43758.5453;
    return x - Math.floor(x);
  };
  const dayNames = ["M", "T", "W", "T", "F", "S", "S"];
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${weeks}, 1fr)`, gap: 4 }}>
        {Array.from({ length: weeks * days }).map((_, idx) => {
          const w = idx % weeks;
          const d = Math.floor(idx / weeks);
          const v = 0.45 + cell(w, d) * 0.55; // bias toward high attendance
          return (
            <div
              key={idx}
              title={`${seedLabel} ${Math.round(v * 100)}%`}
              style={{
                aspectRatio: "1",
                borderRadius: 4,
                background: `color-mix(in srgb, var(--cyan) ${Math.round(v * 100)}%, var(--panel-2))`,
                opacity: 0,
                animation: `fade-in 0.5s ease ${idx * 0.006}s forwards`,
              }}
            />
          );
        })}
      </div>
      <div style={{ display: "flex", gap: 4, marginTop: 6 }}>
        {Array.from({ length: days }).map((_, i) => (
          <span key={i} style={{ flex: 1, textAlign: "center", fontSize: 9, color: "var(--faint)" }}>
            {dayNames[i]}
          </span>
        ))}
      </div>
    </div>
  );
}
