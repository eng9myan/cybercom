/**
 * Server-only helpers for talking to the CyMed backend (Django, at
 * D:\cybercom\cymed). Used by /api/cymed/* route handlers. Never import this
 * from a client component.
 *
 * Deliberately has no Odoo-shaped model-adapter layer (unlike cycom-erp's
 * lib/cycomServer.ts) — CyMed has no legacy pre-Django UI to translate for,
 * so every page talks to real DRF endpoints directly through
 * cymedBackendProxy / the /api/cymed/rest/[...path] route.
 */

import { NextRequest, NextResponse } from 'next/server';

const CYMED_BACKEND_URL = process.env.CYMED_BACKEND_URL || 'http://localhost:8095';
const KEYCLOAK_TOKEN_URL =
  process.env.KEYCLOAK_TOKEN_URL ||
  'http://localhost:8080/realms/cybercom/protocol/openid-connect/token';
const KEYCLOAK_CLIENT_ID = process.env.KEYCLOAK_CLIENT_ID || 'cybercom-backend';
const KEYCLOAK_CLIENT_SECRET = process.env.KEYCLOAK_CLIENT_SECRET || '';
// One deployment per clinic/tenant, same reasoning as cycom-erp's
// CYCOM_TENANT_ID: a platform_admin JWT carries no tenant_id claim, so
// without this fallback header, writes get a NULL tenant and the backend
// correctly rejects them.
const CYMED_TENANT_ID = process.env.CYMED_TENANT_ID || '';
const SESSION_COOKIE = 'cymed_session_id';

export type SessionUser = {
  uid: string;
  name: string;
  username: string;
  tenantId: string;
  roles: string[];
  isClinicalStaff: boolean;
};

/** DEV/demo only: mint the unsigned dev-identity JWT core/dev_auth.py's
 * DevAuthMiddleware accepts. Shared by cymedDevLogin and the no-cookie
 * fallback below. */
function mintDevToken(): string {
  const b64 = (o: unknown) => Buffer.from(JSON.stringify(o)).toString('base64url');
  const now = Math.floor(Date.now() / 1000);
  const tenantId = process.env.CYMED_TENANT_ID || '11111111-1111-1111-1111-111111111111';
  const userId = process.env.CYMED_DEV_USER_ID || 'dev-provider';
  const claims = {
    sub: userId,
    name: 'Dr. Demo',
    email: 'demo@cymed.dev',
    tenant_id: tenantId,
    realm_access: { roles: ['physician'] },
    roles: ['physician'],
    iat: now,
    exp: now + 60 * 60 * 12,
  };
  return `${b64({ alg: 'none', typ: 'JWT' })}.${b64(claims)}.dev`;
}

function getSessionId(req: NextRequest): string | null {
  const cookie = req.cookies.get(SESSION_COOKIE)?.value;
  if (cookie) return cookie;
  // DEV/demo only: with no session cookie, fall back to the dev identity so
  // client-side BFF calls work without first bouncing through
  // /api/cymed/dev-login. Never active unless CYMED_DEV_AUTH=1.
  if (process.env.CYMED_DEV_AUTH === '1') return mintDevToken();
  return null;
}

function applySessionCookie(res: NextResponse, token: string): void {
  res.cookies.set({
    name: SESSION_COOKIE,
    value: token,
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
  });
}

/** Unverified decode for display purposes only — every real API call still
 * gets verified server-side by Django's JWKS check (or, in dev, by
 * core/dev_auth.py's explicit DEBUG + CYMED_DEV_AUTH=1 gate). */
function decodeJwtPayload(token: string): Record<string, any> {
  const part = token.split('.')[1] ?? '';
  const b64 = part.replace(/-/g, '+').replace(/_/g, '/');
  const json = Buffer.from(b64, 'base64').toString('utf-8');
  return JSON.parse(json);
}

function userFromClaims(claims: Record<string, any>): SessionUser {
  const roles: string[] = claims.roles || claims.realm_access?.roles || [];
  return {
    uid: claims.sub,
    name: claims.name || claims.preferred_username || claims.email || 'Unknown',
    username: claims.email || claims.preferred_username || claims.sub,
    tenantId: claims.tenant_id || '',
    roles,
    isClinicalStaff: roles.length > 0,
  };
}

