/**
 * CyberCom Mobile — Tenant Context
 * Resolves and caches the active tenant context for the mobile app.
 * ADR-0002: tenant_id sourced from JWT claim; falls back to stored context.
 */

import { getStoredTokens } from '../security/encryption';

export interface TenantContext {
  tenantId: string;
  tenantSlug: string;
  tenantName: string;
  keycloakRealmName: string;
  locale: string;
  rtlDefault: boolean;
  homeRegion: string;
  tier: 'shared' | 'schema' | 'database' | 'cluster';
  features: Record<string, boolean>;
  branding: TenantBrandingContext;
}

export interface TenantBrandingContext {
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  appName: string;
  logoUrl: string;
  logoDarkUrl: string;
  rtlDefault: boolean;
  defaultLanguage: string;
  theme: 'light' | 'dark' | 'auto';
}

const DEFAULT_BRANDING: TenantBrandingContext = {
  primaryColor: '#1B4F8A',
  secondaryColor: '#00B4D8',
  accentColor: '#90E0EF',
  appName: 'CyberCom',
  logoUrl: '',
  logoDarkUrl: '',
  rtlDefault: true,
  defaultLanguage: 'ar',
  theme: 'auto',
};

let _cachedContext: TenantContext | null = null;

/**
 * Decode tenant_id from a JWT payload without verifying signature.
 * Signature is verified by the backend; mobile only needs the claim for routing.
 */
function decodeJwtPayload(token: string): Record<string, unknown> {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return {};
    const payload = parts[1];
    const padded = payload + '='.repeat((4 - (payload.length % 4)) % 4);
    const decoded = atob(padded.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch {
    return {};
  }
}

/**
 * Resolve tenant context from stored access token.
 * Returns null if no token or no tenant_id claim.
 */
export async function resolveTenantFromToken(): Promise<TenantContext | null> {
  const tokens = await getStoredTokens();
  if (!tokens?.accessToken) return null;

  const claims = decodeJwtPayload(tokens.accessToken);
  const tenantId = (claims['tenant_id'] as string) || (claims['tid'] as string);
  if (!tenantId) return null;

  return {
    tenantId,
    tenantSlug: (claims['tenant_slug'] as string) || '',
    tenantName: (claims['tenant_name'] as string) || '',
    keycloakRealmName: (claims['realm_name'] as string) || '',
    locale: (claims['locale'] as string) || 'ar',
    rtlDefault: (claims['rtl_default'] as boolean) ?? true,
    homeRegion: (claims['home_region'] as string) || 'me-central-1',
    tier: (claims['tenant_tier'] as TenantContext['tier']) || 'shared',
    features: (claims['tenant_features'] as Record<string, boolean>) || {},
    branding: DEFAULT_BRANDING,
  };
}

/**
 * Fetch full tenant context from API (includes branding, features).
 * Called once after login; result cached in memory + AsyncStorage.
 */
export async function fetchTenantContext(
  apiBaseUrl: string,
  accessToken: string,
  tenantId: string,
): Promise<TenantContext | null> {
  try {
    const resp = await fetch(`${apiBaseUrl}/api/v1/tenants/${tenantId}/`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Tenant-ID': tenantId,
      },
    });

    if (!resp.ok) return null;

    const data = await resp.json();
    const brandingResp = await fetch(`${apiBaseUrl}/api/v1/tenants/brandings/?tenant=${tenantId}`, {
      headers: { Authorization: `Bearer ${accessToken}`, 'X-Tenant-ID': tenantId },
    });

    let branding = DEFAULT_BRANDING;
    if (brandingResp.ok) {
      const b = await brandingResp.json();
      const first = b.results?.[0] || b;
      if (first.primary_color) {
        branding = {
          primaryColor: first.primary_color,
          secondaryColor: first.secondary_color,
          accentColor: first.accent_color,
          appName: first.app_name || 'CyberCom',
          logoUrl: first.logo_url || '',
          logoDarkUrl: first.logo_dark_url || '',
          rtlDefault: first.rtl_default ?? true,
          defaultLanguage: first.default_language || 'ar',
          theme: first.theme || 'auto',
        };
      }
    }

    const context: TenantContext = {
      tenantId: data.id,
      tenantSlug: data.slug,
      tenantName: data.name,
      keycloakRealmName: data.keycloak_realm_name || '',
      locale: data.locale || 'ar',
      rtlDefault: branding.rtlDefault,
      homeRegion: data.home_region || 'me-central-1',
      tier: data.tier || 'shared',
      features: {},
      branding,
    };

    _cachedContext = context;
    return context;
  } catch (err) {
    console.error('[TenantContext] fetchTenantContext error:', err);
    return null;
  }
}

export function getCachedTenantContext(): TenantContext | null {
  return _cachedContext;
}

export function clearTenantContext(): void {
  _cachedContext = null;
}
