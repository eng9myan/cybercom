import { describe, it, expect } from "vitest";
import { cn, formatDate } from "@/lib/utils";

describe("cn utility", () => {
  it("merges class names correctly", () => {
    expect(cn("bg-red-500", "text-white")).toBe("bg-red-500 text-white");
  });

  it("handles conditional classes", () => {
    expect(cn("base", true && "active", false && "inactive")).toBe("base active");
  });

  it("deduplicates Tailwind classes (last wins)", () => {
    expect(cn("px-4", "px-6")).toBe("px-6");
  });

  it("handles undefined and null values", () => {
    expect(cn("base", undefined, null, "end")).toBe("base end");
  });
});

describe("formatDate utility", () => {
  it("formats date in English", () => {
    const result = formatDate("2026-01-15", "en");
    expect(result).toContain("2026");
    expect(result).toContain("January");
    expect(result).toContain("15");
  });

  it("formats date for Arabic locale", () => {
    const result = formatDate("2026-01-15", "ar");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });
});
