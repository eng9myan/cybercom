import type { Config } from "tailwindcss";
// eslint-disable-next-line @typescript-eslint/no-require-imports
const baseConfig = require("@cybercom/config/tailwind");

const config: Config = {
  ...baseConfig,
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "../../packages/ui/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    ...baseConfig.theme,
    extend: {
      ...baseConfig.theme?.extend,
      colors: {
        ...baseConfig.theme?.extend?.colors,
        // Portal-specific semantic tokens
        "status-active": "#22c55e",
        "status-pending": "#f59e0b",
        "status-expired": "#ef4444",
        "status-critical": "#ef4444",
        "status-resolved": "#22c55e",
        "status-in-progress": "#3b82f6",
      },
      gridTemplateColumns: {
        ...baseConfig.theme?.extend?.gridTemplateColumns,
        "portal": "16rem 1fr",
        "portal-sm": "4rem 1fr",
      },
    },
  },
};

export default config;
