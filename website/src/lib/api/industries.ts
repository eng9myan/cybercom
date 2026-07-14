/**
 * CyberCom Industries API
 * Fetches the industry verticals and their solution mappings.
 */

import { apiClient, type PaginatedResponse, type PaginationParams } from "./client.js";
import { config } from "../config.js";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface Industry {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  accent_color: string;
  hero_image_url: string;
  challenge_headline: string;
  challenges: IndustryChallenge[];
  solutions: IndustrySolution[];
  case_studies: CaseStudy[];
  is_active: boolean;
  sort_order: number;
}

export interface IndustryChallenge {
  id: string;
  title: string;
  description: string;
  icon: string;
}

export interface IndustrySolution {
  id: string;
  product_slug: string;
  product_name: string;
  solution_title: string;
  solution_description: string;
}

export interface CaseStudy {
  id: string;
  client_name: string;
  client_logo_url: string;
  industry: string;
  headline: string;
  outcome_metrics: OutcomeMetric[];
  published_at: string;
}

export interface OutcomeMetric {
  value: string;
  label: string;
  direction: "up" | "down" | "neutral";
}

export interface IndustryListParams extends PaginationParams {
  is_active?: boolean;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

export async function listIndustries(
  params: IndustryListParams = {}
): Promise<PaginatedResponse<Industry>> {
  const url = apiClient.withParams(config.endpoints.industries, params as Record<string, string | number | boolean | undefined>);
  return apiClient.get<PaginatedResponse<Industry>>(url, { skipAuth: true });
}

export async function getIndustry(slug: string): Promise<Industry> {
  const url = `${config.endpoints.industries}${slug}/`;
  return apiClient.get<Industry>(url, { skipAuth: true });
}

export async function listCaseStudies(
  params: PaginationParams & { industry?: string } = {}
): Promise<PaginatedResponse<CaseStudy>> {
  const url = apiClient.withParams(
    `${config.endpoints.industries}case-studies/`,
    params as Record<string, string | number | boolean | undefined>
  );
  return apiClient.get<PaginatedResponse<CaseStudy>>(url, { skipAuth: true });
}

export const industriesApi = {
  list: listIndustries,
  get: getIndustry,
  caseStudies: listCaseStudies,
};
