import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server bundle (.next/standalone) so the app runs on the
  // tiny demo box with `node server.js` — no build or full node_modules there.
  output: "standalone",
  // No server-side image optimization -> no native `sharp` dependency, so a
  // Windows-built standalone runs unchanged on the Linux demo box. Fine for a
  // demo (images serve as-is).
  images: { unoptimized: true },
  // Next's default trailingSlash:false normalizes ANY route -- including a
  // catch-all Route Handler -- by 308-redirecting a request ending in `/`
  // to the same path without one, before the handler ever runs. The public
  // proxies below (app/api/<prefix>/[...path]/route.ts) forward to Django
  // endpoints that require the opposite (APPEND_SLASH), so without this
  // flag every trailing-slash GET through them 308s away before
  // lib/publicBackendProxy.ts gets a chance to re-add the slash itself.
  skipTrailingSlashRedirect: true,
  // The /api/sign, /api/store, /api/blog, /api/forum, /api/chat, /api/learn,
  // /api/site public backend proxies used to live here as plain rewrites().
  // That silently broke every trailing-slash GET (Next resolves a rewrite's
  // `source` against an already slash-normalized pathname, so `:path*` never
  // saw the slash Django's APPEND_SLASH requires -> Django 301s back to the
  // same URL -> the browser follows it into the same broken proxy, forever;
  // `skipTrailingSlashRedirect` doesn't fix it either, since it only
  // suppresses Next's own redirect, not the earlier normalization). Each of
  // those now has a real catch-all Route Handler under app/api/<prefix>/
  // [...path]/route.ts (see lib/publicBackendProxy.ts) that reads the
  // original request and always re-appends exactly one trailing slash
  // before forwarding, so this rewrites() block is deliberately empty.
};

export default nextConfig;
