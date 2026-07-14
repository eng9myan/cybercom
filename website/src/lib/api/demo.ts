/**
 * CyberCom Demo Request API
 * Submits product demo requests from the marketing website.
 */

import { apiClient } from "./client.js";
import { config } from "../config.js";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface DemoRequest {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  job_title?: string;
  company_name: string;
  company_size?: "1-50" | "51-200" | "201-500" | "501-1000" | "1001-5000" | "5000+";
  industry?: string;
  country?: string;
  products_of_interest: string[];
  message?: string;
  preferred_date?: string;
  preferred_time_zone?: string;
  how_did_you_hear?: string;
  consent_marketing: boolean;
  consent_terms: boolean;
}

export interface DemoRequestResponse {
  id: string;
  status: "pending" | "scheduled" | "completed" | "cancelled";
  reference_number: string;
  submitted_at: string;
  scheduled_at?: string;
  assigned_to?: string;
  message: string;
  next_steps: string[];
}

export interface DemoAvailability {
  date: string;
  slots: DemoSlot[];
}

export interface DemoSlot {
  id: string;
  time: string;
  time_zone: string;
  duration_minutes: number;
  is_available: boolean;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

export async function submitDemoRequest(request: DemoRequest): Promise<DemoRequestResponse> {
  return apiClient.post<DemoRequestResponse>(config.endpoints.demo, request, { skipAuth: true });
}

export async function getDemoAvailability(
  productSlug: string,
  month: string
): Promise<DemoAvailability[]> {
  const url = apiClient.withParams(`${config.endpoints.demo}availability/`, {
    product: productSlug,
    month,
  });
  return apiClient.get<DemoAvailability[]>(url, { skipAuth: true });
}

export async function getDemoRequestStatus(referenceNumber: string): Promise<DemoRequestResponse> {
  return apiClient.get<DemoRequestResponse>(
    `${config.endpoints.demo}${referenceNumber}/status/`,
    { skipAuth: true }
  );
}

/** Handles the website demo form submission with validation */
export async function submitDemoForm(formData: FormData): Promise<DemoRequestResponse> {
  const products = formData.getAll("products_of_interest") as string[];

  const request: DemoRequest = {
    first_name: (formData.get("first_name") as string) ?? "",
    last_name: (formData.get("last_name") as string) ?? "",
    email: (formData.get("email") as string) ?? "",
    phone: (formData.get("phone") as string) || undefined,
    job_title: (formData.get("job_title") as string) || undefined,
    company_name: (formData.get("company_name") as string) ?? "",
    company_size: (formData.get("company_size") as DemoRequest["company_size"]) || undefined,
    industry: (formData.get("industry") as string) || undefined,
    country: (formData.get("country") as string) || undefined,
    products_of_interest: products.length > 0 ? products : ["cymed"],
    message: (formData.get("message") as string) || undefined,
    preferred_date: (formData.get("preferred_date") as string) || undefined,
    preferred_time_zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    how_did_you_hear: (formData.get("how_did_you_hear") as string) || undefined,
    consent_marketing: formData.get("consent_marketing") === "on",
    consent_terms: formData.get("consent_terms") === "on",
  };

  return submitDemoRequest(request);
}

export const demoApi = {
  submit: submitDemoRequest,
  submitForm: submitDemoForm,
  availability: getDemoAvailability,
  status: getDemoRequestStatus,
};
