import { NextRequest } from 'next/server';
import { cycomBackendProxy } from '@/lib/cycomServer';

// Generic authenticated REST proxy:
//   /api/cycom/rest/<path>  ->  backend /api/v1/<path>  (query string preserved)
// Used by the ported Commerce screens (KDS, catalog/inventory onboarding) that
// talk to the real DRF endpoints instead of the legacy {model,method} RPC.
// Auth + tenant scoping are handled inside cycomBackendProxy (session -> bearer).

function target(req: NextRequest, path: string[]): string {
  const suffix = path.join('/');
  const qs = req.nextUrl.search || '';
  const trailing = suffix.endsWith('/') || qs ? '' : '/';
  return `/api/v1/${suffix}${trailing}${qs}`;
}

async function handler(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return cycomBackendProxy(req, target(req, path));
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
