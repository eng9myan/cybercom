import type { Config } from "tailwindcss";
// eslint-disable-next-line @typescript-eslint/no-require-imports
const baseConfig = require("@cybercom/config/tailwind");

const config: Config = {
  ...baseConfig,
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx}",
    "../../packages/ui/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    ...baseConfig.theme,
    extend: {
      ...baseConfig.theme?.extend,
      typography: (theme: (path: string) => string) => ({
        docs: {
          css: {
            "--tw-prose-body": theme("colors.cy.gray-200") || "#e2e8f0",
            "--tw-prose-headings": "#ffffff",
            "--tw-prose-lead": theme("colors.cy.gray-400") || "#94a3b8",
            "--tw-prose-links": theme("colors.cy.orange") || "#ed6c00",
            "--tw-prose-bold": "#ffffff",
            "--tw-prose-counters": theme("colors.cy.gray-400") || "#94a3b8",
            "--tw-prose-bullets": theme("colors.cy.orange") || "#ed6c00",
            "--tw-prose-hr": "rgba(255,255,255,0.08)",
            "--tw-prose-quotes": theme("colors.cy.cyan") || "#59c3e1",
            "--tw-prose-quote-borders": theme("colors.cy.orange") || "#ed6c00",
            "--tw-prose-captions": theme("colors.cy.gray-400") || "#94a3b8",
            "--tw-prose-code": theme("colors.cy.cyan") || "#59c3e1",
            "--tw-prose-pre-code": "#e2e8f0",
            "--tw-prose-pre-bg": "rgba(255,255,255,0.04)",
            "--tw-prose-th-borders": "rgba(255,255,255,0.10)",
            "--tw-prose-td-borders": "rgba(255,255,255,0.06)",
            maxWidth: "none",
            lineHeight: "1.75",
            fontSize: "1rem",
            "h1, h2, h3, h4, h5, h6": {
              fontFamily: "Lexend, system-ui, sans-serif",
              fontWeight: "600",
              letterSpacing: "-0.02em",
            },
            h1: { fontSize: "2.25rem" },
            h2: { fontSize: "1.5rem", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "0.5rem" },
            h3: { fontSize: "1.25rem" },
            code: {
              fontFamily: "JetBrains Mono, Consolas, monospace",
              fontSize: "0.875em",
              padding: "0.15em 0.35em",
              borderRadius: "0.3rem",
              backgroundColor: "rgba(89,195,225,0.1)",
              fontWeight: "400",
            },
            "code::before": { content: '""' },
            "code::after": { content: '""' },
            pre: {
              fontFamily: "JetBrains Mono, Consolas, monospace",
              fontSize: "0.875rem",
              lineHeight: "1.7",
              borderRadius: "0.75rem",
              border: "1px solid rgba(255,255,255,0.08)",
              backgroundColor: "rgba(255,255,255,0.03)",
              boxShadow: "0 0 0 1px rgba(255,255,255,0.06), 0 8px 32px rgba(0,0,0,0.4)",
            },
            blockquote: {
              borderLeftColor: "#ed6c00",
              borderLeftWidth: "3px",
              backgroundColor: "rgba(237,108,0,0.05)",
              borderRadius: "0 0.5rem 0.5rem 0",
              padding: "1rem 1.25rem",
              fontStyle: "normal",
            },
            table: {
              fontSize: "0.875rem",
            },
            "thead th": {
              backgroundColor: "rgba(255,255,255,0.04)",
              fontWeight: "600",
            },
            "tbody tr:nth-child(even)": {
              backgroundColor: "rgba(255,255,255,0.02)",
            },
            "a:hover": {
              color: "#f59332",
            },
          },
        },
      }),
    },
  },
  plugins: [
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    require("@tailwindcss/typography"),
  ],
};

export default config;
