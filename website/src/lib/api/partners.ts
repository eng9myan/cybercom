/**
 * CyberCom Partner API
 * Manages partner listings and partner program applications.
 */

import { apiClient, type PaginatedResponse, type PaginationParams } from "./client.js";
import { config } from "../config.js";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface Partner {
  id: string;
  name: string;
  slug: string;
  logo_url: string;
  website_url: string;
  partner_type: "technology" | "implementation" | "reseller" | "strategic" | "referral";
  tier: "platinum" | "gold" | "silver" | "bronze";
  description: string;
  specializations: string[];
  regions: string[];
  products: string[];
  is_featured: boolean;
  is_active: boolean;
}

export interface PartnerApplication {
  company_name: string;
  company_website: string;
  contact_first_name: string;
  contact_last_name: string;
  contact_email: string;
  contact_phone?: string;
  contact_title?: string;
  partner_type: Partner["partner_type"];
  regions: string[];
  products_of_interest: string[];
  annual_revenue_range?: string;
  company_size?: string;
  message?: string;
}

export interface PartnerApplicationResponse {
  id: string;
  status: "pending" | "under_review" | "approved" | "rejected";
  reference_number: string;
  submitted_at: string;
  message: string;
}

export interface PartnerListParams extends PaginationParams {
  partner_type?: Partner["partner_type"];
  tier?: Partner["tier"];
  region?: string;
  product?: string;
  is_featured?: boolean;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

export async function listPartners(
  params: PartnerListParams = {}
): Promise<PaginatedResponse<Partner>> {
  const url = apiClient.withParams(config.endpoints.partners, params as Record<string, string | number | boolean | undefined>);
  return apiClient.get<PaginatedResponse<Partner>>(url, { skipAuth: true });
}

export async function getFeaturedPartners(): Promise<Partner[]> {
  const url = apiClient.withParams(config.endpoints.partners, { is_featured: true, is_active: true });
  const response = await apiClient.get<PaginatedResponse<Partner>>(url, { skipAuth: true });
  return response.results;
}

export async function submitPartnerApplication(
  application: PartnerApplication
): Promise<PartnerApplicationResponse> {
  return apiClient.post<PartnerApplicationResponse>(
    `${config.endpoints.partners}apply/`,
    application,
    { skipAuth: true }
  );
}

export const partnersApi = {
  list: listPartners,
  featured: getFeaturedPartners,
  apply: submitPartnerApplication,
};
