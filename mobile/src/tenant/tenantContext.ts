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

const BASE64_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

/**
 * Pure-JS base64 -> byte array. `atob` is a browser Web API — it does not
 * exist in the React Native / Hermes runtime (no DOM), so the previous
 * version of this function would throw ReferenceError: atob is not
 * defined on a real device. No new dependency needed for base64, so
 * implemented directly rather than pulling in a polyfill package.
 */
function base64DecodeBytes(input: string): number[] {
  const bytes: number[] = [];
  let buffer = 0;
  let bits = 0;
  for (const char of input) {
    if (char === '=') break;
    const value = BASE64_ALPHABET.indexOf(char);
    if (value === -1) continue;
    buffer = (buffer << 6) | value;
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      bytes.push((buffer >> bits) & 0xff);
    }
  }
  return bytes;
}

/**
 * Decodes a UTF-8 byte sequence into a JS string. JWT claims routinely
 * contain non-ASCII text (Arabic tenant/branding names — this app is
 * RTL/LTR bilingual by spec), so a naive one-byte-per-char decode
 * (String.fromCharCode straight over the base64 bytes) garbles anything
 * outside ASCII. Caught by the Arabic test case in
 * tenantContext.test.ts, not left undetected.
 */
function utf8Decode(bytes: number[]): string {
  let result = '';
  let i = 0;
  while (i < bytes.length) {
    const byte1 = bytes[i++];
    if (byte1 < 0x80) {
      result += String.fromCharCode(byte1);
    } else if (byte1 >= 0xc0 && byte1 < 0xe0 && i < bytes.length) {
      const byte2 = bytes[i++];
      result += String.fromCharCode(((byte1 & 0x1f) << 6) | (byte2 & 0x3f));
    } else if (byte1 >= 0xe0 && byte1 < 0xf0 && i + 1 < bytes.length) {
      const byte2 = bytes[i++];
      const byte3 = bytes[i++];
      result += String.fromCharCode(
        ((byte1 & 0x0f) << 12) | ((byte2 & 0x3f) << 6) | (byte3 & 0x3f)
      );
    } else if (byte1 >= 0xf0 && i + 2 < bytes.length) {
      const byte2 = bytes[i++];
      const byte3 = bytes[i++];
      const byte4 = bytes[i++];
      let codepoint =
        ((byte1 & 0x07) << 18) | ((byte2 & 0x3f) << 12) | ((byte3 & 0x3f) << 6) | (byte4 & 0x3f);
      codepoint -= 0x10000;
      result += String.fromCharCode(0xd800 + (codepoint >> 10), 0xdc00 + (codepoint & 0x3ff));
    }
  }
  return result;
}

function base64Decode(input: string): string {
  return utf8Decode(base64DecodeBytes(input));
}

/**
 * Decode tenant_id from a JWT payload without verifying signature.
 * Signature is verified by the backend; mobile only needs the claim for routing.
 */
export function decodeJwtPayload(token: string): Record<string, unknown> {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return {};
    const payload = parts[1];
    const padded = payload + '='.repeat((4 - (payload.length % 4)) % 4);
    const decoded = base64Decode(padded.replace(/-/g, '+').replace(/_/g, '/'));
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
