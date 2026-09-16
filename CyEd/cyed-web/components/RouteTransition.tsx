"use client";

import { usePathname } from "next/navigation";

/** Fade+slide the main content on each route change (transform/opacity only). */
export default function RouteTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div key={pathname} className="anim-fade-up">
      {children}
    </div>
  );
}
