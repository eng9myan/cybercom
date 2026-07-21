/**
 * CyID ecosystem, Phase 9 — mobile client for Cymed's core.orders API
 * (see products/cymed/core/orders/views.py). Powers the Healthcare and
 * e-Rx screens.
 *
 * Real, honest scope limit: this is tenant-scoped (requires X-Tenant-ID,
 * same as the real backend endpoint), not a cross-tenant "all my orders
 * everywhere" view — PersonIdentity has no link to a clinical Patient
 * record yet (same gap flagged in products/cymed/core/commerce/checkout.py),
 * so there is no real way to resolve "every order this person has across
 * every tenant" today. The screen built on this client shows orders at
 * one active tenant at a time.
 */
import { API_CONFIG } from "./config";
import { apiRequest } from "./client";

// Cymed's DRF views use the default PageNumberPagination
// ({count, next, previous, results}) — NOT cymart's cursor-pagination
// envelope ({data, pagination}). Different backend, different shape;
// using PaginatedResponse here would silently mismatch the real response.
export interface DjangoPageResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CymedOrder {
  id: string;
  patient: string;
  order_type: "laboratory" | "imaging" | "medication" | "procedure" | "referral";
  priority: "routine" | "urgent" | "stat";
  status: "proposed" | "draft" | "active" | "completed" | "cancelled";
  ordered_by: string;
  ordered_at: string;
  fulfilling_tenant_id: string | null;
}

function cymed<T>(path: string, options: Parameters<typeof apiRequest>[2] = {}): Promise<T> {
  return apiRequest<T>(API_CONFIG.cyIdentityBaseUrl, path, options);
}

export const cymedApi = {
  listOrders(
    accessToken: string,
    tenantId: string,
    filters: { order_type?: CymedOrder["order_type"]; status?: CymedOrder["status"] } = {}
  ): Promise<DjangoPageResponse<CymedOrder>> {
    return cymed("/orders/", { accessToken, tenantId, query: filters });
  },
};
