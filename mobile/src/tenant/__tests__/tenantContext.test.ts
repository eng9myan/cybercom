import { decodeJwtPayload } from "../tenantContext";

function makeFakeJwt(payload: Record<string, unknown>): string {
  const header = Buffer.from(JSON.stringify({ alg: "RS256", typ: "JWT" }))
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  const body = Buffer.from(JSON.stringify(payload))
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  return `${header}.${body}.fake-signature`;
}

describe("decodeJwtPayload", () => {
  it("decodes a base64url JWT payload without atob", () => {
    const token = makeFakeJwt({ tenant_id: "tenant-123", sub: "user-1", roles: ["customer"] });
    const claims = decodeJwtPayload(token);
    expect(claims.tenant_id).toBe("tenant-123");
    expect(claims.sub).toBe("user-1");
    expect(claims.roles).toEqual(["customer"]);
  });

  it("handles unicode (Arabic) values correctly", () => {
    const token = makeFakeJwt({ tenant_name: "مستشفى الأمل" });
    const claims = decodeJwtPayload(token);
    expect(claims.tenant_name).toBe("مستشفى الأمل");
  });

  it("returns an empty object for a malformed token", () => {
    expect(decodeJwtPayload("not-a-jwt")).toEqual({});
    expect(decodeJwtPayload("")).toEqual({});
  });

  it("returns an empty object for invalid base64 in the payload segment", () => {
    expect(decodeJwtPayload("header.###.sig")).toEqual({});
  });
});
