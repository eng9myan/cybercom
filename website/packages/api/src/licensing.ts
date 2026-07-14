import { apiClient } from "./client";
import type { ApiResponse } from "./client";

export interface License {
  id: string;
  license_type: string;
  license_scope: string;
  status: string;
  product_code: string;
  edition: string;
  license_key: string;
  issued_to: string;
  issued_to_email: string;
  max_users?: number | null;
  max_concurrent?: number | null;
  max_facilities?: number | null;
  licensed_features: string[];
  licensed_modules: string[];
  valid_from: string;
  valid_until?: string | null;
  grace_period_days: number;
  offline_token?: string;
  offline_valid_days: number;
  activated_at?: string | null;
  last_checked_at?: string | null;
  auto_renew: boolean;
  notes?: string;
}

export interface Subscription {
  id: string;
  license: string;
  plan?: string | null;
  status: string;
  billing_cycle: string;
  amount: number;
  currency: string;
  current_period_start: string;
  current_period_end: string;
  trial_end?: string | null;
  canceled_at?: string | null;
  cancel_at_period_end: boolean;
  external_subscription_id?: string;
  payment_method_last4?: string;
  billing_email?: string;
}

export const licensingApi = {
  getLicenses: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<License>>("/commercial-readiness/licenses/", params, false),

  getLicense: (id: string) =>
    apiClient.get<License>(`/commercial-readiness/licenses/${id}/`, undefined, false),

  activateLicense: (id: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/licenses/${id}/activate/`, {}, false),

  deactivateLicense: (id: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/licenses/${id}/deactivate/`, {}, false),

  renewLicense: (id: string) =>
    apiClient.post<{ status: string; valid_until: string }>(`/commercial-readiness/licenses/${id}/renew/`, {}, false),

  suspendLicense: (id: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/licenses/${id}/suspend/`, {}, false),

  generateOfflineToken: (id: string) =>
    apiClient.post<{ offline_token: string; valid_days: number }>(
      `/commercial-readiness/licenses/${id}/generate_offline_token/`,
      {},
      false
    ),

  getSubscriptions: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<Subscription>>("/commercial-readiness/subscriptions/", params, false),

  getSubscription: (id: string) =>
    apiClient.get<Subscription>(`/commercial-readiness/subscriptions/${id}/`, undefined, false),

  cancelSubscription: (id: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/subscriptions/${id}/cancel/`, {}, false),

  resumeSubscription: (id: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/subscriptions/${id}/resume/`, {}, false),

  checkinConcurrentSession: (sessionId: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/concurrent-sessions/${sessionId}/checkin/`, {}, false),

  checkoutConcurrentSession: (sessionId: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/concurrent-sessions/${sessionId}/checkout/`, {}, false),
};
