import { NextRequest } from 'next/server';
import { cymedBackendProxy } from '@/lib/cymedServer';

// Generic authenticated REST proxy:
//   /api/cymed/rest/<path>  ->  backend /api/v1/<path>  (query string preserved)
// The ONLY data-fetching route in this app — no Odoo-shaped {model,method}
// shim exists here (see lib/cymedServer.ts's docstring for why).

function target(req: NextRequest, path: string[]): string {
  const suffix = path.join('/');
  const qs = req.nextUrl.search || '';
  const trailing = suffix.endsWith('/') || qs ? '' : '/';
  return `/api/v1/${suffix}${trailing}${qs}`;
}

async function handler(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return cymedBackendProxy(req, target(req, path));
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
