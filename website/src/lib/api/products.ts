/**
 * CyberCom Products API
 * Fetches the product/division catalog from the CyberCom Platform.
 */

import { apiClient, type PaginatedResponse, type PaginationParams } from "./client.js";
import { config } from "../config.js";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface Product {
  id: string;
  slug: string;
  name: string;
  tagline: string;
  description: string;
  category: "healthcare" | "commerce" | "enterprise" | "government" | "platform";
  icon: string;
  accent_color: string;
  portal_url: string;
  docs_url: string;
  is_active: boolean;
  is_featured: boolean;
  sort_order: number;
  editions: ProductEdition[];
  features: ProductFeature[];
  industries: string[];
}

export interface ProductEdition {
  id: string;
  name: string;
  tier: "starter" | "standard" | "enterprise" | "government";
  description: string;
  features: string[];
  is_default: boolean;
}

export interface ProductFeature {
  id: string;
  title: string;
  description: string;
  category: string;
  icon: string;
}

export interface ProductListParams extends PaginationParams {
  category?: Product["category"];
  is_featured?: boolean;
  is_active?: boolean;
  industry?: string;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

export async function listProducts(
  params: ProductListParams = {}
): Promise<PaginatedResponse<Product>> {
  const url = apiClient.withParams(config.endpoints.products, params as Record<string, string | number | boolean | undefined>);
  return apiClient.get<PaginatedResponse<Product>>(url, { skipAuth: true });
}

export async function getProduct(slug: string): Promise<Product> {
  const url = `${config.endpoints.products}${slug}/`;
  return apiClient.get<Product>(url, { skipAuth: true });
}

export async function getFeaturedProducts(): Promise<Product[]> {
  const url = apiClient.withParams(config.endpoints.products, {
    is_featured: true,
    is_active: true,
  });
  const response = await apiClient.get<PaginatedResponse<Product>>(url, { skipAuth: true });
  return response.results;
}

export const productsApi = {
  list: listProducts,
  get: getProduct,
  featured: getFeaturedProducts,
};
