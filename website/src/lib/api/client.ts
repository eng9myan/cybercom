/**
 * CyberCom Platform — Centralized API Client
 * Single entry point for all HTTP calls to the CyberCom Platform backend.
 */

import { config } from "../config.js";
import { fetchWithMiddleware, type FetchOptions, type CyberComApiError } from "./middleware.js";

export type { CyberComApiError, ApiError } from "./middleware.js";

// ─── Pagination ─────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  ordering?: string;
  search?: string;
}

// ─── API Client ─────────────────────────────────────────────────────────────

class ApiClient {
  private readonly baseUrl: string;
  private readonly version: string;

  constructor() {
    this.baseUrl = config.api.baseUrl.replace(/\/$/, "");
    this.version = config.api.version;
  }

  /** Build a full URL from a path relative to the versioned API root */
  url(path: string): string {
    const clean = path.replace(/^\//, "");
    return `${this.baseUrl}/${this.version}/${clean}`;
  }

  /** Build a full URL from an absolute path (no version prefix) */
  absoluteUrl(path: string): string {
    const clean = path.replace(/^\//, "");
    return `${this.baseUrl}/${clean}`;
  }

  /** Append pagination / filter query params */
  withParams(url: string, params: Record<string, string | number | boolean | undefined>): string {
    const q = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        q.set(key, String(value));
      }
    }
    const qs = q.toString();
    return qs ? `${url}${url.includes("?") ? "&" : "?"}${qs}` : url;
  }

  async get<T>(path: string, options?: FetchOptions): Promise<T> {
    const response = await fetchWithMiddleware(path, { method: "GET", ...options });
    return response.json() as Promise<T>;
  }

  async post<T>(path: string, body: unknown, options?: FetchOptions): Promise<T> {
    const response = await fetchWithMiddleware(path, {
      method: "POST",
      body: JSON.stringify(body),
      ...options,
    });
    return response.json() as Promise<T>;
  }

  async put<T>(path: string, body: unknown, options?: FetchOptions): Promise<T> {
    const response = await fetchWithMiddleware(path, {
      method: "PUT",
      body: JSON.stringify(body),
      ...options,
    });
    return response.json() as Promise<T>;
  }

  async patch<T>(path: string, body: unknown, options?: FetchOptions): Promise<T> {
    const response = await fetchWithMiddleware(path, {
      method: "PATCH",
      body: JSON.stringify(body),
      ...options,
    });
    return response.json() as Promise<T>;
  }

  async delete(path: string, options?: FetchOptions): Promise<void> {
    await fetchWithMiddleware(path, { method: "DELETE", ...options });
  }

  /** Ping a URL and return true if it responds with 2xx/3xx */
  async healthCheck(url: string, timeoutMs = 5000): Promise<boolean> {
    try {
      await fetchWithMiddleware(url, { method: "GET", timeoutMs, skipAuth: true });
      return true;
    } catch {
      return false;
    }
  }
}

export const apiClient = new ApiClient();
