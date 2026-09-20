import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server bundle (.next/standalone) so the app runs on a
  // small box with `node server.js` — no build or full node_modules there.
  output: "standalone",
  // No server-side image optimization -> no native `sharp` dependency, so a
  // Windows-built standalone runs unchanged on a Linux box.
  images: { unoptimized: true },
};

export default nextConfig;
