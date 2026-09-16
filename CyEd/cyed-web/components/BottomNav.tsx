"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import { useBottomNav, usePrefs } from "@/lib/prefs";
import WorkspaceSettings from "@/components/WorkspaceSettings";

/**
 * Mobile bottom bar. Shows the user's pinned modules, capped at five per
 * Material guidance, plus a customiser so the set can be changed on the phone
 * where the sidebar is not available.
 */
export default function BottomNav() {
  const pathname = usePathname();
  const { prefs } = usePrefs();
  const items = useBottomNav(prefs);
  const [customising, setCustomising] = useState(false);

  return (
    <>
      <nav className="bottom-nav" aria-label="Primary mobile">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href} className={active ? "active" : ""} aria-current={active ? "page" : undefined}>
              <Icon size={19} aria-hidden="true" />
              {label}
            </Link>
          );
        })}
        <button onClick={() => setCustomising(true)} aria-label="Customise workspace">
          <SlidersHorizontal size={19} aria-hidden="true" />
          More
        </button>
      </nav>
      <WorkspaceSettings open={customising} onClose={() => setCustomising(false)} />
    </>
  );
}
