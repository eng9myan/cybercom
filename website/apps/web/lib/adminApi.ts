import { tokenStore } from "./auth/tokens";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// CyMed is its own Django service/deployment, separate from the platform API
// above — the same platform_admin bearer token is valid against both (shared
// Keycloak realm across every CyberCom product).
const CYMED_API_BASE_URL = process.env.NEXT_PUBLIC_CYMED_API_URL || "http://localhost:8095";

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  display_name: string;
  tenant_type: string;
  tier: string;
  status: string;
  country_code: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

export interface TenantSubscription {
  id: string;
  tenant: string;
  plan: string;
  is_active: boolean;
  is_trial: boolean;
  is_expired: boolean;
  trial_ends_at: string | null;
  ends_at: string | null;
  started_at: string;
  monthly_price_usd: string;
  annual_price_usd: string;
  currency: string;
  auto_renew: boolean;
}

export interface TenantSubscriptionInvoice {
  id: string;
  subscription: string;
  tenant_slug: string;
  tenant_name: string;
  invoice_number: string;
  amount: string;
  currency: string;
  payment_method: string;
  status: "pending" | "paid" | "void";
  provider: string;
  provider_ref: string;
  due_date: string;
  paid_at: string | null;
  approved_by: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

async function authedFetch<T>(path: string, init?: RequestInit, baseUrl = API_BASE_URL): Promise<T> {
  const token = tokenStore.getAccessToken();
  const res = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || `${path} → ${res.status} ${res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function cymedFetch<T>(path: string, init?: RequestInit): Promise<T> {
  return authedFetch<T>(path, init, CYMED_API_BASE_URL);
}

export interface CymedProduct {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
}

export interface CymedEdition {
  id: string;
  product: string;
  code: string;
  name: string;
  tier: string;
  is_active: boolean;
}

export interface CymedTenantProductSubscription {
  id: string;
  tenant_id: string;
  product: string;
  product_code: string;
  edition: string;
  edition_code: string;
  is_active: boolean;
  started_at: string;
  ends_at: string | null;
}

interface Paginated<T> {
  count: number;
  results: T[];
}

function unwrap<T>(data: Paginated<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.results;
}

export const adminApi = {
  async listTenants(): Promise<Tenant[]> {
    return unwrap(await authedFetch<Paginated<Tenant> | Tenant[]>("/api/v1/tenants/"));
  },
  async listSubscriptions(): Promise<TenantSubscription[]> {
    return unwrap(
      await authedFetch<Paginated<TenantSubscription> | TenantSubscription[]>(
        "/api/v1/tenants/subscriptions/",
      ),
    );
  },
  async listInvoices(): Promise<TenantSubscriptionInvoice[]> {
    return unwrap(
      await authedFetch<Paginated<TenantSubscriptionInvoice> | TenantSubscriptionInvoice[]>(
        "/api/v1/tenants/subscription-invoices/",
      ),
    );
  },
  async markInvoicePaid(id: string): Promise<TenantSubscriptionInvoice> {
    return authedFetch<TenantSubscriptionInvoice>(
      `/api/v1/tenants/subscription-invoices/${id}/mark-paid/`,
      { method: "POST" },
    );
  },
  async suspendTenant(id: string, reason: string): Promise<Tenant> {
    return authedFetch<Tenant>(`/api/v1/tenants/${id}/suspend/`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  },
  async activateTenant(id: string): Promise<Tenant> {
    return authedFetch<Tenant>(`/api/v1/tenants/${id}/activate/`, { method: "POST" });
  },

  async listCymedProducts(): Promise<CymedProduct[]> {
    return unwrap(
      await cymedFetch<Paginated<CymedProduct> | CymedProduct[]>(
        "/api/v1/commercial/editions/products/",
      ),
    );
  },
  async listCymedEditions(): Promise<CymedEdition[]> {
    return unwrap(
      await cymedFetch<Paginated<CymedEdition> | CymedEdition[]>(
        "/api/v1/commercial/editions/editions/",
      ),
    );
  },
  async listCymedTenantSubscriptions(): Promise<CymedTenantProductSubscription[]> {
    return unwrap(
      await cymedFetch<Paginated<CymedTenantProductSubscription> | CymedTenantProductSubscription[]>(
        "/api/v1/commercial/editions/tenant-subscriptions/",
      ),
    );
  },
  async grantCymedProduct(
    tenantId: string,
    productCode: string,
    editionCode: string,
  ): Promise<CymedTenantProductSubscription> {
    return cymedFetch<CymedTenantProductSubscription>(
      "/api/v1/commercial/editions/tenant-subscriptions/grant/",
      {
        method: "POST",
        body: JSON.stringify({ tenant_id: tenantId, product_code: productCode, edition_code: editionCode }),
      },
    );
  },
  async revokeCymedProduct(subscriptionId: string): Promise<void> {
    return cymedFetch<void>(`/api/v1/commercial/editions/tenant-subscriptions/${subscriptionId}/`, {
      method: "DELETE",
    });
  },
};
