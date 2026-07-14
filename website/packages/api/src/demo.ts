import { apiClient } from "./client";

export interface DemoRequestPayload {
  full_name: string;
  email: string;
  phone?: string;
  job_title: string;
  company: string;
  company_size: "1-10" | "11-50" | "51-200" | "201-500" | "501-1000" | "1001+";
  country: string;
  product_interests: string[];
  message?: string;
  preferred_time?: string;
  source?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  gdpr_consent: true;
  marketing_consent?: boolean;
  tenant_slug?: string;
}

export interface DemoRequestResponse {
  id: string;
  reference_number: string;
  status: "pending" | "assigned" | "scheduled" | "completed" | "cancelled";
  created_at: string;
}

export const demoApi = {
  submit: (payload: DemoRequestPayload) =>
    apiClient.post<DemoRequestResponse>("/demo-request/", payload),

  status: (ref: string) =>
    apiClient.get<DemoRequestResponse>(`/demo-request/${ref}/status/`),
};
