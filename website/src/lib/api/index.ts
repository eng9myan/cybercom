export { apiClient } from "./client.js";
export { productsApi, listProducts, getProduct, getFeaturedProducts } from "./products.js";
export { industriesApi, listIndustries, getIndustry, listCaseStudies } from "./industries.js";
export { partnersApi, listPartners, getFeaturedPartners, submitPartnerApplication } from "./partners.js";
export { demoApi, submitDemoRequest, submitDemoForm, getDemoAvailability } from "./demo.js";
export { contactApi, sendContactMessage, subscribeNewsletter, submitContactForm } from "./contact.js";
export { docsApi, listDocSections, searchDocs, listReleaseNotes } from "./docs.js";
export { CyberComApiError, fetchWithMiddleware } from "./middleware.js";

export type { PaginatedResponse, PaginationParams } from "./client.js";
export type { Product, ProductEdition, ProductFeature, ProductListParams } from "./products.js";
export type { Industry, IndustryChallenge, IndustrySolution, CaseStudy } from "./industries.js";
export type { Partner, PartnerApplication, PartnerApplicationResponse } from "./partners.js";
export type { DemoRequest, DemoRequestResponse, DemoAvailability } from "./demo.js";
export type { ContactMessage, ContactResponse, NewsletterSubscription } from "./contact.js";
export type { DocSection, DocItem, DocSearchResult, ReleaseNote } from "./docs.js";
