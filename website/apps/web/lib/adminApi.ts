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

async function authedFetch<T>(path: string): Promise<T> {
  const token = tokenStore.getAccessToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new Error(`${path} → ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

interface Paginated<T> {
  count: number;
  results: T[];
}

export const adminApi = {
  async listTenants(): Promise<Tenant[]> {
    const data = await authedFetch<Paginated<Tenant> | Tenant[]>("/api/v1/tenants/");
    return Array.isArray(data) ? data : data.results;
  },
  async listSubscriptions(): Promise<TenantSubscription[]> {
    const data = await authedFetch<Paginated<TenantSubscription> | TenantSubscription[]>(
      "/api/v1/tenants/subscriptions/",
    );
    return Array.isArray(data) ? data : data.results;
  },
};
