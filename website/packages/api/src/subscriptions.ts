const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.cy-com.com";

export type SubscriptionTier = "starter" | "professional" | "enterprise";

export interface SubscriptionRegisterPayload {
  product_code: string;
  tier: SubscriptionTier;
  email: string;
  org_name?: string;
  locale?: "en" | "ar";
}

export interface SubscriptionRegisterResponse {
  tenant_slug: string;
  product_code: string;
  tier: SubscriptionTier;
  invoice_number: string;
  amount: string;
  currency: string;
  // "bank_transfer" is the only real path today — "card_placeholder" is a
  // provider-agnostic field with no gateway wired yet (standing decision:
  // real Stripe/card integration is separate, later work).
  payment_method: "bank_transfer" | "card_placeholder";
  due_date: string;
  status: "pending_approval";
  username: string | null;
  password: string | null;
}

export interface SubscriptionRegisterError {
  detail: string;
  contact_required?: boolean;
}

export class SubscriptionApiError extends Error {
  constructor(
    public status: number,
    public body: SubscriptionRegisterError,
  ) {
    super(body.detail);
  }
}

export const subscriptionApi = {
  // Same bypass-the-shared-apiClient rationale as demo-provision.ts — the
  // DRF error shape ({detail, contact_required}) doesn't match apiClient's
  // generic {errors: {...}} convention.
  async register(payload: SubscriptionRegisterPayload): Promise<SubscriptionRegisterResponse> {
    const baseUrl = DEFAULT_BASE_URL.replace(/\/$/, "");
    const res = await fetch(`${baseUrl}/api/v1/public/subscriptions/register/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await res.json().catch(() => ({}) as SubscriptionRegisterError);
    if (!res.ok) {
      throw new SubscriptionApiError(res.status, body as SubscriptionRegisterError);
    }
    return body as SubscriptionRegisterResponse;
  },
};

// Unified tier catalog — mirrors platform/tenant/services.py's
// SUBSCRIPTION_TIER_CATALOG exactly. Backend stays the source of truth for
// what's actually billed; this is only for rendering price cards before a
// user has picked a tier (no API round-trip needed for static pricing copy).
export const SUBSCRIPTION_TIERS: Record<
  SubscriptionTier,
  { displayName: string; monthlyPriceUsd: number }
> = {
  starter: { displayName: "Basic", monthlyPriceUsd: 49 },
  professional: { displayName: "Pro", monthlyPriceUsd: 149 },
  enterprise: { displayName: "Enterprise", monthlyPriceUsd: 399 },
};
