"use client";

import { type ButtonHTMLAttributes, type HTMLAttributes } from "react";
import clsx from "clsx";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx(
        "rounded-[18px] border p-4",
        className,
      )}
      style={{ background: "var(--panel)", borderColor: "var(--line)" }}
      {...props}
    />
  );
}

export function Button({
  className,
  variant = "secondary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" }) {
  const styles: Record<string, React.CSSProperties> = {
    primary: { background: "var(--ink)", color: "var(--ground)", borderColor: "var(--ink)" },
    secondary: { background: "var(--panel)", color: "var(--ink)", borderColor: "var(--line-2)" },
    ghost: { background: "transparent", color: "var(--ink-2)", borderColor: "transparent" },
  };
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-[10px] border px-4 py-2 text-sm font-medium transition active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed hover:brightness-95",
        className,
      )}
      style={styles[variant]}
      {...props}
    />
  );
}

export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "teal" | "violet" | "coral" | "amber";
  children: React.ReactNode;
}) {
  const tones: Record<string, React.CSSProperties> = {
    neutral: { background: "var(--panel-2)", color: "var(--ink-2)" },
    teal: { background: "var(--teal-bg)", color: "var(--teal)" },
    violet: { background: "var(--violet-bg)", color: "var(--violet)" },
    coral: { background: "var(--coral-bg)", color: "var(--coral)" },
    amber: { background: "var(--amber-bg)", color: "var(--amber)" },
  };
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={tones[tone]}
    >
      {children}
    </span>
  );
}

export function Spinner({ size = 16 }: { size?: number }) {
  return (
    <span
      className="inline-block animate-spin rounded-full border-2 border-current border-t-transparent"
      style={{ width: size, height: size, color: "var(--ink-3)" }}
    />
  );
}
