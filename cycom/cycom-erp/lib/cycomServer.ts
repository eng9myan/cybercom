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

/** DEV/demo: mint the unsigned dev-identity JWT (tenant_admin on the fixed dev
 * tenant) the backend's DevAuthMiddleware accepts. Shared by cycomDevLogin and
 * the no-cookie fallback below. */
function mintDevToken(role = 'gm', name = ''): string {
  const b64 = (o: unknown) => Buffer.from(JSON.stringify(o)).toString('base64url');
  const now = Math.floor(Date.now() / 1000);
  const tenantId = process.env.CYCOM_TENANT_ID || '11111111-1111-1111-1111-111111111111';
  const displayName = name || DEV_ROLE_NAMES[role] || 'Dev User';
  const claims = {
    sub: `dev-${role}`,
    name: displayName,
    email: `${role}@cycom.dev`,
    preferred_username: `${role}@cycom.dev`,
    tenant_id: tenantId,
    realm_access: { roles: [role, 'tenant_admin'] },
    cycom_role: role,
    iat: now,
    exp: now + 60 * 60 * 12,
  };
  return `${b64({ alg: 'none', typ: 'JWT' })}.${b64(claims)}.dev`;
}

function getSessionId(req: NextRequest): string | null {
  const cookie = req.cookies.get(SESSION_COOKIE)?.value;
  if (cookie) return cookie;
  // DEV/demo only: with no session cookie, fall back to the dev identity so
  // client-side BFF calls (KDS live tickets, etc.) work without first bouncing
  // through /api/cycom/dev-login. Never active unless CYCOM_DEV_AUTH=1.
  if (process.env.CYCOM_DEV_AUTH === '1') return mintDevToken();
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

/**
 * DEV-ONLY login. Mints an UNSIGNED, well-formed JWT carrying the dev
 * identity (tenant_admin on the fixed dev tenant) and sets it as the session
 * cookie. The backend's DevAuthMiddleware reads these claims without verifying
 * the signature, so no Keycloak is needed. Gated behind CYCOM_DEV_AUTH so it
 * cannot be hit in a normal deployment.
 */
export function cycomDevLogin(role = 'gm', name = ''): NextResponse {
  if (process.env.CYCOM_DEV_AUTH !== '1') {
    return NextResponse.json({ error: 'Dev login disabled' }, { status: 403 });
  }
  const token = mintDevToken(role, name);
  const res = NextResponse.redirect(
    new URL('/', process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:7000'),
  );
  applySessionCookie(res, token);
  return res;
}

const DEV_ROLE_NAMES: Record<string, string> = {
  gm: 'General Manager',
  accounting_officer: 'Accounting Officer',
  hr_officer: 'HR Officer',
  supply_chain_officer: 'Supply Chain Officer',
  ops_manager: 'Operations Manager',
};

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
        roles,
        role: (claims.cycom_role as string)
          || roles.find((r) => r !== 'tenant_admin' && r !== 'platform_admin')
          || 'gm',
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
// Generic authenticated passthrough to a real /api/v1/* backend route. Used by
// genuinely REST-shaped features (e.g. Ready-ERP provisioning) that don't need
// the legacy Odoo {model,method,args,kwargs} shim below. Forwards method,
// query string, and JSON body; injects the Keycloak bearer + tenant header.
// ---------------------------------------------------------------------------

export async function cycomBackendProxy(
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
  // Optional: translate the legacy search_read domain into a DRF query string
  // (django-filter). Without it, domains are ignored and the full list returns.
  listQuery?: (domain: Array<[string, string, unknown]>) => string;
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

// Legacy pages send junk placeholder fields (tenant_id: 1, company_id: 1)
// from the retired backend era — never forward them.
const stripLegacyJunk = (f: Record<string, unknown>) => {
  const { tenant_id, company_id, ...rest } = f;
  return rest;
};

const vehicleFilterQuery = (domain: Array<[string, string, unknown]>) => {
  const byVehicle = domain.find((d) => Array.isArray(d) && d[0] === 'vehicle_id');
  return byVehicle ? `?vehicle=${byVehicle[2]}` : '';
};

const MODEL_ADAPTERS: Record<string, ModelAdapter> = {
  'fleet.vehicle': {
    basePath: '/api/v1/fleet/vehicles/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      const direct = ['name', 'license_plate', 'make', 'model', 'status', 'insurance_expiry', 'license_expiry'];
      for (const key of direct) if (key in src) out[key] = src[key];
      // UI writes both `odometer_km` and legacy `odometer` — only the real field survives.
      if ('odometer_km' in src) out.odometer_km = src.odometer_km;
      else if ('odometer' in src) out.odometer_km = src.odometer;
      if ('state' in src) out.status = src.state;
      if ('driver_id' in src) out.driver_name = Array.isArray(src.driver_id) ? src.driver_id[1] : src.driver_id;
      if ('driver' in src) out.driver_name = src.driver;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      name: r.name || `${r.make || ''} ${r.model || ''}`.trim(),
      license_plate: r.license_plate,
      make: r.make || undefined,
      model: (r.model as string) || undefined,
      driver_id: r.driver_name ? [1, r.driver_name as string] : false,
      odometer_km: Number(r.odometer_km || 0),
      odometer: Number(r.odometer_km || 0),
      state: r.status,
      insurance_expiry: r.insurance_expiry || undefined,
      license_expiry: r.license_expiry || undefined,
    }),
  },
  'cy.fleet.maintenance': {
    basePath: '/api/v1/fleet/maintenance-logs/',
    listQuery: vehicleFilterQuery,
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('vehicle_id' in src) out.vehicle = src.vehicle_id;
      const direct = ['maintenance_date', 'maintenance_type', 'cost', 'odometer_km', 'next_service_km'];
      for (const key of direct) if (key in src && src[key] !== null) out[key] = src[key];
      if ('service_provider' in src) out.service_provider = src.service_provider || '';
      if ('notes' in src) out.notes = src.notes || '';
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      vehicle_id: r.vehicle,
      maintenance_date: r.maintenance_date,
      maintenance_type: r.maintenance_type,
      cost: Number(r.cost || 0),
      service_provider: r.service_provider || false,
      odometer_km: Number(r.odometer_km || 0),
      next_service_km: r.next_service_km != null ? Number(r.next_service_km) : false,
      notes: r.notes || false,
    }),
  },
  'cy.fleet.fuel': {
    basePath: '/api/v1/fleet/fuel-logs/',
    listQuery: vehicleFilterQuery,
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('vehicle_id' in src) out.vehicle = src.vehicle_id;
      const direct = ['log_date', 'liters', 'price_per_liter', 'total_cost', 'odometer_km'];
      for (const key of direct) if (key in src && src[key] !== null) out[key] = src[key];
      if ('fuel_station' in src) out.fuel_station = src.fuel_station || '';
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      vehicle_id: r.vehicle,
      log_date: r.log_date,
      liters: Number(r.liters || 0),
      price_per_liter: Number(r.price_per_liter || 0),
      total_cost: Number(r.total_cost || 0),
      fuel_station: r.fuel_station || false,
      odometer_km: Number(r.odometer_km || 0),
    }),
  },
  'purchase.order': {
    basePath: '/api/v1/procurement/orders/',
    toBackend: () => ({}),
    fromBackend: (r) => ({
      id: r.id,
      name: `PO-${String(r.id).slice(0, 6)}`,
      partner_id: r.vendor ? [r.vendor, (r.vendor_name as string) || 'Vendor'] : false,
      date_order: r.created_at ? String(r.created_at).split('T')[0] : false,
      amount_total: Number(r.amount_total || 0),
      state: r.status,
      currency_id: [1, (r.currency as string) || 'JOD'],
    }),
  },
  'sale.order': {
    basePath: '/api/v1/sales/orders/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('name' in src) out.number = src.name;
      if ('partner_id' in src) out.customer_name = Array.isArray(src.partner_id) ? src.partner_id[1] : src.partner_id;
      if ('date_order' in src) out.order_date = src.date_order;
      if ('amount_total' in src) out.amount_total = src.amount_total;
      if ('state' in src) out.status = src.state;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      name: r.number,
      partner_id: r.customer_name ? [1, r.customer_name as string] : false,
      date_order: r.order_date,
      amount_total: Number(r.amount_total || 0),
      state: r.status,
      currency_id: [1, (r.currency as string) || 'JOD'],
    }),
    customActions: {
      confirm: (args) => ({ path: `/api/v1/sales/orders/${args[0]}/confirm/` }),
    },
  },
  'helpdesk.ticket': {
    basePath: '/api/v1/helpdesk/tickets/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('name' in src) out.subject = src.name;
      if ('partner_id' in src) out.customer_name = Array.isArray(src.partner_id) ? src.partner_id[1] : src.partner_id;
      if ('user_id' in src) out.assignee = Array.isArray(src.user_id) ? src.user_id[1] : src.user_id;
      if ('team_id' in src) out.team = Array.isArray(src.team_id) ? src.team_id[1] : src.team_id;
      if ('priority' in src) out.priority = src.priority;
      if ('stage_id' in src) out.stage = Array.isArray(src.stage_id) ? src.stage_id[1] : src.stage_id;
      if (!('number' in out)) out.number = (src as any).name ? undefined : undefined;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      name: r.subject,
      partner_id: r.customer_name ? [1, r.customer_name as string] : false,
      user_id: r.assignee ? [1, r.assignee as string] : false,
      team_id: r.team ? [1, r.team as string] : false,
      priority: r.priority,
      stage_id: [1, r.stage as string],
    }),
  },
  'hr.applicant': {
    basePath: '/api/v1/recruitment/applicants/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('partner_name' in src) out.name = src.partner_name;
      if ('email_from' in src) out.email = src.email_from || '';
      if ('job_id' in src) out.job_title = Array.isArray(src.job_id) ? src.job_id[1] : src.job_id;
      if ('priority' in src) out.priority = String(src.priority);
      if ('stage_id' in src) out.stage = Array.isArray(src.stage_id) ? src.stage_id[1] : src.stage_id;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      partner_name: r.name,
      name: r.job_title,
      email_from: r.email || false,
      job_id: r.job_title ? [1, r.job_title as string] : false,
      priority: r.priority,
      kanban_state: 'normal',
      stage_id: [1, r.stage as string],
      create_date: r.created_at,
    }),
  },
  'hr.attendance': {
    basePath: '/api/v1/payroll/attendance/',
    toBackend: (f) => stripLegacyJunk(f),
    fromBackend: (r) => ({
      id: r.id,
      employee_id: r.employee ? [1, String(r.employee)] : false,
      check_in: r.check_in,
      check_out: r.check_out,
      worked_hours: r.check_in && r.check_out ? undefined : 0,
    }),
  },
  'hr.payslip': {
    basePath: '/api/v1/payroll/payslips/',
    toBackend: (f) => stripLegacyJunk(f),
    fromBackend: (r) => ({
      id: r.id,
      employee_id: r.employee ? [1, String(r.employee)] : false,
      date_from: r.date_from || false,
      date_to: r.date_to || false,
      net_wage: Number(r.net_pay || 0),
      state: r.status,
      // Additive keys the ESS portal reads (harmless to the payroll page):
      gross: Number(r.gross_pay || 0),
      net: Number(r.net_pay || 0),
      period: r.period || '',
    }),
  },

  // Employee self-service portal reads leave requests via this alias.
  'hr.leave': {
    basePath: '/api/v1/leave/requests/',
    toBackend: (f) => stripLegacyJunk(f),
    fromBackend: (r) => ({
      id: r.id,
      leave_type: r.leave_type_code || r.leave_type_name || '',
      start_date: r.start_date || false,
      end_date: r.end_date || false,
      days: Number(r.days || 0),
      status: r.status,
      name: r.reason || '',
    }),
  },

  'pos.session': {
    basePath: '/api/v1/pos/sessions/',
    toBackend: () => ({}),
    fromBackend: (r) => ({
      id: r.id,
      name: `SES-${String(r.id).slice(0, 6)}`,
      user_id: r.cashier ? [1, r.cashier as string] : false,
      config_id: false,
      start_at: r.opened_at,
      stop_at: r.closed_at || false,
      state: r.status === 'closed' ? 'closed' : 'opened',
      cash_register_balance_end_real: Number(r.closing_cash ?? r.opening_cash ?? 0),
    }),
  },
  'quality.check': {
    basePath: '/api/v1/quality/checkpoints/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('name' in src) out.name = src.name;
      if ('quality_state' in src) out.result = src.quality_state;
      if ('notes' in src) out.notes = src.notes || '';
      if ('description' in src) out.description = src.description || '';
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      name: r.name,
      product_id: r.linked_model ? [1, r.linked_model as string] : false,
      picking_id: false,
      quality_state: r.result,
      create_date: r.created_at,
    }),
  },
  'hr.expense': {
    basePath: '/api/v1/expenses/expenses/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('name' in src) out.description = src.name;
      if ('description' in src) out.description = src.description;
      if ('employee_id' in src) out.employee_name = Array.isArray(src.employee_id) ? src.employee_id[1] : src.employee_id;
      if ('total_amount' in src) out.amount = src.total_amount;
      if ('date' in src) out.expense_date = src.date;
      if ('state' in src) out.status = src.state;
      out.category = (src as any).category || 'General';
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      name: r.description || `EXP-${String(r.id).slice(0, 6)}`,
      employee_id: r.employee_name ? [1, r.employee_name as string] : false,
      product_id: r.category ? [1, r.category as string] : false,
      total_amount: Number(r.amount || 0),
      date: r.expense_date,
      description: r.description || false,
      state: r.status,
      currency_id: [1, (r.currency as string) || 'JOD'],
    }),
    customActions: {
      approve: (args) => ({ path: `/api/v1/expenses/expenses/${args[0]}/approve/` }),
      reject: (args) => ({ path: `/api/v1/expenses/expenses/${args[0]}/reject/`, body: { reason: args[1] } }),
    },
  },
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

  // ── Collaboration / project / planning / plm / marketing (Step 8) ────────
  // Backend stores Odoo-naive-ish ISO; the legacy pages expect
  // "YYYY-MM-DD HH:MM:SS" (space, no tz) so their `.replace(' ','T')+'Z'`
  // parsing works. `toNaiveDt` strips the timezone/fractional part.
  'project.task': {
    basePath: '/api/v1/project/tasks/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('name' in src) out.name = src.name;
      if ('allocated_hours' in src) out.allocated_hours = src.allocated_hours;
      if ('planned_hours' in src && !('allocated_hours' in src)) out.allocated_hours = src.planned_hours;
      if ('effective_hours' in src) out.effective_hours = src.effective_hours;
      return out;
    },
    fromBackend: (r) => {
      const STAGE_LABEL: Record<string, string> = {
        backlog: 'Backlog', in_progress: 'In Progress', review: 'Review', done: 'Done',
      };
      return {
        id: r.id,
        name: r.name,
        project_id: r.project ? [r.project, r.project_name || 'Project'] : false,
        allocated_hours: Number(r.allocated_hours || 0),
        planned_hours: Number(r.allocated_hours || 0),
        effective_hours: Number(r.effective_hours || 0),
        stage_id: [1, STAGE_LABEL[r.stage as string] || 'Backlog'],
      };
    },
  },

  'mass.mailing': {
    basePath: '/api/v1/marketing/campaigns/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('name' in src) out.name = src.name;
      if ('state' in src) out.state = src.state;
      if ('mailing_model_id' in src && Array.isArray(src.mailing_model_id)) out.target = src.mailing_model_id[1];
      if ('target' in src) out.target = src.target;
      if ('campaign_type' in src) out.campaign_type = src.campaign_type;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      name: r.name,
      mailing_model_id: r.target ? [1, r.target] : false,
      state: r.state,
      sent: Number(r.sent || 0),
      failed: Number(r.failed || 0),
      scheduled_date: r.scheduled_date
        ? String(r.scheduled_date).replace('T', ' ').replace('Z', '').split('.')[0]
        : false,
    }),
  },

  'planning.slot': {
    basePath: '/api/v1/planning/slots/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('resource_id' in src && Array.isArray(src.resource_id)) out.resource_name = src.resource_id[1];
      if ('resource_name' in src) out.resource_name = src.resource_name;
      if ('role_id' in src && Array.isArray(src.role_id)) out.role = src.role_id[1];
      if ('role' in src) out.role = src.role;
      if ('start_datetime' in src) out.start_datetime = src.start_datetime;
      if ('end_datetime' in src) out.end_datetime = src.end_datetime;
      if ('department' in src) out.department = src.department;
      return out;
    },
    fromBackend: (r) => {
      const naive = (v: unknown) =>
        v ? String(v).replace('T', ' ').replace('Z', '').split('.')[0] : false;
      return {
        id: r.id,
        resource_id: r.resource_name ? [1, r.resource_name] : false,
        role_id: r.role ? [1, r.role] : false,
        start_datetime: naive(r.start_datetime),
        end_datetime: naive(r.end_datetime),
        state: r.state,
      };
    },
  },

  'mrp.eco': {
    basePath: '/api/v1/plm/ecos/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('name' in src) out.name = src.name;
      if ('title' in src) out.title = src.title;
      if ('reason' in src) out.reason = src.reason;
      if ('product_tmpl_id' in src && Array.isArray(src.product_tmpl_id)) out.product_name = src.product_tmpl_id[1];
      if ('product_name' in src) out.product_name = src.product_name;
      return out;
    },
    fromBackend: (r) => {
      const STAGE_LABEL: Record<string, string> = {
        draft: 'Draft', review: 'Under Review', approved: 'Approved', done: 'Done',
      };
      return {
        id: r.id,
        name: r.name,
        product_tmpl_id: r.product_name ? [1, r.product_name] : false,
        stage_id: [1, STAGE_LABEL[r.stage as string] || 'Draft'],
        user_id: r.owner ? [1, r.owner] : false,
        create_date: r.created_at
          ? String(r.created_at).replace('T', ' ').replace('Z', '').split('.')[0]
          : false,
      };
    },
  },

  'mail.message': {
    basePath: '/api/v1/discuss/messages/',
    listQuery: (domain) => {
      const byChannel = domain.find((d) => Array.isArray(d) && d[0] === 'channel_id');
      return byChannel ? `?channel=${byChannel[2]}` : '';
    },
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('channel_id' in src) out.channel = src.channel_id;
      if ('channel' in src) out.channel = src.channel;
      if ('author' in src) out.author = src.author;
      if ('body' in src) out.body = src.body;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      channel_id: r.channel ? [r.channel, ''] : false,
      author: r.author || '',
      body: r.body || '',
      create_date: r.created_at
        ? String(r.created_at).replace('T', ' ').replace('Z', '').split('.')[0]
        : false,
    }),
  },

  'mail.channel': {
    basePath: '/api/v1/discuss/channels/',
    toBackend: (f) => {
      const src = stripLegacyJunk(f);
      const out: Record<string, unknown> = {};
      if ('name' in src) out.name = src.name;
      if ('channel_type' in src) out.channel_type = src.channel_type;
      if ('topic' in src) out.topic = src.topic;
      return out;
    },
    fromBackend: (r) => ({
      id: r.id,
      name: r.name,
      channel_type: r.channel_type || 'channel',
      member_count: Number(r.member_count || 0),
      last_interest_dt: r.last_interest_dt
        ? String(r.last_interest_dt).replace('T', ' ').replace('Z', '').split('.')[0]
        : false,
    }),
  },
};

