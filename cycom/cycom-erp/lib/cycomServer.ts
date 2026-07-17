/**
 * Server-only helpers for talking to the real Cycom backend (Django, at
 * D:\cybercom\cycom — see Phase B of the rebuild plan). Used by /api/cycom/*
 * route handlers. Never import this from a client component.
 *
 * Auth is real Keycloak password-grant against the shared "cybercom" realm
 * bootstrapped in Phase A — no more per-request `db` selector, no more
 * fake core-kernel session tokens.
 */

import { NextRequest, NextResponse } from 'next/server';

const CYCOM_BACKEND_URL = process.env.CYCOM_BACKEND_URL || 'http://localhost:8090';
const KEYCLOAK_TOKEN_URL =
  process.env.KEYCLOAK_TOKEN_URL ||
  'http://localhost:8080/realms/cybercom/protocol/openid-connect/token';
const KEYCLOAK_CLIENT_ID = process.env.KEYCLOAK_CLIENT_ID || 'cybercom-backend';
const KEYCLOAK_CLIENT_SECRET = process.env.KEYCLOAK_CLIENT_SECRET || '';
// cycom-erp is a per-tenant back-office app (one deployment per business), so
// unlike the cross-tenant admin panel it always operates inside one fixed
// tenant. A platform_admin JWT alone carries no tenant_id — without this
// header, writes get a NULL tenant_id and the backend correctly rejects them.
const CYCOM_TENANT_ID = process.env.CYCOM_TENANT_ID || '';
const SESSION_COOKIE = 'cycom_session_id'; // now holds a real Keycloak access token

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

/** Unverified decode for display purposes only — every real API call still gets verified server-side by Django's JWKS check. */
function decodeJwtPayload(token: string): Record<string, any> {
  const part = token.split('.')[1] ?? '';
  const b64 = part.replace(/-/g, '+').replace(/_/g, '/');
  const json = Buffer.from(b64, 'base64').toString('utf-8');
  return JSON.parse(json);
}

export async function cycomAuthenticate(login: string, password: string): Promise<{
  res: NextResponse;
  user?: { uid: string; name: string; username: string; partner_id: string; company_id: number; is_admin: boolean };
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
    const roles: string[] = claims.realm_access?.roles || [];

    const user = {
      uid: claims.sub as string,
      name: (claims.name as string) || (claims.preferred_username as string) || login,
      username: (claims.email as string) || login,
      partner_id: claims.sub as string,
      company_id: 1,
      is_admin: roles.includes('platform_admin') || roles.includes('tenant_admin'),
    };

    const res = NextResponse.json({ user });
    applySessionCookie(res, accessToken);
    return { res, user };
  } catch (err: any) {
    const msg = err.message || 'Failed to connect to Keycloak';
    const res = NextResponse.json({ error: msg }, { status: 500 });
    return { res, error: msg };
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
    const claims = decodeJwtPayload(sessionId);
    if (claims.exp && claims.exp * 1000 < Date.now()) {
      const res = NextResponse.json({ user: null });
      res.cookies.delete(SESSION_COOKIE);
      return res;
    }
    const roles: string[] = claims.realm_access?.roles || [];
    return NextResponse.json({
      user: {
        uid: claims.sub,
        name: claims.name || claims.preferred_username,
        username: claims.email || claims.preferred_username,
        partner_id: claims.sub,
        company_id: 1,
        is_admin: roles.includes('platform_admin') || roles.includes('tenant_admin'),
      },
    });
  } catch {
    const res = NextResponse.json({ user: null });
    res.cookies.delete(SESSION_COOKIE);
    return res;
  }
}

// ---------------------------------------------------------------------------
// CyAI Local Memory Agent — real, genuinely new REST endpoint (not part of
// the legacy Odoo-shaped {model,method,args,kwargs} shim below), so it gets
// its own thin proxy straight through to the Django backend.
// ---------------------------------------------------------------------------

