import { apiClient } from "./client";
import type { ApiResponse } from "./client";

export interface PartnerProfile {
  id: string;
  name: string;
  partner_type: "implementation" | "reseller" | "technology" | "consulting" | "oem";
  tier: "authorized" | "silver" | "gold" | "platinum";
  status: "pending" | "active" | "suspended" | "terminated";
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
  country: string;
  region: string;
  website?: string;
  logo_url?: string;
  description?: string;
  specializations: string[];
  languages: string[];
  partner_since?: string | null;
  annual_revenue_target?: number | null;
  currency: string;
}

export interface PartnerOpportunity {
  id: string;
  partner: string;
  name: string;
  stage: "prospecting" | "qualification" | "proposal" | "negotiation" | "closed_won" | "closed_lost";
  status: "active" | "inactive";
  customer_name: string;
  customer_country: string;
  products_of_interest: string[];
  estimated_value: number;
  currency: string;
  expected_close_date?: string | null;
  notes?: string;
}

export interface RevenueShare {
  id: string;
  partner: string;
  period_start: string;
  period_end: string;
  gross_revenue: number;
  share_percentage: number;
  share_amount: number;
  currency: string;
  status: "pending" | "approved" | "paid";
  paid_at?: string | null;
}

export interface PartnerAsset {
  id: string;
  title: string;
  asset_type: "brochure" | "presentation" | "video" | "case_study" | "whitepaper" | "logo" | "training" | "contract_template";
  product_codes: string[];
  tier_access: string[];
  language: string;
  file_url: string;
  version: string;
  published_at: string;
}

export interface DealRegistration {
  id: string;
  partner: string;
  opportunity?: string | null;
  customer_name: string;
  customer_country: string;
  products_interested: string[];
  estimated_value: number;
  currency: string;
  status: "submitted" | "approved" | "rejected" | "expired" | "converted";
  submitted_at: string;
  reviewed_at?: string | null;
  expiry_date?: string | null;
  notes?: string;
}

export const partnerApi = {
  getPartners: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<PartnerProfile>>("/partner-ecosystem/partners/", params, false),

  getPartner: (id: string) =>
    apiClient.get<PartnerProfile>(`/partner-ecosystem/partners/${id}/`, undefined, false),

  getOpportunities: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<PartnerOpportunity>>("/partner-ecosystem/opportunities/", params, false),

  createOpportunity: (body: Partial<PartnerOpportunity>) =>
    apiClient.post<PartnerOpportunity>("/partner-ecosystem/opportunities/", body, false),

  getRevenueShares: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<RevenueShare>>("/partner-ecosystem/revenue-shares/", params, false),

  getAssets: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<PartnerAsset>>("/partner-ecosystem/assets/", params, false),

  getAsset: (id: string) =>
    apiClient.get<PartnerAsset>(`/partner-ecosystem/assets/${id}/`, undefined, false),

  getDealRegistrations: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<DealRegistration>>("/partner-ecosystem/deal-registrations/", params, false),

  registerDeal: (body: Partial<DealRegistration>) =>
    apiClient.post<DealRegistration>("/partner-ecosystem/deal-registrations/", body, false),

  applyForPartnership: (body: { company_name: string; partner_type: string; contact_email: string; contact_name: string; country: string; website?: string; message?: string }) =>
    apiClient.post<{ status: string; reference: string }>("/partner-ecosystem/applications/", body, true),
};
