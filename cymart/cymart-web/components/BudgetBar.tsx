"use client";

import { Flame } from "lucide-react";
import type { TodayStatus } from "@/lib/types";

export function BudgetBar({ status }: { status: TodayStatus }) {
  const pct = Math.min(100, Math.max(0, (status.consumed_calories / status.daily_calories) * 100));
  const over = status.remaining_calories < 0;

  return (
    <div
      className="rounded-[14px] border p-3"
      style={{ borderColor: "var(--line)", background: "var(--panel)" }}
    >
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[13px] font-medium" style={{ color: "var(--ink-2)" }}>
          <Flame size={14} style={{ color: over ? "var(--coral)" : "var(--teal)" }} />
          Today&apos;s budget
        </div>
        <div className="text-[13px]" style={{ color: over ? "var(--coral)" : "var(--ink-2)" }}>
          {over ? (
            <>Over by {Math.abs(status.remaining_calories)} kcal</>
          ) : (
            <>{status.remaining_calories} kcal left</>
          )}
        </div>
      </div>
      <div
        className="h-2.5 w-full overflow-hidden rounded-full"
        style={{ background: "var(--panel-2)" }}
      >
        <div
          className="h-full rounded-full transition-all"
          style={{
            width: `${pct}%`,
            background: over ? "var(--coral)" : "var(--teal-2)",
          }}
        />
      </div>
      <div className="mt-1.5 flex justify-between text-[11px]" style={{ color: "var(--ink-3)" }}>
        <span>{status.consumed_calories} eaten</span>
        <span>{status.daily_calories} kcal goal</span>
      </div>
    </div>
  );
}
