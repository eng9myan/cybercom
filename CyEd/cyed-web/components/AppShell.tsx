"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";
import BottomNav from "@/components/BottomNav";
import RouteTransition from "@/components/RouteTransition";
import PortalShell from "@/components/PortalShell";

/**
 * Picks the chrome for the current route.
 *
 * Families and students get their own shell rather than the staff one. Done
 * here, by pathname, instead of by restructuring every existing route into a
 * layout group — the alternative moved twenty-nine working pages to change
 * which navigation renders around them.
 */
const PORTAL_PREFIXES = ["/portal", "/student"];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "/";
  const isPortal = PORTAL_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );

  if (isPortal) {
    return <PortalShell>{children}</PortalShell>;
  }

  return (
    <>
      <div className="app-shell">
        <Sidebar />
        <div className="app-col">
          <Topbar />
          <main id="main" tabIndex={-1} className="app-main">
            <RouteTransition>{children}</RouteTransition>
          </main>
        </div>
      </div>
      <BottomNav />
    </>
  );
}
