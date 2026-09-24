import { NextRequest } from 'next/server';
import { cycomBackendProxy } from '@/lib/cycomServer';

// Generic authenticated REST proxy:
//   /api/cycom/rest/<path>  ->  backend /api/v1/<path>  (query string preserved)
// Used by the ported Commerce screens (KDS, catalog/inventory onboarding) that
// talk to the real DRF endpoints instead of the legacy {model,method} RPC.
// Auth + tenant scoping are handled inside cycomBackendProxy (session -> bearer).

function target(req: NextRequest, path: string[]): string {
  const suffix = path.join('/');
  // Always land on exactly one trailing slash before the query string --
  // Django's APPEND_SLASH needs it regardless of whether a `?...` follows.
  // (A prior version dropped the slash whenever a query string was
  // present, so e.g. PATCH .../products/123?warehouse=main lost its slash,
  // triggering Django's redirect -- which drops the request body on a
  // non-GET method -- so the mutation silently no-opped.)
  const withSlash = suffix.endsWith('/') ? suffix : `${suffix}/`;
  return `/api/v1/${withSlash}${req.nextUrl.search || ''}`;
}

async function handler(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return cycomBackendProxy(req, target(req, path));
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
