import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server bundle (.next/standalone) so the app runs on the
  // tiny demo box with `node server.js` — no build or full node_modules there.
  output: "standalone",
  // No server-side image optimization -> no native `sharp` dependency, so a
  // Windows-built standalone runs unchanged on the Linux demo box. Fine for a
  // demo (images serve as-is).
  images: { unoptimized: true },
  async rewrites() {
    return [
      {
        source: '/api/sign/:path*',
        destination: `${process.env.CYCOM_BACKEND_URL || 'http://localhost:8000'}/api/sign/:path*`,
      },
      {
        source: '/api/store/:path*',
        destination: `${process.env.CYCOM_BACKEND_URL || 'http://localhost:8000'}/api/store/:path*`,
      },
      {
        source: '/api/blog/:path*',
        destination: `${process.env.CYCOM_BACKEND_URL || 'http://localhost:8000'}/api/blog/:path*`,
      },
      {
        source: '/api/forum/:path*',
        destination: `${process.env.CYCOM_BACKEND_URL || 'http://localhost:8000'}/api/forum/:path*`,
      },
      {
        source: '/api/chat/:path*',
        destination: `${process.env.CYCOM_BACKEND_URL || 'http://localhost:8000'}/api/chat/:path*`,
      },
      {
        source: '/api/learn/:path*',
        destination: `${process.env.CYCOM_BACKEND_URL || 'http://localhost:8000'}/api/learn/:path*`,
      },
    ];
  },
};

export default nextConfig;
