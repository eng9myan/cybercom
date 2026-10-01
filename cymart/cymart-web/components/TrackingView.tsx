"use client";

import { Check, Package, Truck } from "lucide-react";
import { useOrderTracking } from "@/lib/queries";
import { Card, Spinner } from "./ui";

const STEP_ORDER = ["assigned", "picked_up", "delivered"];
const STEP_LABEL: Record<string, string> = {
  assigned: "Driver assigned",
  picked_up: "Picked up",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

export function TrackingView({ orderId }: { orderId: string }) {
  const { data, isLoading } = useOrderTracking(orderId);

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner size={24} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-2 py-16 text-center">
        <Package size={22} style={{ color: "var(--ink-3)" }} />
        <p className="text-[14px]" style={{ color: "var(--ink-2)" }}>
          No driver assigned to this order yet.
        </p>
      </div>
    );
  }

  const currentIndex = STEP_ORDER.indexOf(data.status);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-[20px]">Order tracking</h1>
        <p className="text-[13.5px]" style={{ color: "var(--ink-2)" }}>
          Driver: {data.driver_name}
        </p>
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          {STEP_ORDER.map((step, i) => {
            const done = currentIndex >= i;
            return (
              <div key={step} className="flex flex-1 flex-col items-center gap-1.5">
                <div className="flex w-full items-center">
                  {i > 0 && (
                    <div
                      className="h-[2px] flex-1"
                      style={{ background: currentIndex >= i ? "var(--teal)" : "var(--line)" }}
                    />
                  )}
                  <span
                    className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
                    style={{
                      background: done ? "var(--teal)" : "var(--panel-2)",
                      color: done ? "var(--ground)" : "var(--ink-3)",
                    }}
                  >
                    {done ? <Check size={14} /> : <Truck size={13} />}
                  </span>
                  {i < STEP_ORDER.length - 1 && (
                    <div
                      className="h-[2px] flex-1"
                      style={{ background: currentIndex > i ? "var(--teal)" : "var(--line)" }}
                    />
                  )}
                </div>
                <span className="text-center text-[11px]" style={{ color: done ? "var(--teal)" : "var(--ink-3)" }}>
                  {STEP_LABEL[step]}
                </span>
              </div>
            );
          })}
        </div>
      </Card>

      <Card className="flex flex-col gap-2.5">
        <span className="text-[13px] font-medium" style={{ color: "var(--ink-2)" }}>
          Timeline
        </span>
        {data.timeline.map((e, i) => (
          <div key={i} className="flex items-start gap-2.5 text-[13.5px]">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: "var(--teal)" }} />
            <div>
              <span className="font-medium">{STEP_LABEL[e.status] ?? e.status}</span>
              {e.note && <span style={{ color: "var(--ink-2)" }}> — {e.note}</span>}
              <div className="text-[11.5px]" style={{ color: "var(--ink-3)" }}>
                {new Date(e.occurred_at).toLocaleString()}
              </div>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
