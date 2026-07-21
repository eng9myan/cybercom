export { CyberComApiClient, apiClient } from "./client";
export type { ApiClientConfig, ApiResponse, ApiError } from "./client";

export { productsApi } from "./products";
export type { Product, ProductCategory, ProductListParams, Edition } from "./products";

export { industriesApi } from "./industries";
export type { Industry } from "./industries";

export { demoApi } from "./demo";
export type { DemoRequestPayload, DemoRequestResponse } from "./demo";

export { demoProvisionApi, DemoProvisionApiError } from "./demo-provision";
export type { DemoProvisionPayload, DemoProvisionResponse, DemoProvisionError } from "./demo-provision";

export { subscriptionApi, SubscriptionApiError, SUBSCRIPTION_TIERS } from "./subscriptions";
export type {
  SubscriptionTier,
  SubscriptionRegisterPayload,
  SubscriptionRegisterResponse,
  SubscriptionRegisterError,
} from "./subscriptions";

export { contactApi } from "./contact";
export type { ContactPayload, ContactResponse, NewsletterPayload, NewsletterResponse, Department } from "./contact";

export { partnersApi } from "./partners";
export type { Partner, PartnerType, PartnerApplicationPayload, PartnerApplicationResponse } from "./partners";

export { docsApi } from "./docs";
export type { DocSection, DocItem, DocSearchResult, DocContentType } from "./docs";

export { licensingApi } from "./licensing";
export type { License, Subscription } from "./licensing";

export { marketplaceApi } from "./marketplace";
export type { MarketplaceListing, MarketplaceInstallation } from "./marketplace";

export { portalApi } from "./portal";
export type { CustomerPortalAccess, SupportTicket, WhiteLabelConfig, CommercialMetricsSnapshot } from "./portal";

export { partnerApi } from "./partner";
export type { PartnerProfile, PartnerOpportunity, RevenueShare, PartnerAsset, DealRegistration } from "./partner";
