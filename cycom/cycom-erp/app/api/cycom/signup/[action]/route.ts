import { NextRequest, NextResponse } from 'next/server';

// PUBLIC (pre-auth) signup proxy. No session required — this is how a brand-new
// customer creates a tenant before any login exists.
//   POST /api/cycom/signup/demo      -> backend /api/v1/tenants/demo/     (72h trial)
//   POST /api/cycom/signup/register  -> backend /api/v1/tenants/register/ (permanent + invoice)
// Only these two actions are allowed; anything else is rejected so this route
// can't be used as an open proxy to the rest of the tenant API.

const CYCOM_BACKEND_URL = process.env.CYCOM_BACKEND_URL || 'http://localhost:8090';
const ALLOWED = new Set(['demo', 'register']);

export async function POST(req: NextRequest, ctx: { params: Promise<{ action: string }> }) {
  const { action } = await ctx.params;
  if (!ALLOWED.has(action)) {
    return NextResponse.json({ error: 'Unknown signup action' }, { status: 404 });
  }
  let body: string;
  try {
    body = await req.text();
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
  try {
    const upstream = await fetch(`${CYCOM_BACKEND_URL}/api/v1/tenants/${action}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    });
    const data = await upstream.json().catch(() => ({}));
    return NextResponse.json(data, { status: upstream.status });
  } catch (err: any) {
    return NextResponse.json(
      { error: err?.message || 'Signup gateway connection error' },
      { status: 502 },
    );
  }
}
