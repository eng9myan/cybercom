const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.cy-com.com";

export interface ApiClientConfig {
  baseUrl?: string;
  accessToken?: string;
}

export interface ApiResponse<T> {
  data: T;
  count?: number;
  next?: string | null;
  previous?: string | null;
}

export interface ApiError {
  status: number;
  errors: Record<string, string[]>;
}

export class CyberComApiClient {
  private baseUrl: string;
  private accessToken?: string;

  constructor(config: ApiClientConfig = {}) {
    this.baseUrl = (config.baseUrl ?? DEFAULT_BASE_URL).replace(/\/$/, "");
    this.accessToken = config.accessToken;
  }

  private buildHeaders(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    return headers;
  }

  async get<T>(path: string, params?: Record<string, string | number | boolean | undefined>, isPublic = true): Promise<T> {
    const prefix = isPublic ? "/api/v1/public" : "/api/v1";
    const url = new URL(`${this.baseUrl}${prefix}${path}`);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") {
          url.searchParams.set(k, String(v));
        }
      });
    }
    const res = await fetch(url.toString(), {
      headers: this.buildHeaders(),
      next: { revalidate: isPublic ? 300 : 0 },
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw { status: res.status, errors: body.errors ?? {} } as ApiError;
    }
    return res.json() as Promise<T>;
  }

  async post<T>(path: string, body: unknown, isPublic = true): Promise<T> {
    const prefix = isPublic ? "/api/v1/public" : "/api/v1";
    const res = await fetch(`${this.baseUrl}${prefix}${path}`, {
      method: "POST",
      headers: this.buildHeaders(),
      body: JSON.stringify(body),
      credentials: "include",
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw { status: res.status, errors: errBody.errors ?? {} } as ApiError;
    }
    return res.json() as Promise<T>;
  }

  async put<T>(path: string, body: unknown, isPublic = false): Promise<T> {
    const prefix = isPublic ? "/api/v1/public" : "/api/v1";
    const res = await fetch(`${this.baseUrl}${prefix}${path}`, {
      method: "PUT",
      headers: this.buildHeaders(),
      body: JSON.stringify(body),
      credentials: "include",
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw { status: res.status, errors: errBody.errors ?? {} } as ApiError;
    }
    return res.json() as Promise<T>;
  }

  async delete<T>(path: string, isPublic = false): Promise<T> {
    const prefix = isPublic ? "/api/v1/public" : "/api/v1";
    const res = await fetch(`${this.baseUrl}${prefix}${path}`, {
      method: "DELETE",
      headers: this.buildHeaders(),
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw { status: res.status, errors: errBody.errors ?? {} } as ApiError;
    }
    return res.json().catch(() => ({})) as Promise<T>;
  }
}

export const apiClient = new CyberComApiClient();
