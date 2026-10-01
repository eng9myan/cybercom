"use client";

import { AlertTriangle, CheckCircle2, ListChecks, Search, ShieldAlert, ShoppingCart } from "lucide-react";
import type { AgentToolCall } from "@/lib/types";
import { Badge } from "./ui";

/** Renders a compact receipt card for one tool the agent called, instead
 * of dumping raw JSON — this is the "shield decided" / "added to cart"
 * moment the product is built around. */
export function ToolReceipt({ call }: { call: AgentToolCall }) {
  const out = call.output;

  if (call.name === "add_to_cart") {
    const blocked = out.blocked === true;
    return (
      <div
        className="flex items-start gap-2.5 rounded-[12px] border p-3"
        style={{
          borderColor: "var(--line)",
          background: blocked ? "var(--coral-bg)" : "var(--teal-bg)",
        }}
      >
        {blocked ? (
          <ShieldAlert size={16} style={{ color: "var(--coral)" }} className="mt-0.5 shrink-0" />
        ) : (
          <ShoppingCart size={16} style={{ color: "var(--teal)" }} className="mt-0.5 shrink-0" />
        )}
        <div className="text-[13.5px]" style={{ color: blocked ? "var(--coral)" : "var(--teal)" }}>
          {blocked ? (
            <>Diet Shield blocked this: {String(out.reason ?? "doesn't fit your plan")}</>
          ) : (
            <>Added to your cart.</>
          )}
        </div>
      </div>
    );
  }

  if (call.name === "evaluate_items") {
    const overall = String(out.overall ?? "");
    const tone = overall === "ALLOW" ? "teal" : overall.includes("BLOCK") ? "coral" : "amber";
    return (
      <div
        className="flex items-center gap-2.5 rounded-[12px] border p-3"
        style={{ borderColor: "var(--line)", background: "var(--panel)" }}
      >
        <CheckCircle2 size={16} style={{ color: "var(--ink-3)" }} className="shrink-0" />
        <div className="flex items-center gap-2 text-[13.5px]" style={{ color: "var(--ink-2)" }}>
          Diet check: <Badge tone={tone as "teal" | "coral" | "amber"}>{overall}</Badge>
        </div>
      </div>
    );
  }

  if (call.name === "search_catalog") {
    const results = Array.isArray(out.results) ? out.results : [];
    return (
      <div
        className="rounded-[12px] border p-3"
        style={{ borderColor: "var(--line)", background: "var(--panel)" }}
      >
        <div className="mb-1.5 flex items-center gap-1.5 text-[13px] font-medium" style={{ color: "var(--ink-2)" }}>
          <Search size={14} /> Found {results.length} item{results.length === 1 ? "" : "s"}
        </div>
        <div className="flex flex-col gap-1">
          {(results as Array<Record<string, unknown>>).slice(0, 4).map((r, i) => (
            <div key={i} className="flex items-center justify-between text-[13px]" style={{ color: "var(--ink)" }}>
              <span>{String(r.name)}</span>
              <span style={{ color: "var(--ink-3)" }}>{String(r.calories)} kcal</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (call.name === "checkout") {
    const success = out.success === true;
    return (
      <div
        className="flex items-center gap-2.5 rounded-[12px] border p-3"
        style={{ borderColor: "var(--line)", background: success ? "var(--teal-bg)" : "var(--coral-bg)" }}
      >
        {success ? (
          <CheckCircle2 size={16} style={{ color: "var(--teal)" }} />
        ) : (
          <AlertTriangle size={16} style={{ color: "var(--coral)" }} />
        )}
        <span className="text-[13.5px]" style={{ color: success ? "var(--teal)" : "var(--coral)" }}>
          {success ? `Order placed — #${String(out.order_id).slice(0, 8)}` : String(out.reason ?? "Checkout failed")}
        </span>
      </div>
    );
  }

  if (call.name === "diet_plan_status") {
    if (out.has_plan === false) {
      return (
        <div className="rounded-[12px] border p-3 text-[13.5px]" style={{ borderColor: "var(--line)", color: "var(--ink-2)" }}>
          No diet plan set up yet.
        </div>
      );
    }
    return (
      <div className="rounded-[12px] border p-3 text-[13.5px]" style={{ borderColor: "var(--line)", color: "var(--ink)" }}>
        {String(out.remaining_calories)} kcal left of {String(out.daily_calories)} today.
      </div>
    );
  }

  if (call.name === "replenish_basket") {
    const items = Array.isArray(out.items) ? out.items : [];
    return (
      <div
        className="rounded-[12px] border p-3"
        style={{ borderColor: "var(--line)", background: "var(--violet-bg)" }}
      >
        <div className="flex items-center gap-1.5 text-[13.5px] font-medium" style={{ color: "var(--violet)" }}>
          <ListChecks size={14} />
          {items.length ? `${items.length} item(s) running low` : "Nothing running low"}
        </div>
      </div>
    );
  }

  // Generic fallback for any tool without a bespoke card.
  return (
    <div
      className="rounded-[12px] border p-3 text-[12.5px]"
      style={{ borderColor: "var(--line)", color: "var(--ink-3)", fontFamily: "var(--font-mono)" }}
    >
      {call.name}(): {JSON.stringify(out).slice(0, 140)}
    </div>
  );
}
