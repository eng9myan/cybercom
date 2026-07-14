import { apiClient } from "./client";
import type { ApiResponse } from "./client";

export interface CustomerPortalAccess {
  id: string;
  user_id: string;
  access_level: "viewer" | "standard" | "admin";
  can_manage_licenses: boolean;
  can_manage_billing: boolean;
  can_open_tickets: boolean;
  can_download_software: boolean;
  is_active: boolean;
  last_login_at?: string | null;
}

export interface SupportTicket {
  id: string;
  ticket_number: string;
  submitted_by_id: string;
  subject: string;
  description: string;
  product_code: string;
  priority: "low" | "medium" | "high" | "critical";
  status: "open" | "in_progress" | "waiting_customer" | "resolved" | "closed";
  assigned_to_id?: string | null;
  resolution_notes?: string;
  resolved_at?: string | null;
  sla_due_at?: string | null;
  attachments: string[];
}

export interface WhiteLabelConfig {
  id: string;
  tenant_name: string;
  display_name: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  logo_url: string;
  favicon_url: string;
  custom_domain: string;
  login_page_bg_url: string;
  email_from_name: string;
  email_from_address: string;
  support_email: string;
  support_phone: string;
  is_active: boolean;
}

export interface CommercialMetricsSnapshot {
  id: string;
  snapshot_date: string;
  metric_type: string;
  product_code: string;
  value: number;
  breakdown: Record<string, unknown>;
}

export const portalApi = {
  getCustomerAccess: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<CustomerPortalAccess>>("/commercial-readiness/portal-access/", params, false),

  getSupportTickets: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<SupportTicket>>("/commercial-readiness/support-tickets/", params, false),

  getSupportTicket: (id: string) =>
    apiClient.get<SupportTicket>(`/commercial-readiness/support-tickets/${id}/`, undefined, false),

  createSupportTicket: (body: Partial<SupportTicket>) =>
    apiClient.post<SupportTicket>("/commercial-readiness/support-tickets/", body, false),

  assignSupportTicket: (id: string, assignedToId: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/support-tickets/${id}/assign/`, { assigned_to_id: assignedToId }, false),

  resolveSupportTicket: (id: string, resolutionNotes: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/support-tickets/${id}/resolve/`, { resolution_notes: resolutionNotes }, false),

  closeSupportTicket: (id: string) =>
    apiClient.post<{ status: string }>(`/commercial-readiness/support-tickets/${id}/close/`, {}, false),

  getWhiteLabelConfigs: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<WhiteLabelConfig>>("/commercial-readiness/white-label-configs/", params, false),

  getMetricsSnapshots: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<CommercialMetricsSnapshot>>("/commercial-readiness/metrics-snapshots/", params, false),
};
