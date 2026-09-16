"use client";

import { useCountUp } from "@/lib/hooks";
import { Sparkline } from "@/components/viz";

export function StatCard({
  label,
  value,
  hint,
  icon,
  spark,
  accent = "cyan",
  suffix = "",
  prefix = "",
  prefixDollar = false,
  decimals = 0,
}: {
  label: string;
  value: number;
  hint?: string;
  icon?: React.ReactNode;
  spark?: number[];
  accent?: "cyan" | "violet" | "blue";
  suffix?: string;
  prefix?: string;
  prefixDollar?: boolean;
  decimals?: number;
}) {
  const animated = useCountUp(value);
  const pfx = prefixDollar ? "$" : prefix;
  const shown = decimals ? animated.toFixed(decimals) : Math.round(animated).toLocaleString();
  const color = accent === "violet" ? "var(--violet)" : accent === "blue" ? "var(--blue)" : "var(--cyan)";

  return (
    <div className="card card-hover p-5" style={{ overflow: "hidden" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div className="label">{label}</div>
        {icon && (
          <div
            style={{
              display: "grid",
              placeItems: "center",
              width: 34,
              height: 34,
              borderRadius: 10,
              color,
              background: `color-mix(in srgb, ${color} 15%, transparent)`,
              border: `1px solid color-mix(in srgb, ${color} 30%, transparent)`,
            }}
          >
            {icon}
          </div>
        )}
      </div>
      <div style={{ fontSize: "2rem", fontWeight: 800, marginTop: 8, lineHeight: 1.05 }}>
        {pfx && <span style={{ fontSize: "1.2rem", color: "var(--muted)", marginRight: 1 }}>{pfx}</span>}
        {shown}
        {suffix && <span style={{ fontSize: "1rem", color: "var(--muted)", marginLeft: 2 }}>{suffix}</span>}
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginTop: 6, gap: 8 }}>
        {hint && <div style={{ fontSize: 11, color: "var(--muted)" }}>{hint}</div>}
        {spark && spark.length > 1 && <Sparkline data={spark} color={color} width={90} height={28} />}
      </div>
    </div>
  );
}
