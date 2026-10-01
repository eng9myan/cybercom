"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PackageSearch, RefreshCw } from "lucide-react";
import { useReplenishBasket } from "@/lib/queries";
import { Button, Card, Spinner } from "@/components/ui";

export default function OrdersLandingPage() {
  const router = useRouter();
  const [orderId, setOrderId] = useState("");
  const { data: replenish, isLoading } = useReplenishBasket(true);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-[20px]">Track an order</h1>
        <p className="text-[13.5px]" style={{ color: "var(--ink-2)" }}>
          Paste an order id to see live status.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (orderId.trim()) router.push(`/orders/${orderId.trim()}`);
        }}
        className="flex gap-2"
      >
        <input
          value={orderId}
          onChange={(e) => setOrderId(e.target.value)}
          placeholder="Order id"
          className="flex-1 rounded-[10px] border px-3 py-2 text-[14px] outline-none"
          style={{ borderColor: "var(--line)", background: "var(--panel)" }}
        />
        <Button type="submit" variant="primary">
          <PackageSearch size={16} />
          Track
        </Button>
      </form>

      <div>
        <div className="mb-2 flex items-center gap-1.5 text-[13px] font-medium" style={{ color: "var(--ink-2)" }}>
          <RefreshCw size={13} /> Running low
        </div>
        {isLoading ? (
          <Spinner size={18} />
        ) : !replenish || replenish.length === 0 ? (
          <p className="text-[13.5px]" style={{ color: "var(--ink-3)" }}>
            Nothing predicted low yet — CyMart learns as you order groceries.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {replenish.map((item) => (
              <Card key={item.product_id} className="flex items-center justify-between py-2.5">
                <span className="text-[14px]">{item.product_name || item.product_id.slice(0, 8)}</span>
                <span className="text-[12.5px]" style={{ color: "var(--ink-3)" }}>
                  {item.quantity} {item.unit}
                </span>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
