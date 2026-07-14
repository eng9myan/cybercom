/**
 * CyberCom Platform — environment-driven API configuration
 * All values fall back to production defaults when env vars are absent
 * (static site: replace at build time via esbuild --define:process.env.*)
 */

declare const process: { env: Record<string, string | undefined> };

function env(key: string, fallback: string): string {
  return (typeof process !== "undefined" && process.env[key]) ?? fallback;
}

export const config = {
  api: {
    baseUrl: env("CYBERCOM_API_URL", "https://api.cy-com.com"),
    version: env("CYBERCOM_API_VERSION", "v1"),
    timeoutMs: parseInt(env("CYBERCOM_API_TIMEOUT", "30000"), 10),
  },

  auth: {
    issuer: env("CYIDENTITY_URL", "https://identity.cy-com.com"),
    clientId: env("CYIDENTITY_WEBSITE_CLIENT_ID", "cybercom-website-public"),
    redirectUri: env("CYIDENTITY_REDIRECT_URI", "https://cy-com.com/auth/callback"),
    postLogoutUri: env("CYIDENTITY_POST_LOGOUT_URI", "https://cy-com.com"),
    scopes: env("CYIDENTITY_SCOPES", "openid profile email cybercom.read").split(" "),
  },

  portals: {
    portal: env("PORTAL_URL", "https://portal.cy-com.com"),
    health: env("HEALTH_URL", "https://health.cy-com.com"),
    provider: env("PROVIDER_URL", "https://provider.cy-com.com"),
  },

  services: {
    cymed: env("CYMED_HEALTH_URL", "https://api.cy-com.com/cymed/health/"),
    cycom: env("CYCOM_HEALTH_URL", "https://api.cy-com.com/cycom/health/"),
    cygov: env("CYGOV_HEALTH_URL", "https://api.cy-com.com/cygov/health/"),
    cyidentity: env("CYIDENTITY_HEALTH_URL", "https://identity.cy-com.com/health/"),
    cyai: env("CYAI_HEALTH_URL", "https://api.cy-com.com/cyai/health/"),
    cydata: env("CYDATA_HEALTH_URL", "https://api.cy-com.com/cydata/health/"),
    cyintegrationhub: env("CYINTEGRATIONHUB_HEALTH_URL", "https://api.cy-com.com/hub/health/"),
  },

  endpoints: {
    products: env("PRODUCTS_API_URL", "https://api.cy-com.com/v1/website/products/"),
    industries: env("INDUSTRIES_API_URL", "https://api.cy-com.com/v1/website/industries/"),
    partners: env("PARTNERS_API_URL", "https://api.cy-com.com/v1/website/partners/"),
    demo: env("DEMO_API_URL", "https://api.cy-com.com/v1/website/demo-requests/"),
    contact: env("CONTACT_API_URL", "https://api.cy-com.com/v1/website/contact/"),
    docs: env("DOCS_API_URL", "https://api.cy-com.com/v1/website/docs/"),
  },

  status: {
    refreshIntervalMs: parseInt(env("STATUS_REFRESH_INTERVAL", "30000"), 10),
  },
} as const;

export type Config = typeof config;
