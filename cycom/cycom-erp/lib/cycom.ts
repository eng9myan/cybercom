/**
 * Cycom → Cycom client.
 *
 * The Next.js UI does NOT speak to Cycom directly (that would mean CORS gymnastics + leaking
 * session_id to JS). Instead it calls /api/cycom/* routes in this very app, which proxy server-side
 * to the Cycom container at process.env.CYCOM_BACKEND_URL.
 *
 * Keep this client minimal and typed. Every business-logic call should go through one of these
 * helpers so the surface area stays auditable.
 */

export type CycomCall = {
  model: string;
  method: string;
  args?: unknown[];
  kwargs?: Record<string, unknown>;
};

export type SessionUser = {
  uid: number;
  name: string;
  username: string;
  partner_id: number;
  company_id: number;
  is_admin: boolean;
};

async function postJson(path: string, body: unknown): Promise<unknown> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`Cycom backend ${path} → ${res.status}: ${detail || res.statusText}`);
  }
  return res.json();
}

export async function login(db: string, login: string, password: string): Promise<SessionUser> {
  const data = (await postJson('/api/cycom/auth', { db, login, password })) as { user?: SessionUser; error?: string };
  if (data.error || !data.user) {
    throw new Error(data.error || 'Login failed');
  }
  return data.user;
}

export async function logout(): Promise<void> {
  await postJson('/api/cycom/logout', {});
}

export async function whoAmI(): Promise<SessionUser | null> {
  try {
    const data = (await postJson('/api/cycom/me', {})) as { user?: SessionUser };
    return data.user ?? null;
  } catch {
    return null;
  }
}

export async function call<T = unknown>(c: CycomCall): Promise<T> {
  const data = (await postJson('/api/cycom/call', c)) as { result?: T; error?: { message: string } };
  if (data.error) throw new Error(data.error.message);
  return data.result as T;
}

/** Convenience: model.search_read */
export function searchRead<T = Record<string, unknown>>(
  model: string,
  domain: unknown[] = [],
  fields: string[] = [],
  opts: { limit?: number; offset?: number; order?: string } = {},
): Promise<T[]> {
  return call<T[]>({
    model,
    method: 'search_read',
    args: [domain, fields],
    kwargs: { limit: opts.limit ?? 100, offset: opts.offset ?? 0, order: opts.order },
  });
}

/** Convenience: model.write */
export function write(model: string, ids: number[], values: Record<string, unknown>): Promise<boolean> {
  return call<boolean>({ model, method: 'write', args: [ids, values] });
}

/** Convenience: model.create */
export function create(model: string, values: Record<string, unknown>): Promise<number> {
  return call<number>({ model, method: 'create', args: [values] });
}

/** Convenience: model.unlink */
export function unlink(model: string, ids: number[]): Promise<boolean> {
  return call<boolean>({ model, method: 'unlink', args: [ids] });
}
