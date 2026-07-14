/**
 * CyberCom API Middleware
 * Handles: JWT attachment, token refresh, error normalisation, retry with backoff
 */

import { tokenStore } from "../auth/tokens.js";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface ApiError {
  status: number;
  code: string;
  message: string;
  detail?: unknown;
  requestId?: string;
}

export class CyberComApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly detail?: unknown;
  readonly requestId?: string;

  constructor(err: ApiError) {
    super(err.message);
    this.name = "CyberComApiError";
    this.status = err.status;
    this.code = err.code;
    this.detail = err.detail;
    this.requestId = err.requestId;
  }
}

export interface RetryConfig {
  maxAttempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryOn: number[];
}

const DEFAULT_RETRY: RetryConfig = {
  maxAttempts: 3,
  baseDelayMs: 300,
  maxDelayMs: 5000,
  retryOn: [429, 502, 503, 504],
};

// ─── JWT Middleware ─────────────────────────────────────────────────────────

export function attachJwt(headers: Record<string, string>): Record<string, string> {
  const token = tokenStore.getAccessToken();
  if (token) {
    return { ...headers, Authorization: `Bearer ${token}` };
  }
  return headers;
}

// ─── Token Refresh ──────────────────────────────────────────────────────────

let refreshPromise: Promise<void> | null = null;

async function ensureFreshToken(): Promise<void> {
  if (!tokenStore.isExpired()) return;

  if (!refreshPromise) {
    refreshPromise = tokenStore.refresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

// ─── Error Normalisation ────────────────────────────────────────────────────

async function normaliseError(response: Response): Promise<CyberComApiError> {
  let body: Record<string, unknown> = {};
  try {
    body = (await response.json()) as Record<string, unknown>;
  } catch {
    // response body is not JSON
  }

  return new CyberComApiError({
    status: response.status,
    code: (body["code"] as string) ?? `HTTP_${response.status}`,
    message:
      (body["message"] as string) ??
      (body["detail"] as string) ??
      response.statusText ??
      "Unknown error",
    detail: body["detail"],
    requestId: response.headers.get("X-Request-Id") ?? undefined,
  });
}

// ─── Retry Logic ────────────────────────────────────────────────────────────

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function backoff(attempt: number, config: RetryConfig): number {
  const jitter = Math.random() * 100;
  const base = config.baseDelayMs * Math.pow(2, attempt - 1) + jitter;
  return Math.min(base, config.maxDelayMs);
}

// ─── Core Fetch with Middleware ─────────────────────────────────────────────

export interface FetchOptions extends RequestInit {
  timeoutMs?: number;
  retry?: Partial<RetryConfig>;
  skipAuth?: boolean;
}

export async function fetchWithMiddleware(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeoutMs = 30000, retry = {}, skipAuth = false, ...init } = options;
  const retryConfig: RetryConfig = { ...DEFAULT_RETRY, ...retry };

  if (!skipAuth) {
    await ensureFreshToken();
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(init.headers as Record<string, string>),
  };

  const finalHeaders = skipAuth ? headers : attachJwt(headers);

  let lastError: CyberComApiError | null = null;

  for (let attempt = 1; attempt <= retryConfig.maxAttempts; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...init,
        headers: finalHeaders,
        signal: controller.signal,
      });

      clearTimeout(timer);

      // Handle 401 — attempt token refresh and retry once
      if (response.status === 401 && !skipAuth && attempt === 1) {
        await tokenStore.refresh();
        const freshHeaders = attachJwt(finalHeaders);
        const retried = await fetch(url, { ...init, headers: freshHeaders });
        if (retried.ok) return retried;
        throw await normaliseError(retried);
      }

      if (!response.ok) {
        const err = await normaliseError(response);

        if (retryConfig.retryOn.includes(response.status) && attempt < retryConfig.maxAttempts) {
          lastError = err;
          await delay(backoff(attempt, retryConfig));
          continue;
        }

        throw err;
      }

      return response;
    } catch (err) {
      clearTimeout(timer);

      if (err instanceof CyberComApiError) throw err;

      if (err instanceof DOMException && err.name === "AbortError") {
        throw new CyberComApiError({
          status: 0,
          code: "TIMEOUT",
          message: `Request timed out after ${timeoutMs}ms`,
        });
      }

      if (attempt < retryConfig.maxAttempts) {
        await delay(backoff(attempt, retryConfig));
        continue;
      }

      throw new CyberComApiError({
        status: 0,
        code: "NETWORK_ERROR",
        message: err instanceof Error ? err.message : "Network request failed",
      });
    }
  }

  throw lastError ?? new CyberComApiError({ status: 0, code: "UNKNOWN", message: "Request failed" });
}
