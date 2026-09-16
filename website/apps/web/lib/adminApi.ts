import { tokenStore } from "./auth/tokens";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

async function authedFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = tokenStore.getAccessToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
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
};
