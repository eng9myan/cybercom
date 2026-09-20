/**
 * Client → CyMed backend.
 *
 * The UI never talks to the Django backend directly (CORS + leaking the
 * bearer token to JS). It calls /api/cymed/* routes in this app instead,
 * which proxy server-side to process.env.CYMED_BACKEND_URL.
 *
 * There is no generic `call()`/searchRead helper here on purpose — unlike
 * cycom-erp, CyMed has no legacy Odoo-shaped RPC to emulate. Pages fetch
 * real DRF JSON directly from /api/cymed/rest/<path>/ (see app/page.tsx for
 * the pattern). This file only wraps auth, which every page needs.
 */

export type SessionUser = {
  uid: string;
  name: string;
  username: string;
  tenantId: string;
  roles: string[];
  isClinicalStaff: boolean;
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
    throw new Error(`CyMed backend ${path} -> ${res.status}: ${detail || res.statusText}`);
  }
  return res.json();
}

export async function login(login: string, password: string): Promise<SessionUser> {
  const data = (await postJson('/api/cymed/auth', { login, password })) as { user?: SessionUser; error?: string };
  if (data.error || !data.user) {
    throw new Error(data.error || 'Login failed');
  }
  return data.user;
}

export async function logout(): Promise<void> {
  await postJson('/api/cymed/logout', {});
}

export async function whoAmI(): Promise<SessionUser | null> {
  try {
    const data = (await postJson('/api/cymed/me', {})) as { user?: SessionUser };
    return data.user ?? null;
  } catch {
    return null;
  }
}
