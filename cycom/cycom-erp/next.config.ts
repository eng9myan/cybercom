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
    ];
  },
};

export default nextConfig;
