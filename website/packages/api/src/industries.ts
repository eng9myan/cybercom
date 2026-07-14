import { apiClient, type ApiResponse } from "./client";

export interface Industry {
  id: string;
  name: string;
  slug: string;
  tagline: string;
  description: string;
  icon: string;
  hero_image_url: string | null;
  is_featured: boolean;
  product_count: number;
  case_study_count: number;
}

export const industriesApi = {
  list: (params?: { is_featured?: boolean; search?: string }) =>
    apiClient.get<ApiResponse<Industry[]>>("/industries/", params as Record<string, string>),

  get: (slug: string) => apiClient.get<Industry & { products: unknown[]; case_studies: unknown[] }>(`/industries/${slug}/`),

  featured: () => industriesApi.list({ is_featured: true }),
};
