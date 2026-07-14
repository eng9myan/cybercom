import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";
import path from "node:path";

const withNextIntl = createNextIntlPlugin("./lib/i18n.ts");

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(process.cwd(), "../.."),
  transpilePackages: ["@cybercom/ui", "@cybercom/api", "@cybercom/config"],
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "api.cy-com.com" },
      { protocol: "https", hostname: "cdn.cy-com.com" },
    ],
    formats: ["image/avif", "image/webp"],
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
  async redirects() {
    return [
      { source: "/products", destination: "/en/products", permanent: false },
      { source: "/en/products/cymed-rcm", destination: "/en/products/cymed-revenue-cycle", permanent: true },
      { source: "/ar/products/cymed-rcm", destination: "/ar/products/cymed-revenue-cycle", permanent: true },
      { source: "/en/products/cymed-pp", destination: "/en/products/cymed-patient-portal", permanent: true },
      { source: "/ar/products/cymed-pp", destination: "/ar/products/cymed-patient-portal", permanent: true },
      { source: "/en/products/cyshop", destination: "/en/cyshop", permanent: false },
      { source: "/ar/products/cyshop", destination: "/ar/cyshop", permanent: false },
      { source: "/en/products/cycom", destination: "/en/erp", permanent: false },
      { source: "/ar/products/cycom", destination: "/ar/erp", permanent: false },
    ];
  },
};

export default withNextIntl(nextConfig);
