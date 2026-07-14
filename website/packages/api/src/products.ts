import { apiClient, type ApiResponse } from "./client";

export type ProductCategory =
  | "healthcare"
  | "erp"
  | "government"
  | "ai"
  | "identity"
  | "integration"
  | "data"
  | "communications"
  | "citizen";

export interface Product {
  id: string;
  name: string;
  slug: string;
  tagline: string;
  description: string;
  category: ProductCategory;
  features: string[];
  editions: Edition[];
  compliance_badges: string[];
  is_published: boolean;
  is_featured: boolean;
  sort_order: number;
  seo_title: string;
  seo_description: string;
  icon_url: string | null;
  hero_image_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Edition {
  name: string;
  tagline: string;
  features: string[];
}

export interface ProductListParams {
  category?: ProductCategory;
  is_featured?: boolean;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export const productsApi = {
  list: (params?: ProductListParams) =>
    apiClient.get<ApiResponse<Product[]>>("/products/", params as Record<string, string>),

  get: (slug: string) => apiClient.get<Product>(`/products/${slug}/`),

  featured: () =>
    apiClient.get<ApiResponse<Product[]>>("/products/", { is_featured: true, page_size: 12 }),

  byCategory: (category: ProductCategory) =>
    apiClient.get<ApiResponse<Product[]>>("/products/", { category }),
};
