import { apiClient, type ApiResponse } from "./client";

export type DocContentType =
  | "guide"
  | "reference"
  | "tutorial"
  | "release_note"
  | "faq"
  | "changelog";

export interface DocSection {
  id: string;
  title: string;
  slug: string;
  summary: string;
  product: string;
  sort_order: number;
  item_count: number;
}

export interface DocItem {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content_type: DocContentType;
  tags: string[];
  version: string | null;
  updated_at: string;
}

export interface DocSearchResult {
  id: string;
  title: string;
  slug: string;
  summary: string;
  section_slug: string;
  content_type: DocContentType;
  score: number;
}

export const docsApi = {
  listSections: (params?: { product?: string }) =>
    apiClient.get<ApiResponse<DocSection[]>>("/documentation/", params as Record<string, string>),

  getSection: (slug: string) =>
    apiClient.get<DocSection & { items: DocItem[] }>(`/documentation/${slug}/`),

  search: (q: string, params?: { product?: string; content_type?: DocContentType }) =>
    apiClient.get<ApiResponse<DocSearchResult[]>>("/documentation/search/", {
      q,
      ...params,
    } as Record<string, string>),
};
