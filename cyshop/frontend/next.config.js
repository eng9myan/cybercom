/** @type {import('next').NextConfig} */

// Same-origin in production (Caddy reverse-proxies /api/* → backend).
// Local dev / non-proxied runs: set BACKEND_INTERNAL_URL to point at Django.
const BACKEND_INTERNAL_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
  env: {
    // Empty string by default → frontend uses relative URLs (same-origin via Caddy).
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
  },
  async rewrites() {
    // Forward backend paths when there's no upstream reverse proxy
    // (e.g., `next dev` or `next start` without Caddy in front).
    return [
      { source: '/api/:path*',      destination: `${BACKEND_INTERNAL_URL}/api/:path*` },
      { source: '/admin/:path*',    destination: `${BACKEND_INTERNAL_URL}/admin/:path*` },
      { source: '/graphql/:path*',  destination: `${BACKEND_INTERNAL_URL}/graphql/:path*` },
      { source: '/healthz/:path*',  destination: `${BACKEND_INTERNAL_URL}/healthz/:path*` },
      { source: '/static/:path*',   destination: `${BACKEND_INTERNAL_URL}/static/:path*` },
    ];
  },
};

module.exports = nextConfig;
