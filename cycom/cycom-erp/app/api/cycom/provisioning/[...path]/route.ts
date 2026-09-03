import { NextRequest } from 'next/server';
import { cycomBackendProxy } from '@/lib/cycomServer';

// Proxies /api/cycom/provisioning/<path> -> backend /api/v1/provisioning/<path>,
// preserving the query string. Handles the full REST verb set the wizard uses.

function target(req: NextRequest, path: string[]): string {
  const suffix = path.join('/');
  const qs = req.nextUrl.search || '';
  return `/api/v1/provisioning/${suffix}${suffix.endsWith('/') || qs ? '' : '/'}${qs}`;
}

async function handler(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return cycomBackendProxy(req, target(req, path));
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