export async function cycomAskLocalMemory(req: NextRequest, question: string): Promise<NextResponse> {
  const sessionId = getSessionId(req);
  if (!sessionId) {
    return NextResponse.json({ error: { message: 'Not authenticated' } }, { status: 401 });
  }
  try {
    const upstream = await backendFetch('/api/v1/cyai-memory/plans/ask/', sessionId, {
      method: 'POST',
      body: JSON.stringify({ question }),
    });
    const payload = await upstream.json();
    if (!upstream.ok) {
      return NextResponse.json({ error: { message: payload.detail || 'Ask failed' } }, { status: upstream.status });
    }
    return NextResponse.json(payload);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || 'Backend connection error' } }, { status: 500 });
  }
}

// ---------------------------------------------------------------------------
// REST proxy — translates the legacy Odoo-shaped {model, method, args, kwargs}
// calls the UI still makes into real requests against the new Django REST API.
// Only models with a real backend + a settled field mapping are wired here;
// everything else returns a clear "not migrated" error instead of silently
// faking data. See the Phase B step 8 plan note for what's still pending.
// ---------------------------------------------------------------------------

type ModelAdapter = {
  basePath: string; // e.g. /api/v1/crm/leads/
  toBackend: (fields: Record<string, unknown>) => Record<string, unknown>;
  fromBackend: (row: Record<string, unknown>) => Record<string, unknown>;
  // Custom RPC-style methods (e.g. 'approve', 'reject') beyond the standard
  // search_read/create/write/unlink/read set — mapped to a POST action route.
  customActions?: Record<string, (args: unknown[]) => { path: string; body?: unknown }>;
};

const STAGE_UI_TO_BACKEND: Record<string, string> = {
  New: 'new',
  Qualified: 'qualified',
  Proposition: 'proposal',
  Won: 'won',
  Lost: 'lost',
};
const STAGE_BACKEND_TO_UI: Record<string, string> = {
  new: 'New',
  contacted: 'New',
  qualified: 'Qualified',
  proposal: 'Proposition',
  won: 'Won',
  lost: 'Lost',
};