export async function cymedAuthenticate(login: string, password: string): Promise<{
  res: NextResponse;
  user?: SessionUser;
  error?: string;
}> {
  try {
    const params = new URLSearchParams();
    params.append('grant_type', 'password');
    params.append('client_id', KEYCLOAK_CLIENT_ID);
    if (KEYCLOAK_CLIENT_SECRET) params.append('client_secret', KEYCLOAK_CLIENT_SECRET);
    params.append('username', login);
    params.append('password', password);

    const upstream = await fetch(KEYCLOAK_TOKEN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString(),
    });

    const payload = await upstream.json();

    if (!upstream.ok) {
      const errorMsg = payload.error_description || payload.error || 'Authentication failed';
      const res = NextResponse.json({ error: errorMsg }, { status: upstream.status });
      return { res, error: errorMsg };
    }

    const accessToken = payload.access_token as string;
    const claims = decodeJwtPayload(accessToken);
    const user = userFromClaims(claims);

    const res = NextResponse.json({ user });
    applySessionCookie(res, accessToken);
    return { res, user };
  } catch (err: any) {
    const msg = err.message || 'Failed to connect to Keycloak';
    const res = NextResponse.json({ error: msg }, { status: 500 });
    return { res, error: msg };
  }
}

/**
 * DEV-ONLY login. Mints an UNSIGNED, well-formed JWT and sets it as the
 * session cookie. core/dev_auth.py's DevAuthMiddleware reads these claims
 * without verifying the signature, so no Keycloak is needed. Gated behind
 * CYMED_DEV_AUTH so it cannot be hit in a normal deployment.
 */
export function cymedDevLogin(): NextResponse {
  if (process.env.CYMED_DEV_AUTH !== '1') {
    return NextResponse.json({ error: 'Dev login disabled' }, { status: 403 });
  }
  const token = mintDevToken();
  const res = NextResponse.redirect(
    new URL('/', process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:7100'),
  );
  applySessionCookie(res, token);
  return res;
}

export async function cymedLogout(): Promise<NextResponse> {
  const res = NextResponse.json({ ok: true });
  res.cookies.delete(SESSION_COOKIE);
  return res;
}

export async function cymedGetSession(req: NextRequest): Promise<NextResponse> {
  const sessionId = getSessionId(req);
  if (!sessionId) {
    return NextResponse.json({ user: null });
  }
  try {
    const claims = decodeJwtPayload(sessionId);
    if (claims.exp && claims.exp * 1000 < Date.now()) {
      const res = NextResponse.json({ user: null });
      res.cookies.delete(SESSION_COOKIE);
      return res;
    }
    return NextResponse.json({ user: userFromClaims(claims) });
  } catch {
    const res = NextResponse.json({ user: null });
    res.cookies.delete(SESSION_COOKIE);
    return res;
  }
}

function resolveTenantId(token: string): string {
  try {
    const claims = decodeJwtPayload(token);
    if (claims.tenant_id) return String(claims.tenant_id);
  } catch {
    // fall through to the env var
  }
  return CYMED_TENANT_ID;
}

async function backendFetch(path: string, token: string, init: RequestInit = {}) {
  const tenantId = resolveTenantId(token);
  return fetch(`${CYMED_BACKEND_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(tenantId ? { 'X-Tenant-ID': tenantId } : {}),
      ...(init.headers || {}),
    },
  });
}

/**
 * Generic authenticated passthrough to a real /api/v1/* backend route.
 * Forwards method, query string, and JSON body; injects the bearer token +
 * tenant header. This is the ONLY data-fetching pattern in this app.
 */
export async function cymedBackendProxy(
  req: NextRequest,
  targetPath: string,
): Promise<NextResponse> {
  const sessionId = getSessionId(req);
  if (!sessionId) {
    return NextResponse.json({ error: { message: 'Not authenticated' } }, { status: 401 });
  }
  const method = req.method.toUpperCase();
  const init: RequestInit = { method };
  if (method !== 'GET' && method !== 'DELETE') {
    const text = await req.text();
    if (text) init.body = text;
  }
  try {
    const upstream = await backendFetch(targetPath, sessionId, init);
    const payload = await upstream.json().catch(() => ({}));
    return NextResponse.json(payload, { status: upstream.status });
  } catch (err: any) {
    return NextResponse.json(
      { error: { message: err.message || 'Backend connection error' } },
      { status: 500 },
    );
  }
}
