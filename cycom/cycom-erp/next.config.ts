import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
