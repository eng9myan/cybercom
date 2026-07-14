import { apiClient } from "./client";

export type Department =
  | "sales"
  | "support"
  | "partnerships"
  | "press"
  | "careers"
  | "general";

export interface ContactPayload {
  full_name: string;
  email: string;
  company?: string;
  subject: string;
  message: string;
  department: Department;
  gdpr_consent: true;
}

export interface ContactResponse {
  id: string;
  ticket_number: string;
  status: "open" | "in_progress" | "resolved" | "closed";
  created_at: string;
}

export interface NewsletterPayload {
  email: string;
  source?: string;
  gdpr_consent: true;
}

export interface NewsletterResponse {
  id: string;
  status: "subscribed";
  created_at: string;
}

export const contactApi = {
  send: (payload: ContactPayload) =>
    apiClient.post<ContactResponse>("/contact/", payload),

  status: (ticket: string) =>
    apiClient.get<ContactResponse>(`/contact/${ticket}/status/`),

  subscribeNewsletter: (payload: NewsletterPayload) =>
    apiClient.post<NewsletterResponse>("/contact/newsletter/", payload),
};
