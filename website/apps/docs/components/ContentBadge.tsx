"use client";

import { type ContentType, CONTENT_TYPE_META } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ContentBadgeProps {
  type: ContentType;
  className?: string;
  size?: "sm" | "md";
}

export function ContentBadge({ type, className, size = "sm" }: ContentBadgeProps) {
  const meta = CONTENT_TYPE_META[type] ?? CONTENT_TYPE_META.guide;

  return (
    <span
      className={cn("content-badge", size === "md" && "text-xs px-2.5 py-0.5", className)}
      style={{
        color: meta.color,
        backgroundColor: meta.bg,
        borderColor: meta.border,
      }}
    >
      {meta.label}
    </span>
  );
}
