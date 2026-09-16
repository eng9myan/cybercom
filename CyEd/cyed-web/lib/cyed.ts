// Thin client for the CyEd API (via the same-origin /api/cyed proxy).

export type Paginated<T> = { results?: T[] } | T[];

function unwrap<T>(data: Paginated<T>): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}

// Parse a response body that *should* be JSON. When the backend (or the proxy)
// returns HTML — a Django 404/500 page, a gateway error — JSON.parse would throw
// the cryptic "Unexpected token '<'". Detect that and surface a clean message.
function parseBody(text: string): { data: unknown; nonJson: boolean } {
  if (!text) return { data: null, nonJson: false };
  try {
    return { data: JSON.parse(text), nonJson: false };
  } catch {
    return { data: null, nonJson: true };
  }
}

/** Best available message from an error body, falling back to a human one. */
function errorDetail(data: unknown, status: number, path: string): string {
  if (data && typeof data === "object") {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail) return detail;
    try {
      return JSON.stringify(data);
    } catch {
      /* fall through to the generic message */
    }
  }
  return humanError(status, path);
}

function humanError(status: number, path: string): string {
  if (status === 404) return `Not found (404): /api/v1/${path} — endpoint missing or backend out of date.`;
  if (status === 401 || status === 403) return `Not authorized (${status}) for /api/v1/${path}.`;
  if (status >= 500) return `Backend error (${status}) on /api/v1/${path}.`;
  return `Request failed (${status}) on /api/v1/${path}.`;
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api/cyed/${path}`, {
    method,
    headers: { "content-type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  const { data, nonJson } = parseBody(text);
  if (!res.ok) {
    throw new Error(errorDetail(data, res.status, path));
  }
  if (nonJson) throw new Error(humanError(res.status, path));
  return data as T;
}

async function reqForm<T>(method: string, path: string, form: FormData): Promise<T> {
  const res = await fetch(`/api/cyed/${path}`, { method, body: form });
  const text = await res.text();
  const { data, nonJson } = parseBody(text);
  if (!res.ok) {
    throw new Error(errorDetail(data, res.status, path));
  }
  if (nonJson) throw new Error(humanError(res.status, path));
  return data as T;
}

export const cyed = {
  list: async <T>(path: string): Promise<T[]> => unwrap(await req<Paginated<T>>("GET", path)),
  get: <T>(path: string): Promise<T> => req<T>("GET", path),
  create: <T>(path: string, body: unknown): Promise<T> => req<T>("POST", path, body),
  patch: <T>(path: string, body: unknown): Promise<T> => req<T>("PATCH", path, body),
  action: <T>(path: string, body?: unknown): Promise<T> => req<T>("POST", path, body ?? {}),
  upload: <T>(path: string, form: FormData): Promise<T> => reqForm<T>("POST", path, form),
  remove: (path: string): Promise<unknown> => req("DELETE", path),
};

/** Direct same-origin URL to a binary backend resource (PDF, logo) via the proxy. */
export const cyedUrl = (path: string) => `/api/cyed/${path}`;