function resolveTenantId(token: string): string {
  try {
    const claims = decodeJwtPayload(token);
    if (claims.tenant_id) return String(claims.tenant_id);
  } catch {
    // fall through to the env var
  }
  return CYCOM_TENANT_ID;
}

async function backendFetch(path: string, token: string, init: RequestInit = {}) {
  const tenantId = resolveTenantId(token);
  return fetch(`${CYCOM_BACKEND_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(tenantId ? { 'X-Tenant-ID': tenantId } : {}),
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

  // Models with no backend module yet — answer empty (page renders its empty
  // state) instead of a 501 error card. Tracked for future backend work:
  //   hr.attendance.overtime  — overtime approval engine
  //   zk.machine              — biometric device registry (import already exists
  //                             at /api/v1/payroll/attendance/import/)
  if (
    body.model === 'hr.attendance.overtime' ||
    body.model === 'zk.machine'
  ) {
    if (body.method === 'search_read' || body.method === 'read') {
      return NextResponse.json({ result: [] });
    }
    return NextResponse.json({ result: false });
  }

  // Legacy setup wizards persist choices via ir.config_parameter — backed by
  // the real tenant KV store at /api/v1/provisioning/config-parameters/.
  if (body.model === 'ir.config_parameter') {
    try {
      if (body.method === 'set_param') {
        const [key, value] = (body.args || []) as [string, unknown];
        const upstream = await backendFetch('/api/v1/provisioning/config-parameters/set/', sessionId, {
          method: 'POST',
          body: JSON.stringify({ key, value }),
        });
        if (!upstream.ok) {
          const payload = await upstream.json().catch(() => ({}));
          return jsonError(payload.detail || 'set_param failed', upstream.status);
        }
        return NextResponse.json({ result: true });
      }
      if (body.method === 'get_param') {
        const [key] = (body.args || []) as [string];
        const upstream = await backendFetch(
          `/api/v1/provisioning/config-parameters/get/?key=${encodeURIComponent(key)}`,
          sessionId,
          { method: 'GET' },
        );
        const payload = await upstream.json().catch(() => ({}));
        if (!upstream.ok) return jsonError(payload.detail || 'get_param failed', upstream.status);
        return NextResponse.json({ result: payload.value ?? false });
      }
      return jsonError(`Method '${body.method}' not supported for ir.config_parameter.`, 501);
    } catch (err: any) {
      return jsonError(err.message || 'Backend connection error', 500);
    }
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

  // Employee bulk import — real endpoint returns a rich payload (imported
  // count + per-row errors), so pass the whole thing through as `result`
  // rather than the generic customAction's boolean.
  if (body.model === 'hr.employee' && (body.method === 'bulk_import' || body.method === 'validate_import')) {
    try {
      const rows = (body.args?.[0] as unknown[]) || [];
      const upstream = await backendFetch('/api/v1/hr/employees/bulk-import/', sessionId, {
        method: 'POST',
        body: JSON.stringify({ rows, dry_run: body.method === 'validate_import' }),
      });
      const payload = await upstream.json().catch(() => ({}));
      if (!upstream.ok) return jsonError(payload.detail || 'Import failed', upstream.status);
      return NextResponse.json({ result: payload });
    } catch (err: any) {
      return jsonError(err.message || 'Backend connection error', 500);
    }
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
      const domain = (body.args?.[0] as Array<[string, string, unknown]>) || [];
      const query = adapter.listQuery ? adapter.listQuery(domain) : '';
      const upstream = await backendFetch(`${adapter.basePath}${query}`, sessionId, { method: 'GET' });
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
