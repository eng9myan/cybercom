/**
 * Thin fetch wrapper for CyberCom backends. Matches the API conventions
 * from docs/api/API_STANDARDS.md: RFC 7807 error bodies, cursor pagination
 * envelope, Idempotency-Key header on writes, Bearer auth.
 */

export class ApiError extends Error {
  status: number;
  problem: ProblemDetail | null;

  constructor(status: number, problem: ProblemDetail | null, message: string) {
    super(message);
    this.status = status;
    this.problem = problem;
  }
}

export interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string | null;
  code?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    next_cursor: string | null;
    previous_cursor: string | null;
    has_more: boolean;
    count: number;
    limit: number;
  };
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  accessToken?: string | null;
  idempotencyKey?: string;
  query?: Record<string, string | number | boolean | undefined>;
  // CyID ecosystem, Phase 9 — cymed's tenant-scoped endpoints (orders,
  // consents, ...) require X-Tenant-ID; CyID/wallet endpoints don't
  // (person-scoped, not tenant-scoped) — optional, same pattern as
  // accessToken, so existing callers are unaffected.
  tenantId?: string | null;
}

function buildUrl(baseUrl: string, path: string, query?: RequestOptions["query"]): string {
  const trimmedBase = baseUrl.replace(/\/+$/, "");
  const trimmedPath = path.replace(/^\/+/, "");
  let url = `${trimmedBase}/${trimmedPath}`;

  if (query) {
    const params = Object.entries(query)
      .filter(([, value]) => value !== undefined)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
    if (params.length > 0) url += `?${params.join("&")}`;
  }
  return url;
}

export async function apiRequest<T>(
  baseUrl: string,
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, accessToken, idempotencyKey, query, tenantId } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
  if (tenantId) headers["X-Tenant-ID"] = tenantId;

  const response = await fetch(buildUrl(baseUrl, path, query), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const text = await response.text();
  const parsed = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const problem: ProblemDetail | null =
      parsed && typeof parsed === "object" && "status" in parsed ? (parsed as ProblemDetail) : null;
    throw new ApiError(
      response.status,
      problem,
      problem?.detail ?? `Request failed with status ${response.status}`
    );
  }

  return parsed as T;
}