const MODEL_ADAPTERS: Record<string, ModelAdapter> = {
  'crm.lead': {
    basePath: '/api/v1/crm/leads/',
    toBackend: (f) => {
      const out: Record<string, unknown> = {};
      if ('partner_name' in f) out.name = f.partner_name;
      if ('expected_revenue' in f) out.estimated_value = f.expected_revenue;
      if ('probability' in f) out.probability = f.probability;
      if ('email_from' in f) out.email = f.email_from || '';
      if ('stage' in f) out.stage = f.stage;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      partner_name: r.name,
      contact_name: r.contact_name,
      expected_revenue: Number(r.estimated_value || 0),
      probability: Number(r.probability || 0),
      stage_id: [1, STAGE_BACKEND_TO_UI[r.stage as string] || 'New'],
      email_from: r.email || false,
    }),
  },
  'hr.employee': {
    basePath: '/api/v1/hr/employees/',
    toBackend: (f) => {
      const out: Record<string, unknown> = {};
      if ('name' in f) {
        const parts = String(f.name).trim().split(/\s+/);
        out.first_name = parts[0] || '';
        out.last_name = parts.slice(1).join(' ') || '';
      }
      if ('work_email' in f) out.email = f.work_email || '';
      if ('work_phone' in f) out.phone = f.work_phone || '';
      if ('job_title' in f) out.job_title = f.job_title || '';
      if ('department_id' in f && Array.isArray(f.department_id)) out.department = f.department_id[1];
      if ('employee_number' in f) out.employee_number = f.employee_number;
      if ('hire_date' in f) out.hire_date = f.hire_date;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      name: `${r.first_name || ''} ${r.last_name || ''}`.trim() || '—',
      work_email: r.email || false,
      work_phone: r.phone || false,
      // No separate work-location concept in the new backend yet — surface
      // department for both fields rather than fabricating a location.
      work_location_id: r.department ? [1, r.department as string] : false,
      department_id: r.department ? [1, r.department as string] : false,
      job_title: r.job_title || false,
      create_date: r.hire_date ? `${r.hire_date} 00:00:00` : undefined,
      employee_number: r.employee_number,
    }),
  },
  'account.move': {
    basePath: '/api/v1/accounting/journal-entries/',
    toBackend: (f) => {
      const out: Record<string, unknown> = {};
      // Only the bulk-draft-reset mutation is used against this model today.
      if ('state' in f) out.status = f.state;
      return out;
    },
    fromBackend: (r) => {
      const lines = Array.isArray(r.lines) ? (r.lines as Array<Record<string, unknown>>) : [];
      const total = lines.reduce((sum, l) => sum + Number(l.debit || 0), 0);
      return {
        id: r.id,
        name: r.reference || null,
        ref: false,
        journal_id: [1, 'General'],
        partner_id: false,
        date: r.date,
        amount_total: total,
        state: r.status,
        currency_id: [1, r.currency as string],
      };
    },
  },
  'cy.vendor': {
    basePath: '/api/v1/ar-ap/partners/',
    toBackend: (f) => {
      const out: Record<string, unknown> = { partner_type: 'vendor' };
      const direct = [
        'category', 'cr_number', 'cr_expiry', 'bank_name', 'bank_branch',
        'iban', 'swift_code', 'credit_limit', 'payment_terms_days',
        'contact_name', 'address', 'city', 'approval_status',
      ];
      for (const key of direct) {
        if (key in f) out[key] = f[key as keyof typeof f];
      }
      if ('legal_name' in f) out.name = f.legal_name;
      if ('legal_name_ar' in f) out.legal_name_ar = f.legal_name_ar;
      if ('trade_name' in f) out.trade_name = f.trade_name;
      if ('tax_number' in f) out.tax_id = f.tax_number;
      if ('contact_email' in f) out.email = f.contact_email;
      if ('contact_phone' in f) out.phone = f.contact_phone;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      legal_name: r.name,
      legal_name_ar: r.legal_name_ar || undefined,
      trade_name: r.trade_name || undefined,
      vendor_code: undefined,
      category: r.category,
      cr_number: r.cr_number || undefined,
      cr_expiry: r.cr_expiry || undefined,
      tax_number: r.tax_id || undefined,
      bank_name: r.bank_name || undefined,
      bank_branch: r.bank_branch || undefined,
      iban: r.iban || undefined,
      swift_code: r.swift_code || undefined,
      payment_terms_days: r.payment_terms_days,
      credit_limit: r.credit_limit ? Number(r.credit_limit) : undefined,
      contact_name: r.contact_name || undefined,
      contact_email: r.email || undefined,
      contact_phone: r.phone || undefined,
      address: r.address || undefined,
      city: r.city || undefined,
      approval_status: r.approval_status,
      rejection_reason: r.rejection_reason || undefined,
    }),
    customActions: {
      approve: (args) => ({ path: `/api/v1/ar-ap/partners/${args[0]}/approve/` }),
      reject: (args) => ({ path: `/api/v1/ar-ap/partners/${args[0]}/reject/`, body: { reason: args[1] } }),
      submit_for_review: (args) => ({ path: `/api/v1/ar-ap/partners/${args[0]}/submit/` }),
    },
  },
};

