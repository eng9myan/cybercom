import {
  LayoutDashboard,
  Users,
  CalendarCheck,
  GraduationCap,
  Sparkles,
  ClipboardCheck,
  UserPlus,
  BookOpen,
  HeartPulse,
  Receipt,
  Wand2,
  Compass,
  Activity,
  FileText,
  Settings,
  Bus,
  CreditCard,
  MapPin,
  Upload,
  ClipboardList,
  Library,
  Banknote,
  Calculator,
  ShoppingCart,
  Package,
  FileSignature,
  Siren,
  CalendarX,
  CalendarClock,
  Megaphone,
  Stethoscope,
  UserCheck,
  Thermometer,
  Tent,
  Mail,
  HeartHandshake,
  ListChecks,
  BarChart3,
  MessageSquare,
  BookMarked,
  Syringe,
  DoorOpen,
  CalendarDays,
  FileSpreadsheet,
  ShieldCheck,
  Building2,
  Network,
  GraduationCap as Alumni,
  type LucideIcon,
} from "lucide-react";

export type NavItem = { href: string; label: string; icon: LucideIcon; keywords?: string };
export type NavGroup = { group: string; role: "Admin" | "Teacher" | "Student" | "Parent"; items: NavItem[] };

export const NAV_GROUPS: NavGroup[] = [
  {
    group: "Overview",
    role: "Admin",
    items: [
      { href: "/", label: "Dashboard", icon: LayoutDashboard, keywords: "home mission control kpi" },
      { href: "/leadership", label: "Leadership", icon: BarChart3, keywords: "principal executive analytics trend chronic absence achievement campus comparison board" },
    ],
  },
  {
    group: "Administration",
    role: "Admin",
    items: [
      { href: "/admissions", label: "Admissions", icon: UserPlus, keywords: "enrol application offer" },
      { href: "/students", label: "Students", icon: Users, keywords: "sis roster pupils" },
      { href: "/fees", label: "Fees", icon: Receipt, keywords: "invoice payment" },
      { href: "/billing", label: "Billing", icon: CreditCard, keywords: "installments plan" },
      { href: "/messages", label: "Messages", icon: MessageSquare, keywords: "parent teacher conversation reply inbox thread two-way contact family" },
      { href: "/newsletters", label: "Newsletters", icon: Mail, keywords: "bulk message broadcast community email push parents communication" },
      { href: "/visitors", label: "Visitors", icon: DoorOpen, keywords: "sign in out front desk reception badge contractor volunteer wwc kiosk" },
      { href: "/excursions", label: "Excursions", icon: Tent, keywords: "camp incursion trip consent permission slip roll medical bus" },
      { href: "/data-import", label: "Data Import", icon: Upload, keywords: "csv migration onboard" },
      { href: "/settings", label: "School Settings", icon: Settings, keywords: "branding logo config" },
    ],
  },
  {
    group: "Safety & Cover",
    role: "Admin",
    items: [
      { href: "/emergency", label: "Emergency Roll", icon: Siren, keywords: "evacuation fire drill lockdown muster assembly safe missing" },
      { href: "/sick-bay", label: "Sick Bay", icon: Thermometer, keywords: "first aid clinic nurse unwell injury sent home collected treatment" },
      { href: "/health", label: "Health Register", icon: Syringe, keywords: "immunisation vaccination air medication dose outbreak exclusion measles gaps" },
      { href: "/action-plans", label: "Action Plans", icon: Stethoscope, keywords: "anaphylaxis asthma diabetes seizure epipen medical emergency" },
      { href: "/relief", label: "Relief Teachers", icon: UserCheck, keywords: "crt casual cover substitute booking agency" },
      { href: "/interviews", label: "Interviews", icon: CalendarClock, keywords: "parent teacher booking slots round reporting" },
    ],
  },
  {
    group: "Teaching",
    role: "Teacher",
    items: [
      { href: "/timetable", label: "My Timetable", icon: CalendarDays, keywords: "my classes periods teaching load week schedule rooms" },
      { href: "/attendance", label: "Attendance", icon: CalendarCheck, keywords: "roll call present absent" },
      { href: "/absences", label: "Absence Notes", icon: CalendarX, keywords: "explanation parent excuse sick absent review queue" },
      { href: "/notices", label: "Daily Notices", icon: Megaphone, keywords: "announcement bulletin board assembly" },
      { href: "/gradebook", label: "Gradebook", icon: GraduationCap, keywords: "grades marks assessment" },
      { href: "/rubrics", label: "Rubric Marking", icon: ListChecks, keywords: "criteria levels descriptor standard moderation derived score achievement" },
      { href: "/reports", label: "Report Cards", icon: FileText, keywords: "report pdf publish" },
      { href: "/lms", label: "Learning", icon: BookOpen, keywords: "lms course lessons" },
      { href: "/assessment", label: "Assessment", icon: ClipboardList, keywords: "assignment submission quiz marking homework" },
      { href: "/curriculum", label: "Curriculum", icon: Library, keywords: "acara australian curriculum outcomes v9 capabilities" },
      { href: "/library", label: "Library", icon: BookMarked, keywords: "borrow loan return overdue fine book catalogue circulation issue renew" },
      { href: "/teacher-tools", label: "Teacher Tools", icon: Wand2, keywords: "ai lesson rubric differentiator" },
      { href: "/review", label: "Review Queue", icon: ClipboardCheck, keywords: "hitl approve integrity" },
    ],
  },
  {
    group: "Wellbeing & AI",
    role: "Student",
    items: [
      { href: "/wellbeing", label: "Wellbeing", icon: HeartPulse, keywords: "pastoral learner profile" },
      { href: "/support-plans", label: "Support Plans", icon: HeartHandshake, keywords: "iep ilp nccd adjustment disability learning support review goal consultation" },
      { href: "/at-risk", label: "At-Risk", icon: Activity, keywords: "early warning analytics" },
      { href: "/tutor", label: "AI Tutor", icon: Sparkles, keywords: "ask curriculum grounded" },
      { href: "/study", label: "Study Buddy", icon: Compass, keywords: "socratic guided" },
    ],
  },
  {
    group: "Back Office (ERP)",
    role: "Admin",
    items: [
      { href: "/erp/hr", label: "HR", icon: Users, keywords: "staff contracts leave performance review onboarding offboarding" },
      { href: "/erp/staff-attendance", label: "Staff Attendance", icon: CalendarCheck, keywords: "check in out timesheet lateness" },
      { href: "/erp/payroll", label: "Payroll", icon: Banknote, keywords: "payslip salary payg super pay run allowance deduction" },
      { href: "/erp/finance", label: "Accounting", icon: Calculator, keywords: "ledger journal budget bank reconciliation profit loss balance sheet" },
      { href: "/erp/procurement", label: "Procurement", icon: ShoppingCart, keywords: "purchase request approval order supplier goods receipt" },
      { href: "/erp/inventory", label: "Inventory", icon: Package, keywords: "stock assets low stock reorder register" },
      { href: "/erp/documents", label: "Document Sign", icon: FileSignature, keywords: "esign signature contract consent permission slip audit" },
    ],
  },
  {
    group: "Group & Compliance",
    role: "Admin",
    items: [
      { href: "/campuses", label: "Campuses", icon: Building2, keywords: "group multi site rollup consolidated state totals unassigned" },
      { href: "/alumni", label: "Leavers & Alumni", icon: Alumni, keywords: "exit withdraw graduate transfer certificate former student destination" },
      { href: "/compliance", label: "Statutory Returns", icon: FileSpreadsheet, keywords: "nccd naplan census attendance return export csv government portal lodge" },
      { href: "/security", label: "Security (MFA)", icon: ShieldCheck, keywords: "mfa totp two factor authenticator backup codes coverage audit trail" },
      { href: "/interoperability", label: "Interoperability", icon: Network, keywords: "sif au refid zone objects xml json mapping certification gaps" },
    ],
  },
  {
    group: "Transport",
    role: "Parent",
    items: [
      { href: "/transport", label: "Transport", icon: Bus, keywords: "bus route zone subscription" },
      { href: "/bus-tracking", label: "Bus Tracking", icon: MapPin, keywords: "gps live map eta" },
    ],
  },
];

export const ALL_NAV: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);

/** Role → accent CSS var, for role-based theming of the active state. */
export const ROLE_ACCENT: Record<NavGroup["role"], { role: string; role2: string }> = {
  Admin: { role: "var(--blue)", role2: "var(--cyan)" },
  Teacher: { role: "var(--violet)", role2: "#d946ef" },
  Student: { role: "var(--cyan)", role2: "var(--blue)" },
  Parent: { role: "#34d399", role2: "var(--cyan)" },
};

/** Primary items surfaced in the mobile bottom nav. */
export const BOTTOM_NAV: NavItem[] = [
  ALL_NAV.find((n) => n.href === "/")!,
  ALL_NAV.find((n) => n.href === "/students")!,
  ALL_NAV.find((n) => n.href === "/attendance")!,
  ALL_NAV.find((n) => n.href === "/tutor")!,
  ALL_NAV.find((n) => n.href === "/settings")!,
];
