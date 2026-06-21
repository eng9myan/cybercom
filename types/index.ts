/**
 * CyberCom Shared Type Definitions — used by frontend, mobile, and backend Python stubs.
 * ADR-0001 (stack), ADR-0002 (multi-tenancy), ADR-0005 (identity).
 */

// ── Tenant ──────────────────────────────────────────────────────────────────

export type TenantTier = "shared" | "schema" | "database" | "cluster";
export type TenantStatus = "pending" | "active" | "suspended" | "terminated";

export interface TenantContext {
  tenantId: string;
  slug: string;
  domain: string;
  tier: TenantTier;
  status: TenantStatus;
  locale: "ar" | "en";
  timezone: string;
  countryCode: string;
}

// ── Identity ─────────────────────────────────────────────────────────────────

export interface UserSession {
  userId: string;
  email: string;
  displayName?: string;
  realm: string;
  tenantId: string;
  roles: string[];
  permissions: string[];
  accessToken: string;
  tokenExpiresAt: number;
}

export interface ServicePrincipal {
  clientId: string;
  name: string;
  scopes: string[];
}

// ── Base Entity ───────────────────────────────────────────────────────────────

export interface BaseEntity {
  id: string;
  tenantId: string;
  createdAt: string;
  updatedAt: string;
}

export interface SoftDeletableEntity extends BaseEntity {
  isDeleted: boolean;
  deletedAt: string | null;
}

// ── API ───────────────────────────────────────────────────────────────────────

export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  code?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  page: number;
  pages: number;
  results: T[];
}

// ── Events (ADR-0004) ─────────────────────────────────────────────────────────

export interface DomainEvent<TPayload = Record<string, unknown>> {
  eventId: string;
  eventType: string;
  tenantId: string;
  occurredAt: string;
  correlationId?: string;
  causationId?: string;
  version: number;
  payload: TPayload;
  metadata: Record<string, string>;
}

// ── Audit (ADR-0028) ──────────────────────────────────────────────────────────

export type AuditAction =
  | "create" | "read" | "update" | "delete"
  | "login" | "logout"
  | "permission_denied" | "break_glass"
  | "export" | "import";

export interface AuditEntry {
  id: string;
  timestamp: string;
  tenantId: string | null;
  userId: string;
  action: AuditAction;
  resourceType: string;
  resourceId: string;
  status: "success" | "failure" | "denied";
  ipAddress: string | null;
  details: Record<string, unknown>;
}

// ── Localization ──────────────────────────────────────────────────────────────

export type Locale = "ar" | "en";
export type TextDirection = "rtl" | "ltr";

export function getDirection(locale: Locale): TextDirection {
  return locale === "ar" ? "rtl" : "ltr";
}

export function isRTL(locale: Locale): boolean {
  return locale === "ar";
}
