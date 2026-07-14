import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock IntersectionObserver (not in JSDOM) — must be a real constructor, not arrow fn
class MockIntersectionObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  constructor(_cb: IntersectionObserverCallback, _opts?: IntersectionObserverInit) {}
}
vi.stubGlobal("IntersectionObserver", MockIntersectionObserver);

// Mock next-intl
const translations: Record<string, string> = {
  "form.fullName": "Full Name",
  "form.email": "Work Email",
  "form.jobTitle": "Job Title",
  "form.company": "Company Name",
  "form.country": "Country",
  "form.companySize": "Company Size",
  "form.phone": "Phone",
  "form.productInterests": "Product Interests",
  "form.message": "Message",
  "form.gdprConsent": "I agree to the privacy policy",
  "form.submitting": "Submitting",
  "form.submit": "Request Demo",
  "form.success": "Request received",
  "form.reference": "Reference number",
};

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => translations[key] ?? key,
  useLocale: () => "en",
}));

// Mock framer-motion to avoid animation issues in tests
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: React.HTMLProps<HTMLDivElement>) => <div {...props}>{children}</div>,
    h1: ({ children, ...props }: React.HTMLProps<HTMLHeadingElement>) => <h1 {...props}>{children}</h1>,
    h2: ({ children, ...props }: React.HTMLProps<HTMLHeadingElement>) => <h2 {...props}>{children}</h2>,
    p: ({ children, ...props }: React.HTMLProps<HTMLParagraphElement>) => <p {...props}>{children}</p>,
    span: ({ children, ...props }: React.HTMLProps<HTMLSpanElement>) => <span {...props}>{children}</span>,
    section: ({ children, ...props }: React.HTMLProps<HTMLElement>) => <section {...props}>{children}</section>,
    ul: ({ children, ...props }: React.HTMLProps<HTMLUListElement>) => <ul {...props}>{children}</ul>,
    li: ({ children, ...props }: React.HTMLProps<HTMLLIElement>) => <li {...props}>{children}</li>,
    form: ({ children, ...props }: React.HTMLProps<HTMLFormElement>) => <form {...props}>{children}</form>,
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useReducedMotion: () => false,
  useScroll: () => ({ scrollY: { get: () => 0 } }),
  useTransform: (_v: unknown, _i: unknown, o: unknown[]) => o[0],
  useInView: () => true,
}));

// Mock @cybercom/api
vi.mock("@cybercom/api", () => ({
  demoApi: {
    submit: vi.fn().mockResolvedValue({ id: "1", reference_number: "CYB-123456", status: "pending", created_at: new Date().toISOString() }),
  },
  contactApi: {
    send: vi.fn().mockResolvedValue({ id: "1", ticket_number: "TKT-001", status: "open", created_at: new Date().toISOString() }),
    subscribeNewsletter: vi.fn().mockResolvedValue({ id: "1", status: "subscribed", created_at: new Date().toISOString() }),
  },
  productsApi: {
    list: vi.fn().mockResolvedValue({ data: [], count: 0 }),
    featured: vi.fn().mockResolvedValue({ data: [], count: 0 }),
  },
}));
