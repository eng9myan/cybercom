// English message catalog. Keep keys stable; ar.ts mirrors this shape
// exactly (a vitest test enforces key parity). Namespaced by surface.

const en = {
  common: {
    loading: "Loading…",
    retry: "Retry",
    logout: "Log out",
    language: "Language",
    refresh: "Refresh",
  },
  nav: {
    overview: "Overview",
    patients: "My Patients",
    schedule: "Schedule",
  },
  auth: {
    signInTitle: "Sign in to see this",
    signInDetail: "Your dashboard loads here once you sign in with your provider account.",
    signIn: "Sign in",
    continueAsDemo: "Continue as Dr. Demo",
    emailLabel: "Email",
    passwordLabel: "Password",
    loginFailed: "Sign-in failed",
  },
  overview: {
    title: "Provider Overview",
    subtitle: "Today at a glance",
    todaysAppointments: "Today's Appointments",
    activePatients: "Active Patients",
    pendingResults: "Pending Results",
    telemedicineQueue: "Telemedicine Queue",
    criticalAlerts: "Critical Alerts",
    noAlerts: "No active alerts.",
    acknowledge: "Acknowledge",
    acknowledged: "Acknowledged",
    noProviderLinkedTitle: "No provider profile linked",
    noProviderLinkedDetail: "This account isn't linked to a provider record — contact an administrator.",
    onCall: "On call",
    offCall: "Off call",
    npi: "NPI",
    loadFailed: "Couldn't load the dashboard",
  },
} as const;

export default en;

type Widen<T> = { [K in keyof T]: T[K] extends string ? string : Widen<T[K]> };
export type Messages = Widen<typeof en>;
