import { NextRequest } from 'next/server';
import { cycomBackendProxy } from '@/lib/cycomServer';

// Proxies /api/cycom/provisioning/<path> -> backend /api/v1/provisioning/<path>,
// preserving the query string. Handles the full REST verb set the wizard uses.

function target(req: NextRequest, path: string[]): string {
  const suffix = path.join('/');
  // Always land on exactly one trailing slash before the query string --
  // see app/api/cycom/rest/[...path]/route.ts's target() for why (the
  // previous `|| qs` check dropped the slash whenever a query string was
  // present, breaking non-GET requests via Django's APPEND_SLASH redirect).
  const withSlash = suffix.endsWith('/') ? suffix : `${suffix}/`;
  return `/api/v1/provisioning/${withSlash}${req.nextUrl.search || ''}`;
}

async function handler(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return cycomBackendProxy(req, target(req, path));
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
