import { apiClient } from "./client";
import type { ApiResponse } from "./client";

export interface MarketplaceListing {
  id: string;
  code: string;
  name: string;
  category: "module" | "extension" | "theme" | "connector" | "ai_package" | "clinical_template" | "report" | "dashboard";
  product_codes: string[];
  publisher: string;
  publisher_type: "official" | "partner" | "community";
  version: string;
  description: string;
  icon_url?: string;
  screenshots_urls: string[];
  documentation_url?: string;
  price_model: "free" | "one_time" | "subscription" | "usage";
  price_amount: number;
  currency: string;
  status: string;
  install_count: number;
  rating_avg: number;
  rating_count: number;
  tags: string[];
  is_featured: boolean;
  published_at?: string | null;
}

export interface MarketplaceInstallation {
  id: string;
  listing: string;
  installed_by_id: string;
  installed_version: string;
  is_active: boolean;
  installed_at: string;
  config: Record<string, unknown>;
}

export const marketplaceApi = {
  getListings: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<MarketplaceListing>>("/commercial-readiness/marketplace-listings/", params, true),

  getListing: (id: string) =>
    apiClient.get<MarketplaceListing>(`/commercial-readiness/marketplace-listings/${id}/`, undefined, true),

  installListing: (id: string) =>
    apiClient.post<{ status: string; installation_id: string }>(
      `/commercial-readiness/marketplace-listings/${id}/install/`,
      {},
      false
    ),

  getInstallations: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<ApiResponse<MarketplaceInstallation>>("/commercial-readiness/marketplace-installations/", params, false),

  createInstallation: (body: Partial<MarketplaceInstallation>) =>
    apiClient.post<MarketplaceInstallation>("/commercial-readiness/marketplace-installations/", body, false),
};
