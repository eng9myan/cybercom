/**
 * CyberCom Documentation API
 * Fetches product documentation, API references, and release notes.
 */

import { apiClient, type PaginatedResponse, type PaginationParams } from "./client.js";
import { config } from "../config.js";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface DocSection {
  id: string;
  slug: string;
  product: string;
  title: string;
  description: string;
  icon: string;
  items: DocItem[];
  sort_order: number;
}

export interface DocItem {
  id: string;
  slug: string;
  title: string;
  excerpt: string;
  url: string;
  type: "guide" | "api_reference" | "tutorial" | "release_notes" | "faq";
  last_updated: string;
  tags: string[];
  is_featured: boolean;
}

export interface DocSearchResult {
  id: string;
  title: string;
  excerpt: string;
  url: string;
  product: string;
  section: string;
  relevance_score: number;
}

export interface ReleaseNote {
  id: string;
  version: string;
  product: string;
  released_at: string;
  summary: string;
  changes: ReleaseChange[];
}

export interface ReleaseChange {
  type: "feature" | "improvement" | "fix" | "breaking" | "deprecated";
  description: string;
  module?: string;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

export async function listDocSections(product?: string): Promise<DocSection[]> {
  const url = apiClient.withParams(config.endpoints.docs, product ? { product } : {});
  const response = await apiClient.get<PaginatedResponse<DocSection>>(url, { skipAuth: true });
  return response.results;
}

export async function searchDocs(
  query: string,
  params: PaginationParams & { product?: string } = {}
): Promise<PaginatedResponse<DocSearchResult>> {
  const url = apiClient.withParams(`${config.endpoints.docs}search/`, {
    q: query,
    ...params,
  } as Record<string, string | number | boolean | undefined>);
  return apiClient.get<PaginatedResponse<DocSearchResult>>(url, { skipAuth: true });
}

export async function listReleaseNotes(
  params: PaginationParams & { product?: string } = {}
): Promise<PaginatedResponse<ReleaseNote>> {
  const url = apiClient.withParams(
    `${config.endpoints.docs}releases/`,
    params as Record<string, string | number | boolean | undefined>
  );
  return apiClient.get<PaginatedResponse<ReleaseNote>>(url, { skipAuth: true });
}

export async function getDocItem(slug: string): Promise<DocItem> {
  return apiClient.get<DocItem>(`${config.endpoints.docs}items/${slug}/`, { skipAuth: true });
}

export const docsApi = {
  sections: listDocSections,
  search: searchDocs,
  releases: listReleaseNotes,
  getItem: getDocItem,
};
