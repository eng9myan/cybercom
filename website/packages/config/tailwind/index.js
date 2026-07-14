/** @type {import('tailwindcss').Config} */
const config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "../../packages/ui/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // CyberCom Design System — Liquid Glass Dark Premium
        cy: {
          // Brand primaries
          black: "#0a0a0f",
          dark: "#0f0f1a",
          navy: "#0d1117",
          slate: "#1e293b",
          // Accent colors
          orange: "#ed6c00",
          "orange-light": "#f59332",
          "orange-dim": "#ed6c0022",
          cyan: "#59c3e1",
          "cyan-light": "#7dd3ea",
          "cyan-dim": "#59c3e115",
          // Neutral
          white: "#ffffff",
          "gray-100": "#f1f5f9",
          "gray-200": "#e2e8f0",
          "gray-400": "#94a3b8",
          "gray-600": "#475569",
          "glass-border": "rgba(255,255,255,0.08)",
          "glass-bg": "rgba(255,255,255,0.04)",
          "glass-bg-hover": "rgba(255,255,255,0.08)",
        },
        // Semantic tokens
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        heading: ["Lexend", "system-ui", "sans-serif"],
        body: ["Source Sans 3", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
        xs: ["0.75rem", { lineHeight: "1.125rem" }],
        sm: ["0.875rem", { lineHeight: "1.375rem" }],
        base: ["1rem", { lineHeight: "1.625rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.875rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.375rem" }],
        "4xl": ["2.25rem", { lineHeight: "2.75rem" }],
        "5xl": ["3rem", { lineHeight: "3.5rem" }],
        "6xl": ["3.75rem", { lineHeight: "4.25rem" }],
        "7xl": ["4.5rem", { lineHeight: "5rem" }],
        "8xl": ["6rem", { lineHeight: "6.5rem" }],
      },
      borderRadius: {
        "4xl": "2rem",
        "5xl": "2.5rem",
      },
      spacing: {
        18: "4.5rem",
        22: "5.5rem",
        30: "7.5rem",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "gradient-glass": "linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)",
        "gradient-cy": "linear-gradient(135deg, #ed6c00 0%, #59c3e1 100%)",
        "gradient-hero": "radial-gradient(ellipse 80% 80% at 50% -20%, rgba(237,108,0,0.15) 0%, transparent 60%)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "fade-up": "fadeUp 0.6s ease-out forwards",
        "slide-in": "slideIn 0.4s ease-out forwards",
        "glow-pulse": "glowPulse 3s ease-in-out infinite",
        "flow": "flow 8s linear infinite",
        "float": "float 6s ease-in-out infinite",
        "gradient-shift": "gradientShift 6s ease infinite",
        "aurora-1": "aurora1 18s ease-in-out infinite",
        "aurora-2": "aurora2 22s ease-in-out infinite",
        "aurora-3": "aurora3 26s ease-in-out infinite",
        "marquee": "marquee 32s linear infinite",
        "marquee-reverse": "marqueeReverse 32s linear infinite",
        "shimmer": "shimmer 2.4s linear infinite",
        "border-spin": "borderSpin 4s linear infinite",
        "count-up": "countUp 0.01ms linear forwards",
        "scale-in": "scaleIn 0.4s ease-out forwards",
        "slide-up": "slideUp 0.5s ease-out forwards",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        fadeUp: {
          from: { opacity: "0", transform: "translateY(24px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          from: { opacity: "0", transform: "translateX(-16px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(100%)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        scaleIn: {
          from: { opacity: "0", transform: "scale(0.92)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        glowPulse: {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.9" },
        },
        flow: {
          "0%": { strokeDashoffset: "100" },
          "100%": { strokeDashoffset: "0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
        gradientShift: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        aurora1: {
          "0%":   { transform: "translate(0%, 0%) scale(1)" },
          "33%":  { transform: "translate(8%, -12%) scale(1.15)" },
          "66%":  { transform: "translate(-6%, 8%) scale(0.9)" },
          "100%": { transform: "translate(0%, 0%) scale(1)" },
        },
        aurora2: {
          "0%":   { transform: "translate(0%, 0%) scale(1)" },
          "40%":  { transform: "translate(-10%, 6%) scale(1.1)" },
          "80%":  { transform: "translate(12%, -8%) scale(0.92)" },
          "100%": { transform: "translate(0%, 0%) scale(1)" },
        },
        aurora3: {
          "0%":   { transform: "translate(0%, 0%) scale(1)" },
          "50%":  { transform: "translate(6%, 10%) scale(1.08)" },
          "100%": { transform: "translate(0%, 0%) scale(1)" },
        },
        marquee: {
          from: { transform: "translateX(0%)" },
          to:   { transform: "translateX(-50%)" },
        },
        marqueeReverse: {
          from: { transform: "translateX(-50%)" },
          to:   { transform: "translateX(0%)" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% center" },
          "100%": { backgroundPosition: "200% center" },
        },
        borderSpin: {
          "0%":   { "--border-angle": "0deg" },
          "100%": { "--border-angle": "360deg" },
        },
        countUp: {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
      },
      boxShadow: {
        glass: "0 0 0 1px rgba(255,255,255,0.06), 0 8px 32px rgba(0,0,0,0.4)",
        "glass-hover": "0 0 0 1px rgba(255,255,255,0.12), 0 16px 48px rgba(0,0,0,0.5)",
        "orange-glow": "0 0 32px rgba(237,108,0,0.3)",
        "cyan-glow": "0 0 32px rgba(89,195,225,0.3)",
        "card-elevated": "0 4px 24px rgba(0,0,0,0.3)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

module.exports = config;
