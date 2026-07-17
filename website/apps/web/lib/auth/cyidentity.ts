/**
 * CyIdentity (Keycloak) OAuth 2.1 + PKCE — admin panel login.
 *
 * Flow:
 *   1. initiateLogin()  — redirect to Keycloak's authorize endpoint
 *   2. handleCallback() — exchange code for tokens, verify state
 *   3. tokenStore       — access token kept in sessionStorage
 *   4. logout()         — clear tokens + redirect to end_session_endpoint
 */

import { authConfig } from "./config";
import { generatePkceParams } from "./pkce";
import { tokenStore, type TokenSet } from "./tokens";

const PKCE_STORAGE_KEY = "cy_pkce_verifier";
const STATE_STORAGE_KEY = "cy_oauth_state";
const RETURN_URL_KEY = "cy_return_url";

export interface OidcConfiguration {
  issuer: string;
  authorization_endpoint: string;
  token_endpoint: string;
  end_session_endpoint: string;
  jwks_uri: string;
}

let cachedOidcConfig: OidcConfiguration | null = null;

export async function discoverOidcConfiguration(): Promise<OidcConfiguration> {
  if (cachedOidcConfig) return cachedOidcConfig;
  const url = `${authConfig.issuer}/.well-known/openid-configuration`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`OIDC discovery failed: ${response.status}`);
  cachedOidcConfig = (await response.json()) as OidcConfiguration;
  return cachedOidcConfig;
}

function callbackRedirectUri(locale: string): string {
  return `${window.location.origin}/${locale}/admin/auth/callback`;
}

export async function initiateLogin(locale: string, returnUrl?: string): Promise<void> {
  const oidc = await discoverOidcConfiguration();
  const pkce = await generatePkceParams();

  sessionStorage.setItem(PKCE_STORAGE_KEY, pkce.codeVerifier);
  sessionStorage.setItem(STATE_STORAGE_KEY, pkce.state);
  if (returnUrl) sessionStorage.setItem(RETURN_URL_KEY, returnUrl);

  const params = new URLSearchParams({
    response_type: "code",
    client_id: authConfig.clientId,
    redirect_uri: callbackRedirectUri(locale),
    scope: authConfig.scopes.join(" "),
    state: pkce.state,
    code_challenge: pkce.codeChallenge,
    code_challenge_method: "S256",
  });

  window.location.href = `${oidc.authorization_endpoint}?${params.toString()}`;
}

export interface CallbackResult {
  tokens: TokenSet;
  returnUrl: string;
}

export async function handleCallback(locale: string): Promise<CallbackResult> {
  const url = new URL(window.location.href);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const error = url.searchParams.get("error");
  const errorDesc = url.searchParams.get("error_description");

  if (error) throw new Error(`OAuth error: ${error} — ${errorDesc}`);
  if (!code || !state) throw new Error("Missing code or state in callback URL");

  const storedState = sessionStorage.getItem(STATE_STORAGE_KEY);
  if (state !== storedState) throw new Error("State mismatch — possible CSRF attack");

  const codeVerifier = sessionStorage.getItem(PKCE_STORAGE_KEY);
  if (!codeVerifier) throw new Error("Missing code_verifier — session may have expired");

  const oidc = await discoverOidcConfiguration();

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: authConfig.clientId,
    redirect_uri: callbackRedirectUri(locale),
    code,
    code_verifier: codeVerifier,
  });

  const response = await fetch(oidc.token_endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!response.ok) {
    const err = (await response.json().catch(() => ({}))) as Record<string, string>;
    throw new Error(`Token exchange failed: ${err.error_description ?? err.error ?? response.statusText}`);
  }

  // Real Keycloak/OAuth2 responses are snake_case — map explicitly rather
  // than casting, which would silently store "undefined" for every field.
  const raw = (await response.json()) as {
    access_token: string;
    id_token?: string;
    expires_in: number;
    token_type: string;
    scope?: string;
  };
  const tokens: TokenSet = {
    accessToken: raw.access_token,
    idToken: raw.id_token,
    expiresIn: raw.expires_in,
    tokenType: raw.token_type,
    scope: raw.scope,
  };
  tokenStore.setTokens(tokens);

  sessionStorage.removeItem(PKCE_STORAGE_KEY);
  sessionStorage.removeItem(STATE_STORAGE_KEY);

  const returnUrl = sessionStorage.getItem(RETURN_URL_KEY) ?? `/${locale}/admin`;
  sessionStorage.removeItem(RETURN_URL_KEY);

  return { tokens, returnUrl };
}

export async function logout(locale: string): Promise<void> {
  const idToken = tokenStore.getIdToken();
  tokenStore.clearTokens();
  try {
    const oidc = await discoverOidcConfiguration();
    const params = new URLSearchParams({
      post_logout_redirect_uri: `${window.location.origin}/${locale}/admin/login`,
    });
    if (idToken) params.set("id_token_hint", idToken);
    window.location.href = `${oidc.end_session_endpoint}?${params.toString()}`;
  } catch {
    window.location.href = `/${locale}/admin/login`;
  }
}

/** Unverified decode for UI display/role-gating — every real API call is
 * still verified server-side by Django's JWKS check regardless of this. */
export function decodeAccessTokenClaims(): Record<string, any> | null {
  const token = tokenStore.getAccessToken();
  if (!token) return null;
  try {
    const part = token.split(".")[1] ?? "";
    const b64 = part.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(b64));
  } catch {
    return null;
  }
}

export function isPlatformAdmin(): boolean {
  const claims = decodeAccessTokenClaims();
  const roles: string[] = claims?.realm_access?.roles || [];
  return roles.includes("platform_admin") || roles.includes("tenant_admin");
}
