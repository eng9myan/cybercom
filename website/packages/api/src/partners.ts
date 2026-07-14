import { apiClient, type ApiResponse } from "./client";

export type PartnerType = "implementation" | "reseller" | "technology" | "consulting";

export interface Partner {
  id: string;
  company_name: string;
  partner_type: PartnerType;
  country: string;
  region: string;
  expertise_areas: string[];
  logo_url: string | null;
  website: string | null;
  is_featured: boolean;
}

export interface PartnerApplicationPayload {
  company_name: string;
  contact_name: string;
  email: string;
  phone?: string;
  website?: string;
  country: string;
  partner_type: PartnerType;
  expertise_areas: string[];
  years_in_business?: number;
  message?: string;
  gdpr_consent: true;
}

export interface PartnerApplicationResponse {
  id: string;
  reference_number: string;
  status: "pending";
  created_at: string;
}

export const partnersApi = {
  list: (params?: { country?: string; partner_type?: PartnerType; is_featured?: boolean }) =>
    apiClient.get<ApiResponse<Partner[]>>("/partners/", params as Record<string, string>),

  submitApplication: (payload: PartnerApplicationPayload) =>
    apiClient.post<PartnerApplicationResponse>("/partners/apply/", payload),
};
