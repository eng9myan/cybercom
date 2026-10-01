"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChefHat, MessageCircle, Salad, ShoppingCart, Truck } from "lucide-react";
import clsx from "clsx";

const LINKS = [
  { href: "/", label: "Order", icon: MessageCircle },
  { href: "/onboarding", label: "Diet plan", icon: Salad },
  { href: "/cart", label: "Cart", icon: ShoppingCart },
  { href: "/orders", label: "Track", icon: Truck },
];

export function TopNav() {
  const pathname = usePathname();
  return (
    <header
      className="sticky top-0 z-20 border-b backdrop-blur"
      style={{ borderColor: "var(--line)", background: "color-mix(in srgb, var(--ground) 88%, transparent)" }}
    >
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-[10px]"
            style={{ background: "var(--teal-bg)", color: "var(--teal)" }}
          >
            <ChefHat size={18} />
          </span>
          <span className="text-[17px] font-semibold" style={{ fontFamily: "var(--font-display)" }}>
            CyMart
          </span>
        </Link>
        <nav className="flex items-center gap-1">
          {LINKS.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-1.5 rounded-[10px] px-2.5 py-1.5 text-sm font-medium transition",
                )}
                style={{
                  color: active ? "var(--teal)" : "var(--ink-2)",
                  background: active ? "var(--teal-bg)" : "transparent",
                }}
              >
                <Icon size={16} />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
