/**
 * CyIdentity Integration — OAuth 2.1 + OpenID Connect + PKCE
 * CyIdentity is the CyberCom Platform IAM (P2.1).
 *
 * Flow:
 *   1. initiateLogin()   — redirect to CyIdentity authorize endpoint
 *   2. handleCallback()  — exchange code for tokens
 *   3. tokenStore        — tokens stored in sessionStorage
 *   4. logout()          — clear tokens + redirect to end_session_endpoint
 */

import { config } from "../config.js";
import { generatePkceParams } from "./pkce.js";
import { tokenStore, type TokenSet } from "./tokens.js";

const PKCE_STORAGE_KEY = "cy_pkce_verifier";
const STATE_STORAGE_KEY = "cy_oauth_state";
const NONCE_STORAGE_KEY = "cy_oauth_nonce";
const RETURN_URL_KEY = "cy_return_url";

// ─── OIDC Discovery ─────────────────────────────────────────────────────────

export interface OidcConfiguration {
  issuer: string;
  authorization_endpoint: string;
  token_endpoint: string;
  userinfo_endpoint: string;
  end_session_endpoint: string;
  jwks_uri: string;
  scopes_supported: string[];
  response_types_supported: string[];
  code_challenge_methods_supported: string[];
}

let cachedOidcConfig: OidcConfiguration | null = null;

export async function discoverOidcConfiguration(): Promise<OidcConfiguration> {
  if (cachedOidcConfig) return cachedOidcConfig;

  const url = `${config.auth.issuer}/.well-known/openid-configuration`;
  const response = await fetch(url, { method: "GET" });

  if (!response.ok) {
    throw new Error(`OIDC discovery failed: ${response.status}`);
  }

  cachedOidcConfig = (await response.json()) as OidcConfiguration;
  return cachedOidcConfig;
}

// ─── Login ──────────────────────────────────────────────────────────────────

export interface LoginOptions {
  /** URL to return to after login (stored, then restored post-callback) */
  returnUrl?: string;
  /** Additional scopes beyond the configured defaults */
  extraScopes?: string[];
  /** Portal hint: tells CyIdentity which branded login page to show */
  portalHint?: "portal" | "health" | "provider";
  /** prompt=login forces re-authentication even if session exists */
  prompt?: "login" | "none" | "consent" | "select_account";
  /** ui_locales hint */
  locale?: string;
}

export async function initiateLogin(options: LoginOptions = {}): Promise<void> {
  const oidc = await discoverOidcConfiguration();
  const pkce = await generatePkceParams();

  // Store PKCE params in sessionStorage (same-origin, same-tab)
  sessionStorage.setItem(PKCE_STORAGE_KEY, pkce.codeVerifier);
  sessionStorage.setItem(STATE_STORAGE_KEY, pkce.state);
  sessionStorage.setItem(NONCE_STORAGE_KEY, pkce.nonce);
  if (options.returnUrl) {
    sessionStorage.setItem(RETURN_URL_KEY, options.returnUrl);
  }

  const scopes = [
    ...config.auth.scopes,
    ...(options.extraScopes ?? []),
  ];

  const params = new URLSearchParams({
    response_type: "code",
    client_id: config.auth.clientId,
    redirect_uri: config.auth.redirectUri,
    scope: scopes.join(" "),
    state: pkce.state,
    nonce: pkce.nonce,
    code_challenge: pkce.codeChallenge,
    code_challenge_method: "S256",
  });

  if (options.prompt) params.set("prompt", options.prompt);
  if (options.locale) params.set("ui_locales", options.locale);
  if (options.portalHint) params.set("acr_values", `portal:${options.portalHint}`);

  window.location.href = `${oidc.authorization_endpoint}?${params.toString()}`;
}

// ─── Callback Handler ────────────────────────────────────────────────────────

export interface CallbackResult {
  tokens: TokenSet;
  returnUrl: string;
}

export async function handleCallback(callbackUrl?: string): Promise<CallbackResult> {
  const url = new URL(callbackUrl ?? window.location.href);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const error = url.searchParams.get("error");
  const errorDesc = url.searchParams.get("error_description");

  if (error) {
    throw new Error(`OAuth error: ${error} — ${errorDesc}`);
  }

  if (!code || !state) {
    throw new Error("Missing code or state in callback URL");
  }

  const storedState = sessionStorage.getItem(STATE_STORAGE_KEY);
  if (state !== storedState) {
    throw new Error("State mismatch — possible CSRF attack");
  }

  const codeVerifier = sessionStorage.getItem(PKCE_STORAGE_KEY);
  if (!codeVerifier) {
    throw new Error("Missing code_verifier — session may have expired");
  }

  const oidc = await discoverOidcConfiguration();

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: config.auth.clientId,
    redirect_uri: config.auth.redirectUri,
    code,
    code_verifier: codeVerifier,
  });

  const response = await fetch(oidc.token_endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
    credentials: "include",
  });

  if (!response.ok) {
    const err = (await response.json()) as Record<string, string>;
    throw new Error(`Token exchange failed: ${err["error"] ?? response.statusText}`);
  }

  const tokens = (await response.json()) as TokenSet;
  tokenStore.setTokens(tokens);

  // Clean up PKCE state
  sessionStorage.removeItem(PKCE_STORAGE_KEY);
  sessionStorage.removeItem(STATE_STORAGE_KEY);
  sessionStorage.removeItem(NONCE_STORAGE_KEY);

  const returnUrl = sessionStorage.getItem(RETURN_URL_KEY) ?? "/";
  sessionStorage.removeItem(RETURN_URL_KEY);

  return { tokens, returnUrl };
}

// ─── Logout ─────────────────────────────────────────────────────────────────

export async function logout(options: { redirectUri?: string } = {}): Promise<void> {
  const idToken = tokenStore.getIdToken();
  tokenStore.clearTokens();

  try {
    const oidc = await discoverOidcConfiguration();
    const params = new URLSearchParams({
      post_logout_redirect_uri: options.redirectUri ?? config.auth.postLogoutUri,
    });
    if (idToken) params.set("id_token_hint", idToken);
    window.location.href = `${oidc.end_session_endpoint}?${params.toString()}`;
  } catch {
    window.location.href = options.redirectUri ?? config.auth.postLogoutUri;
  }
}

// ─── Exports ────────────────────────────────────────────────────────────────

export const cyIdentity = {
  login: initiateLogin,
  handleCallback,
  logout,
  discover: discoverOidcConfiguration,
  isAuthenticated: () => tokenStore.isAuthenticated(),
  getAccessToken: () => tokenStore.getAccessToken(),
};
