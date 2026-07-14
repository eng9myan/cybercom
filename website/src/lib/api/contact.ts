/**
 * CyberCom Contact API
 * Handles general contact form submissions and newsletter sign-ups.
 */

import { apiClient } from "./client.js";
import { config } from "../config.js";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface ContactMessage {
  first_name?: string;
  last_name?: string;
  email: string;
  phone?: string;
  subject: string;
  message: string;
  department?: "sales" | "support" | "partnerships" | "press" | "careers" | "general";
  company?: string;
  country?: string;
  consent_marketing?: boolean;
}

export interface ContactResponse {
  id: string;
  ticket_number: string;
  status: "received" | "in_progress" | "resolved";
  submitted_at: string;
  estimated_response: string;
  message: string;
}

export interface NewsletterSubscription {
  email: string;
  first_name?: string;
  topics?: ("product_updates" | "case_studies" | "industry_news" | "events")[];
  consent_marketing: boolean;
}

export interface NewsletterResponse {
  id: string;
  status: "subscribed" | "already_subscribed" | "unsubscribed";
  message: string;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

export async function sendContactMessage(message: ContactMessage): Promise<ContactResponse> {
  return apiClient.post<ContactResponse>(config.endpoints.contact, message, { skipAuth: true });
}

export async function subscribeNewsletter(
  subscription: NewsletterSubscription
): Promise<NewsletterResponse> {
  return apiClient.post<NewsletterResponse>(
    `${config.endpoints.contact}newsletter/`,
    subscription,
    { skipAuth: true }
  );
}

/** Handles the website contact / email sign-up form */
export async function submitContactForm(
  email: string,
  source: "hero_cta" | "footer_newsletter" | "contact_page" | "cta_section" = "footer_newsletter"
): Promise<NewsletterResponse> {
  return subscribeNewsletter({
    email,
    topics: ["product_updates"],
    consent_marketing: true,
  });
}

export async function getTicketStatus(ticketNumber: string): Promise<ContactResponse> {
  return apiClient.get<ContactResponse>(
    `${config.endpoints.contact}${ticketNumber}/status/`,
    { skipAuth: true }
  );
}

export const contactApi = {
  send: sendContactMessage,
  newsletter: subscribeNewsletter,
  submitForm: submitContactForm,
  ticketStatus: getTicketStatus,
};
