export type ContentType =
  | "guide"
  | "reference"
  | "tutorial"
  | "release_note"
  | "faq"
  | "changelog";

export interface DocItem {
  id: string | number;
  title: string;
  slug: string;
  summary: string;
  content_type: ContentType;
  last_updated: string;
  tags?: string[];
  section?: string;
  section_slug?: string;
  url?: string;
}

export interface DocSection {
  id: string | number;
  title: string;
  slug: string;
  summary: string;
  icon?: string;
  items: DocItem[];
  total_count?: number;
}

export interface DocsHomeResponse {
  sections: DocSection[];
  featured?: DocItem[];
  total_docs?: number;
}

export interface SearchResult {
  items: DocItem[];
  total: number;
  query: string;
  suggestions?: string[];
}

export type ProductKey = "cymed" | "cycom" | "cygov" | "cyai" | "cyidentity" | "cyintegrationhub";

export interface ProductInfo {
  key: ProductKey;
  label: string;
  description: string;
  color: string;
  slug: string;
}

export const PRODUCTS: ProductInfo[] = [
  {
    key: "cymed",
    label: "CyMed",
    description: "FHIR-native healthcare & EHR platform",
    color: "#10b981",
    slug: "cymed",
  },
  {
    key: "cycom",
    label: "CyCom",
    description: "Enterprise resource planning platform",
    color: "#3b82f6",
    slug: "cycom",
  },
  {
    key: "cygov",
    label: "CyGov",
    description: "Digital government & e-services platform",
    color: "#8b5cf6",
    slug: "cygov",
  },
  {
    key: "cyai",
    label: "CyAI",
    description: "AI & machine learning services",
    color: "#ed6c00",
    slug: "cyai",
  },
  {
    key: "cyidentity",
    label: "CyIdentity",
    description: "Identity, access & security management",
    color: "#59c3e1",
    slug: "cyidentity",
  },
  {
    key: "cyintegrationhub",
    label: "CyIntegrationHub",
    description: "API gateway & integration middleware",
    color: "#f59e0b",
    slug: "cyintegrationhub",
  },
];

export const CONTENT_TYPE_META: Record<
  ContentType,
  { label: string; color: string; bg: string; border: string }
> = {
  guide: {
    label: "Guide",
    color: "#60a5fa",
    bg: "rgba(59,130,246,0.12)",
    border: "rgba(59,130,246,0.25)",
  },
  reference: {
    label: "Reference",
    color: "#a78bfa",
    bg: "rgba(139,92,246,0.12)",
    border: "rgba(139,92,246,0.25)",
  },
  tutorial: {
    label: "Tutorial",
    color: "#34d399",
    bg: "rgba(52,211,153,0.12)",
    border: "rgba(52,211,153,0.25)",
  },
  release_note: {
    label: "Release Note",
    color: "#fb923c",
    bg: "rgba(251,146,60,0.12)",
    border: "rgba(251,146,60,0.25)",
  },
  faq: {
    label: "FAQ",
    color: "#94a3b8",
    bg: "rgba(148,163,184,0.10)",
    border: "rgba(148,163,184,0.20)",
  },
  changelog: {
    label: "Changelog",
    color: "#22d3ee",
    bg: "rgba(34,211,238,0.12)",
    border: "rgba(34,211,238,0.25)",
  },
};

export const NAV_SECTIONS = [
  {
    title: "Getting Started",
    slug: "getting-started",
    items: [
      { title: "Introduction", slug: "getting-started/introduction" },
      { title: "Quick Start", slug: "getting-started/quick-start" },
      { title: "Architecture Overview", slug: "getting-started/architecture" },
      { title: "Authentication", slug: "getting-started/authentication" },
    ],
  },
  {
    title: "API Reference",
    slug: "api-reference",
    items: [
      { title: "REST API", slug: "api-reference/rest" },
      { title: "GraphQL API", slug: "api-reference/graphql" },
      { title: "WebSockets", slug: "api-reference/websockets" },
      { title: "Rate Limits", slug: "api-reference/rate-limits" },
    ],
  },
  {
    title: "CyMed",
    slug: "cymed",
    items: [
      { title: "Overview", slug: "cymed/overview" },
      { title: "Patient Management", slug: "cymed/patients" },
      { title: "Clinical Records", slug: "cymed/clinical" },
      { title: "Imaging & DICOM", slug: "cymed/imaging" },
      { title: "Pharmacy", slug: "cymed/pharmacy" },
      { title: "FHIR Integration", slug: "cymed/fhir" },
    ],
  },
  {
    title: "CyCom",
    slug: "cycom",
    items: [
      { title: "Overview", slug: "cycom/overview" },
      { title: "Finance Module", slug: "cycom/finance" },
      { title: "HR Module", slug: "cycom/hr" },
      { title: "Inventory", slug: "cycom/inventory" },
    ],
  },
  {
    title: "CyGov",
    slug: "cygov",
    items: [
      { title: "Overview", slug: "cygov/overview" },
      { title: "E-Services", slug: "cygov/eservices" },
      { title: "Citizen Portal", slug: "cygov/citizen" },
    ],
  },
  {
    title: "CyAI",
    slug: "cyai",
    items: [
      { title: "Overview", slug: "cyai/overview" },
      { title: "Models & Endpoints", slug: "cyai/models" },
      { title: "Clinical AI", slug: "cyai/clinical" },
    ],
  },
  {
    title: "CyIdentity",
    slug: "cyidentity",
    items: [
      { title: "Overview", slug: "cyidentity/overview" },
      { title: "SSO Setup", slug: "cyidentity/sso" },
      { title: "Role Management", slug: "cyidentity/roles" },
    ],
  },
  {
    title: "CyIntegrationHub",
    slug: "cyintegrationhub",
    items: [
      { title: "Overview", slug: "cyintegrationhub/overview" },
      { title: "Connectors", slug: "cyintegrationhub/connectors" },
      { title: "Webhooks", slug: "cyintegrationhub/webhooks" },
    ],
  },
  {
    title: "Release Notes",
    slug: "release-notes",
    items: [
      { title: "v2.0 — June 2026", slug: "release-notes/v2-0" },
      { title: "v1.9 — March 2026", slug: "release-notes/v1-9" },
    ],
  },
];
