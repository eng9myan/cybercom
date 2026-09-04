import { describe, expect, it } from "vitest";

import ar from "./messages/ar";
import en from "./messages/en";
import { SUPPORTED_LOCALES, t } from "./index";

function flatKeys(obj: Record<string, unknown>, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === "object"
      ? flatKeys(v as Record<string, unknown>, `${prefix}${k}.`)
      : [`${prefix}${k}`],
  );
}

describe("i18n catalogs", () => {
  it("ar mirrors en key-for-key (no missing / extra keys)", () => {
    expect(flatKeys(ar).sort()).toEqual(flatKeys(en).sort());
  });

  it("every ar value is non-empty", () => {
    for (const key of flatKeys(ar)) {
      const val = key.split(".").reduce<any>((a, p) => a?.[p], ar);
      expect(typeof val === "string" && val.length > 0).toBe(true);
    }
  });

  it("SUPPORTED_LOCALES is en + ar", () => {
    expect([...SUPPORTED_LOCALES]).toEqual(["en", "ar"]);
  });
});

describe("t()", () => {
  it("resolves a dotted key", () => {
    expect(t("pos.processPayment")).toBe("Process Payment"); // jsdom localStorage empty -> en
    expect(t("common.total")).toBe("Total");
  });

  it("returns the key unchanged when missing", () => {
    expect(t("pos.nope.missing")).toBe("pos.nope.missing");
  });

  it("interpolates {vars}", () => {
    // no such key, but interpolation still runs on the fallback (the key string)
    expect(t("x {n}", { n: 5 })).toBe("x 5");
  });
});
