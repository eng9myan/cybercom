import { NextRequest } from 'next/server';
import { publicBackendProxy, publicProxyTarget } from '@/lib/publicBackendProxy';

async function handler(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return publicBackendProxy(req, publicProxyTarget(req, 'store', path));
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