async function backendFetch(path: string, token: string, init: RequestInit = {}) {
  return fetch(`${CYCOM_BACKEND_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(CYCOM_TENANT_ID ? { 'X-Tenant-ID': CYCOM_TENANT_ID } : {}),
      ...(init.headers || {}),
    },
  });
}

function jsonError(message: string, status = 400) {
  return NextResponse.json({ error: { message } }, { status });
}

async function handleInventoryProductSearch(
  sessionId: string,
  body: { args?: unknown[] },
): Promise<NextResponse> {
  const domain = (body.args?.[0] as Array<[string, string, string]>) || [];
  const nameFilter = domain.find((d) => d[0] === 'name')?.[2]?.replace(/%/g, '').toLowerCase();

  const upstream = await backendFetch('/api/v1/inventory/products/', sessionId, { method: 'GET' });
  const payload = await upstream.json();
  if (!upstream.ok) return jsonError(payload.detail || 'Fetch failed', upstream.status);

  let rows = (payload.results || payload) as Array<Record<string, unknown>>;
  if (nameFilter) {
    rows = rows.filter((r) => String(r.name).toLowerCase().includes(nameFilter));
  }
  return NextResponse.json({
    result: rows.map((r) => ({ id: r.id, name: r.name, code: r.sku })),
  });
}

// Legacy internal-order pages never expose warehouse selection — they only
// ever operated against one implicit "central warehouse -> branch" pair.
// Cache resolution per request; first two warehouses by code, deterministic.
async function _resolveDefaultWarehouses(sessionId: string) {
  const upstream = await backendFetch('/api/v1/inventory/warehouses/', sessionId, { method: 'GET' });
  const payload = await upstream.json();
  const rows = (payload.results || payload) as Array<{ id: string; code: string }>;
  if (rows.length < 2) {
    throw new Error(
      `Need at least 2 warehouses (source + destination) for branch replenishment; found ${rows.length}.`,
    );
  }
  // Replenishment always flows central warehouse -> branch. Plain
  // alphabetical sort picked "WH-BR1" before "WH-MAIN" (B < M) and sent
  // stock backwards — look for "main"/"central" in the code first.
  const isCentral = (code: string) => /main|central|hq/i.test(code);
  const central = rows.find((r) => isCentral(r.code));
  const others = rows.filter((r) => r.id !== central?.id);
  const source = central ?? [...rows].sort((a, b) => a.code.localeCompare(b.code))[0]!;
  const destination = (central ? others[0] : rows.filter((r) => r.id !== source.id)[0])!;
  return { source: source.id, destination: destination.id };
}

async function handleInternalOrderCall(
  sessionId: string,
  body: { model: string; method: string; args?: unknown[]; kwargs?: Record<string, unknown> },
): Promise<NextResponse> {
  const basePath = '/api/v1/inventory/internal-orders/';
  const linesPath = '/api/v1/inventory/internal-order-lines/';

  try {
    if (body.model === 'cy.internal.order') {
      if (body.method === 'search_read') {
        const domain = (body.args?.[0] as unknown[]) || [];
        const stateIn = domain.find(
          (d) => Array.isArray(d) && d[0] === 'state' && d[1] === 'in',
        ) as [string, string, string[]] | undefined;
        const query = stateIn ? `?status__in=${stateIn[2].join(',')}` : '';
        const upstream = await backendFetch(`${basePath}${query}`, sessionId, { method: 'GET' });
        const payload = await upstream.json();
        if (!upstream.ok) return jsonError(payload.detail || 'Fetch failed', upstream.status);
        const rows = (payload.results || payload) as Array<Record<string, unknown>>;
        return NextResponse.json({
          result: rows.map((r) => ({
            id: r.id,
            name: r.number,
            branch_id: 1, // legacy UI has no real per-order branch concept
            required_date: r.required_date,
            priority: r.priority,
            state: r.status,
            notes: r.notes,
          })),
        });
      }

      if (body.method === 'read') {
        const id = (body.args || [])[0];
        const upstream = await backendFetch(`${basePath}${id}/`, sessionId, { method: 'GET' });
        const payload = await upstream.json();
        if (!upstream.ok) return jsonError(payload.detail || 'Fetch failed', upstream.status);
        return NextResponse.json({
          result: {
            id: payload.id,
            name: payload.number,
            branch_id: 1,
            required_date: payload.required_date,
            notes: payload.notes,
            state: payload.status,
          },
        });
      }

      if (body.method === 'create') {
        const values = (body.args?.[0] as Record<string, unknown>) || {};
        const { source, destination } = await _resolveDefaultWarehouses(sessionId);
        const upstream = await backendFetch(basePath, sessionId, {
          method: 'POST',
          body: JSON.stringify({
            number: values.name,
            source_warehouse: source,
            destination_warehouse: destination,
            required_date: values.required_date || null,
            priority: values.priority || 'normal',
            notes: values.notes || '',
          }),
        });
        const payload = await upstream.json();
        if (!upstream.ok) return jsonError(payload.detail || JSON.stringify(payload), upstream.status);
        return NextResponse.json({ result: payload.id });
      }

      const customActions: Record<string, () => Promise<NextResponse>> = {
        submit_for_review: async () => {
          const id = (body.args || [])[0];
          const upstream = await backendFetch(`${basePath}${id}/submit/`, sessionId, { method: 'POST' });
          const payload = await upstream.json().catch(() => ({}));
          if (!upstream.ok) return jsonError(payload.detail || JSON.stringify(payload), upstream.status);
          return NextResponse.json({ result: true });
        },
        allocate_items: async () => {
          const [id, allocations] = body.args || [];
          const upstream = await backendFetch(`${basePath}${id}/allocate/`, sessionId, {
            method: 'POST',
            body: JSON.stringify({ allocations }),
          });
          const payload = await upstream.json().catch(() => ({}));
          if (!upstream.ok) return jsonError(payload.detail || JSON.stringify(payload), upstream.status);
          return NextResponse.json({ result: true });
        },
        dispatch_order: async () => {
          const id = (body.args || [])[0];
          const upstream = await backendFetch(`${basePath}${id}/dispatch/`, sessionId, { method: 'POST' });
          const payload = await upstream.json().catch(() => ({}));
          if (!upstream.ok) return jsonError(payload.detail || JSON.stringify(payload), upstream.status);
          return NextResponse.json({ result: true });
        },
        receive_order: async () => {
          const [id, receipts] = body.args || [];
          const upstream = await backendFetch(`${basePath}${id}/receive/`, sessionId, {
            method: 'POST',
            body: JSON.stringify({ receipts }),
          });
          const payload = await upstream.json().catch(() => ({}));
          if (!upstream.ok) return jsonError(payload.detail || JSON.stringify(payload), upstream.status);
          return NextResponse.json({ result: true });
        },
      };

      if (customActions[body.method]) return customActions[body.method]!();
      return jsonError(`Method '${body.method}' not supported for cy.internal.order.`, 501);
    }

    // cy.internal.order.line
    if (body.method === 'search_read') {
      const domain = (body.args?.[0] as unknown[]) || [];
      const orderFilter = domain.find(
        (d) => Array.isArray(d) && d[0] === 'order_id',
      ) as [string, string, string] | undefined;
      const query = orderFilter ? `?order=${orderFilter[2]}` : '';
      const upstream = await backendFetch(`${linesPath}${query}`, sessionId, { method: 'GET' });
      const payload = await upstream.json();
      if (!upstream.ok) return jsonError(payload.detail || 'Fetch failed', upstream.status);
      const rows = (payload.results || payload) as Array<Record<string, unknown>>;
      return NextResponse.json({
        result: rows.map((r) => ({
          id: r.id,
          product_name: r.product_name ?? '',
          product_code: r.product_sku ?? '',
          requested_qty: Number(r.requested_qty),
          allocated_qty: Number(r.allocated_qty),
          shipped_qty: Number(r.shipped_qty),
          received_qty: Number(r.received_qty),
        })),
      });
    }

    if (body.method === 'create') {
      const values = (body.args?.[0] as Record<string, unknown>) || {};
      const upstream = await backendFetch(linesPath, sessionId, {
        method: 'POST',
        body: JSON.stringify({
          order: values.order_id,
          product: values.product_id,
          requested_qty: values.requested_qty,
        }),
      });
      const payload = await upstream.json();
      if (!upstream.ok) return jsonError(payload.detail || JSON.stringify(payload), upstream.status);
      return NextResponse.json({ result: payload.id });
    }

    return jsonError(`Method '${body.method}' not supported for cy.internal.order.line.`, 501);
  } catch (err: any) {
    return jsonError(err.message || 'Backend connection error', 500);
  }
}

export async function cycomCallKw(
  req: NextRequest,
  body: { model: string; method: string; args?: unknown[]; kwargs?: Record<string, unknown> },
): Promise<NextResponse> {
  const sessionId = getSessionId(req);
  if (!sessionId) {
    return NextResponse.json({ error: { message: 'Not authenticated' } }, { status: 401 });
  }

  // No document-storage backend exists — always answer "no documents" rather
  // than querying an unrelated endpoint or faking attachments.
  if (body.model === 'cy.vendor.document') {
    return NextResponse.json({ result: [] });
  }

  // Branch replenishment (internal orders) — real multi-line, multi-stage
  // workflow (submit -> allocate -> dispatch -> receive). Doesn't fit the
  // generic ModelAdapter shape: the legacy UI creates the order header
  // first, then adds lines one call at a time, then calls custom RPC-style
  // method names (submit_for_review/allocate_items/dispatch_order/
  // receive_order) that map onto the real backend's submit/allocate/
  // dispatch/receive actions with reshaped bodies.
  if (body.model === 'cy.internal.order' || body.model === 'cy.internal.order.line') {
    return handleInternalOrderCall(sessionId, body);
  }

  if (body.model === 'inventory.product') {
    return handleInventoryProductSearch(sessionId, body);
  }

  const adapter = MODEL_ADAPTERS[body.model];
  if (!adapter) {
    return NextResponse.json(
      {
        error: {
          message: `Model '${body.model}' is not yet migrated to the new Cycom backend. This page still expects the retired engine's schema — needs dedicated per-page rewiring, not a generic shim.`,
        },
      },
      { status: 501 },
    );
  }

  try {
    if (body.method === 'search_read') {
      const upstream = await backendFetch(adapter.basePath, sessionId, { method: 'GET' });
      const payload = await upstream.json();
      if (!upstream.ok) {
        return NextResponse.json({ error: { message: payload.detail || 'Fetch failed' } }, { status: upstream.status });
      }
      const rows = (payload.results || payload).map(adapter.fromBackend);
      return NextResponse.json({ result: rows });
    }

    if (body.method === 'create') {
      const values = (body.args?.[0] as Record<string, unknown>) || {};
      const upstream = await backendFetch(adapter.basePath, sessionId, {
        method: 'POST',
        body: JSON.stringify(adapter.toBackend(values)),
      });
      const payload = await upstream.json();
      if (!upstream.ok) {
        return NextResponse.json({ error: { message: payload.detail || JSON.stringify(payload) } }, { status: upstream.status });
      }
      return NextResponse.json({ result: payload.id });
    }

    if (body.method === 'write') {
      const [ids, values] = (body.args || []) as [number[], Record<string, unknown>];
      const id = ids[0];
      const upstream = await backendFetch(`${adapter.basePath}${id}/`, sessionId, {
        method: 'PATCH',
        body: JSON.stringify(adapter.toBackend(values)),
      });
      const payload = await upstream.json();
      if (!upstream.ok) {
        return NextResponse.json({ error: { message: payload.detail || JSON.stringify(payload) } }, { status: upstream.status });
      }
      return NextResponse.json({ result: true });
    }

    if (body.method === 'unlink') {
      const [ids] = (body.args || []) as [number[]];
      const id = ids[0];
      const upstream = await backendFetch(`${adapter.basePath}${id}/`, sessionId, { method: 'DELETE' });
      if (!upstream.ok && upstream.status !== 204) {
        const payload = await upstream.json().catch(() => ({}));
        return NextResponse.json({ error: { message: payload.detail || 'Delete failed' } }, { status: upstream.status });
      }
      return NextResponse.json({ result: true });
    }

    if (body.method === 'read') {
      const id = (body.args || [])[0];
      const upstream = await backendFetch(`${adapter.basePath}${id}/`, sessionId, { method: 'GET' });
      const payload = await upstream.json();
      if (!upstream.ok) {
        return NextResponse.json({ error: { message: payload.detail || 'Fetch failed' } }, { status: upstream.status });
      }
      return NextResponse.json({ result: adapter.fromBackend(payload) });
    }

    if (adapter.customActions?.[body.method]) {
      const { path, body: actionBody } = adapter.customActions[body.method]!(body.args || []);
      const upstream = await backendFetch(path, sessionId, {
        method: 'POST',
        body: actionBody ? JSON.stringify(actionBody) : undefined,
      });
      const payload = await upstream.json().catch(() => ({}));
      if (!upstream.ok) {
        return NextResponse.json({ error: { message: payload.detail || JSON.stringify(payload) } }, { status: upstream.status });
      }
      return NextResponse.json({ result: true });
    }

    return NextResponse.json({ error: { message: `Method '${body.method}' not supported.` } }, { status: 501 });
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || 'Backend connection error' } }, { status: 500 });
  }
}
