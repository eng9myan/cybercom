/**
 * Token storage and refresh — sessionStorage backed, never localStorage for access tokens.
 * Refresh tokens use httpOnly cookies set by CyIdentity (not stored in JS).
 */

import { config } from "../config.js";

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
    return sessionStorage.getItem(ACCESS_KEY);
  }

  getIdToken(): string | null {
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
    const expiry = sessionStorage.getItem(EXPIRY_KEY);
    if (!expiry) return true;
    return Date.now() >= parseInt(expiry, 10);
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken() && !this.isExpired();
  }

  /** Refresh access token using the httpOnly refresh token cookie */
  async refresh(): Promise<void> {
    const tokenEndpoint = `${config.auth.issuer}/oauth/token`;

    const response = await fetch(tokenEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        client_id: config.auth.clientId,
      }).toString(),
      credentials: "include", // sends the httpOnly refresh token cookie
    });

    if (!response.ok) {
      this.clearTokens();
      throw new Error("Token refresh failed — user must re-authenticate");
    }

    const tokens = (await response.json()) as TokenSet;
    this.setTokens(tokens);
  }
}

export const tokenStore = new TokenStore();
