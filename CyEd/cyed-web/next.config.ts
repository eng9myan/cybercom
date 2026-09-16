import type { NextConfig } from "next";

// The CyEd Django backend base URL. In no-Docker dev it runs on :8095
// (settings_dev, DevAuth injects the demo tenant automatically).
const nextConfig: NextConfig = {
  env: {
    CYED_BACKEND_URL: process.env.CYED_BACKEND_URL || "http://localhost:8095",
  },
};

export default nextConfig;
