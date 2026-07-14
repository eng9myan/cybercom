import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.tsx"],
    exclude: ["__tests__/e2e/**", "**/node_modules/**", "**/.next/**"],
    coverage: {
      reporter: ["text", "json", "html"],
      include: ["app/**", "components/**", "lib/**"],
      exclude: ["**/*.d.ts", "**/*.config.*", "**/node_modules/**"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
