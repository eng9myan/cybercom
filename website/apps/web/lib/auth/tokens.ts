/**
 * Access token storage — sessionStorage backed, cleared on tab close.
 * Real Keycloak/OAuth2 token responses are snake_case (access_token,
 * id_token, expires_in) — mapped explicitly at the callback boundary in
 * cyidentity.ts before ever reaching this store.
 */

const ACCESS_KEY = "cy_access_token";
const EXPIRY_KEY = "cy_token_expiry";
const ID_TOKEN_KEY = "cy_id_token";

export interface TokenSet {
  accessToken: string;
  idToken?: string;
  expiresIn: number;
  tokenType: string;
  scope?: string;
}

class TokenStore {
  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem(ACCESS_KEY);
  }

  getIdToken(): string | null {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem(ID_TOKEN_KEY);
  }

  setTokens(tokens: TokenSet): void {
    const expiresAt = Date.now() + tokens.expiresIn * 1000 - 30_000; // 30s buffer
    sessionStorage.setItem(ACCESS_KEY, tokens.accessToken);
    sessionStorage.setItem(EXPIRY_KEY, String(expiresAt));
    if (tokens.idToken) {
      sessionStorage.setItem(ID_TOKEN_KEY, tokens.idToken);
    }
  }

  clearTokens(): void {
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(EXPIRY_KEY);
    sessionStorage.removeItem(ID_TOKEN_KEY);
  }

  isExpired(): boolean {
    if (typeof window === "undefined") return true;
    const expiry = sessionStorage.getItem(EXPIRY_KEY);
    if (!expiry) return true;
    return Date.now() >= parseInt(expiry, 10);
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken() && !this.isExpired();
  }
}

export const tokenStore = new TokenStore();
