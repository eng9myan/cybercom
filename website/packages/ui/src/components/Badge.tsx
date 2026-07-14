import { type HTMLAttributes } from "react";

type BadgeVariant = "default" | "orange" | "cyan" | "green" | "red" | "amber" | "violet";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const BADGE_VARIANTS: Record<BadgeVariant, string> = {
  default: "text-[#94a3b8] border-white/10 bg-white/5",
  orange: "text-[#ED6C00] border-[#ED6C00]/20 bg-[#ED6C00]/5",
  cyan: "text-[#59c3e1] border-[#59c3e1]/20 bg-[#59c3e1]/5",
  green: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
  red: "text-red-400 border-red-500/20 bg-red-500/5",
  amber: "text-amber-400 border-amber-500/20 bg-amber-500/5",
  violet: "text-violet-400 border-violet-500/20 bg-violet-500/5",
};

export function Badge({ variant = "default", className = "", children, ...props }: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
        BADGE_VARIANTS[variant],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </span>
  );
}
