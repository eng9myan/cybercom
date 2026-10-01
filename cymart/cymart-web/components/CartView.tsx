"use client";

import Link from "next/link";
import { CheckCircle2, Loader2, ShoppingBag } from "lucide-react";
import { useActiveCart, useCheckout } from "@/lib/queries";
import { Button, Card, Spinner } from "./ui";

export function CartView() {
  const { data: cart, isLoading } = useActiveCart();
  const checkout = useCheckout();

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner size={24} />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 py-16 text-center">
        <span
          className="flex h-12 w-12 items-center justify-center rounded-full"
          style={{ background: "var(--panel-2)", color: "var(--ink-3)" }}
        >
          <ShoppingBag size={20} />
        </span>
        <div>
          <p className="text-[15px] font-medium">Your cart is empty</p>
          <p className="mt-1 text-[13.5px]" style={{ color: "var(--ink-2)" }}>
            Ask CyMart to order something — nothing to browse here.
          </p>
        </div>
        <Link href="/">
          <Button variant="primary">Go order</Button>
        </Link>
      </div>
    );
  }

  const total = cart.items.reduce(
    (sum, i) => sum + Number(i.quantity) * Number(i.unit_price) - Number(i.item_discount || 0),
    0,
  );

  if (checkout.isSuccess) {
    return (
      <Card className="flex flex-col items-center gap-3 py-10 text-center">
        <CheckCircle2 size={28} style={{ color: "var(--teal)" }} />
        <div>
          <p className="text-[16px] font-medium">Order placed</p>
          <p className="mt-1 text-[13.5px]" style={{ color: "var(--ink-2)" }}>
            #{checkout.data.order_id.slice(0, 8)} — status: {checkout.data.status}
          </p>
        </div>
        <Link href={`/orders/${checkout.data.order_id}`}>
          <Button variant="primary">Track it</Button>
        </Link>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-[20px]">Your cart</h1>
      <Card className="flex flex-col divide-y" style={{ borderColor: "var(--line)" }}>
        {cart.items.map((item) => (
          <div key={item.id} className="flex items-center justify-between py-2.5 first:pt-0 last:pb-0" style={{ borderColor: "var(--line)" }}>
            <div>
              <p className="text-[14px]">{item.product_name_snapshot || item.product_id.slice(0, 8)}</p>
              <p className="text-[12.5px]" style={{ color: "var(--ink-3)" }}>
                {item.quantity} × {Number(item.unit_price).toFixed(2)} JD
              </p>
            </div>
            <p className="text-[14px] font-medium">
              {(Number(item.quantity) * Number(item.unit_price)).toFixed(2)} JD
            </p>
          </div>
        ))}
      </Card>

      <Card className="flex items-center justify-between">
        <span className="text-[14px]" style={{ color: "var(--ink-2)" }}>
          Total
        </span>
        <span className="text-[18px] font-semibold" style={{ fontFamily: "var(--font-display)" }}>
          {total.toFixed(2)} JD
        </span>
      </Card>

      {checkout.isError && (
        <p className="text-[13px]" style={{ color: "var(--coral)" }}>
          Couldn&apos;t check out — try again.
        </p>
      )}

      <Button
        variant="primary"
        className="justify-center py-3"
        disabled={checkout.isPending}
        onClick={() => checkout.mutate(cart.id)}
      >
        {checkout.isPending ? <Loader2 size={16} className="animate-spin" /> : "Checkout"}
      </Button>
    </div>
  );
}
