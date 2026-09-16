"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CalendarCheck,
  CalendarClock,
  CalendarDays,
  CalendarX,
  ClipboardList,
  FileText,
  GraduationCap,
  Home,
  MessageSquare,
  Receipt,
} from "lucide-react";

/**
 * Chrome for the family- and student-facing portal.
 *
 * Deliberately not the staff shell. A parent must never see Procurement,
 * Payroll or the student register in a sidebar — not because the API would
 * let them through (it would not), but because showing a family the school's
 * back office is alarming and makes every real link harder to find.
 */

const PARENT_NAV = [
  { href: "/portal", label: "Home", icon: Home },
  { href: "/portal/attendance", label: "Attendance", icon: CalendarDays },
  { href: "/portal/absences", label: "Absences", icon: CalendarX },
  { href: "/portal/interviews", label: "Interviews", icon: CalendarClock },
  { href: "/portal/reports", label: "Reports", icon: FileText },
  { href: "/portal/fees", label: "Fees", icon: Receipt },
  { href: "/portal/messages", label: "Messages", icon: MessageSquare },
];

const STUDENT_NAV = [
  { href: "/student", label: "Today", icon: Home },
  { href: "/student/assignments", label: "Assignments", icon: ClipboardList },
  { href: "/student/results", label: "Results", icon: GraduationCap },
  { href: "/student/attendance", label: "Attendance", icon: CalendarCheck },
  { href: "/student/reports", label: "Reports", icon: FileText },
  { href: "/portal/messages", label: "Messages", icon: MessageSquare },
];

export default function PortalShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isStudent = pathname.startsWith("/student");
  const nav = isStudent ? STUDENT_NAV : PARENT_NAV;

  return (
    <div className="portal-shell">
      <header className="portal-topbar">
        <Link href={isStudent ? "/student" : "/portal"} className="portal-brand">
          Cy<span className="grad-text">Ed</span>
          <span className="portal-brand-sub">{isStudent ? "Student" : "Family"}</span>
        </Link>
        <nav aria-label="Portal" className="portal-nav">
          {nav.map((item) => {
            const active =
              item.href === pathname ||
              (item.href !== "/portal" && item.href !== "/student" && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`portal-nav-link ${active ? "is-active" : ""}`}
              >
                <Icon size={16} aria-hidden />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </header>

      <main id="main" tabIndex={-1} className="portal-main">
        {children}
      </main>
    </div>
  );
}
