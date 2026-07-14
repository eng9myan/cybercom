/**
 * Server-only helpers for talking to the FastAPI backend.
 * Used by /api/cycom/* route handlers. Never import this from a client component.
 */

import { NextRequest, NextResponse } from 'next/server';

const CYCOM_BACKEND_URL = process.env.CYCOM_BACKEND_URL || 'http://localhost:8000';
const SESSION_COOKIE = 'cycom_session_id';

function getSessionId(req: NextRequest): string | null {
  return req.cookies.get(SESSION_COOKIE)?.value ?? null;
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

export async function cycomAuthenticate(login: string, password: string, db?: string): Promise<{
  res: NextResponse;
  user?: { uid: number; name: string; username: string; partner_id: number; company_id: number; is_admin: boolean };
  error?: string;
}> {
  try {
    const params = new URLSearchParams();
    params.append('username', login);
    params.append('password', password);

    const upstream = await fetch(`${CYCOM_BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString(),
    });

    const payload = await upstream.json();

    if (!upstream.ok) {
      const errorMsg = payload.detail || 'Authentication failed';
      const res = NextResponse.json({ error: errorMsg }, { status: upstream.status });
      return { res, error: errorMsg };
    }

    const user = {
      uid: payload.user.id as number,
      name: payload.user.full_name ?? '',
      username: payload.user.email ?? login,
      partner_id: payload.user.id as number,
      company_id: payload.user.company_id || 1,
      is_admin: Boolean(payload.user.is_superuser),
    };

    const res = NextResponse.json({ user });
    applySessionCookie(res, payload.access_token);
    return { res, user };
  } catch (err: any) {
    const msg = err.message || 'Failed to connect to FastAPI backend';
    const res = NextResponse.json({ error: msg }, { status: 500 });
    return { res, error: msg };
  }
}

export async function cycomCallKw(req: NextRequest, body: { model: string; method: string; args?: unknown[]; kwargs?: Record<string, unknown> }): Promise<NextResponse> {
  const sessionId = getSessionId(req);
  if (!sessionId) {
    return NextResponse.json({ error: { message: 'Not authenticated' } }, { status: 401 });
  }

  try {
    const upstream = await fetch(`${CYCOM_BACKEND_URL}/api/rpc`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionId}`,
      },
      body: JSON.stringify({
        model: body.model,
        method: body.method,
        args: body.args || [],
        kwargs: body.kwargs || {},
      }),
    });

    const payload = await upstream.json();
    if (!upstream.ok) {
      return NextResponse.json({ error: { message: payload.detail || 'RPC Call failed' } }, { status: upstream.status });
    }

    return NextResponse.json({ result: payload });
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || 'RPC Connection error' } }, { status: 500 });
  }
}

export async function cycomLogout(req: NextRequest): Promise<NextResponse> {
  const res = NextResponse.json({ ok: true });
  res.cookies.delete(SESSION_COOKIE);
  return res;
}

export async function cycomGetSession(req: NextRequest): Promise<NextResponse> {
  const sessionId = getSessionId(req);
  if (!sessionId) {
    return NextResponse.json({ user: null });
  }

  try {
    const upstream = await fetch(`${CYCOM_BACKEND_URL}/api/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${sessionId}`,
      },
    });

    if (!upstream.ok) {
      const res = NextResponse.json({ user: null });
      res.cookies.delete(SESSION_COOKIE);
      return res;
    }

    const u = await upstream.json();
    return NextResponse.json({
      user: {
        uid: u.id,
        name: u.full_name,
        username: u.email,
        partner_id: u.id,
        company_id: u.company_id || 1,
        is_admin: u.is_superuser,
      },
    });
  } catch {
    const res = NextResponse.json({ user: null });
    res.cookies.delete(SESSION_COOKIE);
    return res;
  }
}

