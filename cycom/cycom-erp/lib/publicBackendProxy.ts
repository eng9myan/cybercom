/**
 * Server-only proxy for the CMS/blog/forum/storefront/etc's *public*,
 * unauthenticated backend routes (products/cycom/<app>/public_urls.py) --
 * no session/token involved, unlike cycomBackendProxy in cycomServer.ts.
 *
 * A plain next.config.ts `rewrites()` entry looked like it worked but
 * doesn't: Next resolves the `source` pattern against an already
 * slash-normalized pathname, so a request ending in `/` gets proxied to
 * Django WITHOUT the trailing slash Django's APPEND_SLASH requires --
 * Django 301s back to the same URL, and since that's a real redirect
 * response (not a rewrite), the browser follows it straight back into the
 * same broken proxy, forever. `skipTrailingSlashRedirect` alone doesn't
 * fix this either -- it only stops *Next's own* redirect from firing, not
 * the earlier normalization that already dropped the slash before the
 * rewrite's `:path*` ever saw it. A real catch-all Route Handler sidesteps
 * all of that: it reads the original request itself and always re-appends
 * exactly one trailing slash before forwarding, regardless of what Next's
 * router did to get here.
 */

import { NextRequest, NextResponse } from 'next/server';

const CYCOM_BACKEND_URL = process.env.CYCOM_BACKEND_URL || 'http://localhost:8090';

export function publicProxyTarget(req: NextRequest, prefix: string, path: string[]): string {
  const suffix = path.join('/');
  const withSlash = suffix.endsWith('/') || suffix === '' ? suffix : `${suffix}/`;
  return `/api/${prefix}/${withSlash}${req.nextUrl.search || ''}`;
}

export async function publicBackendProxy(req: NextRequest, targetPath: string): Promise<NextResponse> {
  const method = req.method.toUpperCase();
  const init: RequestInit = { method, headers: { 'Content-Type': 'application/json' } };
  if (method !== 'GET' && method !== 'DELETE') {
    const text = await req.text();
    if (text) init.body = text;
  }
  try {
    const upstream = await fetch(`${CYCOM_BACKEND_URL}${targetPath}`, init);
    const payload = await upstream.json().catch(() => ({}));
    return NextResponse.json(payload, { status: upstream.status });
  } catch (err: any) {
    return NextResponse.json(
      { error: { message: err.message || 'Backend connection error' } },
      { status: 500 },
    );
  }
}
